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


def _sample_signal() -> dict[str, object]:
    return {
        "strategy_id": "momentum",
        "signal_ts": "2026-03-15T13:30:00+00:00",
        "side": "BUY",
        "contract": {"symbol": "AAPL", "exchange": "SMART", "currency": "USD"},
        "orders": [
            {
                "orderRef": "KEY-P",
                "action": "BUY",
                "orderType": "LMT",
                "totalQuantity": 10,
                "lmtPrice": 100.0,
                "tif": "DAY",
                "transmit": False,
            },
            {
                "orderRef": "KEY-TP",
                "parentRef": "KEY-P",
                "action": "SELL",
                "orderType": "LMT",
                "totalQuantity": 10,
                "lmtPrice": 108.0,
                "tif": "GTC",
                "transmit": False,
            },
            {
                "orderRef": "KEY-SL",
                "parentRef": "KEY-P",
                "action": "SELL",
                "orderType": "STP",
                "totalQuantity": 10,
                "auxPrice": 95.0,
                "tif": "GTC",
                "transmit": True,
            },
        ],
    }


class _BaseSafeClient:
    def __init__(self) -> None:
        self.submit_count = 0

    def reconcile_snapshot(self) -> dict[str, object]:
        return {"ok": True, "open_orders": [], "positions": [], "trades": []}

    def activate_kill_switch(self) -> dict[str, object]:
        return {"ok": True, "cancelled_orders": 0, "flattened_positions": 0}

    def close(self) -> None:
        return None


class FundSafetyCoreTests(unittest.TestCase):
    def test_restart_recovery_prevents_duplicate_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            signal = _sample_signal()

            class _Client(_BaseSafeClient):
                def reconcile_snapshot(self) -> dict[str, object]:
                    return {
                        "ok": True,
                        "open_orders": [
                            {
                                "order_ref": "KEY-P",
                                "symbol": "AAPL",
                                "side": "BUY",
                                "quantity": 10.0,
                                "broker_order_id": "1001",
                                "broker_status": "Submitted",
                                "local_status": "ACK",
                            }
                        ],
                        "positions": [],
                        "trades": [],
                    }

                def submit_bracket_signal(self, payload: dict[str, object]) -> dict[str, object]:
                    self.submit_count += 1
                    return {
                        "ok": True,
                        "symbol": "AAPL",
                        "orders": [
                            {
                                "status": "Submitted",
                                "order_ref": "KEY-P",
                                "order_id": "1001",
                                "filled_quantity": 0.0,
                                "remaining_quantity": 10.0,
                            }
                        ],
                    }

            shared_client = _Client()
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_cycle:
                    mocked_cycle.return_value = {"ibkr_order_signals": [signal]}
                    first = execute_cycle(
                        symbol="AAPL",
                        config=config,
                        send=True,
                        client_factory=lambda _: shared_client,
                    )
                    second = execute_cycle(
                        symbol="AAPL",
                        config=config,
                        send=True,
                        client_factory=lambda _: shared_client,
                    )
            self.assertEqual(1, shared_client.submit_count)
            self.assertEqual("RUNNING", first["system_state"]["status"])
            self.assertTrue(second["executions"][0]["deduplicated"])
            self.assertTrue(len(second["open_orders"]) >= 1)

    def test_duplicate_messages_do_not_repeat_submit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            signal = _sample_signal()

            class _Client(_BaseSafeClient):
                def submit_bracket_signal(self, payload: dict[str, object]) -> dict[str, object]:
                    self.submit_count += 1
                    return {"ok": True, "symbol": "AAPL", "orders": []}

            shared_client = _Client()
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_cycle:
                    mocked_cycle.return_value = {"ibkr_order_signals": [signal, signal]}
                    report = execute_cycle(
                        symbol="AAPL",
                        config=config,
                        send=True,
                        client_factory=lambda _: shared_client,
                    )
            self.assertEqual(1, shared_client.submit_count)
            self.assertEqual(2, len(report["executions"]))
            dedup_count = sum(1 for item in report["executions"] if item.get("deduplicated"))
            self.assertEqual(1, dedup_count)

    def test_partial_fill_state_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            signal = _sample_signal()

            class _Client(_BaseSafeClient):
                def submit_bracket_signal(self, payload: dict[str, object]) -> dict[str, object]:
                    self.submit_count += 1
                    return {
                        "ok": True,
                        "symbol": "AAPL",
                        "orders": [
                            {
                                "status": "PartiallyFilled",
                                "order_ref": "KEY-P",
                                "order_id": "2001",
                                "filled_quantity": 4.0,
                                "remaining_quantity": 6.0,
                            }
                        ],
                    }

            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_cycle:
                    mocked_cycle.return_value = {"ibkr_order_signals": [signal]}
                    report = execute_cycle(
                        symbol="AAPL",
                        config=config,
                        send=True,
                        client_factory=lambda _: _Client(),
                    )
            self.assertTrue(report["open_orders"])
            self.assertEqual("PARTIAL", report["open_orders"][0]["local_status"])

    def test_gateway_flap_switches_to_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            signal_1 = _sample_signal()
            signal_2 = dict(_sample_signal())
            signal_2["signal_ts"] = "2026-03-15T13:31:00+00:00"

            class _Client(_BaseSafeClient):
                def __init__(self) -> None:
                    super().__init__()
                    self._call = 0

                def submit_bracket_signal(self, payload: dict[str, object]) -> dict[str, object]:
                    self._call += 1
                    if self._call == 1:
                        raise ConnectionError("gateway flap")
                    self.submit_count += 1
                    return {"ok": True, "symbol": "AAPL", "orders": []}

            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_cycle:
                    mocked_cycle.return_value = {"ibkr_order_signals": [signal_1, signal_2]}
                    report = execute_cycle(
                        symbol="AAPL",
                        config=config,
                        send=True,
                        client_factory=lambda _: _Client(),
                    )
            self.assertEqual("RUNNING", report["system_state"]["status"])
            self.assertEqual(2, len(report["executions"]))
            self.assertTrue(report["executions"][0]["ok"])
            self.assertEqual(2, report["executions"][0]["retry_attempt"])
            self.assertTrue(report["executions"][1]["ok"])


if __name__ == "__main__":
    unittest.main()
