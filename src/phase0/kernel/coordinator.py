from __future__ import annotations

from ..config import AppConfig
from ..lanes import InMemoryLaneBus, run_lane_cycle, run_lane_cycle_with_guard


def run_coordinator_cycle(
    symbol: str,
    config: AppConfig,
    bus: InMemoryLaneBus | None = None,
    seed_event: dict[str, str] | None = None,
    market_snapshot: dict[str, dict[str, float | str]] | None = None,
    headlines: list[str] | None = None,
    daily_state: dict[str, object] | None = None,
) -> dict[str, object]:
    # Transitional coordinator wrapper so callers stop binding to lanes/__init__.py directly.
    return run_lane_cycle(
        symbol=symbol,
        config=config,
        bus=bus,
        seed_event=seed_event,
        market_snapshot=market_snapshot,
        headlines=headlines,
        daily_state=daily_state,
    )


def run_guarded_coordinator_cycle(
    symbol: str,
    config: AppConfig,
    allow_risk_execution: bool,
    bus: InMemoryLaneBus | None = None,
) -> dict[str, object]:
    return run_lane_cycle_with_guard(
        symbol=symbol,
        config=config,
        allow_risk_execution=allow_risk_execution,
        bus=bus,
    )


__all__ = [
    "run_coordinator_cycle",
    "run_guarded_coordinator_cycle",
]
