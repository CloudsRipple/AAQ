from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from typing import Any

from .ai import evaluate_ultra_guard
from .config import load_config
from .lanes import InMemoryLaneBus, LaneEvent, run_lane_cycle_with_guard
from .lanes.high import evaluate_event


def _base_event(now: datetime) -> dict[str, str]:
    return {
        "lane": "ultra",
        "kind": "signal",
        "symbol": "AAPL",
        "side": "buy",
        "entry_price": "100",
        "stop_loss_price": "95",
        "take_profit_price": "110",
        "equity": "100000",
        "current_exposure": "12000",
        "last_exit_at": (now - timedelta(days=3)).isoformat(),
    }


def _breaking_news_event(now: datetime) -> dict[str, str]:
    payload = _base_event(now)
    payload.update(
        {
            "injection_kind": "breaking_news",
            "headline": "SEC headline shock",
            "last_exit_at": (now - timedelta(hours=4)).isoformat(),
        }
    )
    return payload


def _high_volatility_event(now: datetime) -> dict[str, str]:
    payload = _base_event(now)
    payload.update(
        {
            "injection_kind": "high_volatility",
            "entry_price": "100",
            "stop_loss_price": "95",
            "take_profit_price": "112",
            "atr_ratio": "0.16",
        }
    )
    return payload


def _run_single(name: str, event: dict[str, str], expected_status: str, expected_reason: str | None) -> dict[str, Any]:
    decision = evaluate_event(event)
    reasons = decision.get("reject_reasons", [])
    checks: list[dict[str, Any]] = [
        {
            "name": "status_match",
            "ok": decision.get("status") == expected_status,
            "actual": decision.get("status"),
            "expected": expected_status,
        }
    ]
    if expected_reason is not None:
        checks.append(
            {
                "name": "reason_match",
                "ok": expected_reason in reasons,
                "actual": reasons,
                "expected": expected_reason,
            }
        )
    ok = all(check["ok"] for check in checks)
    return {
        "scenario": name,
        "ok": ok,
        "event": event,
        "decision": decision,
        "checks": checks,
    }


def _run_duplicate_event_dedup() -> dict[str, Any]:
    bus = InMemoryLaneBus()
    payload = {"symbol": "AAPL", "lane": "ultra", "kind": "signal"}
    event = LaneEvent.from_payload(event_type="signal", source_lane="ultra", payload=payload)
    first_ok = bus.publish("ultra.signal", event)
    second_ok = bus.publish("ultra.signal", event)
    checks = [
        {"name": "first_publish_ok", "ok": first_ok, "actual": first_ok, "expected": True},
        {"name": "second_publish_deduped", "ok": not second_ok, "actual": second_ok, "expected": False},
    ]
    return {
        "scenario": "duplicate_event_dedup",
        "ok": all(item["ok"] for item in checks),
        "event": payload,
        "decision": {"first_publish_ok": first_ok, "second_publish_ok": second_ok},
        "checks": checks,
    }


def _run_unverified_stale_message(now: datetime) -> dict[str, Any]:
    ultra = evaluate_ultra_guard(
        headline="unverified rumor clickbait says merger",
        published_at=now - timedelta(hours=6),
        now=now,
        max_age_minutes=180,
    )
    checks = [
        {"name": "wake_high_blocked", "ok": not ultra.wake_high, "actual": ultra.wake_high, "expected": False},
        {"name": "reason_is_block", "ok": ultra.reason == "LOW_CREDIBILITY_OR_STALE", "actual": ultra.reason, "expected": "LOW_CREDIBILITY_OR_STALE"},
    ]
    return {
        "scenario": "unverified_stale_message",
        "ok": all(item["ok"] for item in checks),
        "event": {"headline": "unverified rumor clickbait says merger"},
        "decision": {
            "authenticity_score": ultra.authenticity_score,
            "timeliness_score": ultra.timeliness_score,
            "wake_high": ultra.wake_high,
            "reason": ultra.reason,
        },
        "checks": checks,
    }


def _run_safety_blocked_execution() -> dict[str, Any]:
    config = load_config()
    output = run_lane_cycle_with_guard("AAPL", config=config, allow_risk_execution=False)
    decision = output["decisions"][0]
    checks = [
        {
            "name": "blocked_by_safety_mode",
            "ok": decision.get("status") == "rejected" and "SAFETY_MODE_BLOCKED" in decision.get("reject_reasons", []),
            "actual": decision,
            "expected": "rejected+SAFETY_MODE_BLOCKED",
        }
    ]
    return {
        "scenario": "safety_mode_blocked",
        "ok": all(item["ok"] for item in checks),
        "event": output["event"],
        "decision": decision,
        "checks": checks,
    }


def run_replay(mode: str = "all") -> dict[str, Any]:
    now = datetime.now(tz=timezone.utc)
    scenarios = {
        "breaking_news": _run_single(
            name="breaking_news",
            event=_breaking_news_event(now),
            expected_status="rejected",
            expected_reason="COOLDOWN_24H_ACTIVE",
        ),
        "high_volatility": _run_single(
            name="high_volatility",
            event=_high_volatility_event(now),
            expected_status="accepted",
            expected_reason=None,
        ),
        "duplicate_event_dedup": _run_duplicate_event_dedup(),
        "unverified_stale_message": _run_unverified_stale_message(now),
        "safety_mode_blocked": _run_safety_blocked_execution(),
    }
    if mode == "all":
        selected = list(scenarios.values())
    else:
        selected = [scenarios[mode]]
    passed = sum(1 for item in selected if item["ok"])
    return {
        "kind": "phase0_injection_replay",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "mode": mode,
        "passed": passed,
        "total": len(selected),
        "results": selected,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="phase0-replay")
    parser.add_argument(
        "--mode",
        choices=[
            "all",
            "breaking_news",
            "high_volatility",
            "duplicate_event_dedup",
            "unverified_stale_message",
            "safety_mode_blocked",
        ],
        default="all",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = run_replay(mode=args.mode)
    print(json.dumps(report, ensure_ascii=False))
    if report["passed"] == report["total"]:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
