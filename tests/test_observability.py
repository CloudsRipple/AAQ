from __future__ import annotations

import json
import logging
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import load_config
from phase0.ibkr_execution import execute_cycle
from phase0.logger import JsonFormatter
from phase0.observability import build_metrics_snapshot, evaluate_alerts, generate_daily_health_report
from phase0.state_store import set_runtime_state


def _signal() -> dict[str, object]:
    return {
        "strategy_id": "momentum",
        "signal_ts": "2026-03-15T13:30:00+00:00",
        "side": "BUY",
        "contract": {"symbol": "AAPL", "exchange": "SMART", "currency": "USD"},
        "orders": [
            {"orderRef": "OBS-P", "action": "BUY", "orderType": "LMT", "totalQuantity": 10, "lmtPrice": 100.0, "tif": "DAY", "transmit": False},
            {"orderRef": "OBS-TP", "parentRef": "OBS-P", "action": "SELL", "orderType": "LMT", "totalQuantity": 10, "lmtPrice": 108.0, "tif": "GTC", "transmit": False},
            {"orderRef": "OBS-SL", "parentRef": "OBS-P", "action": "SELL", "orderType": "STP", "totalQuantity": 10, "auxPrice": 95.0, "tif": "GTC", "transmit": True},
        ],
    }


class ObservabilityTests(unittest.TestCase):
    def test_metrics_snapshot_contains_required_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")

            class _Client:
                def reconcile_snapshot(self) -> dict[str, object]:
                    return {"ok": True, "open_orders": [], "positions": [], "trades": []}

                def submit_bracket_signal(self, _: dict[str, object]) -> dict[str, object]:
                    return {
                        "ok": True,
                        "orders": [
                            {"order_ref": "OBS-P", "status": "Filled", "filled_quantity": 10.0, "remaining_quantity": 0.0, "avg_fill_price": 100.5},
                            {"order_ref": "OBS-TP", "status": "Submitted", "filled_quantity": 0.0, "remaining_quantity": 10.0, "avg_fill_price": 0.0},
                            {"order_ref": "OBS-SL", "status": "Submitted", "filled_quantity": 0.0, "remaining_quantity": 10.0, "avg_fill_price": 0.0},
                        ],
                    }

                def activate_kill_switch(self) -> dict[str, object]:
                    return {"ok": True, "cancelled_orders": 0, "flattened_positions": 0}

                def close(self) -> None:
                    return None

            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_lane:
                    mocked_lane.return_value = {"ibkr_order_signals": [_signal()], "data_quality_gate": {"degraded": False, "quality": {"errors": []}}}
                    execute_cycle(symbol="AAPL", config=config, send=True, client_factory=lambda _: _Client())
                snapshot = build_metrics_snapshot(config)
        metrics = snapshot["metrics"]
        for key in ("order_success_rate", "order_reject_rate", "p95_latency_ms", "avg_slippage_bps", "drawdown_pct", "risk_reject_rate"):
            self.assertIn(key, metrics)

    def test_alert_rules_cover_required_conditions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                set_runtime_state(
                    db_path,
                    drawdown=config.risk_max_drawdown_pct * 0.85,
                    day_trade_count=1,
                    cooldown_until="",
                    kill_switch_active=False,
                )
                alerts = evaluate_alerts(
                    config=config,
                    cycle_report={
                        "system_state": {"status": "DEGRADED", "reason": "RECONCILE_FAILED"},
                        "executions": [{"deduplicated": True}],
                        "lane": {"data_quality_gate": {"degraded": True, "blocked_reasons": ["PRIMARY_SOURCE_UNAVAILABLE"]}},
                    },
                    metrics_snapshot={"metrics": {"drawdown_pct": config.risk_max_drawdown_pct * 0.85}},
                )
        rule_ids = {item["rule_id"] for item in alerts}
        self.assertIn("ALERT_GATEWAY_DISCONNECT", rule_ids)
        self.assertIn("ALERT_DUPLICATE_ORDER_RISK", rule_ids)
        self.assertIn("ALERT_ABNORMAL_DRAWDOWN", rule_ids)
        self.assertIn("ALERT_DATA_OUTAGE", rule_ids)

    def test_daily_health_report_generates_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            cwd = os.getcwd()
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                os.chdir(tmp)
                try:
                    report = generate_daily_health_report(config)
                    self.assertTrue(Path(tmp, "artifacts", "daily_health_report.latest.json").exists())
                finally:
                    os.chdir(cwd)
        self.assertEqual("phase0_daily_health_report", report["kind"])
        self.assertIn("summary", report)

    def test_json_formatter_keeps_structured_payload(self) -> None:
        formatter = JsonFormatter()
        record = logging.LogRecord("test", logging.INFO, __file__, 10, "hello", (), None)
        record.event_payload = {"event": "unit_test", "value": 7}
        text = formatter.format(record)
        payload = json.loads(text)
        self.assertEqual("unit_test", payload["event"])
        self.assertEqual(7, payload["value"])


if __name__ == "__main__":
    unittest.main()
