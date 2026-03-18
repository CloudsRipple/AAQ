from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import load_config
from phase0.execution_lifecycle import process_execution_report
from phase0.ibkr_execution import execute_cycle
from phase0.state_store import (
    apply_reconcile_snapshot,
    get_runtime_state,
    get_system_status,
    list_order_lifecycle_events,
)


def _signal() -> dict[str, object]:
    return {
        "strategy_id": "momentum",
        "signal_ts": "2026-03-15T13:30:00+00:00",
        "side": "BUY",
        "contract": {"symbol": "AAPL", "exchange": "SMART", "currency": "USD"},
        "orders": [
            {
                "orderRef": "ACK-P",
                "action": "BUY",
                "orderType": "LMT",
                "totalQuantity": 10,
                "lmtPrice": 100.0,
                "tif": "DAY",
                "transmit": False,
            },
            {
                "orderRef": "ACK-TP",
                "parentRef": "ACK-P",
                "action": "SELL",
                "orderType": "LMT",
                "totalQuantity": 10,
                "lmtPrice": 108.0,
                "tif": "GTC",
                "transmit": False,
            },
            {
                "orderRef": "ACK-SL",
                "parentRef": "ACK-P",
                "action": "SELL",
                "orderType": "STP",
                "totalQuantity": 10,
                "auxPrice": 95.0,
                "tif": "GTC",
                "transmit": True,
            },
        ],
    }


class ExecutionLifecycleTests(unittest.TestCase):
    def test_ack_loss_is_tolerated_when_partial_arrives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            signal = _signal()
            result = {
                "ok": True,
                "orders": [
                    {"order_ref": "ACK-P", "status": "PartiallyFilled", "filled_quantity": 3.0, "remaining_quantity": 7.0, "avg_fill_price": 100.2},
                    {"order_ref": "ACK-TP", "status": "Submitted", "filled_quantity": 0.0, "remaining_quantity": 10.0, "avg_fill_price": 0.0},
                    {"order_ref": "ACK-SL", "status": "Submitted", "filled_quantity": 0.0, "remaining_quantity": 10.0, "avg_fill_price": 0.0},
                ],
            }
            lifecycle = process_execution_report(db_path=db_path, signal=signal, execution_result=result)
        self.assertFalse(lifecycle["rejected"])
        self.assertFalse(lifecycle["atomicity"]["needs_emergency"])
        parent = next(item for item in lifecycle["transitions"] if item["order_ref"] == "ACK-P")
        self.assertEqual("PARTIAL", parent["next_state"])

    def test_partial_multiple_reports_keep_state_machine_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            signal = _signal()
            first = {
                "ok": True,
                "orders": [
                    {"order_ref": "ACK-P", "status": "PartiallyFilled", "filled_quantity": 2.0, "remaining_quantity": 8.0, "avg_fill_price": 100.1},
                    {"order_ref": "ACK-TP", "status": "Submitted", "filled_quantity": 0.0, "remaining_quantity": 10.0},
                    {"order_ref": "ACK-SL", "status": "Submitted", "filled_quantity": 0.0, "remaining_quantity": 10.0},
                ],
            }
            second = {
                "ok": True,
                "orders": [
                    {"order_ref": "ACK-P", "status": "PartiallyFilled", "filled_quantity": 6.0, "remaining_quantity": 4.0, "avg_fill_price": 100.4},
                    {"order_ref": "ACK-TP", "status": "Submitted", "filled_quantity": 0.0, "remaining_quantity": 10.0},
                    {"order_ref": "ACK-SL", "status": "Submitted", "filled_quantity": 0.0, "remaining_quantity": 10.0},
                ],
            }
            process_execution_report(db_path=db_path, signal=signal, execution_result=first)
            process_execution_report(db_path=db_path, signal=signal, execution_result=second)
            events = list_order_lifecycle_events(db_path, order_ref="ACK-P", limit=10)
        self.assertGreaterEqual(len(events), 2)
        self.assertEqual("PARTIAL", events[-1]["next_state"])

    def test_missing_protection_leg_triggers_emergency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            signal = _signal()
            result = {
                "ok": True,
                "orders": [
                    {"order_ref": "ACK-P", "status": "Filled", "filled_quantity": 10.0, "remaining_quantity": 0.0, "avg_fill_price": 100.8},
                    {"order_ref": "ACK-TP", "status": "Submitted", "filled_quantity": 0.0, "remaining_quantity": 10.0},
                ],
            }
            lifecycle = process_execution_report(db_path=db_path, signal=signal, execution_result=result)
        self.assertTrue(lifecycle["atomicity"]["needs_emergency"])
        self.assertIn("ACK-SL", lifecycle["atomicity"]["missing_protection_refs"])

    def test_missing_in_transition_but_present_in_db_does_not_trigger_emergency(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            apply_reconcile_snapshot(
                db_path,
                positions=[],
                open_orders=[
                    {
                        "order_ref": "ACK-TP",
                        "symbol": "AAPL",
                        "side": "SELL",
                        "quantity": 10.0,
                        "reference_price": 108.0,
                        "broker_order_id": "2",
                        "broker_status": "SUBMITTED",
                        "local_status": "ACK",
                    },
                    {
                        "order_ref": "ACK-SL",
                        "symbol": "AAPL",
                        "side": "SELL",
                        "quantity": 10.0,
                        "reference_price": 95.0,
                        "broker_order_id": "3",
                        "broker_status": "SUBMITTED",
                        "local_status": "ACK",
                    },
                ],
            )
            signal = _signal()
            result = {
                "ok": True,
                "orders": [
                    {"order_ref": "ACK-P", "status": "Filled", "filled_quantity": 10.0, "remaining_quantity": 0.0, "avg_fill_price": 100.8}
                ],
            }
            lifecycle = process_execution_report(db_path=db_path, signal=signal, execution_result=result)
        self.assertFalse(lifecycle["atomicity"]["needs_emergency"])

    def test_rejected_order_triggers_recovery_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            signal = _signal()

            class _RejectClient:
                def submit_bracket_signal(self, payload: dict[str, object]) -> dict[str, object]:
                    return {
                        "ok": True,
                        "orders": [
                            {
                                "order_ref": "ACK-P",
                                "status": "Rejected",
                                "filled_quantity": 0.0,
                                "remaining_quantity": 10.0,
                                "avg_fill_price": 0.0,
                            }
                        ],
                    }

                def reconcile_snapshot(self) -> dict[str, object]:
                    return {"ok": True, "open_orders": [], "positions": [], "trades": []}

                def activate_kill_switch(self) -> dict[str, object]:
                    return {"ok": True, "cancelled_orders": 0, "flattened_positions": 0}

                def close(self) -> None:
                    return None

            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "REJECT_RECOVERY_COOLDOWN_MINUTES": "5"}, clear=False):
                cfg = load_config()
                with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_lane:
                    mocked_lane.return_value = {
                        "ibkr_order_signals": [signal],
                        "data_quality_gate": {"degraded": False, "quality": {"errors": []}},
                    }
                    report = execute_cycle(
                        symbol="AAPL",
                        config=cfg,
                        send=True,
                        client_factory=lambda _: _RejectClient(),
                    )
                runtime = get_runtime_state(db_path)
                system = get_system_status(db_path)
        self.assertEqual("DEGRADED", system["status"])
        self.assertTrue(runtime.cooldown_until)
        self.assertEqual("REJECTED", report["executions"][0]["lifecycle"]["transitions"][0]["next_state"])


if __name__ == "__main__":
    unittest.main()
