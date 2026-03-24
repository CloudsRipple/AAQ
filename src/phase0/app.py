from __future__ import annotations

import socket

from .config import AppConfig
from .runtime import health as runtime_health

socket = runtime_health.socket


def health_check(config: AppConfig) -> dict[str, str]:
    return runtime_health.health_check(
        config,
        socket_check=_check_socket,
        drawdown_reader=_read_current_drawdown_pct,
        llm_connectivity_check=_check_llm_connectivity,
    )


def _check_socket(host: str, port: int, timeout_seconds: float = 0.3) -> bool:
    return runtime_health._check_socket(host, port, timeout_seconds)


def _read_current_drawdown_pct() -> float:
    return runtime_health._read_current_drawdown_pct()


def _check_llm_connectivity(config: AppConfig) -> bool:
    return runtime_health._check_llm_connectivity(config)


def config_snapshot(config: AppConfig) -> dict[str, str]:
    return runtime_health.config_snapshot(config)


__all__ = [
    "config_snapshot",
    "health_check",
]
