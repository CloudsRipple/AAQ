from __future__ import annotations

import asyncio
from dataclasses import dataclass


from ..llm_gateway import UnifiedLLMGateway
from ..config import AppConfig
from datetime import datetime, timezone
import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..lanes.bus import AsyncEventBus

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommitteeVote:
    model: str
    support: bool
    score: float


@dataclass(frozen=True)
class LowAnalysis:
    preferred_sector: str
    strategy_fit: dict[str, float]
    sector_allocation: dict[str, float]
    committee_votes: list[CommitteeVote]
    committee_approved: bool


async def start_low_engine(
    bus: AsyncEventBus,
    config: AppConfig,
    market_snapshot: dict[str, dict[str, float | str]],
    interval_seconds: float = 3600.0,
) -> None:
    logger.info("Starting LowEngine Daemon...")
    llm_gateway = None
    if config.ai_enabled:
        from ..llm_gateway import LLMGatewaySettings
        settings = LLMGatewaySettings.from_app_config(config)
        llm_gateway = UnifiedLLMGateway(settings=settings, profile=config.runtime_profile)
    
    committee_models = [item.strip() for item in config.ai_low_committee_models.split(",") if item.strip()]

    while True:
        try:
            logger.info("LowEngine: Running periodic AI evaluation")
            analysis = await analyze_low_lane_async(
                market_snapshot=market_snapshot,
                committee_models=committee_models[:3],
                committee_min_support=config.ai_low_committee_min_support,
                strategy_name="periodic_macro",
                strategy_confidence=1.0,
                llm_gateway=llm_gateway,
            )
            # You would save this analysis to a state store here.
            # Currently we publish it to the bus to mimic old behavior
            output = {
                "lane": "low",
                "symbol": "MACRO",
                "preferred_sector": analysis.preferred_sector,
                "strategy_fit": analysis.strategy_fit,
                "sector_allocation": analysis.sector_allocation,
                "committee_approved": analysis.committee_approved,
                "committee_votes": [
                    {"model": vote.model, "support": vote.support, "score": vote.score}
                    for vote in analysis.committee_votes
                ],
                "analyzed_at": datetime.now(tz=timezone.utc).isoformat(),
            }
            from ..lanes.bus import LaneEvent
            low_event = LaneEvent.from_payload(event_type="analysis", source_lane="low", payload=output)
            bus.publish("low.analysis", low_event)

        except asyncio.CancelledError:
            logger.info("LowEngine: Shutting down")
            break
        except Exception as exc:
            logger.error(f"LowEngine: Error during evaluation: {exc}")
        
        await asyncio.sleep(interval_seconds)


def analyze_low_lane(
    *,
    market_snapshot: dict[str, dict[str, float | str]],
    committee_models: list[str],
    committee_min_support: int,
    strategy_name: str,
    strategy_confidence: float,
    llm_gateway: UnifiedLLMGateway | None = None,
    headlines: list[str] | None = None,
) -> LowAnalysis:
    return _analyze_low_lane_core(
        market_snapshot=market_snapshot,
        committee_models=committee_models,
        committee_min_support=committee_min_support,
        strategy_name=strategy_name,
        strategy_confidence=strategy_confidence,
        llm_gateway=llm_gateway,
        headlines=headlines,
        votes_resolver=_committee_vote,
    )


async def analyze_low_lane_async(
    *,
    market_snapshot: dict[str, dict[str, float | str]],
    committee_models: list[str],
    committee_min_support: int,
    strategy_name: str,
    strategy_confidence: float,
    llm_gateway: UnifiedLLMGateway | None = None,
    headlines: list[str] | None = None,
) -> LowAnalysis:
    return await _analyze_low_lane_core_async(
        market_snapshot=market_snapshot,
        committee_models=committee_models,
        committee_min_support=committee_min_support,
        strategy_name=strategy_name,
        strategy_confidence=strategy_confidence,
        llm_gateway=llm_gateway,
        headlines=headlines,
    )


