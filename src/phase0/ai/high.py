from __future__ import annotations

import asyncio
from ..llm_gateway import UnifiedLLMGateway
from ..config import AppConfig
import ast
import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

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
    from ..lanes.low_subscriber import get_cached_low_analysis
    
    logger.info("Starting HighEngine Daemon...")
    queue = bus.subscribe("ultra.signal")
    
    llm_gateway = None
    if config.ai_enabled:
        from ..llm_gateway import LLMGatewaySettings
        settings = LLMGatewaySettings.from_app_config(config)
        llm_gateway = UnifiedLLMGateway(settings=settings, profile=config.runtime_profile)
    
    committee_models = [item.strip() for item in config.ai_high_committee_models.split(",") if item.strip()]
    
    try:
        while True:
            event = await queue.get()
            try:
                payload = event.payload
                symbol = payload.get("symbol", "")
                
                logger.info(f"HighEngine: Received ultra signal for {symbol}, processing...")
                
                low_analysis = get_cached_low_analysis(symbol)
                low_approved = getattr(low_analysis, "committee_approved", False) if low_analysis else False

                assessment = await assess_high_lane_async(
                    strategy_name=str(payload.get("strategy", "unknown")),
                    strategy_confidence=float(payload.get("confidence", 0.8)),
                    low_committee_approved=low_approved,
                    ultra_authenticity_score=float(payload.get("authenticity_score", 1.0)),
                    quick_filter_score=float(payload.get("quick_filter_score", 1.0)),
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
                
                decision_payload = {
                    "symbol": symbol,
                    "approved": assessment.decision.approved,
                    "risk_multiplier": assessment.decision.risk_multiplier,
                    "stop_loss_pct": assessment.decision.stop_loss_pct,
                    "reason": assessment.decision.reason,
                    "ultra_signal": payload,
                }
                decision_event = LaneEvent.from_payload(event_type="decision", source_lane="high", payload=decision_payload)
                bus.publish("high.decision", decision_event)
                
            except Exception as e:
                logger.error(f"HighEngine: Error processing event: {e}")
            finally:
                queue.task_done()
    except asyncio.CancelledError:
        logger.info("HighEngine: Shutting down")
    finally:
        bus.unsubscribe("ultra.signal", queue)

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
