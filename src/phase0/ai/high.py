from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from ..llm_gateway import UnifiedLLMGateway
from ..config import AppConfig
import ast
import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable
from uuid import uuid4

from pydantic import ValidationError

from ..advisory.contracts import AdjustmentProposal
from ..advisory.governance import GovernancePlane, HighPolicySnapshot
from ..lanes.high import HighLaneSettings, evaluate_event
from ..models.signals import TradeDecision, UltraSignalEvent
from ..llm_gateway import LLMGatewaySettings, build_optional_gateway
from ..state_store import get_latest_low_analysis_state, get_runtime_state, list_open_orders, list_positions

if TYPE_CHECKING:
    from ..lanes.bus import AsyncEventBus

logger = logging.getLogger(__name__)
CloudVoteFn = Callable[[str, str], str]


@dataclass(frozen=True)
class HighAdjustmentDecision:
    approved: bool
    risk_multiplier: float
    stop_loss_pct: float
    reason: str


@dataclass(frozen=True)
class HighCommitteeVote:
    model: str
    support: bool
    score: float
    risk_multiplier: float
    stop_loss_pct: float


@dataclass(frozen=True)
class HighAssessment:
    decision: HighAdjustmentDecision
    mode: str
    committee_votes: list[HighCommitteeVote]
    prompt: str


async def start_high_engine(
    bus: AsyncEventBus,
    config: AppConfig,
    market_snapshot: dict[str, dict[str, float | str]],
) -> None:
    from ..lanes.bus import LaneEvent
    
    logger.info("Starting HighEngine Daemon...")
    queue = bus.subscribe("ultra.signal")
    
    llm_gateway = None
    if config.ai_enabled:
        settings = LLMGatewaySettings.from_app_config(config)
        llm_gateway = build_optional_gateway(settings=settings, profile=config.runtime_profile)
        if llm_gateway is None:
            logger.info("HighEngine: LLM gateway unavailable or unconfigured, continuing in placeholder mode")
    
    committee_models = [item.strip() for item in config.ai_high_committee_models.split(",") if item.strip()]
    governance_plane = GovernancePlane.from_app_config(config)
    
    try:
        while True:
            event = await queue.get()
            try:
                ultra_signal = UltraSignalEvent.model_validate(event.payload)
                symbol = ultra_signal.symbol.upper()
                logger.info("HighEngine: Received ultra signal for %s, processing...", symbol)
                low_state = get_latest_low_analysis_state(config.ai_state_db_path, symbol=symbol)
                if low_state is None:
                    unavailable_decision = _build_rejected_trade_decision(
                        symbol=symbol,
                        ultra_signal=ultra_signal,
                        stop_loss_pct=config.ai_stop_loss_default_pct,
                        reason="LOW_ANALYSIS_UNAVAILABLE",
                    )
                    decision_event = LaneEvent.from_payload(
                        event_type="decision",
                        source_lane="high",
                        payload=unavailable_decision.model_dump(mode="json"),
                    )
                    bus.publish("high.decision", decision_event)
                    continue

                analysis_payload = dict(low_state.get("analysis", {}) or {})
                low_approved = bool(analysis_payload.get("committee_approved", False))
                if not low_approved:
                    rejected = _build_rejected_trade_decision(
                        symbol=symbol,
                        ultra_signal=ultra_signal,
                        stop_loss_pct=config.ai_stop_loss_default_pct,
                        reason="LOW_COMMITTEE_REJECTED",
                    )
                    bus.publish(
                        "high.decision",
                        LaneEvent.from_payload(
                            event_type="decision",
                            source_lane="high",
                            payload=rejected.model_dump(mode="json"),
                        ),
                    )
                    continue

                assessment = await assess_high_lane_async(
                    strategy_name=str(ultra_signal.raw_data.get("strategy", ultra_signal.event_type)),
                    strategy_confidence=float(
                        ultra_signal.raw_data.get("strategy_confidence", ultra_signal.confidence_score)
                    ),
                    low_committee_approved=low_approved,
                    ultra_authenticity_score=float(
                        ultra_signal.raw_data.get("authenticity_score", ultra_signal.confidence_score)
                    ),
                    quick_filter_score=float(
                        ultra_signal.raw_data.get("quick_filter_score", ultra_signal.confidence_score)
                    ),
                    high_confidence_gate=config.ai_high_confidence_gate,
                    current_stop_loss_pct=config.ai_stop_loss_default_pct,
                    stop_loss_override_used=False,
                    default_stop_loss_pct=config.ai_stop_loss_default_pct,
                    max_stop_loss_pct=config.ai_stop_loss_break_max_pct,
                    mode=config.ai_high_mode,
                    committee_models=committee_models,
                    committee_min_support=config.ai_high_committee_min_support,
                    llm_gateway=llm_gateway,
                )
                for proposal in _build_adjustment_proposals(
                    symbol=symbol,
                    assessment=assessment,
                    config=config,
                    governance_mode=governance_plane.mode.value,
                ):
                    governance_decision = governance_plane.submit_adjustment(proposal)
                    logger.info(
                        "HighEngine governance: proposal=%s target=%s outcome=%s reason=%s",
                        proposal.proposal_id,
                        proposal.target_param,
                        governance_decision.outcome.value,
                        governance_decision.reason,
                    )

                decision_payload = _build_execution_ready_trade_decision(
                    symbol=symbol,
                    ultra_signal=ultra_signal,
                    policy_snapshot=governance_plane.current_snapshot(),
                    policy_reason=_compose_policy_reason(assessment=assessment, governance_plane=governance_plane),
                    config=config,
                    market_snapshot=market_snapshot,
                )
                decision_event = LaneEvent.from_payload(
                    event_type="decision",
                    source_lane="high",
                    payload=decision_payload.model_dump(mode="json"),
                )
                bus.publish("high.decision", decision_event)
                
            except ValidationError as exc:
                logger.error("HighEngine: Invalid event contract: %s", str(exc))
            except Exception as exc:
                logger.error("HighEngine: Error processing event: %s", str(exc))
            finally:
                queue.task_done()
    except asyncio.CancelledError:
        logger.info("HighEngine: Shutting down")
    finally:
        bus.unsubscribe("ultra.signal", queue)