def _analyze_low_lane_core(
    *,
    market_snapshot: dict[str, dict[str, float | str]],
    committee_models: list[str],
    committee_min_support: int,
    strategy_name: str,
    strategy_confidence: float,
    llm_gateway: UnifiedLLMGateway | None,
    headlines: list[str] | None,
    votes_resolver: Any,
) -> LowAnalysis:
    sector_strength: dict[str, float] = {}
    for payload in market_snapshot.values():
        sector = str(payload.get("sector", "other"))
        momentum = float(payload.get("momentum_20d", 0.0))
        rel_strength = float(payload.get("relative_strength", 0.0))
        sector_strength[sector] = sector_strength.get(sector, 0.0) + momentum * 0.55 + rel_strength * 0.45
    preferred_sector = max(sector_strength.items(), key=lambda item: item[1])[0] if sector_strength else "other"
    total = sum(max(0.0, score) for score in sector_strength.values()) or 1.0
    allocation = {k: round(max(0.0, v) / total, 4) for k, v in sector_strength.items()}
    votes = _committee_vote(
        committee_models=committee_models,
        strategy_name=strategy_name,
        strategy_confidence=strategy_confidence,
        preferred_sector=preferred_sector,
        llm_gateway=llm_gateway,
        market_snapshot=market_snapshot,
        headlines=headlines or [],
    )
    support_count = sum(1 for vote in votes if vote.support)
    strategy_fit = {
        "momentum": 0.74 if preferred_sector == "technology" else 0.61,
        "mean_reversion": 0.66,
        "sector_rotation": 0.79,
        "news_sentiment": 0.71,
    }
    return LowAnalysis(
        preferred_sector=preferred_sector,
        strategy_fit=strategy_fit,
        sector_allocation=allocation,
        committee_votes=votes,
        committee_approved=support_count >= committee_min_support,
    )


async def _analyze_low_lane_core_async(
    *,
    market_snapshot: dict[str, dict[str, float | str]],
    committee_models: list[str],
    committee_min_support: int,
    strategy_name: str,
    strategy_confidence: float,
    llm_gateway: UnifiedLLMGateway | None,
    headlines: list[str] | None,
) -> LowAnalysis:
    sector_strength: dict[str, float] = {}
    for payload in market_snapshot.values():
        sector = str(payload.get("sector", "other"))
        momentum = float(payload.get("momentum_20d", 0.0))
        rel_strength = float(payload.get("relative_strength", 0.0))
        sector_strength[sector] = sector_strength.get(sector, 0.0) + momentum * 0.55 + rel_strength * 0.45
    preferred_sector = max(sector_strength.items(), key=lambda item: item[1])[0] if sector_strength else "other"
    total = sum(max(0.0, score) for score in sector_strength.values()) or 1.0
    allocation = {k: round(max(0.0, v) / total, 4) for k, v in sector_strength.items()}
    votes = await _committee_vote_async(
        committee_models=committee_models,
        strategy_name=strategy_name,
        strategy_confidence=strategy_confidence,
        preferred_sector=preferred_sector,
        llm_gateway=llm_gateway,
        market_snapshot=market_snapshot,
        headlines=headlines or [],
    )
    support_count = sum(1 for vote in votes if vote.support)
    strategy_fit = {
        "momentum": 0.74 if preferred_sector == "technology" else 0.61,
        "mean_reversion": 0.66,
        "sector_rotation": 0.79,
        "news_sentiment": 0.71,
    }
    return LowAnalysis(
        preferred_sector=preferred_sector,
        strategy_fit=strategy_fit,
        sector_allocation=allocation,
        committee_votes=votes,
        committee_approved=support_count >= committee_min_support,
    )


def _committee_vote(
    *,
    committee_models: list[str],
    strategy_name: str,
    strategy_confidence: float,
    preferred_sector: str,
    llm_gateway: UnifiedLLMGateway | None = None,
    market_snapshot: dict[str, dict[str, float | str]] | None = None,
    headlines: list[str] | None = None,
) -> list[CommitteeVote]:
    votes: list[CommitteeVote] = []
    
    # If gateway is available, perform real AI voting
    if llm_gateway is not None:
        prompt = _build_low_prompt(
            strategy_name=strategy_name,
            strategy_confidence=strategy_confidence,
            preferred_sector=preferred_sector,
            market_snapshot=market_snapshot or {},
            headlines=headlines or [],
        )
        for model in committee_models:
            try:
                content = llm_gateway.generate(
                    user_prompt=prompt,
                    system_prompt="You are a senior investment committee member. Analyze the market context and strategy fit. Return JSON only.",
                    temperature=0.2,
                    max_tokens=200,
                    model=model,
                )
                payload = _parse_low_vote_payload(content)
                if payload:
                    votes.append(CommitteeVote(
                        model=model,
                        support=bool(payload.get("approve", False)),
                        score=float(payload.get("score", 0.0))
                    ))
                else:
                    logger.warning("Low lane vote failed for model %s: invalid JSON, using deterministic fallback", model)
                    votes.append(_mock_vote(model, strategy_name, strategy_confidence, preferred_sector))
            except Exception as exc:
                logger.warning("Low lane vote failed for model %s: %s; using deterministic fallback", model, str(exc))
                votes.append(_mock_vote(model, strategy_name, strategy_confidence, preferred_sector))
        return votes

    logger.warning("Low lane voting skipped (no gateway), using deterministic fallback")
    for model in committee_models:
        votes.append(_mock_vote(model, strategy_name, strategy_confidence, preferred_sector))
    return votes


