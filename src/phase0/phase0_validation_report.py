from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .ibkr_paper_check import PortStatus, ProbeConfig, run_probe
from .lanes.high import evaluate_event
from .replay import run_replay


def _base_event(now: datetime) -> dict[str, str]:
    return {
        "lane": "ultra",
        "kind": "signal",
        "symbol": "AAPL",
        "side": "buy",
        "entry_price": "100",
        "stop_loss_price": "95",
        "take_profit_price": "108",
        "equity": "100000",
        "current_exposure": "5000",
        "last_exit_at": (now - timedelta(days=3)).isoformat(),
    }


def _hard_rule_checks(now: datetime) -> list[dict[str, Any]]:
    accepted = evaluate_event(_base_event(now))
    cooldown_event = _base_event(now)
    cooldown_event["last_exit_at"] = (now - timedelta(hours=3)).isoformat()
    cooldown = evaluate_event(cooldown_event)
    exposure_event = _base_event(now)
    exposure_event["current_exposure"] = "30000"
    exposure = evaluate_event(exposure_event)
    return [
        {
            "name": "single_trade_risk_1pct",
            "ok": accepted.get("status") == "accepted" and accepted.get("quantity", 0) <= 500,
            "detail": accepted,
        },
        {
            "name": "cooldown_24h",
            "ok": cooldown.get("status") == "rejected" and "COOLDOWN_24H_ACTIVE" in cooldown.get("reject_reasons", []),
            "detail": cooldown,
        },
        {
            "name": "total_exposure_30pct",
            "ok": exposure.get("status") == "rejected" and "TOTAL_EXPOSURE_LIMIT" in exposure.get("reject_reasons", []),
            "detail": exposure,
        },
    ]


def _order_checks(now: datetime) -> list[dict[str, Any]]:
    decision = evaluate_event(_base_event(now))
    bracket = decision.get("bracket_order", {})
    parent = bracket.get("parent", {})
    take_profit = bracket.get("take_profit", {})
    stop_loss = bracket.get("stop_loss", {})
    quantity = decision.get("quantity")
    return [
        {
            "name": "bracket_required",
            "ok": decision.get("status") == "accepted" and bool(bracket),
            "detail": decision,
        },
        {
            "name": "integer_quantity",
            "ok": isinstance(quantity, int) and quantity > 0,
            "detail": quantity,
        },
        {
            "name": "order_legs_consistent",
            "ok": parent.get("quantity") == take_profit.get("quantity") == stop_loss.get("quantity") == quantity,
            "detail": bracket,
        },
        {
            "name": "stop_takeprofit_present",
            "ok": stop_loss.get("order_type") == "STOP" and take_profit.get("order_type") == "LIMIT",
            "detail": {"take_profit": take_profit, "stop_loss": stop_loss},
        },
    ]


class _ValidationProbeClient:
    def request_l1_snapshot(self, symbol: str) -> dict[str, Any]:
        return {"symbol": symbol.upper(), "bid": 188.1, "ask": 188.3, "last": 188.2, "timestamp": "2026-01-01T00:00:00Z"}

    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, Any]]:
        return [
            {
                "headline": f"{symbol.upper()} validation headline",
                "provider_code": "BRFG",
                "article_id": "validation-1",
                "time": "2026-01-01T00:00:00Z",
            }
        ][:limit]

    def close(self) -> None:
        return None