def _build_execution_ready_trade_decision(
    *,
    symbol: str,
    ultra_signal: UltraSignalEvent,
    policy_snapshot: HighPolicySnapshot,
    policy_reason: str,
    config: AppConfig,
    market_snapshot: dict[str, dict[str, float | str]],
) -> TradeDecision:
    raw_data = dict(ultra_signal.raw_data or {})
    side = _normalize_side(raw_data.get("side"))
    strategy_id = _extract_strategy_id(ultra_signal)
    snapshot_id = _extract_snapshot_id(raw_data)
    snapshot_ts = _parse_optional_datetime(raw_data.get("snapshot_ts"))
    allow_opening = bool(raw_data.get("allow_opening", True))
    data_degraded = bool(raw_data.get("data_degraded", False))
    data_quality_errors = list(raw_data.get("data_quality_errors", []) or [])
    decision_time = datetime.now(tz=timezone.utc)
    risk_multiplier = float(policy_snapshot.risk_multiplier)
    stop_loss_pct = float(policy_snapshot.stop_loss_pct)

    if side is None:
        return _build_rejected_trade_decision(
            symbol=symbol,
            ultra_signal=ultra_signal,
            stop_loss_pct=stop_loss_pct,
            reason="ULTRA_SIDE_INVALID",
        )
    if strategy_id is None:
        return _build_rejected_trade_decision(
            symbol=symbol,
            ultra_signal=ultra_signal,
            stop_loss_pct=stop_loss_pct,
            reason="STRATEGY_ID_MISSING",
        )
    if snapshot_id is None or snapshot_ts is None:
        return _build_rejected_trade_decision(
            symbol=symbol,
            ultra_signal=ultra_signal,
            stop_loss_pct=stop_loss_pct,
            reason="SNAPSHOT_METADATA_MISSING",
        )

    row = dict(market_snapshot.get(symbol, {}) or {})
    entry_price = float(raw_data.get("price_current", row.get("reference_price", 0.0)) or 0.0)
    if entry_price <= 0:
        return _build_rejected_trade_decision(
            symbol=symbol,
            ultra_signal=ultra_signal,
            stop_loss_pct=stop_loss_pct,
            reason="ENTRY_PRICE_UNAVAILABLE",
        )

    runtime = get_runtime_state(config.ai_state_db_path)
    equity = float(runtime.equity or 0.0)
    if equity <= 0:
        return _build_rejected_trade_decision(
            symbol=symbol,
            ultra_signal=ultra_signal,
            stop_loss_pct=stop_loss_pct,
            reason="RUNTIME_EQUITY_UNAVAILABLE",
        )

    current_symbol_exposure = _symbol_exposure_notional(
        symbol=symbol,
        positions=list_positions(config.ai_state_db_path),
        open_orders=list_open_orders(config.ai_state_db_path),
    )
    stop_loss_price, take_profit_price = _build_price_targets(
        side=side,
        entry_price=entry_price,
        stop_loss_pct=stop_loss_pct,
    )
    high_event = {
        "lane": "ultra",
        "kind": "signal",
        "symbol": symbol,
        "side": side,
        "entry_price": f"{entry_price:.6f}",
        "stop_loss_price": f"{stop_loss_price:.6f}",
        "take_profit_price": f"{take_profit_price:.6f}",
        "equity": f"{equity:.6f}",
        "current_exposure": f"{current_symbol_exposure:.6f}",
        "current_symbol_exposure": f"{current_symbol_exposure:.6f}",
        "current_exposure_unit": "notional",
        "last_exit_at": str(raw_data.get("last_exit_at", "")),
        "position_opened_at": str(raw_data.get("position_opened_at", "")),
        "snapshot_id": snapshot_id,
        "snapshot_ts": snapshot_ts.isoformat(),
        "target_weight": str(raw_data.get("target_weight", "1.0")),
        "equity_peak": str(raw_data.get("equity_peak", equity)),
    }
    final_decision = evaluate_event(
        high_event,
        settings=HighLaneSettings.from_app_config(config),
        strategy_adjustments={
            "risk_multiplier": risk_multiplier,
            "take_profit_boost_pct": 0.0,
        },
    )
    if final_decision.get("status") != "accepted":
        reject_reasons = [str(item) for item in final_decision.get("reject_reasons", []) or []]
        return TradeDecision(
            symbol=symbol,
            approved=False,
            risk_multiplier=risk_multiplier,
            stop_loss_pct=stop_loss_pct,
            reason=reject_reasons[0] if reject_reasons else "HIGH_RULE_REJECTED",
            reject_reasons=reject_reasons or ["HIGH_RULE_REJECTED"],
            ultra_signal=ultra_signal,
            decision_ts=decision_time,
            side=side,
            strategy_id=strategy_id,
            signal_ts=ultra_signal.timestamp,
            snapshot_id=snapshot_id,
            snapshot_ts=snapshot_ts,
            allow_opening=allow_opening,
            data_degraded=data_degraded,
            data_quality_errors=data_quality_errors,
        )

    return TradeDecision(
        symbol=symbol,
        approved=True,
        risk_multiplier=risk_multiplier,
        stop_loss_pct=stop_loss_pct,
        reason=policy_reason,
        reject_reasons=[],
        ultra_signal=ultra_signal,
        decision_ts=decision_time,
        side=side,
        strategy_id=strategy_id,
        signal_ts=ultra_signal.timestamp,
        snapshot_id=snapshot_id,
        snapshot_ts=snapshot_ts,
        quantity=int(final_decision["quantity"]),
        bracket_order=dict(final_decision.get("bracket_order", {}) or {}),
        estimated_transaction_cost=dict(final_decision.get("estimated_transaction_cost", {}) or {}),
        allow_opening=allow_opening,
        data_degraded=data_degraded,
        data_quality_errors=data_quality_errors,
)


