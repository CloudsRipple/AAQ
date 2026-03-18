from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import load_config
from phase0.lanes import run_lane_cycle
from phase0.market_data import get_market_calendar_status, load_market_snapshot_with_gate


class MarketDataGateTests(unittest.TestCase):
    def test_primary_source_outage_enters_degraded_and_blocks_trading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            env = {
                "AI_STATE_DB_PATH": db_path,
                "MARKET_DATA_MODE": "live",
                "MARKET_SNAPSHOT_JSON": "",
            }
            with patch.dict(os.environ, env, clear=False):
                config = load_config()
                with patch("phase0.market_data._load_market_snapshot_from_yfinance", return_value={}):
                    output = run_lane_cycle("AAPL", config=config)
        self.assertTrue(output["data_quality_gate"]["degraded"])
        self.assertFalse(output["data_quality_gate"]["allow_trading"])
        self.assertEqual([], output["ibkr_order_signals"])
        self.assertIn("PRIMARY_SOURCE_UNAVAILABLE", output["data_quality_gate"]["blocked_reasons"])

    def test_dirty_snapshot_is_blocked_by_quality_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            dirty_json = (
                '{"AAPL":{"reference_price":-2,"volatility":0.2,"snapshot_ts":"2026-03-15T13:30:00+00:00"},'
                '"MSFT":{"volatility":0.2,"snapshot_ts":"2026-03-15T13:30:00+00:00"}}'
            )
            env = {
                "AI_STATE_DB_PATH": db_path,
                "MARKET_DATA_MODE": "default",
                "MARKET_SNAPSHOT_JSON": dirty_json,
            }
            with patch.dict(os.environ, env, clear=False):
                config = load_config()
                output = run_lane_cycle("AAPL", config=config)
        self.assertTrue(output["data_quality_gate"]["degraded"])
        self.assertFalse(output["data_quality_gate"]["allow_trading"])
        self.assertIn("MISSING_OR_INVALID_VALUES", output["data_quality_gate"]["quality"]["errors"])
        self.assertEqual([], output["ibkr_order_signals"])

    def test_calendar_handles_holiday_dst_and_half_day_boundaries(self) -> None:
        holiday = get_market_calendar_status(now_utc=datetime(2026, 12, 25, 15, 0, tzinfo=timezone.utc))
        self.assertFalse(holiday["is_trading_day"])
        self.assertTrue(holiday["is_holiday"])
        pre_dst = get_market_calendar_status(now_utc=datetime(2026, 3, 6, 15, 0, tzinfo=timezone.utc))
        post_dst = get_market_calendar_status(now_utc=datetime(2026, 3, 9, 15, 0, tzinfo=timezone.utc))
        self.assertEqual("2026-03-06T14:30:00+00:00", pre_dst["session_start_utc"])
        self.assertEqual("2026-03-09T13:30:00+00:00", post_dst["session_start_utc"])
        half_day = get_market_calendar_status(now_utc=datetime(2026, 11, 27, 16, 0, tzinfo=timezone.utc))
        self.assertTrue(half_day["is_half_day"])
        self.assertEqual("2026-11-27T18:00:00+00:00", half_day["session_end_utc"])

    def test_signal_contains_snapshot_trace_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            env = {"AI_STATE_DB_PATH": db_path}
            with patch.dict(os.environ, env, clear=False):
                config = load_config()
                output = run_lane_cycle("AAPL", config=config)
        self.assertTrue(output["data_quality_gate"]["snapshot_id"])
        decision = output["decisions"][0]
        self.assertEqual(output["data_quality_gate"]["snapshot_id"], decision.get("snapshot_id"))

    def test_allow_opening_is_false_outside_rth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            weekend_now = datetime(2026, 11, 28, 15, 0, tzinfo=timezone.utc)
            snapshot_json = (
                '{"AAPL":{"reference_price":180.0,"volatility":0.2,'
                '"snapshot_ts":"2026-11-28T15:00:00+00:00"}}'
            )
            env = {
                "AI_STATE_DB_PATH": db_path,
                "MARKET_DATA_MODE": "default",
                "MARKET_SNAPSHOT_JSON": snapshot_json,
            }
            with patch.dict(os.environ, env, clear=False):
                config = load_config()
                gate = load_market_snapshot_with_gate(
                    config=config,
                    now_utc=weekend_now,
                )
        self.assertFalse(gate["allow_opening"])
        self.assertTrue(gate["allow_trading"])

    def test_db_lock_conflict_forces_allow_opening_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            now_utc = datetime(2026, 3, 10, 15, 0, tzinfo=timezone.utc)
            snapshot_json = (
                '{"AAPL":{"reference_price":180.0,"volatility":0.2,'
                '"snapshot_ts":"2026-03-10T14:59:00+00:00"}}'
            )
            env = {
                "AI_STATE_DB_PATH": db_path,
                "MARKET_DATA_MODE": "default",
                "MARKET_SNAPSHOT_JSON": snapshot_json,
            }
            with patch.dict(os.environ, env, clear=False):
                config = load_config()
                with patch(
                    "phase0.market_data.record_market_snapshot_state",
                    side_effect=sqlite3.OperationalError("database is locked"),
                ):
                    gate = load_market_snapshot_with_gate(config=config, now_utc=now_utc)
        self.assertFalse(gate["allow_trading"])
        self.assertFalse(gate["allow_opening"])
        self.assertIn("DB_LOCK_CONFLICT", gate["blocked_reasons"])


if __name__ == "__main__":
    unittest.main()
