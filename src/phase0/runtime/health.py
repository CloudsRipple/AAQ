from __future__ import annotations

from dataclasses import asdict
import os
import socket
from typing import Callable

from ..config import AppConfig
from ..kernel.coordinator import run_guarded_coordinator_cycle
from ..llm_gateway import LLMGatewaySettings, build_optional_gateway
from ..observability import log_event
from ..runtime_budget import build_runtime_budget
from ..safety import assess_safety


def health_check(
    config: AppConfig,
    *,
    socket_check: Callable[[str, int, float], bool] | None = None,
    drawdown_reader: Callable[[], float] | None = None,
    llm_connectivity_check: Callable[[AppConfig], bool] | None = None,
) -> dict[str, str]:
    runtime_budget = build_runtime_budget(config)
    socket_probe = socket_check or _check_socket
    read_drawdown = drawdown_reader or _read_current_drawdown_pct
    check_llm = llm_connectivity_check or _check_llm_connectivity
    ibkr_reachable = socket_probe(
        config.ibkr_host,
        config.ibkr_port,
        runtime_budget.ibkr_socket_timeout_seconds,
    )
    current_drawdown_pct = read_drawdown()
    llm_reachable = check_llm(config)
    safety = assess_safety(
        ibkr_reachable=ibkr_reachable,
        llm_reachable=llm_reachable,
        max_drawdown_breached=current_drawdown_pct >= config.risk_max_drawdown_pct,
    )
    lane_result = run_guarded_coordinator_cycle(
        "AAPL",
        config=config,
        allow_risk_execution=safety.allows_risk_execution,
    )
    event = lane_result["event"]
    decisions = lane_result["decisions"]
    watchlist = lane_result["watchlist"]
    first_decision_lane = str(decisions[0]["lane"]) if decisions else "none"
    first_decision_status = str(decisions[0]["status"]) if decisions else "none"

    summary = {
        "profile": config.runtime_profile.value,
        "runtime_mode": config.runtime_mode.value,
        "safety_mode": safety.mode.value,
        "safety_reason": safety.reason,
        "ibkr": "reachable" if ibkr_reachable else "unreachable",
        "llm": _llm_status_label(config=config, llm_reachable=llm_reachable),
        "event_lane": event["lane"],
        "execution_lane": first_decision_lane,
        "execution_status": first_decision_status,
        "risk_execution_enabled": str(safety.allows_risk_execution).lower(),
        "machine_profile": runtime_budget.machine_profile,
        "lane_loop_interval_ms": str(runtime_budget.lane_loop_interval_ms),
        "llm_max_parallel_requests": str(runtime_budget.llm_max_parallel_requests),
        "watchlist_size": str(len(watchlist)),
        "current_drawdown_pct": str(round(current_drawdown_pct, 6)),
    }
    log_event("health_check_finished", summary=summary)
    return summary


def _check_socket(host: str, port: int, timeout_seconds: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


def _read_current_drawdown_pct() -> float:
    raw = os.getenv("CURRENT_DRAWDOWN_PCT", "0")
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.0


def _check_llm_connectivity(config: AppConfig) -> bool | None:
    if not config.ai_enabled:
        return None
    settings = LLMGatewaySettings.from_app_config(config)
    gateway = build_optional_gateway(settings=settings, profile=config.runtime_profile)
    if gateway is None:
        return None
    try:
        outcome = gateway.check_connectivity()
        return bool(outcome.get("ok", False))
    except Exception:
        return False


def _llm_status_label(*, config: AppConfig, llm_reachable: bool | None) -> str:
    if not config.ai_enabled:
        return "disabled"
    if llm_reachable is None:
        return "placeholder"
    return "reachable" if llm_reachable else "unreachable"


def config_snapshot(config: AppConfig) -> dict[str, str]:
    payload = asdict(config)
    payload["runtime_profile"] = config.runtime_profile.value
    payload["runtime_mode"] = config.runtime_mode.value
    payload["llm_api_key"] = "***"
    return {k: str(v) for k, v in payload.items()}


__all__ = [
    "config_snapshot",
    "health_check",
]
