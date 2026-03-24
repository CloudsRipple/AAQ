from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import json
import logging
import math
import queue
import threading

from ..ai import (
    MemoryRecord,
    PersistentLayeredMemoryStore,
    analyze_low_lane,
    analyze_low_lane_async,
    assess_high_lane,
    assess_high_lane_async,
    build_ultra_sentinel,
    evaluate_ultra_guard,
)
from ..audit import (
    ParameterAuditEntry,
    is_stoploss_override_used,
    mark_stoploss_override_used,
    write_parameter_audit,
)
from ..config import AppConfig
from ..discipline import build_daily_discipline_plan, evaluate_hold_worthiness
from ..ibkr_order_adapter import map_decision_to_ibkr_bracket
from ..llm_gateway import LLMGatewaySettings, build_optional_gateway
from ..market_data import compute_snapshot_id, load_market_snapshot_with_gate
from ..strategies import StrategyContext, run_strategies
from .bus import AsyncEventBus, InMemoryLaneBus, LaneEvent
from .high import HighLaneSettings, evaluate_event
from .low import build_watchlist, build_watchlist_with_rotation
from .low_subscriber import (
    consume_high_decisions_and_publish_low_analysis,
    consume_high_decisions_and_publish_low_analysis_async,
    get_cached_low_analysis,
)
from .ultra import emit_event

logger = logging.getLogger(__name__)


