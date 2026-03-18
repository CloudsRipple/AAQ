from __future__ import annotations

from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import load_config
from phase0.ibkr_execution import execute_cycle


class IntegrationE2ETests(unittest.TestCase):
    def test_data_to_signal_to_risk_to_execution_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            env = {
                "AI_STATE_DB_PATH": db_path,
                "AI_ENABLED": "false",
                "MARKET_DATA_MODE": "default",
            }

            class _Client:
                def reconcile_snapshot(self) -> dict[str, object]:
                    return {"ok": True, "open_orders": [], "positions": [], "trades": []}

                def submit_bracket_signal(self, signal: dict[str, object]) -> dict[str, object]:
                    parent = signal["orders"][0]
                    tp = signal["orders"][1]
                    sl = signal["orders"][2]
                    return {
                        "ok": True,
                        "orders": [
                            {
                                "order_ref": parent["orderRef"],
                                "status": "Submitted",
                                "filled_quantity": 0.0,
                                "remaining_quantity": parent["totalQuantity"],
                                "avg_fill_price": 0.0,
                            },
                            {
                                "order_ref": tp["orderRef"],
                                "status": "Submitted",
                                "filled_quantity": 0.0,
                                "remaining_quantity": tp["totalQuantity"],
                                "avg_fill_price": 0.0,
                            },
                            {
                                "order_ref": sl["orderRef"],
                                "status": "Submitted",
                                "filled_quantity": 0.0,
                                "remaining_quantity": sl["totalQuantity"],
                                "avg_fill_price": 0.0,
                            },
                        ],
                    }

                def activate_kill_switch(self) -> dict[str, object]:
                    return {"ok": True, "cancelled_orders": 0, "flattened_positions": 0}

                def close(self) -> None:
                    return None

            with patch.dict(os.environ, env, clear=False):
                config = load_config()
                report = execute_cycle(
                    symbol="AAPL",
                    config=config,
                    send=True,
                    daily_state={"actions_today": 1, "has_open_position": False},
                    client_factory=lambda _: _Client(),
                )
        self.assertIn("data_quality_gate", report["lane"])
        self.assertIn("risk_engine", report)
        self.assertIn("executions", report)
        self.assertTrue(report["lane"]["data_quality_gate"]["snapshot_id"])
        self.assertGreaterEqual(len(report["risk_engine"]["decisions"]), 1)
        self.assertTrue(all(item.get("ok", False) for item in report["executions"]))


if __name__ == "__main__":
    unittest.main()
