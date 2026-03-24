from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable

from ..ai import start_high_engine, start_low_engine, start_ultra_engine
from ..config import AppConfig
from ..execution_subscriber import start_execution_subscriber
from ..market_data import load_market_snapshot_with_gate
from ..observability import generate_daily_health_report, log_event
from ..runtime.health import health_check
from ..lanes.__init__ import _normalize_headlines
from ..lanes.bus import AsyncEventBus

logger = logging.getLogger(__name__)


async def run_event_driven_architecture(config: AppConfig) -> None:
    bus = AsyncEventBus(max_queue_size=2048)

    now_utc = _utc_now()
    data_gate = load_market_snapshot_with_gate(config=config, now_utc=now_utc)
    market_snapshot = dict(data_gate.get("snapshot", {}) or {})
    headlines = _normalize_headlines(None, now=now_utc)

    logger.info("Initializing Event-Driven Engines...")

    low_task = asyncio.create_task(
        start_low_engine(
            bus=bus,
            config=config,
            market_snapshot=market_snapshot,
            interval_seconds=3600.0,
        )
    )
    high_task = asyncio.create_task(
        start_high_engine(
            bus=bus,
            config=config,
            market_snapshot=market_snapshot,
        )
    )
    ultra_task = asyncio.create_task(
        start_ultra_engine(
            bus=bus,
            config=config,
            market_snapshot=market_snapshot,
            headlines=headlines,
            interval_seconds=1.0,
        )
    )
    execution_task = asyncio.create_task(
        start_execution_subscriber(
            bus=bus,
            config=config,
            market_snapshot=market_snapshot,
        )
    )

    try:
        await asyncio.gather(low_task, high_task, ultra_task, execution_task)
    except asyncio.CancelledError:
        logger.info("Event-Driven Architecture shutting down...")
        low_task.cancel()
        high_task.cancel()
        ultra_task.cancel()
        execution_task.cancel()
        await asyncio.gather(low_task, high_task, ultra_task, execution_task, return_exceptions=True)


def run_runtime(
    config: AppConfig,
    *,
    health_check_fn: Callable[[AppConfig], dict[str, str]] = health_check,
    daily_report_fn: Callable[[AppConfig], dict[str, object]] = generate_daily_health_report,
    sleep_fn: Callable[[float], None] = time.sleep,
    asyncio_runner: Callable[[object], object] = asyncio.run,
) -> None:
    if not config.event_driven_runtime_enabled:
        cycles = max(1, config.lane_scheduler_cycles)
        status: dict[str, str] = {}
        for index in range(cycles):
            status = health_check_fn(config)
            log_event("health_cycle", health=status, cycle=index + 1, cycles=cycles)
            if index + 1 < cycles:
                sleep_fn(max(1, config.lane_rebalance_interval_seconds))
        report = daily_report_fn(config)
        log_event("daily_health_summary", summary=report.get("summary", {}))
        return

    logger.info("Starting Event-Driven Architecture (explicitly enabled)...")
    asyncio_runner(run_event_driven_architecture(config))


def _utc_now():
    from datetime import datetime, timezone

    return datetime.now(tz=timezone.utc)


__all__ = [
    "run_event_driven_architecture",
    "run_runtime",
]
