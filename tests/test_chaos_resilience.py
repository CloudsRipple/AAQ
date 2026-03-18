from __future__ import annotations

from pathlib import Path
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import load_config
from phase0.ibkr_execution import execute_cycle
from phase0.market_data import load_market_snapshot_with_gate


def _sample_signal(ts: str) -> dict[str, object]:
    return {
        "strategy_id": "momentum",
        "signal_ts": ts,
        "side": "BUY",
        "contract": {"symbol": "AAPL", "exchange": "SMART", "currency": "USD"},
        "orders": [
            {
                "orderRef": "CHAOS-P",
                "action": "BUY",
                "orderType": "LMT",
                "totalQuantity": 10,
                "lmtPrice": 100.0,
                "tif": "DAY",
                "transmit": False,
            },
            {
                "orderRef": "CHAOS-TP",
                "parentRef": "CHAOS-P",
                "action": "SELL",
                "orderType": "LMT",
                "totalQuantity": 10,
                "lmtPrice": 108.0,
                "tif": "GTC",
                "transmit": False,
            },
            {
                "orderRef": "CHAOS-SL",
                "parentRef": "CHAOS-P",
                "action": "SELL",
                "orderType": "STP",
                "totalQuantity": 10,
                "auxPrice": 95.0,
                "tif": "GTC",
                "transmit": True,
            },
        ],
    }


class ChaosResilienceTests(unittest.TestCase):
    def test_network_disconnect_retry_then_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            signal = _sample_signal("2026-03-15T13:30:00+00:00")

            class _Client:
                def __init__(self) -> None:
                    self.called = 0

                def reconcile_snapshot(self) -> dict[str, object]:
                    return {"ok": True, "open_orders": [], "positions": [], "trades": []}

                def submit_bracket_signal(self, _: dict[str, object]) -> dict[str, object]:
                    self.called += 1
                    if self.called == 1:
                        raise ConnectionError("network down")
                    return {"ok": True, "orders": []}

                def activate_kill_switch(self) -> dict[str, object]:
                    return {"ok": True, "cancelled_orders": 0, "flattened_positions": 0}

                def close(self) -> None:
                    return None

            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_lane:
                    mocked_lane.return_value = {"ibkr_order_signals": [signal], "data_quality_gate": {"degraded": False, "quality": {"errors": []}}}
                    report = execute_cycle(
                        symbol="AAPL",
                        config=config,
                        send=True,
                        client_factory=lambda _: _Client(),
                    )
        self.assertTrue(report["executions"][0]["ok"])
        self.assertEqual(2, report["executions"][0]["retry_attempt"])

    def test_latency_and_dirty_data_block_trading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            stale_dirty = (
                '{"AAPL":{"reference_price":-1,"volatility":0.2,"snapshot_ts":"2025-01-01T00:00:00+00:00"}}'
            )
            with patch.dict(
                os.environ,
                {
                    "AI_STATE_DB_PATH": db_path,
                    "MARKET_DATA_MODE": "default",
                    "MARKET_SNAPSHOT_JSON": stale_dirty,
                },
                clear=False,
            ):
                config = load_config()
                gate = load_market_snapshot_with_gate(config=config)
                report = execute_cycle(symbol="AAPL", config=config, send=False)
        self.assertTrue(gate["degraded"])
        self.assertFalse(gate["allow_trading"])
        self.assertEqual([], report["lane"]["ibkr_order_signals"])

    def test_restart_dedup_prevents_duplicate_submit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            signal = _sample_signal("2026-03-15T13:30:00+00:00")

            class _Client:
                def __init__(self) -> None:
                    self.sent = 0

                def reconcile_snapshot(self) -> dict[str, object]:
                    return {"ok": True, "open_orders": [], "positions": [], "trades": []}

                def submit_bracket_signal(self, _: dict[str, object]) -> dict[str, object]:
                    self.sent += 1
                    return {"ok": True, "orders": []}

                def activate_kill_switch(self) -> dict[str, object]:
                    return {"ok": True, "cancelled_orders": 0, "flattened_positions": 0}

                def close(self) -> None:
                    return None

            client = _Client()
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_lane:
                    mocked_lane.return_value = {"ibkr_order_signals": [signal], "data_quality_gate": {"degraded": False, "quality": {"errors": []}}}
                    execute_cycle(symbol="AAPL", config=config, send=True, client_factory=lambda _: client)
                    second = execute_cycle(symbol="AAPL", config=config, send=True, client_factory=lambda _: client)
        self.assertEqual(1, client.sent)
        self.assertTrue(second["executions"][0]["deduplicated"])

    def test_db_lock_conflict_degrades_data_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(
                os.environ,
                {
                    "AI_STATE_DB_PATH": db_path,
                    "MARKET_DATA_MODE": "default",
                    "MARKET_SNAPSHOT_JSON": '{"AAPL":{"reference_price":100,"volatility":0.2,"snapshot_ts":"2026-03-15T13:30:00+00:00"}}',
                },
                clear=False,
            ):
                config = load_config()
                with patch("phase0.market_data.sqlite3.connect", side_effect=sqlite3.OperationalError("database is locked")):
                    gate = load_market_snapshot_with_gate(config=config)
        self.assertTrue(gate["degraded"])
        self.assertIn("DB_LOCK_CONFLICT", gate["blocked_reasons"])


if __name__ == "__main__":
    unittest.main()
