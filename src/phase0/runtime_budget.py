from __future__ import annotations

from dataclasses import dataclass
import platform

from .config import AppConfig, RuntimeMode


@dataclass(frozen=True)
class RuntimeBudget:
    machine_profile: str
    lane_loop_interval_ms: int
    max_lane_cycles_per_healthcheck: int
    llm_max_parallel_requests: int
    ibkr_socket_timeout_seconds: float


def build_runtime_budget(config: AppConfig) -> RuntimeBudget:
    machine_profile = _detect_machine_profile()
    if config.runtime_mode == RuntimeMode.ECO:
        base = RuntimeBudget(
            machine_profile=machine_profile,
            lane_loop_interval_ms=1200,
            max_lane_cycles_per_healthcheck=1,
            llm_max_parallel_requests=1,
            ibkr_socket_timeout_seconds=0.45,
        )
    elif config.runtime_mode == RuntimeMode.PERF:
        base = RuntimeBudget(
            machine_profile=machine_profile,
            lane_loop_interval_ms=300,
            max_lane_cycles_per_healthcheck=3,
            llm_max_parallel_requests=3,
            ibkr_socket_timeout_seconds=0.25,
        )
    else:
        base = RuntimeBudget(
            machine_profile=machine_profile,
            lane_loop_interval_ms=700,
            max_lane_cycles_per_healthcheck=2,
            llm_max_parallel_requests=2,
            ibkr_socket_timeout_seconds=0.30,
        )
    if machine_profile != "macbook_air_m2_16_256":
        return base
    if config.runtime_mode == RuntimeMode.PERF:
        return base
    return RuntimeBudget(
        machine_profile=machine_profile,
        lane_loop_interval_ms=max(500, base.lane_loop_interval_ms),
        max_lane_cycles_per_healthcheck=base.max_lane_cycles_per_healthcheck,
        llm_max_parallel_requests=min(base.llm_max_parallel_requests, 2),
        ibkr_socket_timeout_seconds=max(0.3, base.ibkr_socket_timeout_seconds),
    )


def _detect_machine_profile() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    processor = platform.processor().lower()
    if system == "darwin" and machine in {"arm64", "aarch64"}:
        if "m2" in processor or processor == "":
            return "macbook_air_m2_16_256"
    return "generic"