async def run_lane_cycle_async(
    symbol: str,
    config: AppConfig,
    bus: InMemoryLaneBus | None = None,
    seed_event: dict[str, str] | None = None,
    market_snapshot: dict[str, dict[str, float | str]] | None = None,
    headlines: list[str] | None = None,
    daily_state: dict[str, object] | None = None,
) -> dict[str, object]:
    now = datetime.now(tz=timezone.utc)
    ai_enabled = config.ai_enabled
    runtime_daily_state = daily_state or {}
    active_bus = bus or InMemoryLaneBus(dedup_capacity=max(256, config.lane_bus_dedup_ttl_seconds))
    if market_snapshot is not None:
        snapshot = market_snapshot
        snapshot_ts = now.isoformat()
        snapshot_id = compute_snapshot_id(snapshot=snapshot, source="injected", snapshot_ts=snapshot_ts)
        data_gate = {
            "ok": bool(snapshot),
            "allow_trading": bool(snapshot),
            "allow_opening": bool(snapshot),
            "degraded": not bool(snapshot),
            "source_primary": "injected",
            "source_used": "injected",
            "blocked_reasons": [] if snapshot else ["SNAPSHOT_EMPTY"],
            "snapshot": snapshot,
            "snapshot_id": snapshot_id,
            "snapshot_ts": snapshot_ts,
            "quality": {"ok": bool(snapshot), "errors": [] if snapshot else ["SNAPSHOT_EMPTY"]},
            "calendar": {},
        }
    else:
        data_gate = load_market_snapshot_with_gate(config=config, now_utc=now)
        snapshot = dict(data_gate.get("snapshot", {}) or {})
    data_allow_trading = bool(data_gate.get("allow_trading", True))
    watchlist = build_watchlist_with_rotation(snapshot, top_k=config.strategy_rotation_top_k)
    headline_entries = _normalize_headlines(headlines, now=now)
    context = StrategyContext(
        watchlist=watchlist,
        market_snapshot=snapshot,
        headlines=[item["headline"] for item in headline_entries],
        news_positive_threshold=config.strategy_news_positive_threshold,
        news_negative_threshold=config.strategy_news_negative_threshold,
        rotation_top_k=config.strategy_rotation_top_k,
    )
    enabled = _parse_enabled_strategies(config.strategy_enabled_list)
    strategy_signals = run_strategies(
        enabled,
        context,
        strategy_plugin_modules=config.strategy_plugin_modules,
        factor_plugin_modules=config.factor_plugin_modules,
    )
    signal_weights = _normalize_signal_weights(
        strategy_signals,
        temperature=max(0.1, config.risk_exposure_softmax_temperature),
    )
    chosen = strategy_signals[0] if strategy_signals else None
    selected_symbol = str(getattr(chosen, "symbol", symbol)).upper()
    selected_market_row = snapshot.get(selected_symbol, {})
    lead_headline = headline_entries[0]
    if ai_enabled:
        settings = LLMGatewaySettings.from_app_config(config)
        llm_gateway = build_optional_gateway(settings=settings, profile=config.runtime_profile)
        if llm_gateway is None:
            logger.info("Lane cycle: LLM gateway unavailable or unconfigured, continuing in placeholder mode")
        
        ultra = await _build_ultra_signal_snapshot(
            symbol=selected_symbol,
            config=config,
            lead_headline=lead_headline,
            market_row=selected_market_row,
            now=now,
            max_age_minutes=config.ai_message_max_age_minutes,
        )
    else:
        llm_gateway = None
        ultra = _non_ai_ultra_signal()
    committee_models = [item.strip() for item in config.ai_low_committee_models.split(",") if item.strip()]
    if ai_enabled:
        cached_low_analysis = get_cached_low_analysis(str(getattr(chosen, "symbol", symbol)))
        low_analysis = cached_low_analysis or await analyze_low_lane_async(
            market_snapshot=snapshot,
            committee_models=committee_models[:3],
            committee_min_support=config.ai_low_committee_min_support,
            strategy_name=str(getattr(chosen, "strategy", "none")),
            strategy_confidence=float(getattr(chosen, "confidence", 0.0)),
            llm_gateway=llm_gateway,
            headlines=[item["headline"] for item in headline_entries],
        )
        memory_store = PersistentLayeredMemoryStore(config.ai_memory_db_path, _default_memory_records(now))
        memory_context = memory_store.query(
            query_text=f'{getattr(chosen, "symbol", symbol)} {" ".join(context.headlines)}',
            now=now,
            limit=3,
        )
    else:
        low_analysis = _non_ai_low_analysis()
        memory_context = []
    if seed_event is not None:
        raw_event = dict(seed_event)
    else:
        raw_event = _build_strategy_event(
            symbol,
            chosen,
            context.market_snapshot,
            default_stop_loss_pct=config.ai_stop_loss_default_pct,
        )
    raw_event["snapshot_id"] = str(data_gate.get("snapshot_id", ""))
    raw_event["snapshot_ts"] = str(data_gate.get("snapshot_ts", now.isoformat()))
    raw_event["data_source"] = str(data_gate.get("source_used", "unknown"))
    allow_from_event = not _is_risk_execution_blocked(raw_event.get("allow_risk_execution", "true"))
    raw_event["allow_risk_execution"] = "true" if (allow_from_event and data_allow_trading) else "false"
    selected_weight = signal_weights.get(
        str(getattr(chosen, "strategy", "")),
        1.0 if chosen is not None else 1.0,
    )
    raw_event["target_weight"] = f"{selected_weight:.6f}"
    raw_event["current_exposure_unit"] = "notional"
    raw_event["equity_peak"] = str(runtime_daily_state.get("equity_peak", raw_event.get("equity", "100000")))
    stop_ratio = _current_stop_loss_pct(raw_event)
    symbol_key = str(raw_event.get("symbol", symbol))
    if ai_enabled:
        high_assessment = await assess_high_lane_async(
            strategy_name=str(getattr(chosen, "strategy", "none")),
            strategy_confidence=float(getattr(chosen, "confidence", 0.0)),
            low_committee_approved=low_analysis.committee_approved and ultra.wake_low and ultra.wake_high,
            ultra_authenticity_score=float(getattr(ultra, "authenticity_score", 0.0)),
            quick_filter_score=float(getattr(ultra, "quick_filter_score", 0.0)),
            high_confidence_gate=config.ai_high_confidence_gate,
            current_stop_loss_pct=stop_ratio,
            stop_loss_override_used=is_stoploss_override_used(config.ai_state_db_path, symbol_key),
            default_stop_loss_pct=config.ai_stop_loss_default_pct,
            max_stop_loss_pct=config.ai_stop_loss_break_max_pct,
            mode=config.ai_high_mode,
            committee_models=[item.strip() for item in config.ai_high_committee_models.split(",") if item.strip()],
            committee_min_support=config.ai_high_committee_min_support,
            llm_gateway=llm_gateway,
        )
        high_adjustment = high_assessment.decision
        if high_adjustment.approved and high_adjustment.stop_loss_pct > stop_ratio:
            _apply_stop_loss_pct(raw_event, high_adjustment.stop_loss_pct)
            mark_stoploss_override_used(
                config.ai_state_db_path,
                symbol_key,
                ttl_hours=config.ai_stoploss_override_ttl_hours,
            )
        write_parameter_audit(
            config.ai_state_db_path,
            ParameterAuditEntry(
                ts=now.isoformat(),
                symbol=symbol_key,
                strategy=str(getattr(chosen, "strategy", "none")),
                approved=high_adjustment.approved,
                reason=high_adjustment.reason,
                before_stop_loss_pct=round(stop_ratio, 6),
                after_stop_loss_pct=round(_current_stop_loss_pct(raw_event), 6),
                before_risk_multiplier=1.0,
                after_risk_multiplier=high_adjustment.risk_multiplier if high_adjustment.approved else 1.0,
                low_committee_approved=low_analysis.committee_approved,
                ultra_wake_high=ultra.wake_high,
            ),
        )
    else:
        high_adjustment = _non_ai_high_adjustment(stop_ratio)
        high_assessment = _non_ai_high_assessment()
    signal_event = LaneEvent.from_payload(event_type="signal", source_lane="ultra", payload=raw_event)
    await active_bus.apublish("ultra.signal", signal_event)
    signals = await active_bus.aconsume("ultra.signal")
    high_settings = HighLaneSettings.from_app_config(config)
    decisions: list[dict[str, object]] = []
    for event in signals:
        if _is_risk_execution_blocked(event.payload.get("allow_risk_execution", "true")):
            decision = {
                "lane": "high",
                "status": "rejected",
                "symbol": event.payload.get("symbol", ""),
                "reject_reasons": ["SAFETY_MODE_BLOCKED"],
            }
        else:
            adjustments = _extract_adjustments(chosen)
            adjustments["risk_multiplier"] = min(
                adjustments["risk_multiplier"],
                high_adjustment.risk_multiplier if high_adjustment.approved else 1.0,
            )
            decision = evaluate_event(event.payload, settings=high_settings, strategy_adjustments=adjustments)
            if chosen is not None:
                decision["strategy"] = chosen.strategy
                decision["strategy_score"] = round(chosen.score, 4)
                decision["strategy_confidence"] = round(chosen.confidence, 4)
                decision["strategy_rationale"] = chosen.rationale
                decision["strategy_id"] = chosen.strategy
            else:
                decision["strategy_id"] = "unknown"
            decision["signal_ts"] = event.emitted_at
            decision["side"] = str(event.payload.get("side", "buy")).lower()
            decision["ultra_authenticity_score"] = ultra.authenticity_score
            decision["ultra_timeliness_score"] = ultra.timeliness_score
            decision["low_committee_approved"] = low_analysis.committee_approved
            decision["high_adjustment_reason"] = high_adjustment.reason
            decision["snapshot_id"] = str(event.payload.get("snapshot_id", ""))
            decision["snapshot_ts"] = str(event.payload.get("snapshot_ts", ""))
            decision["stop_loss_override_used"] = (
                is_stoploss_override_used(config.ai_state_db_path, event.payload.get("symbol", symbol))
                if ai_enabled
                else False
            )
        decision_event = LaneEvent.from_payload(event_type="decision", source_lane="high", payload=decision)
        await active_bus.apublish("high.decision", decision_event)
        decisions.append(decision)
    if ai_enabled:
        low_async_results = await consume_high_decisions_and_publish_low_analysis_async(
            bus=active_bus,
            market_snapshot=snapshot,
            committee_models=committee_models[:3],
            committee_min_support=config.ai_low_committee_min_support,
        )
        low_analysis_events = await active_bus.aconsume("low.analysis")
    else:
        low_async_results = []
        low_analysis_events = []
    hold_market_row = snapshot.get(selected_symbol, {})
    hold = evaluate_hold_worthiness(
        market_row=hold_market_row,
        strategy_confidence=float(getattr(chosen, "confidence", 0.0)),
        ultra_authenticity_score=float(getattr(ultra, "authenticity_score", 1.0)),
        low_committee_approved=bool(getattr(low_analysis, "committee_approved", True)),
        hold_score_threshold=config.discipline_hold_score_threshold,
        max_holding_days=max(1, config.holding_days),
    )
    actions_today = int(runtime_daily_state.get("actions_today", len(decisions)))
    has_open_position = bool(runtime_daily_state.get("has_open_position", False))
    daily_plan = build_daily_discipline_plan(
        actions_today=actions_today,
        has_open_position=has_open_position,
        min_actions_per_day=max(0, config.discipline_min_actions_per_day),
        discipline_enabled=config.discipline_enable_daily_cycle,
        hold=hold,
    )
    disciplined_decisions = [_apply_discipline_gate(item, daily_plan) for item in decisions]
    disciplined_ibkr_signals: list[dict[str, object]] = []
    for item in disciplined_decisions:
        mapped = map_decision_to_ibkr_bracket(item)
        if mapped is not None:
            disciplined_ibkr_signals.append(mapped)
    return {
        "event": raw_event,
        "decisions": disciplined_decisions,
        "watchlist": watchlist,
        "ultra_signal": {
            "authenticity_score": ultra.authenticity_score,
            "timeliness_score": ultra.timeliness_score,
            "quick_filter_score": ultra.quick_filter_score,
            "wake_high": ultra.wake_high,
            "wake_low": ultra.wake_low,
            "reason": ultra.reason,
            "fast_reject_reasons": ultra.fast_reject_reasons,
        },
        "low_analysis": {
            "preferred_sector": low_analysis.preferred_sector,
            "strategy_fit": low_analysis.strategy_fit,
            "sector_allocation": low_analysis.sector_allocation,
            "committee_approved": low_analysis.committee_approved,
            "committee_votes": [
                {"model": vote.model, "support": vote.support, "score": vote.score}
                for vote in low_analysis.committee_votes
            ],
        },
        "low_async_analysis": [event.payload for event in low_analysis_events],
        "low_async_processed": len(low_async_results),
        "memory_context": [
            {
                "memory_id": item.memory_id,
                "tier": item.tier,
                "score": item.score,
                "text": item.text,
                "published_at": item.published_at,
            }
            for item in memory_context
        ],
        "strategy_signals": [_signal_to_dict(signal) for signal in strategy_signals],
        "published_events": len(signals) + len(disciplined_decisions) + len(low_analysis_events),
        "ai_bypassed": not ai_enabled,
        "daily_discipline": daily_plan,
        "high_assessment": {
            "mode": high_assessment.mode,
            "prompt": high_assessment.prompt,
            "committee_votes": [
                {
                    "model": vote.model,
                    "support": vote.support,
                    "score": vote.score,
                    "risk_multiplier": vote.risk_multiplier,
                    "stop_loss_pct": vote.stop_loss_pct,
                }
                for vote in high_assessment.committee_votes
            ],
        },
        "data_quality_gate": {
            "allow_trading": data_allow_trading,
            "allow_opening": bool(data_gate.get("allow_opening", data_allow_trading)),
            "degraded": bool(data_gate.get("degraded", False)),
            "blocked_reasons": list(data_gate.get("blocked_reasons", []) or []),
            "snapshot_id": str(data_gate.get("snapshot_id", "")),
            "snapshot_ts": str(data_gate.get("snapshot_ts", "")),
            "source_used": str(data_gate.get("source_used", "")),
            "source_primary": str(data_gate.get("source_primary", "")),
            "quality": dict(data_gate.get("quality", {}) or {}),
            "calendar": dict(data_gate.get("calendar", {}) or {}),
        },
        "ibkr_order_signals": disciplined_ibkr_signals,
    }


