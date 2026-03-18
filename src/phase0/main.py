from __future__ import annotations

import logging
import sys
import time
import asyncio

from .app import config_snapshot, health_check
from .config import load_config
from .errors import AppError, ErrorCode
from .logger import setup_logging
from .observability import generate_daily_health_report, log_event
from .lanes.bus import AsyncEventBus
from .ai import start_low_engine, start_high_engine, start_ultra_engine
from .execution_subscriber import start_execution_subscriber
from .market_data import load_market_snapshot_with_gate
from .lanes.__init__ import _normalize_headlines

logger = logging.getLogger(__name__)

async def _run_event_driven_architecture(config) -> None:
    bus = AsyncEventBus(max_queue_size=2048)
    
    # Load initial market snapshot for engines
    now = time.time()
    from datetime import datetime, timezone
    now_utc = datetime.now(tz=timezone.utc)
    data_gate = load_market_snapshot_with_gate(config=config, now_utc=now_utc)
    market_snapshot = dict(data_gate.get("snapshot", {}) or {})
    headlines = _normalize_headlines(None, now=now_utc)
    
    logger.info("Initializing Event-Driven Engines...")
    
    # Create the daemon tasks
    low_task = asyncio.create_task(start_low_engine(
        bus=bus,
        config=config,
        market_snapshot=market_snapshot,
        interval_seconds=3600.0  # Run every hour
    ))
    
    high_task = asyncio.create_task(start_high_engine(
        bus=bus,
        config=config,
        market_snapshot=market_snapshot,
    ))
    
    ultra_task = asyncio.create_task(start_ultra_engine(
        bus=bus,
        config=config,
        market_snapshot=market_snapshot,
        headlines=headlines,
        interval_seconds=1.0 # Poll frequently
    ))
    
    execution_task = asyncio.create_task(start_execution_subscriber(
        bus=bus,
        config=config,
        market_snapshot=market_snapshot
    ))
    
    # Wait for tasks to complete (they shouldn't, unless cancelled)
    try:
        await asyncio.gather(low_task, high_task, ultra_task, execution_task)
    except asyncio.CancelledError:
        logger.info("Event-Driven Architecture shutting down...")
        low_task.cancel()
        high_task.cancel()
        ultra_task.cancel()
        execution_task.cancel()
        await asyncio.gather(low_task, high_task, ultra_task, execution_task, return_exceptions=True)


def main() -> int:
    try:
        config = load_config()
        setup_logging(config.log_level)
        log_event("bootstrap_ready", config=config_snapshot(config))
        
        # Event-driven runtime is explicitly opt-in. Default path remains the
        # stable health-check loop until the event pipeline is fully hardened.
        if not config.event_driven_runtime_enabled:
            cycles = max(1, config.lane_scheduler_cycles)
            status: dict[str, str] = {}
            for index in range(cycles):
                status = health_check(config)
                log_event("health_cycle", health=status, cycle=index + 1, cycles=cycles)
                if index + 1 < cycles:
                    time.sleep(max(1, config.lane_rebalance_interval_seconds))
            report = generate_daily_health_report(config)
            log_event("daily_health_summary", summary=report.get("summary", {}))
        else:
            logger.info("Starting Event-Driven Architecture (explicitly enabled)...")
            asyncio.run(_run_event_driven_architecture(config))
            
        return 0
    except AppError as exc:
        logger.error(exc.message, extra={"error_code": exc.code.value})
        return 2
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
        return 0
    except Exception as exc:
        logger.exception(str(exc), extra={"error_code": ErrorCode.INTERNAL_ERROR.value})
        return 1

if __name__ == "__main__":
    sys.exit(main())
