from __future__ import annotations

from dataclasses import asdict
import os
import socket

from .config import AppConfig
from .lanes import run_lane_cycle_with_guard
from .llm_gateway import LLMGatewaySettings, UnifiedLLMGateway
from .observability import log_event
from .runtime_budget import build_runtime_budget
from .safety import assess_safety


def health_check(config: AppConfig) -> dict[str, str]:
    runtime_budget = build_runtime_budget(config)
    ibkr_reachable = _check_socket(
        config.ibkr_host,
        config.ibkr_port,
        timeout_seconds=runtime_budget.ibkr_socket_timeout_seconds,
    )
    current_drawdown_pct = _read_current_drawdown_pct()
    llm_reachable = _check_llm_connectivity(config)
    safety = assess_safety(
        ibkr_reachable=ibkr_reachable,
        llm_reachable=llm_reachable,
        max_drawdown_breached=current_drawdown_pct >= config.risk_max_drawdown_pct,
    )
    lane_result = run_lane_cycle_with_guard(
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
        "llm": "reachable" if llm_reachable else "unreachable",
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


def _check_llm_connectivity(config: AppConfig) -> bool:
    try:
        settings = LLMGatewaySettings.from_app_config(config)
        gateway = UnifiedLLMGateway(settings=settings, profile=config.runtime_profile)
        outcome = gateway.check_connectivity()
        return bool(outcome.get("ok", False))
    except Exception:
        return False


def config_snapshot(config: AppConfig) -> dict[str, str]:
    payload = asdict(config)
    payload["runtime_profile"] = config.runtime_profile.value
    payload["runtime_mode"] = config.runtime_mode.value
    payload["llm_api_key"] = "***"
    return {k: str(v) for k, v in payload.items()}