def run_lane_cycle(
    symbol: str,
    config: AppConfig,
    bus: InMemoryLaneBus | None = None,
    seed_event: dict[str, str] | None = None,
    market_snapshot: dict[str, dict[str, float | str]] | None = None,
    headlines: list[str] | None = None,
    daily_state: dict[str, object] | None = None,
) -> dict[str, object]:
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None
    coroutine = run_lane_cycle_async(
        symbol=symbol,
        config=config,
        bus=bus,
        seed_event=seed_event,
        market_snapshot=market_snapshot,
        headlines=headlines,
        daily_state=daily_state,
    )
    if running_loop is None or not running_loop.is_running():
        return asyncio.run(coroutine)
    return _run_coroutine_in_thread(coroutine)


def run_lane_cycle_with_guard(
    symbol: str,
    config: AppConfig,
    allow_risk_execution: bool,
    bus: InMemoryLaneBus | None = None,
) -> dict[str, object]:
    raw_event = emit_event(symbol)
    raw_event["allow_risk_execution"] = "true" if allow_risk_execution else "false"
    return run_lane_cycle(symbol=symbol, config=config, bus=bus, seed_event=raw_event)


def _run_coroutine_in_thread(coroutine: object) -> dict[str, object]:
    result_queue: queue.Queue[tuple[str, object]] = queue.Queue(maxsize=1)

    def _target() -> None:
        try:
            result = asyncio.run(coroutine)  # type: ignore[arg-type]
            result_queue.put(("ok", result))
        except BaseException as exc:
            result_queue.put(("error", exc))

    worker = threading.Thread(target=_target, daemon=True)
    worker.start()
    status, payload = result_queue.get()
    worker.join()
    if status == "error":
        raise payload  # type: ignore[misc]
    return payload  # type: ignore[return-value]