def _build_rejected_trade_decision(
    *,
    symbol: str,
    ultra_signal: UltraSignalEvent,
    stop_loss_pct: float,
    reason: str,
) -> TradeDecision:
    raw_data = dict(ultra_signal.raw_data or {})
    return TradeDecision(
        symbol=symbol,
        approved=False,
        risk_multiplier=1.0,
        stop_loss_pct=stop_loss_pct,
        reason=reason,
        reject_reasons=[reason],
        ultra_signal=ultra_signal,
        decision_ts=datetime.now(tz=timezone.utc),
        side=_normalize_side(raw_data.get("side")),
        strategy_id=_extract_strategy_id(ultra_signal),
        signal_ts=ultra_signal.timestamp,
        snapshot_id=_extract_snapshot_id(raw_data),
        snapshot_ts=_parse_optional_datetime(raw_data.get("snapshot_ts")),
        allow_opening=bool(raw_data.get("allow_opening", True)),
        data_degraded=bool(raw_data.get("data_degraded", False)),
        data_quality_errors=list(raw_data.get("data_quality_errors", []) or []),
    )


def _build_adjustment_proposals(
    *,
    symbol: str,
    assessment: HighAssessment,
    config: AppConfig,
    governance_mode: str,
) -> list[AdjustmentProposal]:
    if not assessment.decision.approved:
        return []
    proposal_scope = f"symbol:{symbol.upper()}"
    mode = governance_mode
    ttl_seconds = max(60, int(config.ai_message_max_age_minutes * 60))
    return [
        AdjustmentProposal(
            proposal_id=f"{symbol.upper()}-{uuid4().hex[:12]}-risk",
            scope=proposal_scope,
            target_param="high.risk_multiplier",
            current_value=1.0,
            suggested_value=assessment.decision.risk_multiplier,
            min_allowed=config.high_risk_multiplier_min,
            max_allowed=config.high_risk_multiplier_max,
            confidence=1.0,
            reason=assessment.decision.reason,
            evidence_refs=[f"high.assessment:{assessment.mode}"],
            ttl_seconds=ttl_seconds,
            mode=mode,
        ),
        AdjustmentProposal(
            proposal_id=f"{symbol.upper()}-{uuid4().hex[:12]}-stoploss",
            scope=proposal_scope,
            target_param="high.stop_loss_pct",
            current_value=config.ai_stop_loss_default_pct,
            suggested_value=assessment.decision.stop_loss_pct,
            min_allowed=config.ai_stop_loss_default_pct,
            max_allowed=config.ai_stop_loss_break_max_pct,
            confidence=1.0,
            reason=assessment.decision.reason,
            evidence_refs=[f"high.assessment:{assessment.mode}"],
            ttl_seconds=ttl_seconds,
            mode=mode,
        ),
    ]


