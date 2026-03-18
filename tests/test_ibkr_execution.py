from __future__ import annotations

from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import load_config
from phase0.ibkr_execution import (
    ExecutionConfig,
    IbkrExecutionClient,
    _build_idempotency_key,
    _parse_hhmm,
    execute_cycle,
)
from phase0.state_store import get_runtime_state, list_execution_reports, set_system_status


class _FakeOrder:
    def __init__(self) -> None:
        self.orderId = None
        self.permId = None
        self.orderRef = ""
        self.tif = "DAY"
        self.transmit = False
        self.account = ""


class _FakeTrade:
    def __init__(self, order: _FakeOrder, idx: int) -> None:
        self.order = order
        self.order.orderId = 100 + idx
        self.order.permId = 200 + idx
        self.orderStatus = type("_Status", (), {"status": "Submitted"})()


class _FakeIB:
    def __init__(self) -> None:
        self.connected = False
        self.placed: list[_FakeOrder] = []

    def connect(self, host: str, port: int, clientId: int, timeout: float, readonly: bool) -> None:
        self.connected = True

    def isConnected(self) -> bool:
        return self.connected

    def disconnect(self) -> None:
        self.connected = False

    def qualifyContracts(self, contract: object) -> None:
        return None

    def bracketOrder(
        self,
        action: str,
        quantity: float,
        limitPrice: float,
        takeProfitPrice: float,
        stopLossPrice: float,
    ) -> tuple[_FakeOrder, _FakeOrder, _FakeOrder]:
        return _FakeOrder(), _FakeOrder(), _FakeOrder()

    def placeOrder(self, contract: object, order: _FakeOrder) -> _FakeTrade:
        self.placed.append(order)
        return _FakeTrade(order, len(self.placed))


def _fake_stock(symbol: str, exchange: str, currency: str) -> dict[str, str]:
    return {"symbol": symbol, "exchange": exchange, "currency": currency}


class IbkrExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self._db_path = str(Path(self._tmp_dir.name) / "state.db")
        self._env_patch = patch.dict("os.environ", {"AI_STATE_DB_PATH": self._db_path}, clear=False)
        self._env_patch.start()

    def tearDown(self) -> None:
        self._env_patch.stop()
        self._tmp_dir.cleanup()

    def test_submit_bracket_signal_with_ibkr_semantics(self) -> None:
        client = IbkrExecutionClient(
            ExecutionConfig(),
            ib_factory=lambda: _FakeIB(),
            stock_factory=_fake_stock,
        )
        result = client.submit_bracket_signal(
            {
                "contract": {"symbol": "AAPL", "exchange": "SMART", "currency": "USD"},
                "orders": [
                    {
                        "orderRef": "P",
                        "action": "BUY",
                        "orderType": "LMT",
                        "totalQuantity": 10,
                        "lmtPrice": 100.0,
                        "tif": "DAY",
                        "transmit": False,
                    },
                    {
                        "orderRef": "TP",
                        "parentRef": "P",
                        "action": "SELL",
                        "orderType": "LMT",
                        "totalQuantity": 10,
                        "lmtPrice": 108.0,
                        "tif": "GTC",
                        "transmit": False,
                    },
                    {
                        "orderRef": "SL",
                        "parentRef": "P",
                        "action": "SELL",
                        "orderType": "STP",
                        "totalQuantity": 10,
                        "auxPrice": 95.0,
                        "tif": "GTC",
                        "transmit": True,
                    },
                ],
            }
        )
        self.assertTrue(result["ok"])
        self.assertEqual(3, len(result["orders"]))
        self.assertEqual("Submitted", result["orders"][0]["status"])
        client.close()

    def test_execute_cycle_dry_run_returns_signal(self) -> None:
        config = load_config()
        report = execute_cycle(symbol="AAPL", config=config, send=False)
        self.assertEqual("phase0_ibkr_execution", report["kind"])
        self.assertIn("lane", report)
        self.assertIn("executions", report)
        self.assertTrue(report["signals_count"] >= 0)

    def test_execute_cycle_send_with_injected_client(self) -> None:
        config = load_config()

        class _FakeExecClient:
            def submit_bracket_signal(self, signal: dict[str, object]) -> dict[str, object]:
                return {"ok": True, "signal": signal}

            def reconcile_snapshot(self) -> dict[str, object]:
                return {"ok": True, "open_orders": [], "positions": [], "trades": []}

            def activate_kill_switch(self) -> dict[str, object]:
                return {"ok": True, "cancelled_orders": 0, "flattened_positions": 0}

            def close(self) -> None:
                return None

        with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_cycle:
            mocked_cycle.return_value = {"ibkr_order_signals": [{"contract": {"symbol": "AAPL"}, "orders": [1, 2, 3]}]}
            report = execute_cycle(
                symbol="AAPL",
                config=config,
                send=True,
                client_factory=lambda _: _FakeExecClient(),
            )
        self.assertEqual(1, report["signals_count"])
        self.assertTrue(report["executions"][0]["ok"])

    def test_execute_cycle_send_continues_when_single_signal_fails(self) -> None:
        config = load_config()

        class _FlakyExecClient:
            def __init__(self) -> None:
                self._called = 0

            def submit_bracket_signal(self, signal: dict[str, object]) -> dict[str, object]:
                self._called += 1
                if self._called == 1:
                    raise RuntimeError("boom")
                return {"ok": True, "signal": signal}

            def reconcile_snapshot(self) -> dict[str, object]:
                return {"ok": True, "open_orders": [], "positions": [], "trades": []}

            def activate_kill_switch(self) -> dict[str, object]:
                return {"ok": True, "cancelled_orders": 0, "flattened_positions": 0}

            def close(self) -> None:
                return None

        with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_cycle:
            mocked_cycle.return_value = {
                "ibkr_order_signals": [
                    {"contract": {"symbol": "AAPL"}, "orders": [1, 2, 3]},
                    {"contract": {"symbol": "MSFT"}, "orders": [1, 2, 3]},
                ]
            }
            report = execute_cycle(
                symbol="AAPL",
                config=config,
                send=True,
                client_factory=lambda _: _FlakyExecClient(),
            )
        self.assertEqual(2, report["signals_count"])
        self.assertEqual(2, len(report["executions"]))
        self.assertFalse(report["executions"][0]["ok"])
        self.assertEqual("RuntimeError", report["executions"][0]["error"])
        self.assertTrue(report["executions"][1]["ok"])

    def test_execute_cycle_keeps_halted_state(self) -> None:
        config = load_config()
        set_system_status(self._db_path, "HALTED", "PRESET")
        with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_cycle:
            mocked_cycle.return_value = {
                "ibkr_order_signals": [{"contract": {"symbol": "AAPL"}, "orders": [1, 2, 3]}],
                "data_quality_gate": {"degraded": False, "quality": {"errors": []}},
            }
            report = execute_cycle(
                symbol="AAPL",
                config=config,
                send=True,
            )
        self.assertEqual("HALTED", report["system_state"]["status"])
        self.assertEqual("SYSTEM_HALTED_BY_RISK", report["blocked_reason"])

    def test_idempotency_key_distinguishes_quantity_and_price(self) -> None:
        base = {
            "strategy_id": "s1",
            "signal_ts": "2026-03-15T13:30:00+00:00",
            "side": "BUY",
            "contract": {"symbol": "AAPL"},
            "orders": [
                {"orderRef": "ORD-1", "action": "BUY", "totalQuantity": 10, "lmtPrice": 100.0},
            ],
        }
        changed = {
            **base,
            "orders": [
                {"orderRef": "ORD-1", "action": "BUY", "totalQuantity": 20, "lmtPrice": 101.0},
            ],
        }
        key1 = _build_idempotency_key(base)["idempotency_key"]
        key2 = _build_idempotency_key(changed)["idempotency_key"]
        self.assertNotEqual(key1, key2)

    def test_execute_cycle_updates_drawdown_before_risk_evaluation(self) -> None:
        config = load_config()
        observed: dict[str, float] = {}

        def _capture_risk(*, intents: list[dict[str, object]], config: object, lane_output: dict[str, object]) -> dict[str, object]:
            observed["drawdown"] = get_runtime_state(self._db_path).drawdown
            return {
                "approved_intents": list(intents),
                "rejected_intents": [],
                "decisions": [],
                "fail_closed": False,
                "hard_stop": False,
                "risk_unavailable_mode": False,
            }

        with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_cycle, patch(
            "phase0.ibkr_execution.evaluate_order_intents", side_effect=_capture_risk
        ), patch("phase0.ibkr_execution._read_current_drawdown_pct", return_value=0.23):
            mocked_cycle.return_value = {"ibkr_order_signals": [], "data_quality_gate": {"degraded": False, "quality": {"errors": []}}}
            execute_cycle(symbol="AAPL", config=config, send=False)
        self.assertEqual(0.23, observed["drawdown"])

    def test_parse_hhmm_rejects_invalid_seconds(self) -> None:
        self.assertIsNone(_parse_hhmm("13:30:99"))
        self.assertEqual(13 * 60 + 30, _parse_hhmm("13:30:59"))

    def test_execute_cycle_marks_post_submit_error_without_failed_dedup(self) -> None:
        config = load_config()

        class _OkExecClient:
            def submit_bracket_signal(self, signal: dict[str, object]) -> dict[str, object]:
                return {"ok": True, "orders": [{"order_ref": "P", "status": "Submitted"}], "signal": signal}

            def reconcile_snapshot(self) -> dict[str, object]:
                return {"ok": True, "open_orders": [], "positions": [], "trades": []}

            def activate_kill_switch(self) -> dict[str, object]:
                return {"ok": True, "cancelled_orders": 0, "flattened_positions": 0}

            def close(self) -> None:
                return None

        with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_cycle, patch(
            "phase0.ibkr_execution.process_execution_report", side_effect=RuntimeError("post submit failed")
        ):
            mocked_cycle.return_value = {"ibkr_order_signals": [{"contract": {"symbol": "AAPL"}, "orders": [1, 2, 3]}]}
            report = execute_cycle(
                symbol="AAPL",
                config=config,
                send=True,
                client_factory=lambda _: _OkExecClient(),
            )
        self.assertTrue(report["executions"][0]["ok"])
        self.assertIn("post_submit_error", report["executions"][0])
        persisted = list_execution_reports(self._db_path, limit=1)
        self.assertEqual("runtime", persisted[0]["post_submit_error"]["category"])

    def test_execute_cycle_routes_through_unified_control_plane(self) -> None:
        config = load_config()
        expected = {"kind": "phase0_ibkr_execution", "via": "unified", "executions": []}
        with patch("phase0.ibkr_execution.run_lane_cycle", return_value={"ibkr_order_signals": []}), patch(
            "phase0.ibkr_execution.execute_intents_with_control_plane",
            return_value=expected,
        ) as mocked_unified:
            report = execute_cycle(symbol="AAPL", config=config, send=False)
        self.assertEqual(expected, report)
        mocked_unified.assert_called_once()


if __name__ == "__main__":
    unittest.main()