class _UltraSignalSnapshot:
    def __init__(
        self,
        *,
        authenticity_score: float,
        timeliness_score: float,
        quick_filter_score: float,
        wake_high: bool,
        wake_low: bool,
        reason: str,
        fast_reject_reasons: list[str],
    ) -> None:
        self.authenticity_score = authenticity_score
        self.timeliness_score = timeliness_score
        self.quick_filter_score = quick_filter_score
        self.wake_high = wake_high
        self.wake_low = wake_low
        self.reason = reason
        self.fast_reject_reasons = fast_reject_reasons


async def _build_ultra_signal_snapshot(
    *,
    symbol: str,
    config: AppConfig,
    lead_headline: dict[str, object],
    market_row: dict[str, float | str],
    now: datetime,
    max_age_minutes: int,
) -> _UltraSignalSnapshot:
    sentinel = build_ultra_sentinel(symbol=symbol, config=config)
    event = None
    try:
        await sentinel.start()
        reference_price = max(1.0, float(market_row.get("reference_price", 100.0)))
        momentum = float(market_row.get("momentum_20d", 0.0))
        base_volume = max(1.0, float(market_row.get("volume", 1000.0)))
        await sentinel.on_market_tick(
            price=reference_price,
            volume=base_volume,
            timestamp=now - timedelta(seconds=1),
            raw_data={"market_row": dict(market_row), "stage": "bootstrap"},
        )
        tick_event = await sentinel.on_market_tick(
            price=reference_price * (1.0 + momentum),
            volume=base_volume * 1.5,
            timestamp=now,
            raw_data={"market_row": dict(market_row), "stage": "realtime"},
        )
        news_event = await sentinel.on_news(
            headline=str(lead_headline.get("headline", "")),
            timestamp=lead_headline.get("published_at", now),
            raw_data={"market_row": dict(market_row)},
        )
        event = news_event or tick_event
        if event is None:
            try:
                event = await sentinel.get_signal(timeout_seconds=0.01)
            except TimeoutError:
                event = None
    except Exception as exc:
        fallback = evaluate_ultra_guard(
            headline=str(lead_headline.get("headline", "")),
            published_at=lead_headline.get("published_at", now),
            now=now,
            max_age_minutes=max_age_minutes,
            market_row=market_row,
        )
        reasons = list(fallback.fast_reject_reasons)
        reasons.append(f"ULTRA_ASYNC_FALLBACK:{exc.__class__.__name__}")
        return _UltraSignalSnapshot(
            authenticity_score=fallback.authenticity_score,
            timeliness_score=fallback.timeliness_score,
            quick_filter_score=fallback.quick_filter_score,
            wake_high=fallback.wake_high,
            wake_low=fallback.wake_low,
            reason=fallback.reason,
            fast_reject_reasons=reasons,
        )
    finally:
        await sentinel.stop()
    if event is None:
        return _UltraSignalSnapshot(
            authenticity_score=0.0,
            timeliness_score=0.0,
            quick_filter_score=0.0,
            wake_high=False,
            wake_low=False,
            reason="NO_ULTRA_SIGNAL",
            fast_reject_reasons=["NO_ULTRA_SIGNAL"],
        )
    event_ts = event.timestamp.astimezone(timezone.utc)
    age_minutes = max(0.0, (now.astimezone(timezone.utc) - event_ts).total_seconds() / 60.0)
    timeliness = max(0.0, 1.0 - age_minutes / max(1, max_age_minutes))
    confidence = max(0.0, min(1.0, float(event.confidence_score)))
    quick_filter = confidence if event.source != "vector_match" else confidence * 0.85
    wake_high = confidence >= 0.55 and timeliness >= 0.35
    wake_low = confidence >= 0.3 and timeliness >= 0.2
    fast_reject_reasons: list[str] = []
    if not wake_high:
        fast_reject_reasons.append("ULTRA_CONFIDENCE_OR_TIMELINESS_LOW")
    return _UltraSignalSnapshot(
        authenticity_score=round(confidence, 4),
        timeliness_score=round(timeliness, 4),
        quick_filter_score=round(max(0.0, min(1.0, quick_filter)), 4),
        wake_high=wake_high,
        wake_low=wake_low,
        reason=f"{event.source}:{event.event_type}",
        fast_reject_reasons=fast_reject_reasons,
    )


