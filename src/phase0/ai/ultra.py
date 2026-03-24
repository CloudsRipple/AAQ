from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..config import AppConfig

if TYPE_CHECKING:
    from ..lanes.bus import AsyncEventBus
    from ..models.signals import UltraSignalEvent

logger = logging.getLogger(__name__)

_PROTOTYPE_EVENTS: list[tuple[str, str]] = [
    ("earnings_positive", "Earnings beat expectations with strong guidance and upside revisions"),
    ("earnings_negative", "Earnings miss, guidance cut, and material margin pressure reported"),
    ("executive_risk", "Executive resignation, board conflict, or internal investigation disclosed"),
    ("regulatory_pressure", "Regulatory penalty, policy crackdown, or compliance sanctions announced"),
    ("geopolitical_supply", "Geopolitical shock or supply chain disruption impacts operations"),
    ("macro_shock", "Unexpected CPI, payrolls, or rate decision creates macro shock"),
    ("liquidity_credit", "Liquidity stress, refinancing risk, or credit rating downgrade emerges"),
]


class BaseUltraSentinel(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_market_tick(
        self,
        *,
        price: float,
        volume: float,
        timestamp: datetime | None = None,
        raw_data: dict[str, Any] | None = None,
    ) -> "UltraSignalEvent" | None:
        raise NotImplementedError

    @abstractmethod
    async def on_news(
        self,
        *,
        headline: str,
        timestamp: datetime | None = None,
        raw_data: dict[str, Any] | None = None,
    ) -> "UltraSignalEvent" | None:
        raise NotImplementedError

    @abstractmethod
    async def get_signal(self, timeout_seconds: float | None = None) -> "UltraSignalEvent":
        raise NotImplementedError


class AsyncUltraSentinel(BaseUltraSentinel):
    # 后续改造点：High/Low 层的同步 llm_gateway 调用需要用 asyncio.to_thread 隔离，避免阻塞主事件循环。
    def __init__(
        self,
        *,
        symbol: str,
        config: AppConfig,
        signal_queue: asyncio.Queue[Any] | None = None,
    ) -> None:
        self._symbol = symbol.upper()
        self._queue = signal_queue or asyncio.Queue(maxsize=max(1, config.ultra_queue_maxsize))
        self._rule_window_seconds = max(5, int(config.ultra_rule_window_seconds))
        self._price_spike_threshold_pct = max(0.0, float(config.ultra_price_spike_threshold_pct))
        self._volume_zscore_threshold = max(0.0, float(config.ultra_volume_zscore_threshold))
        self._trailing_stop_break_pct = max(0.001, float(config.ultra_trailing_stop_break_pct))
        self._vector_similarity_threshold = max(0.0, min(1.0, float(config.ultra_vector_similarity_threshold)))
        self._embedding_model_name = str(config.ultra_embedding_model_name).strip() or "BAAI/bge-small-en-v1.5"
        self._store_uri = Path(config.ultra_lancedb_uri)
        self._executor_workers = max(1, int(config.ultra_executor_workers))
        self._vector_enabled = bool(config.ai_enabled and str(config.llm_base_url).strip())
        self._ticks: deque[tuple[datetime, float, float]] = deque()
        self._executor: ThreadPoolExecutor | None = None
        self._embedder: Any = None
        self._table: Any = None
        self._started = False
        self._last_rule_event_at: datetime | None = None

    async def start(self) -> None:
        if self._started:
            return
        if not self._vector_enabled:
            self._started = True
            return
        self._store_uri.mkdir(parents=True, exist_ok=True)
        self._executor = ThreadPoolExecutor(max_workers=self._executor_workers, thread_name_prefix="ultra-sentinel")
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(self._executor, self._init_vector_engine_sync)
        except Exception as exc:
            # Keep the rule-engine path available even when optional vector stack is missing.
            logger.warning(
                "Ultra sentinel vector engine unavailable for %s: %s; continuing in rule-only mode",
                self._symbol,
                str(exc),
            )
            self._embedder = None
            self._table = None
        self._started = True

    async def stop(self) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None
        self._started = False

    async def on_market_tick(
        self,
        *,
        price: float,
        volume: float,
        timestamp: datetime | None = None,
        raw_data: dict[str, Any] | None = None,
    ) -> "UltraSignalEvent" | None:
        import numpy as np

        ts = (timestamp or datetime.now(tz=timezone.utc)).astimezone(timezone.utc)
        self._ticks.append((ts, float(price), float(volume)))
        self._trim_old_ticks(now=ts)
        if len(self._ticks) < 2:
            return None
        prices = np.array([item[1] for item in self._ticks], dtype=np.float64)
        volumes = np.array([item[2] for item in self._ticks], dtype=np.float64)
        first_price = float(prices[0]) if float(prices[0]) != 0.0 else 1e-9
        current_price = float(prices[-1])
        price_change_pct = abs(current_price - float(prices[0])) / abs(first_price)
        trailing_line = float(np.max(prices) * (1.0 - self._trailing_stop_break_pct))
        break_trailing_stop = current_price < trailing_line
        volume_mean = float(np.mean(volumes))
        volume_std = float(np.std(volumes))
        volume_zscore = (float(volumes[-1]) - volume_mean) / volume_std if volume_std > 1e-9 else 0.0
        rule_event: "UltraSignalEvent" | None = None
        if price_change_pct >= self._price_spike_threshold_pct:
            confidence = min(1.0, price_change_pct / max(self._price_spike_threshold_pct, 1e-9))
            rule_event = _build_ultra_signal_event(
                symbol=self._symbol,
                timestamp=ts,
                event_type="price_spike",
                confidence_score=round(confidence, 6),
                source="rule_engine",
                matched_prototype=None,
                raw_data={
                    "price_change_pct": price_change_pct,
                    "threshold": self._price_spike_threshold_pct,
                    "window_seconds": self._rule_window_seconds,
                    "price_first": float(prices[0]),
                    "price_current": current_price,
                    **(raw_data or {}),
                },
            )
        elif volume_zscore >= self._volume_zscore_threshold:
            confidence = min(1.0, volume_zscore / max(self._volume_zscore_threshold, 1e-9))
            rule_event = _build_ultra_signal_event(
                symbol=self._symbol,
                timestamp=ts,
                event_type="volume_surge",
                confidence_score=round(confidence, 6),
                source="rule_engine",
                matched_prototype=None,
                raw_data={
                    "volume_zscore": volume_zscore,
                    "threshold": self._volume_zscore_threshold,
                    "window_seconds": self._rule_window_seconds,
                    "volume_current": float(volumes[-1]),
                    "volume_mean": volume_mean,
                    "volume_std": volume_std,
                    **(raw_data or {}),
                },
            )
        elif break_trailing_stop:
            confidence = min(1.0, (trailing_line - current_price) / max(trailing_line, 1e-9))
            rule_event = _build_ultra_signal_event(
                symbol=self._symbol,
                timestamp=ts,
                event_type="price_spike",
                confidence_score=round(confidence, 6),
                source="rule_engine",
                matched_prototype=None,
                raw_data={
                    "trailing_stop_line": trailing_line,
                    "trailing_break_pct": self._trailing_stop_break_pct,
                    "price_current": current_price,
                    "window_seconds": self._rule_window_seconds,
                    **(raw_data or {}),
                },
            )
        if rule_event is None:
            return None
        self._last_rule_event_at = ts
        await self._emit_signal(rule_event)
        return rule_event

    async def on_news(
        self,
        *,
        headline: str,
        timestamp: datetime | None = None,
        raw_data: dict[str, Any] | None = None,
    ) -> "UltraSignalEvent" | None:
        if not self._vector_enabled:
            return None
        if not headline.strip():
            return None
        if not self._started:
            await self.start()
        if self._executor is None:
            return None
        loop = asyncio.get_running_loop()
        matched = await loop.run_in_executor(self._executor, self._match_news_sync, headline.strip())
        if matched is None:
            return None
        ts = (timestamp or datetime.now(tz=timezone.utc)).astimezone(timezone.utc)
        event_type = "news_alert"
        source = "vector_match"
        confidence = matched["similarity"]
        if self._last_rule_event_at is not None:
            delta_seconds = (ts - self._last_rule_event_at).total_seconds()
            if 0.0 <= delta_seconds <= float(self._rule_window_seconds):
                event_type = "composite"
                source = "composite"
                confidence = min(1.0, confidence + 0.1)
        event = _build_ultra_signal_event(
            symbol=self._symbol,
            timestamp=ts,
            event_type=event_type,
            confidence_score=round(confidence, 6),
            source=source,
            matched_prototype=matched["prototype"],
            raw_data={
                "headline": headline.strip(),
                "vector_similarity": matched["similarity"],
                "vector_distance": matched["distance"],
                "prototype_category": matched["category"],
                "threshold": self._vector_similarity_threshold,
                **(raw_data or {}),
            },
        )
        await self._emit_signal(event)
        return event

    async def get_signal(self, timeout_seconds: float | None = None) -> "UltraSignalEvent":
        if timeout_seconds is None:
            return await self._queue.get()
        return await asyncio.wait_for(self._queue.get(), timeout=max(0.0, timeout_seconds))

    @property
    def signal_queue(self) -> asyncio.Queue[Any]:
        return self._queue

    async def _emit_signal(self, event: "UltraSignalEvent") -> None:
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            _ = self._queue.get_nowait()
            self._queue.put_nowait(event)

    def _trim_old_ticks(self, *, now: datetime) -> None:
        while self._ticks and (now - self._ticks[0][0]).total_seconds() > float(self._rule_window_seconds):
            self._ticks.popleft()

    def _init_vector_engine_sync(self) -> None:
        import lancedb
        from sentence_transformers import SentenceTransformer

        db = lancedb.connect(str(self._store_uri))
        self._embedder = SentenceTransformer(self._embedding_model_name)
        texts = [item[1] for item in _PROTOTYPE_EVENTS]
        vectors = self._embedder.encode(texts, normalize_embeddings=True).tolist()
        rows = [
            {
                "id": index,
                "category": category,
                "prototype": text,
                "vector": vector,
            }
            for index, ((category, text), vector) in enumerate(zip(_PROTOTYPE_EVENTS, vectors, strict=True), start=1)
        ]
        self._table = db.create_table("ultra_event_prototypes", data=rows, mode="overwrite")

    def _match_news_sync(self, headline: str) -> dict[str, Any] | None:
        if self._embedder is None or self._table is None:
            return None
        query_vector = self._embedder.encode([headline], normalize_embeddings=True)[0].tolist()
        results = self._table.search(query_vector).limit(1).to_list()
        if not results:
            return None
        top = dict(results[0])
        distance = float(top.get("_distance", 1.0))
        similarity = 1.0 / (1.0 + max(distance, 0.0))
        if similarity < self._vector_similarity_threshold:
            return None
        return {
            "category": str(top.get("category", "")),
            "prototype": str(top.get("prototype", "")),
            "distance": distance,
            "similarity": similarity,
        }


def build_ultra_sentinel(
    *,
    symbol: str,
    config: AppConfig,
    signal_queue: asyncio.Queue[Any] | None = None,
) -> AsyncUltraSentinel:
    return AsyncUltraSentinel(symbol=symbol, config=config, signal_queue=signal_queue)


def _build_ultra_signal_event(**kwargs: Any) -> "UltraSignalEvent":
    from ..models.signals import UltraSignalEvent

    return UltraSignalEvent(**kwargs)


@dataclass(frozen=True)
class UltraSignal:
    authenticity_score: float
    timeliness_score: float
    quick_filter_score: float
    wake_high: bool
    wake_low: bool
    reason: str
    fast_reject_reasons: list[str]


async def start_ultra_engine(
    bus: AsyncEventBus,
    config: AppConfig,
    market_snapshot: dict[str, dict[str, float | str]],
    headlines: list[dict[str, object]],
    interval_seconds: float = 1.0,
) -> None:
    from ..lanes.bus import LaneEvent
    from ..models.signals import UltraSignalEvent
    from pydantic import ValidationError
    logger = logging.getLogger(__name__)
    logger.info("Starting UltraEngine Daemon...")

    # We start one sentinel per symbol in the snapshot
    sentinels: dict[str, AsyncUltraSentinel] = {}
    for symbol in market_snapshot.keys():
        s = build_ultra_sentinel(symbol=symbol, config=config)
        await s.start()
        sentinels[symbol.upper()] = s

    # Bootstrap with initial snapshot data
    now = datetime.now(tz=timezone.utc)
    for symbol, row in market_snapshot.items():
        symbol_key = symbol.upper()
        s = sentinels[symbol_key]
        reference_price = max(1.0, float(row.get("reference_price", 100.0)))
        base_volume = max(1.0, float(row.get("volume", 1000.0)))
        await s.on_market_tick(
            price=reference_price,
            volume=base_volume,
            timestamp=now - timedelta(seconds=1),
            raw_data={"market_row": dict(row), "stage": "bootstrap"},
        )

    symbol_order = sorted(sentinels.keys())
    headline_cursor = 0
    min_publish_gap_seconds = max(1.0, float(interval_seconds))
    last_published_at: dict[str, datetime] = {}

    def _can_publish(symbol: str, ts: datetime) -> bool:
        previous = last_published_at.get(symbol)
        if previous is None:
            return True
        return (ts.astimezone(timezone.utc) - previous.astimezone(timezone.utc)).total_seconds() >= min_publish_gap_seconds

    def _publish_ultra_signal(event: UltraSignalEvent) -> None:
        symbol = event.symbol.upper()
        ts = event.timestamp.astimezone(timezone.utc)
        if not _can_publish(symbol, ts):
            return
        try:
            validated = UltraSignalEvent.model_validate(event.model_dump(mode="json"))
        except ValidationError as exc:
            logger.error("UltraEngine: ultra.signal contract validation failed: %s", str(exc))
            return
        lane_event = LaneEvent.from_payload(
            event_type="signal",
            source_lane="ultra",
            payload=validated.model_dump(mode="json"),
        )
        bus.publish("ultra.signal", lane_event)
        last_published_at[symbol] = ts

    if not sentinels:
        logger.warning("UltraEngine: no symbols available in market snapshot, idle.")

    try:
        while True:
            loop_now = datetime.now(tz=timezone.utc)
            for symbol in symbol_order:
                row = dict(market_snapshot.get(symbol, {}) or {})
                reference_price = max(1.0, float(row.get("reference_price", 100.0)))
                base_volume = max(1.0, float(row.get("volume", 1000.0)))
                momentum = abs(float(row.get("momentum_20d", 0.0)))
                price_drift = max(config.ultra_price_spike_threshold_pct * 1.05, momentum)
                tick_price = reference_price * (1.0 + price_drift)
                tick_event = await sentinels[symbol].on_market_tick(
                    price=tick_price,
                    volume=base_volume * 1.05,
                    timestamp=loop_now,
                    raw_data={
                        "market_row": row,
                        "price_current": tick_price,
                        "price_reference": reference_price,
                        "strategy": "ultra_event",
                        "strategy_confidence": max(0.3, min(1.0, price_drift * 10.0)),
                        "quick_filter_score": max(0.2, min(1.0, 0.35 + price_drift * 8.0)),
                        "snapshot_id": str(row.get("snapshot_id", "runtime_snapshot")),
                        "snapshot_ts": str(row.get("snapshot_ts", loop_now.isoformat())),
                        "allow_opening": True,
                        "data_degraded": False,
                    },
                )
                if tick_event is not None:
                    _publish_ultra_signal(tick_event)

            if headlines and sentinels:
                item = dict(headlines[headline_cursor % len(headlines)] or {})
                headline_cursor += 1
                raw_symbol = str(item.get("symbol", symbol_order[0])).upper()
                symbol = raw_symbol if raw_symbol in sentinels else symbol_order[0]
                headline = str(item.get("headline", "")).strip()
                published_at = item.get("published_at", loop_now)
                news_event = await sentinels[symbol].on_news(
                    headline=headline,
                    timestamp=published_at if isinstance(published_at, datetime) else loop_now,
                    raw_data={
                        "headline": headline,
                        "strategy": str(item.get("strategy", "ultra_news")),
                        "strategy_confidence": float(item.get("confidence", 0.7) or 0.7),
                        "quick_filter_score": float(item.get("quick_filter_score", 0.6) or 0.6),
                        "snapshot_id": str(item.get("snapshot_id", "runtime_snapshot")),
                        "snapshot_ts": str(item.get("snapshot_ts", loop_now.isoformat())),
                        "allow_opening": bool(item.get("allow_opening", True)),
                        "data_degraded": bool(item.get("data_degraded", False)),
                    },
                )
                if news_event is not None:
                    _publish_ultra_signal(news_event)

            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        logger.info("UltraEngine: Shutting down")
    except Exception as exc:
        logger.error(f"UltraEngine: Error during execution: {exc}")
    finally:
        for s in sentinels.values():
            await s.stop()

def evaluate_ultra_guard(
    headline: str,
    published_at: datetime,
    now: datetime,
    max_age_minutes: int,
    market_row: dict[str, float | str] | None = None,
    min_local_quick_score: float = 0.26,
) -> UltraSignal:
    # 兼容层：保持旧版同步评估接口，避免在未改主链路阶段破坏现有调用。
    text = headline.lower()
    suspicious_hits = sum(text.count(word) for word in ("rumor", "unverified", "clickbait", "fake"))
    authenticity = max(0.0, 0.9 - suspicious_hits * 0.25)
    age_minutes = max(0.0, (now.astimezone(timezone.utc) - published_at.astimezone(timezone.utc)).total_seconds() / 60)
    timeliness = max(0.0, 1.0 - age_minutes / max(1, max_age_minutes))
    row = market_row or {}
    momentum = max(0.0, float(row.get("momentum_20d", 0.0)))
    relative_strength = max(0.0, float(row.get("relative_strength", 0.0)))
    liquidity = max(0.0, min(1.0, float(row.get("liquidity_score", 0.6))))
    volatility = max(0.01, float(row.get("volatility", 0.25)))
    quick_filter_score = max(
        0.0,
        min(
            1.0,
            momentum * 2.5 + relative_strength * 1.4 + liquidity * 0.35 - min(0.45, volatility * 0.5),
        ),
    )
    fast_reject_reasons: list[str] = []
    if quick_filter_score < min_local_quick_score:
        fast_reject_reasons.append("LOCAL_QUICK_FILTER_WEAK")
    if volatility > 0.42:
        fast_reject_reasons.append("LOCAL_VOLATILITY_TOO_HIGH")
    credibility_ok = authenticity >= 0.55 and timeliness >= 0.35
    wake = credibility_ok and not fast_reject_reasons
    reason = "VERIFIED_AND_TIMELY"
    if not credibility_ok:
        reason = "LOW_CREDIBILITY_OR_STALE"
    elif fast_reject_reasons:
        reason = "LOCAL_QUICK_FILTER_BLOCKED"
    return UltraSignal(
        authenticity_score=round(authenticity, 4),
        timeliness_score=round(timeliness, 4),
        quick_filter_score=round(quick_filter_score, 4),
        wake_high=wake,
        wake_low=(wake or timeliness >= 0.2) and "LOCAL_VOLATILITY_TOO_HIGH" not in fast_reject_reasons,
        reason=reason,
        fast_reject_reasons=fast_reject_reasons,
    )
