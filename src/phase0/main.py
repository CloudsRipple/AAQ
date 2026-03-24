from __future__ import annotations

import asyncio
import logging
import sys
import time

from .app import config_snapshot, health_check
from .config import load_config
from .errors import AppError, ErrorCode
from .logger import setup_logging
from .observability import generate_daily_health_report, log_event
from .runtime.bootstrap import run_runtime

logger = logging.getLogger(__name__)

def main() -> int:
    try:
        config = load_config()
        setup_logging(config.log_level)
        log_event("bootstrap_ready", config=config_snapshot(config))

        run_runtime(
            config,
            health_check_fn=health_check,
            daily_report_fn=generate_daily_health_report,
            sleep_fn=time.sleep,
            asyncio_runner=asyncio.run,
        )
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