def _parse_enabled_strategies(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _extract_adjustments(chosen: object | None) -> dict[str, float]:
    if chosen is None:
        return {"risk_multiplier": 1.0, "take_profit_boost_pct": 0.0}
    signal = chosen
    return {
        "risk_multiplier": float(getattr(signal, "risk_multiplier", 1.0)),
        "take_profit_boost_pct": float(getattr(signal, "take_profit_boost_pct", 0.0)),
    }


def _build_strategy_event(
    fallback_symbol: str,
    chosen: object | None,
    snapshot: dict[str, dict[str, float]],
    default_stop_loss_pct: float,
) -> dict[str, str]:
    symbol = fallback_symbol.upper()
    side = "buy"
    if chosen is not None:
        symbol = str(getattr(chosen, "symbol", symbol)).upper()
        side = str(getattr(chosen, "side", side)).lower()
    row = snapshot.get(symbol, {})
    ref_price = max(1.0, float(row.get("reference_price", 100.0)))
    stop_ratio = max(default_stop_loss_pct, min(0.08, float(row.get("stop_ratio", default_stop_loss_pct))))
    tp_ratio = max(0.06, min(0.2, float(row.get("take_profit_ratio", 0.1))))
    if side == "sell":
        stop_price = ref_price * (1 + stop_ratio)
        take_profit = ref_price * (1 - tp_ratio)
    else:
        stop_price = ref_price * (1 - stop_ratio)
        take_profit = ref_price * (1 + tp_ratio)
    overrides = {
        "side": side,
        "entry_price": f"{ref_price:.4f}",
        "stop_loss_price": f"{stop_price:.4f}",
        "take_profit_price": f"{take_profit:.4f}",
    }
    return emit_event(symbol, overrides=overrides)


def _signal_to_dict(signal: object) -> dict[str, object]:
    return {
        "strategy": str(getattr(signal, "strategy", "")),
        "symbol": str(getattr(signal, "symbol", "")),
        "side": str(getattr(signal, "side", "")),
        "score": round(float(getattr(signal, "score", 0.0)), 4),
        "confidence": round(float(getattr(signal, "confidence", 0.0)), 4),
        "rationale": str(getattr(signal, "rationale", "")),
    }


def _default_market_snapshot() -> dict[str, dict[str, float | str]]:
    return {
        "AAPL": {
            "momentum_20d": 0.08,
            "z_score_5d": -0.6,
            "relative_strength": 0.26,
            "volatility": 0.22,
            "reference_price": 180.0,
            "sector": "technology",
        },
        "MSFT": {
            "momentum_20d": 0.07,
            "z_score_5d": 0.8,
            "relative_strength": 0.21,
            "volatility": 0.19,
            "reference_price": 420.0,
            "sector": "technology",
        },
        "NVDA": {
            "momentum_20d": 0.14,
            "z_score_5d": 1.4,
            "relative_strength": 0.33,
            "volatility": 0.34,
            "reference_price": 950.0,
            "sector": "technology",
        },
        "XOM": {
            "momentum_20d": 0.05,
            "z_score_5d": -1.3,
            "relative_strength": 0.18,
            "volatility": 0.18,
            "reference_price": 115.0,
            "sector": "energy",
        },
    }


def _default_headlines() -> list[str]:
    return [
        "Tech earnings beat estimates and growth outlook remains strong",
        "Analysts upgrade semiconductor leaders after breakout results",
    ]


class _NonAIUltraSignal:
    def __init__(self) -> None:
        self.authenticity_score = 1.0
        self.timeliness_score = 1.0
        self.quick_filter_score = 1.0
        self.wake_high = True
        self.wake_low = True
        self.reason = "AI_BYPASSED"
        self.fast_reject_reasons = []


class _NonAILowAnalysis:
    def __init__(self) -> None:
        self.preferred_sector = "bypassed"
        self.strategy_fit = {}
        self.sector_allocation = {}
        self.committee_approved = True
        self.committee_votes = []


class _NonAIHighAdjustment:
    def __init__(self, stop_loss_pct: float) -> None:
        self.approved = False
        self.risk_multiplier = 1.0
        self.stop_loss_pct = stop_loss_pct
        self.reason = "AI_BYPASSED"


class _NonAIHighAssessment:
    def __init__(self) -> None:
        self.mode = "bypassed"
        self.prompt = "{}"
        self.committee_votes: list[object] = []


def _non_ai_ultra_signal() -> _NonAIUltraSignal:
    return _NonAIUltraSignal()


def _non_ai_low_analysis() -> _NonAILowAnalysis:
    return _NonAILowAnalysis()


def _non_ai_high_adjustment(stop_loss_pct: float) -> _NonAIHighAdjustment:
    return _NonAIHighAdjustment(stop_loss_pct=stop_loss_pct)


def _non_ai_high_assessment() -> _NonAIHighAssessment:
    return _NonAIHighAssessment()


def _normalize_headlines(headlines: list[str] | None, now: datetime) -> list[dict[str, object]]:
    if not headlines:
        return _default_headline_entries(now)
    return [{"headline": text, "published_at": now - timedelta(minutes=30)} for text in headlines]


def _default_headline_entries(now: datetime) -> list[dict[str, object]]:
    return [
        {
            "headline": "消费电子需求修复，供应链订单环比走强",
            "published_at": now - timedelta(minutes=45),
        },
        {
            "headline": "半导体设备龙头获上调评级并公布强劲指引",
            "published_at": now - timedelta(hours=2),
        },
    ]


def _default_memory_records(now: datetime) -> list[MemoryRecord]:
    return [
        MemoryRecord(
            memory_id="mem-short-1",
            tier="short",
            text="一天前消费电子行业周报提到小米手机和可穿戴需求回暖。",
            published_at=now - timedelta(days=1),
            tags=("小米", "消费电子", "需求"),
        ),
        MemoryRecord(
            memory_id="mem-long-1",
            tier="long",
            text="一个月前上游芯片与模组供应链价格下行，改善硬件毛利。",
            published_at=now - timedelta(days=30),
            tags=("小米", "供应链", "芯片"),
        ),
        MemoryRecord(
            memory_id="mem-rel-1",
            tier="relational",
            text="小米与消费电子渠道补库存节奏同步，板块相关性较高。",
            published_at=now - timedelta(days=6),
            tags=("小米", "渠道", "消费电子"),
        ),
        MemoryRecord(
            memory_id="mem-noise-1",
            tier="short",
            text="一小时前麦当劳新品营销活动。",
            published_at=now - timedelta(hours=1),
            tags=("餐饮", "麦当劳"),
        ),
        MemoryRecord(
            memory_id="mem-noise-2",
            tier="long",
            text="半年前国际油价波动与石油库存变化。",
            published_at=now - timedelta(days=180),
            tags=("石油", "能源"),
        ),
    ]


def _current_stop_loss_pct(event: dict[str, str]) -> float:
    side = event.get("side", "buy").lower()
    entry = float(event.get("entry_price", "100"))
    stop = float(event.get("stop_loss_price", "98"))
    if side == "sell":
        return max(0.0, (stop - entry) / entry)
    return max(0.0, (entry - stop) / entry)


def _apply_stop_loss_pct(event: dict[str, str], stop_loss_pct: float) -> None:
    side = event.get("side", "buy").lower()
    entry = float(event.get("entry_price", "100"))
    if side == "sell":
        stop = entry * (1 + stop_loss_pct)
    else:
        stop = entry * (1 - stop_loss_pct)
    event["stop_loss_price"] = f"{stop:.4f}"


def _is_risk_execution_blocked(raw_value: object) -> bool:
    if isinstance(raw_value, bool):
        return not raw_value
    return str(raw_value).strip().lower() in {"0", "false", "no", "off"}


def _apply_discipline_gate(decision: dict[str, object], daily_plan: dict[str, object]) -> dict[str, object]:
    if decision.get("status") != "accepted":
        return decision
    required_action = str(daily_plan.get("required_action", "none"))
    side = str(decision.get("bracket_order", {}).get("parent", {}).get("action", "")).upper()
    if required_action == "hold":
        return _discipline_reject(decision, "DISCIPLINE_HOLD_REQUIRED")
    if required_action == "sell" and side == "BUY":
        return _discipline_reject(decision, "DISCIPLINE_SELL_PRIORITY")
    return decision


def _discipline_reject(decision: dict[str, object], reason: str) -> dict[str, object]:
    rejected = dict(decision)
    rejected["status"] = "rejected"
    rejected["bracket_order"] = {}
    reasons = list(rejected.get("reject_reasons", []))
    reasons.append(reason)
    rejected["reject_reasons"] = reasons
    return rejected


def _normalize_signal_weights(strategy_signals: list[object], temperature: float) -> dict[str, float]:
    if not strategy_signals:
        return {}
    temp = max(0.1, temperature)
    score_pairs: list[tuple[str, float]] = []
    for item in strategy_signals:
        key = str(getattr(item, "strategy", "unknown"))
        score = float(getattr(item, "score", 0.0)) * max(0.01, float(getattr(item, "confidence", 0.0)))
        score_pairs.append((key, score))
    max_score = max(score for _, score in score_pairs)
    exps: list[tuple[str, float]] = []
    for key, score in score_pairs:
        exps.append((key, math.exp((score - max_score) / temp)))
    total = sum(value for _, value in exps) or 1.0
    weights: dict[str, float] = {}
    for key, value in exps:
        weights[key] = weights.get(key, 0.0) + value / total
    return weights


def _load_market_snapshot(config: AppConfig) -> dict[str, dict[str, float | str]]:
    if config.market_snapshot_json:
        loaded = _load_market_snapshot_from_json_env(config.market_snapshot_json)
        if loaded:
            return loaded
        logger.warning("market snapshot json provided but invalid or empty, fallback to runtime source")
    if config.market_data_mode == "live":
        live = _load_market_snapshot_from_yfinance(config.market_symbols)
        if live:
            return live
        logger.warning("live market data unavailable, fallback to default snapshot")
    return _default_market_snapshot()


def _load_market_snapshot_from_json_env(raw_json: str) -> dict[str, dict[str, float | str]]:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        logger.warning("market snapshot json parse failed: %s", str(exc))
        return {}
    if not isinstance(payload, dict):
        logger.warning("market snapshot json payload is not object")
        return {}
    normalized: dict[str, dict[str, float | str]] = {}
    for symbol, row in payload.items():
        if not isinstance(row, dict):
            continue
        normalized[str(symbol).upper()] = dict(row)
    return normalized


def _load_market_snapshot_from_yfinance(raw_symbols: str) -> dict[str, dict[str, float | str]]:
    symbols = [item.strip().upper() for item in raw_symbols.split(",") if item.strip()]
    if not symbols:
        return {}
    try:
        import yfinance as yf
    except Exception as exc:
        logger.warning("yfinance import failed: %s", str(exc))
        return {}
    snapshot: dict[str, dict[str, float | str]] = {}
    for symbol in symbols:
        try:
            history = yf.Ticker(symbol).history(period="3mo", interval="1d")
            if history.empty or len(history) < 25:
                continue
            closes = history["Close"].dropna()
            if len(closes) < 25:
                continue
            ref_price = float(closes.iloc[-1])
            momentum_20d = (ref_price - float(closes.iloc[-21])) / max(1e-6, float(closes.iloc[-21]))
            returns = closes.pct_change().dropna()
            volatility = float(returns.tail(20).std()) if len(returns) >= 20 else 0.2
            mean_5 = float(closes.tail(5).mean())
            std_20 = float(closes.tail(20).std()) if len(closes) >= 20 else 1.0
            z_score_5d = (ref_price - mean_5) / max(1e-6, std_20)
            snapshot[symbol] = {
                "momentum_20d": round(momentum_20d, 6),
                "z_score_5d": round(z_score_5d, 6),
                "relative_strength": round(max(0.0, momentum_20d), 6),
                "volatility": round(max(0.01, volatility), 6),
                "reference_price": round(ref_price, 6),
                "liquidity_score": 0.8,
                "sector": "unknown",
            }
        except Exception as exc:
            logger.warning("yfinance load failed for %s: %s", symbol, str(exc))
            continue
    return snapshot


__all__ = [
    "emit_event",
    "evaluate_event",
    "build_watchlist",
    "HighLaneSettings",
    "LaneEvent",
    "InMemoryLaneBus",
    "AsyncEventBus",
    "run_lane_cycle",
    "run_lane_cycle_with_guard",
]
