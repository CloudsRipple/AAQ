from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SafetyMode(str, Enum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    LOCKDOWN = "lockdown"


@dataclass(frozen=True)
class SafetyState:
    mode: SafetyMode
    reason: str

    @property
    def allows_risk_execution(self) -> bool:
        return self.mode != SafetyMode.LOCKDOWN


def assess_safety(
    *,
    ibkr_reachable: bool,
    llm_reachable: bool | None = None,
    max_drawdown_breached: bool = False,
) -> SafetyState:
    if not ibkr_reachable:
        return SafetyState(mode=SafetyMode.LOCKDOWN, reason="IBKR_UNREACHABLE")
    if max_drawdown_breached:
        return SafetyState(mode=SafetyMode.LOCKDOWN, reason="MAX_DRAWDOWN_BREACHED")
    if llm_reachable is False:
        return SafetyState(mode=SafetyMode.DEGRADED, reason="LLM_UNREACHABLE")
    return SafetyState(mode=SafetyMode.NORMAL, reason="ALL_SYSTEMS_READY")
