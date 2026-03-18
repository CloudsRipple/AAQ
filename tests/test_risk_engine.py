from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import load_config
from phase0.risk_engine import evaluate_order_intents
from phase0.state_store import (
    apply_reconcile_snapshot,
    get_system_status,
    set_runtime_state,
)


def _intent(side: str, qty: int = 10, symbol: str = "AAPL") -> dict[str, object]:
    return {
        "symbol": symbol,
        "side": side,
        "contract": {"symbol": symbol, "exchange": "SMART", "currency": "USD"},
        "orders": [
            {
                "orderRef": f"{symbol}-{side}-P",
                "action": side,
                "orderType": "LMT",
                "totalQuantity": qty,
                "lmtPrice": 100.0,
            },
            {
                "orderRef": f"{symbol}-{side}-TP",
                "parentRef": f"{symbol}-{side}-P",
                "action": "SELL" if side == "BUY" else "BUY",
                "orderType": "LMT",
                "totalQuantity": qty,
                "lmtPrice": 108.0,
            },
            {
                "orderRef": f"{symbol}-{side}-SL",
                "parentRef": f"{symbol}-{side}-P",
                "action": "SELL" if side == "BUY" else "BUY",
                "orderType": "STP",
                "totalQuantity": qty,
                "auxPrice": 95.0,
            },
        ],
    }


class RiskEngineTests(unittest.TestCase):
    def test_rejects_opening_when_cooldown_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                set_runtime_state(
                    db_path,
                    drawdown=0.0,
                    day_trade_count=1,
                    cooldown_until=(datetime.now(tz=timezone.utc) + timedelta(minutes=30)).isoformat(),
                    kill_switch_active=False,
                )
                report = evaluate_order_intents(
                    intents=[_intent("BUY")],
                    config=config,
                    lane_output={"data_quality_gate": {"degraded": False, "quality": {"errors": []}}},
                )
        self.assertEqual(0, len(report["approved_intents"]))
        self.assertEqual("PRE_COOLDOWN_ACTIVE", report["rejected_intents"][0]["rule_id"])

    def test_risk_unavailable_allows_reduce_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                apply_reconcile_snapshot(
                    db_path,
                    positions=[{"symbol": "AAPL", "quantity": 10.0, "avg_price": 100.0}],
                    open_orders=[],
                )
                with patch("phase0.risk_engine._evaluate_single_intent", side_effect=RuntimeError("down")):
                    report = evaluate_order_intents(
                        intents=[_intent("BUY"), _intent("SELL", qty=5)],
                        config=config,
                        lane_output={},
                    )
        self.assertEqual(1, len(report["approved_intents"]))
        self.assertEqual("SELL", str(report["approved_intents"][0]["side"]))
        self.assertTrue(report["fail_closed"])
        self.assertEqual("RISK_UNAVAILABLE_REDUCE_ONLY", report["rejected_intents"][0]["rule_id"])

    def test_post_trade_drawdown_triggers_halt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                set_runtime_state(
                    db_path,
                    drawdown=config.risk_max_drawdown_pct + 0.01,
                    day_trade_count=1,
                    cooldown_until="",
                    kill_switch_active=False,
                )
                report = evaluate_order_intents(
                    intents=[_intent("BUY")],
                    config=config,
                    lane_output={"data_quality_gate": {"degraded": False, "quality": {"errors": []}}},
                )
                system_state = get_system_status(db_path)
        self.assertEqual("POST_DRAWDOWN_HALT", report["rejected_intents"][0]["rule_id"])
        self.assertEqual("HALTED", system_state["status"])

    def test_blocks_opening_outside_rth_but_allows_reduce_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path}, clear=False):
                config = load_config()
                apply_reconcile_snapshot(
                    db_path,
                    positions=[{"symbol": "AAPL", "quantity": 10.0, "avg_price": 100.0}],
                    open_orders=[],
                )
                opening = evaluate_order_intents(
                    intents=[_intent("BUY", qty=5)],
                    config=config,
                    lane_output={"data_quality_gate": {"allow_opening": False, "degraded": False, "quality": {"errors": []}}},
                )
                reduce_only = evaluate_order_intents(
                    intents=[_intent("SELL", qty=5)],
                    config=config,
                    lane_output={"data_quality_gate": {"allow_opening": False, "degraded": False, "quality": {"errors": []}}},
                )
        self.assertEqual("PRE_MARKET_OPENING_BLOCKED", opening["rejected_intents"][0]["rule_id"])
        self.assertEqual(1, len(reduce_only["approved_intents"]))

    def test_open_order_exposure_uses_reference_price(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "CURRENT_EQUITY": "100000"}, clear=False):
                config = load_config()
                apply_reconcile_snapshot(
                    db_path,
                    positions=[],
                    open_orders=[
                        {
                            "order_ref": "OO-1",
                            "symbol": "AAPL",
                            "side": "BUY",
                            "quantity": 350.0,
                            "reference_price": 100.0,
                            "broker_order_id": "1",
                            "broker_status": "SUBMITTED",
                            "local_status": "ACK",
                        }
                    ],
                )
                report = evaluate_order_intents(
                    intents=[_intent("BUY", qty=10)],
                    config=config,
                    lane_output={"data_quality_gate": {"allow_opening": True, "degraded": False, "quality": {"errors": []}}},
                )
        self.assertEqual("PRE_POSITION_LIMIT", report["rejected_intents"][0]["rule_id"])


if __name__ == "__main__":
    unittest.main()