def _compose_policy_reason(*, assessment: HighAssessment, governance_plane: GovernancePlane) -> str:
    snapshot = governance_plane.current_snapshot()
    if snapshot.source == "governance":
        return f"GOVERNANCE_APPLIED:{snapshot.proposal_id}"
    return f"BASELINE_POLICY:{assessment.decision.reason}"


def _extract_strategy_id(ultra_signal: UltraSignalEvent) -> str | None:
    raw_value = str(ultra_signal.raw_data.get("strategy", f"ultra_{ultra_signal.event_type}")).strip()
    return raw_value or None


def _extract_snapshot_id(raw_data: dict[str, Any]) -> str | None:
    raw_value = str(raw_data.get("snapshot_id", "")).strip()
    return raw_value or None


def _normalize_side(raw_value: object) -> str | None:
    side = str(raw_value or "").strip().lower()
    if side in {"buy", "sell"}:
        return side
    return None


def _parse_optional_datetime(raw_value: object) -> datetime | None:
    if isinstance(raw_value, datetime):
        if raw_value.tzinfo is None:
            return raw_value.replace(tzinfo=timezone.utc)
        return raw_value.astimezone(timezone.utc)
    text = str(raw_value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _build_price_targets(*, side: str, entry_price: float, stop_loss_pct: float) -> tuple[float, float]:
    if side == "sell":
        return entry_price * (1.0 + stop_loss_pct), entry_price * (1.0 - stop_loss_pct * 2.0)
    return entry_price * (1.0 - stop_loss_pct), entry_price * (1.0 + stop_loss_pct * 2.0)


def _symbol_exposure_notional(
    *,
    symbol: str,
    positions: list[dict[str, Any]],
    open_orders: list[dict[str, Any]],
) -> float:
    symbol_key = symbol.upper()
    exposure = 0.0
    avg_price = 0.0
    for item in positions:
        if str(item.get("symbol", "")).upper() != symbol_key:
            continue
        qty = abs(float(item.get("quantity", 0.0) or 0.0))
        price = abs(float(item.get("avg_price", 0.0) or 0.0))
        if price > 0:
            avg_price = price
        exposure += qty * price
    for item in open_orders:
        if str(item.get("symbol", "")).upper() != symbol_key:
            continue
        qty = abs(float(item.get("quantity", 0.0) or 0.0))
        price = abs(float(item.get("reference_price", 0.0) or 0.0))
        if price <= 0:
            price = avg_price if avg_price > 0 else 1.0
        exposure += qty * price
    return max(0.0, exposure)

def assess_high_lane(
    *,
    strategy_name: str,
    strategy_confidence: float,
    low_committee_approved: bool,
    ultra_authenticity_score: float,
    quick_filter_score: float,
    high_confidence_gate: float,
    current_stop_loss_pct: float,
    stop_loss_override_used: bool,
    default_stop_loss_pct: float,
    max_stop_loss_pct: float,
    mode: str,
    committee_models: list[str],
    committee_min_support: int,
    llm_gateway: UnifiedLLMGateway | None = None,
    cloud_vote_fn: CloudVoteFn | None = None,
) -> HighAssessment:
    return asyncio.run(
        assess_high_lane_async(
            strategy_name=strategy_name,
            strategy_confidence=strategy_confidence,
            low_committee_approved=low_committee_approved,
            ultra_authenticity_score=ultra_authenticity_score,
            quick_filter_score=quick_filter_score,
            high_confidence_gate=high_confidence_gate,
            current_stop_loss_pct=current_stop_loss_pct,
            stop_loss_override_used=stop_loss_override_used,
            default_stop_loss_pct=default_stop_loss_pct,
            max_stop_loss_pct=max_stop_loss_pct,
            mode=mode,
            committee_models=committee_models,
            committee_min_support=committee_min_support,
            llm_gateway=llm_gateway,
            cloud_vote_fn=cloud_vote_fn,
        )
    )


async def assess_high_lane_async(
    *,
    strategy_name: str,
    strategy_confidence: float,
    low_committee_approved: bool,
    ultra_authenticity_score: float,
    quick_filter_score: float,
    high_confidence_gate: float,
    current_stop_loss_pct: float,
    stop_loss_override_used: bool,
    default_stop_loss_pct: float,
    max_stop_loss_pct: float,
    mode: str,
    committee_models: list[str],
    committee_min_support: int,
    llm_gateway: UnifiedLLMGateway | None = None,
    cloud_vote_fn: CloudVoteFn | None = None,
) -> HighAssessment:
    normalized_mode = mode.strip().lower() if mode.strip() else "local"
    models = [item.strip() for item in committee_models if item.strip()] or ["local-risk-v1"]
    prompt = build_high_prompt(
        strategy_name=strategy_name,
        strategy_confidence=strategy_confidence,
        ultra_authenticity_score=ultra_authenticity_score,
        quick_filter_score=quick_filter_score,
        mode=normalized_mode,
        committee_models=models,
    )
    semaphore = asyncio.Semaphore(max(1, min(3, len(models))))

    async def _vote_one(model: str) -> HighCommitteeVote:
        async with semaphore:
            return await _single_vote_async(
                model=model,
                mode=normalized_mode,
                prompt=prompt,
                llm_gateway=llm_gateway,
                cloud_vote_fn=cloud_vote_fn,
                strategy_name=strategy_name,
                strategy_confidence=strategy_confidence,
                low_committee_approved=low_committee_approved,
                ultra_authenticity_score=ultra_authenticity_score,
                quick_filter_score=quick_filter_score,
                default_stop_loss_pct=default_stop_loss_pct,
                max_stop_loss_pct=max_stop_loss_pct,
            )

    votes = list(await asyncio.gather(*[_vote_one(model) for model in models]))
    support_count = sum(1 for vote in votes if vote.support)
    required_support = max(1, min(len(votes), committee_min_support))
    if not low_committee_approved:
        return HighAssessment(
            decision=HighAdjustmentDecision(
                approved=False,
                risk_multiplier=1.0,
                stop_loss_pct=current_stop_loss_pct,
                reason="LOW_COMMITTEE_REJECTED",
            ),
            mode=normalized_mode,
            committee_votes=votes,
            prompt=prompt,
        )
    if strategy_confidence < high_confidence_gate:
        return HighAssessment(
            decision=HighAdjustmentDecision(
                approved=False,
                risk_multiplier=1.0,
                stop_loss_pct=current_stop_loss_pct,
                reason="HIGH_CONFIDENCE_TOO_LOW",
            ),
            mode=normalized_mode,
            committee_votes=votes,
            prompt=prompt,
        )
    if support_count < required_support:
        return HighAssessment(
            decision=HighAdjustmentDecision(
                approved=False,
                risk_multiplier=1.0,
                stop_loss_pct=current_stop_loss_pct,
                reason="HIGH_COMMITTEE_REJECTED",
            ),
            mode=normalized_mode,
            committee_votes=votes,
            prompt=prompt,
        )
    avg_risk = sum(vote.risk_multiplier for vote in votes if vote.support) / max(1, support_count)
    risk_multiplier = round(max(0.8, min(1.5, avg_risk)), 4)
    if stop_loss_override_used:
        return HighAssessment(
            decision=HighAdjustmentDecision(
                approved=True,
                risk_multiplier=risk_multiplier,
                stop_loss_pct=current_stop_loss_pct,
                reason="RISK_ONLY_STOPLOSS_ALREADY_OVERRIDDEN",
            ),
            mode=normalized_mode,
            committee_votes=votes,
            prompt=prompt,
        )
    approved_stoploss = sum(vote.stop_loss_pct for vote in votes if vote.support) / max(1, support_count)
    new_stop_loss = round(max(default_stop_loss_pct, min(max_stop_loss_pct, approved_stoploss)), 4)
    return HighAssessment(
        decision=HighAdjustmentDecision(
            approved=True,
            risk_multiplier=risk_multiplier,
            stop_loss_pct=new_stop_loss,
            reason=f"APPROVED_BY_{normalized_mode.upper()}_COMMITTEE",
        ),
        mode=normalized_mode,
        committee_votes=votes,
        prompt=prompt,
    )


def build_high_prompt(
    *,
    strategy_name: str,
    strategy_confidence: float,
    ultra_authenticity_score: float,
    quick_filter_score: float,
    mode: str,
    committee_models: list[str],
) -> str:
    payload: dict[str, Any] = {
        "task": "high_lane_risk_adjustment",
        "mode": mode,
        "strategy": strategy_name,
        "strategy_confidence": round(strategy_confidence, 6),
        "ultra_authenticity_score": round(ultra_authenticity_score, 6),
        "ultra_quick_filter_score": round(quick_filter_score, 6),
        "committee_models": committee_models,
        "required_output": {
            "approve": "bool",
            "risk_multiplier": "float(0.8-1.5)",
            "stop_loss_pct": "float(default..max)",
            "reason": "short_text",
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def _single_vote(
    *,
    model: str,
    mode: str,
    prompt: str,
    llm_gateway: UnifiedLLMGateway | None,
    cloud_vote_fn: CloudVoteFn | None,
    strategy_name: str,
    strategy_confidence: float,
    low_committee_approved: bool,
    ultra_authenticity_score: float,
    quick_filter_score: float,
    default_stop_loss_pct: float,
    max_stop_loss_pct: float,
) -> HighCommitteeVote:
    return asyncio.run(
        _single_vote_async(
            model=model,
            mode=mode,
            prompt=prompt,
            llm_gateway=llm_gateway,
            cloud_vote_fn=cloud_vote_fn,
            strategy_name=strategy_name,
            strategy_confidence=strategy_confidence,
            low_committee_approved=low_committee_approved,
            ultra_authenticity_score=ultra_authenticity_score,
            quick_filter_score=quick_filter_score,
            default_stop_loss_pct=default_stop_loss_pct,
            max_stop_loss_pct=max_stop_loss_pct,
        )
    )


async def _single_vote_async(
    *,
    model: str,
    mode: str,
    prompt: str,
    llm_gateway: UnifiedLLMGateway | None,
    cloud_vote_fn: CloudVoteFn | None,
    strategy_name: str,
    strategy_confidence: float,
    low_committee_approved: bool,
    ultra_authenticity_score: float,
    quick_filter_score: float,
    default_stop_loss_pct: float,
    max_stop_loss_pct: float,
) -> HighCommitteeVote:
    if mode == "cloud" and cloud_vote_fn is not None:
        injected_vote = await _vote_with_cloud_fn_async(
            model=model,
            prompt=prompt,
            cloud_vote_fn=cloud_vote_fn,
            default_stop_loss_pct=default_stop_loss_pct,
            max_stop_loss_pct=max_stop_loss_pct,
        )
        if injected_vote is not None:
            return injected_vote
        logger.warning("High lane injected cloud vote failed for model %s, falling back", model)

    if llm_gateway is not None:
        real_vote = await _real_vote_async(
            model=model,
            prompt=prompt,
            llm_gateway=llm_gateway,
            default_stop_loss_pct=default_stop_loss_pct,
            max_stop_loss_pct=max_stop_loss_pct,
        )
        if real_vote is not None:
            return real_vote
        logger.warning("High lane real vote failed for model %s, using deterministic fallback", model)
    else:
        logger.warning("High lane vote skipped for model %s (no gateway), using deterministic fallback", model)

    return _mock_vote(
        model=model,
        strategy_name=strategy_name,
        strategy_confidence=strategy_confidence,
        low_committee_approved=low_committee_approved,
        ultra_authenticity_score=ultra_authenticity_score,
        quick_filter_score=quick_filter_score,
        default_stop_loss_pct=default_stop_loss_pct,
        max_stop_loss_pct=max_stop_loss_pct,
    )


def _real_vote(
    *,
    model: str,
    prompt: str,
    llm_gateway: UnifiedLLMGateway,
    default_stop_loss_pct: float,
    max_stop_loss_pct: float,
) -> HighCommitteeVote | None:
    return asyncio.run(
        _real_vote_async(
            model=model,
            prompt=prompt,
            llm_gateway=llm_gateway,
            default_stop_loss_pct=default_stop_loss_pct,
            max_stop_loss_pct=max_stop_loss_pct,
        )
    )


async def _real_vote_async(
    *,
    model: str,
    prompt: str,
    llm_gateway: UnifiedLLMGateway,
    default_stop_loss_pct: float,
    max_stop_loss_pct: float,
) -> HighCommitteeVote | None:
    try:
        content = await llm_gateway.async_generate(
            user_prompt=prompt,
            system_prompt="You are a senior risk manager. Evaluate the trade setup and authorize parameters. Return JSON only.",
            temperature=0.0,
            max_tokens=200,
            model=model,
        )
    except Exception as exc:
        logger.warning(f"LLM call failed for {model}: {exc}")
        return None
        
    payload = _parse_cloud_vote_payload(content)
    if payload is None:
        return None
    return _vote_from_payload(
        model=model,
        payload=payload,
        default_stop_loss_pct=default_stop_loss_pct,
        max_stop_loss_pct=max_stop_loss_pct,
    )


def _parse_cloud_vote_payload(content: str) -> dict[str, Any] | None:
    raw = str(content or "").strip()
    if not raw:
        return None
    for parser in (json.loads, ast.literal_eval):
        try:
            payload = parser(raw)
            if isinstance(payload, dict):
                return payload
        except Exception:
            continue
    return None


async def _vote_with_cloud_fn_async(
    *,
    model: str,
    prompt: str,
    cloud_vote_fn: CloudVoteFn,
    default_stop_loss_pct: float,
    max_stop_loss_pct: float,
) -> HighCommitteeVote | None:
    try:
        content = await asyncio.to_thread(cloud_vote_fn, prompt, model)
    except Exception as exc:
        logger.warning("Injected cloud vote function failed for %s: %s", model, str(exc))
        return None
    payload = _parse_cloud_vote_payload(str(content))
    if payload is None:
        return None
    return _vote_from_payload(
        model=model,
        payload=payload,
        default_stop_loss_pct=default_stop_loss_pct,
        max_stop_loss_pct=max_stop_loss_pct,
    )


def _vote_from_payload(
    *,
    model: str,
    payload: dict[str, Any],
    default_stop_loss_pct: float,
    max_stop_loss_pct: float,
) -> HighCommitteeVote:
    support = bool(payload.get("approve", payload.get("support", False)))
    score = float(payload.get("score", 0.5) or 0.5)
    risk_multiplier = float(payload.get("risk_multiplier", 1.0) or 1.0)
    stop_loss_pct = float(payload.get("stop_loss_pct", default_stop_loss_pct) or default_stop_loss_pct)
    return HighCommitteeVote(
        model=model,
        support=support,
        score=round(max(0.0, min(1.0, score)), 4),
        risk_multiplier=round(max(0.8, min(1.5, risk_multiplier)), 4),
        stop_loss_pct=round(max(default_stop_loss_pct, min(max_stop_loss_pct, stop_loss_pct)), 4),
    )


def _mock_vote(
    *,
    model: str,
    strategy_name: str,
    strategy_confidence: float,
    low_committee_approved: bool,
    ultra_authenticity_score: float,
    quick_filter_score: float,
    default_stop_loss_pct: float,
    max_stop_loss_pct: float,
) -> HighCommitteeVote:
    baseline = 0.4 + strategy_confidence * 0.5
    if low_committee_approved:
        baseline += 0.05
    baseline += (ultra_authenticity_score - 0.5) * 0.3
    baseline += (quick_filter_score - 0.5) * 0.2
    if strategy_name == "momentum":
        baseline += 0.02
    jitter = ((sum(ord(ch) for ch in model) % 9) - 4) * 0.01
    score = max(0.0, min(1.0, baseline + jitter))
    support = low_committee_approved and score >= 0.55
    risk_multiplier = max(0.8, min(1.5, 1.0 + (score - 0.5) * 0.6))
    stop_span = max(0.0, max_stop_loss_pct - default_stop_loss_pct)
    stop_loss_pct = default_stop_loss_pct + stop_span * (1.0 - score) * 0.6
    return HighCommitteeVote(
        model=model,
        support=support,
        score=round(score, 4),
        risk_multiplier=round(risk_multiplier, 4),
        stop_loss_pct=round(max(default_stop_loss_pct, min(max_stop_loss_pct, stop_loss_pct)), 4),
    )


def evaluate_high_adjustment(
    *,
    strategy_confidence: float,
    low_committee_approved: bool,
    high_confidence_gate: float,
    current_stop_loss_pct: float,
    stop_loss_override_used: bool,
    default_stop_loss_pct: float,
    max_stop_loss_pct: float,
) -> HighAdjustmentDecision:
    assessment = assess_high_lane(
        strategy_name="legacy",
        strategy_confidence=strategy_confidence,
        low_committee_approved=low_committee_approved,
        ultra_authenticity_score=0.8,
        quick_filter_score=0.7,
        high_confidence_gate=high_confidence_gate,
        current_stop_loss_pct=current_stop_loss_pct,
        stop_loss_override_used=stop_loss_override_used,
        default_stop_loss_pct=default_stop_loss_pct,
        max_stop_loss_pct=max_stop_loss_pct,
        mode="local",
        committee_models=["legacy-high"],
        committee_min_support=1,
    )
    return assessment.decision