def _ibkr_validation() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    dynamic_probe = run_probe(
        ProbeConfig(symbol="AAPL", timeout_seconds=0.8, news_limit=1, max_retries=1),
    )
    probe = dynamic_probe
    if not dynamic_probe.get("ok"):
        probe = run_probe(
            ProbeConfig(symbol="AAPL", timeout_seconds=0.5, news_limit=1, max_retries=1),
            client_factory=lambda _: _ValidationProbeClient(),
            port_checker=lambda host, port, timeout: PortStatus(ok=True, host=host, port=port, latency_ms=0.1, error=None),
            fallback_fetcher=lambda symbol: {"ok": False, "source": "yfinance", "symbol": symbol.upper(), "error": "not-needed"},
        )
        probe["validation_mode"] = "fallback_sample"
        probe["dynamic_probe_ok"] = False
    else:
        probe["validation_mode"] = "dynamic_live"
        probe["dynamic_probe_ok"] = True
    critical_steps = {item.get("step") for item in probe.get("critical_path_logs", [])}
    checks = [
        {
            "name": "dynamic_probe_must_pass",
            "ok": bool(dynamic_probe.get("ok", False)),
            "detail": {"dynamic_ok": bool(dynamic_probe.get("ok", False))},
        },
        {
            "name": "dynamic_probe_attempted",
            "ok": "port_7497" in dynamic_probe,
            "detail": {"dynamic_ok": bool(dynamic_probe.get("ok")), "mode": probe.get("validation_mode")},
        },
        {
            "name": "l1_news_probe_ok",
            "ok": bool(probe.get("l1_market_data", {}).get("ok")) and len(probe.get("news", [])) > 0,
            "detail": {
                "l1_ok": probe.get("l1_market_data", {}).get("ok"),
                "news_count": len(probe.get("news", [])),
            },
        },
        {
            "name": "pass_evidence_present",
            "ok": bool(probe.get("pass_evidence", {}).get("l1_market_data", {}).get("ok"))
            and bool(probe.get("pass_evidence", {}).get("news", {}).get("ok")),
            "detail": probe.get("pass_evidence"),
        },
        {
            "name": "critical_path_logged",
            "ok": {"port_probe", "ibkr_probe"}.issubset(critical_steps),
            "detail": probe.get("critical_path_logs", []),
        },
        {
            "name": "retry_validation_recorded",
            "ok": probe.get("retry_validation", {}).get("attempts", 0) >= 1,
            "detail": probe.get("retry_validation", {}),
        },
        {
            "name": "no_error_alerts_on_success",
            "ok": all(item.get("level") != "ERROR" for item in probe.get("alerts", [])),
            "detail": probe.get("alerts", []),
        },
    ]
    return probe, checks


def generate_phase0_validation_report() -> dict[str, Any]:
    now = datetime.now(tz=timezone.utc)
    replay = run_replay(mode="all")
    hard_rule_checks = _hard_rule_checks(now)
    order_checks = _order_checks(now)
    ibkr_probe, ibkr_checks = _ibkr_validation()
    all_checks = hard_rule_checks + order_checks + ibkr_checks
    passed_checks = sum(1 for check in all_checks if check["ok"])
    report: dict[str, Any] = {
        "kind": "phase0_validation_report",
        "generated_at": now.isoformat(),
        "replay": replay,
        "ibkr_probe": ibkr_probe,
        "hard_rule_checks": hard_rule_checks,
        "order_checks": order_checks,
        "ibkr_validation_checks": ibkr_checks,
        "summary": {
            "replay_passed": replay["passed"],
            "replay_total": replay["total"],
            "checks_passed": passed_checks,
            "checks_total": len(all_checks),
        },
    }
    report["ok"] = (
        replay["passed"] == replay["total"]
        and passed_checks == len(all_checks)
        and bool(ibkr_probe.get("dynamic_probe_ok", False))
    )
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="phase0-validation-report")
    parser.add_argument("--output", default="artifacts/phase0_validation_report.json")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = generate_phase0_validation_report()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(output_path, report)
    print(json.dumps({"ok": report["ok"], "output": str(output_path)}, ensure_ascii=False))
    if report["ok"]:
        return 0
    return 2


def _write_json_atomic(output_path: Path, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(output_path.parent),
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp_path = Path(tmp.name)
    temp_path.replace(output_path)


if __name__ == "__main__":
    raise SystemExit(main())
