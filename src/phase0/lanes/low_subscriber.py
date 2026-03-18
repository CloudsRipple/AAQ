from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from ..ai import LowAnalysis, analyze_low_lane, analyze_low_lane_async
from .bus import InMemoryLaneBus, LaneEvent
from .low_engine import LOW_ANALYSIS_CACHE, get_cached_low_analysis

LOW_SUBSCRIBER_ID = "low_subscriber"


def consume_high_decisions_and_publish_low_analysis(
    *,
    bus: InMemoryLaneBus,
    market_snapshot: dict[str, dict[str, float | str]],
    committee_models: list[str],
    committee_min_support: int,
) -> list[dict[str, object]]:
    analyses: list[dict[str, object]] = []
    decisions = bus.consume_for("high.decision", LOW_SUBSCRIBER_ID)
    for item in decisions:
        payload = item.payload
        symbol = str(payload.get("symbol", "")).upper()
        
        analysis = get_cached_low_analysis(symbol)
        if analysis is None:
            strategy_name = str(payload.get("strategy", "none"))
            strategy_confidence = float(payload.get("strategy_confidence", 0.0))
            analysis = analyze_low_lane(
                market_snapshot=market_snapshot,
                committee_models=committee_models[:3],
                committee_min_support=committee_min_support,
                strategy_name=strategy_name,
                strategy_confidence=strategy_confidence,
            )
            if symbol:
                LOW_ANALYSIS_CACHE[symbol] = analysis
                
        output = {
            "lane": "low",
            "symbol": symbol,
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
        analyses.append(output)
        low_event = LaneEvent.from_payload(event_type="analysis", source_lane="low", payload=output)
        bus.publish("low.analysis", low_event)
    return analyses


async def consume_high_decisions_and_publish_low_analysis_async(
    *,
    bus: InMemoryLaneBus,
    market_snapshot: dict[str, dict[str, float | str]],
    committee_models: list[str],
    committee_min_support: int,
) -> list[dict[str, object]]:
    analyses: list[dict[str, object]] = []
    if hasattr(bus, "aconsume_for"):
        decisions = await bus.aconsume_for("high.decision", LOW_SUBSCRIBER_ID)
    else:
        decisions = await asyncio.to_thread(bus.consume_for, "high.decision", LOW_SUBSCRIBER_ID)
    for item in decisions:
        payload = item.payload
        symbol = str(payload.get("symbol", "")).upper()
        
        analysis = get_cached_low_analysis(symbol)
        if analysis is None:
            strategy_name = str(payload.get("strategy", "none"))
            strategy_confidence = float(payload.get("strategy_confidence", 0.0))
            analysis = await analyze_low_lane_async(
                market_snapshot=market_snapshot,
                committee_models=committee_models[:3],
                committee_min_support=committee_min_support,
                strategy_name=strategy_name,
                strategy_confidence=strategy_confidence,
            )
            if symbol:
                LOW_ANALYSIS_CACHE[symbol] = analysis
                
        output = {
            "lane": "low",
            "symbol": symbol,
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
        analyses.append(output)
        low_event = LaneEvent.from_payload(event_type="analysis", source_lane="low", payload=output)
        if hasattr(bus, "apublish"):
            await bus.apublish("low.analysis", low_event)
        else:
            await asyncio.to_thread(bus.publish, "low.analysis", low_event)
    return analyses