async def _committee_vote_async(
    *,
    committee_models: list[str],
    strategy_name: str,
    strategy_confidence: float,
    preferred_sector: str,
    llm_gateway: UnifiedLLMGateway | None = None,
    market_snapshot: dict[str, dict[str, float | str]] | None = None,
    headlines: list[str] | None = None,
) -> list[CommitteeVote]:
    votes: list[CommitteeVote] = []
    if llm_gateway is not None:
        prompt = _build_low_prompt(
            strategy_name=strategy_name,
            strategy_confidence=strategy_confidence,
            preferred_sector=preferred_sector,
            market_snapshot=market_snapshot or {},
            headlines=headlines or [],
        )
        semaphore = asyncio.Semaphore(max(1, min(3, len(committee_models))))

        async def _vote_one(model: str) -> CommitteeVote:
            async with semaphore:
                try:
                    content = await llm_gateway.async_generate(
                        user_prompt=prompt,
                        system_prompt="You are a senior investment committee member. Analyze the market context and strategy fit. Return JSON only.",
                        temperature=0.2,
                        max_tokens=200,
                        model=model,
                    )
                    payload = _parse_low_vote_payload(content)
                    if payload:
                        return CommitteeVote(
                            model=model,
                            support=bool(payload.get("approve", False)),
                            score=float(payload.get("score", 0.0)),
                        )
                    logger.warning("Low lane vote failed for model %s: invalid JSON, using deterministic fallback", model)
                except Exception as exc:
                    logger.warning("Low lane vote failed for model %s: %s; using deterministic fallback", model, str(exc))
                return _mock_vote(model, strategy_name, strategy_confidence, preferred_sector)

        return list(await asyncio.gather(*[_vote_one(model) for model in committee_models]))
    
    logger.warning("Low lane voting skipped (no gateway), using deterministic fallback")
    for model in committee_models:
        votes.append(_mock_vote(model, strategy_name, strategy_confidence, preferred_sector))
    return votes


def _mock_vote(model: str, strategy_name: str, strategy_confidence: float, preferred_sector: str) -> CommitteeVote:
    baseline = 0.35 + strategy_confidence * 0.5
    if strategy_name == "sector_rotation":
        baseline += 0.08
    if preferred_sector == "technology":
        baseline += 0.04
    jitter = ((sum(ord(ch) for ch in model) % 7) - 3) * 0.015
    score = max(0.0, min(1.0, baseline + jitter))
    return CommitteeVote(model=model, support=score >= 0.55, score=round(score, 4))


def _build_low_prompt(
    strategy_name: str,
    strategy_confidence: float,
    preferred_sector: str,
    market_snapshot: dict[str, Any],
    headlines: list[str],
) -> str:
    # Summarize market state for prompt compactness
    snapshot_summary = {
        k: {
            "mom20d": v.get("momentum_20d"),
            "rsi": v.get("relative_strength"),
            "price": v.get("reference_price")
        } 
        for k, v in list(market_snapshot.items())[:5]
    }
    
    payload = {
        "task": "low_lane_strategy_approval",
        "strategy": strategy_name,
        "confidence": round(strategy_confidence, 4),
        "sector_bias": preferred_sector,
        "market_sample": snapshot_summary,
        "news_sample": headlines[:3] if headlines else [],
        "required_output": {
            "approve": "bool",
            "score": "float(0.0-1.0)",
            "reason": "short_text"
        }
    }
    return json.dumps(payload, ensure_ascii=False)


def _parse_low_vote_payload(content: str) -> dict[str, Any] | None:
    try:
        clean = content.strip()
        if clean.startswith("```json"):
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif clean.startswith("```"):
            clean = clean.split("```")[1].split("```")[0].strip()
        return json.loads(clean)
    except Exception:
        return None
