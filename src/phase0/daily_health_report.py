from __future__ import annotations

import argparse
import json

from .config import load_config
from .logger import setup_logging
from .observability import generate_daily_health_report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="phase0-daily-health-report")
    parser.add_argument("--log-level", default="")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config = load_config()
    setup_logging(args.log_level or config.log_level)
    report = generate_daily_health_report(config)
    print(json.dumps({"ok": True, "summary": report.get("summary", {})}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
