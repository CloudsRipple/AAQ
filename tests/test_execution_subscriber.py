from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.ai.high import start_high_engine
from phase0.config import load_config
from phase0.execution_subscriber import start_execution_subscriber
from phase0.kernel.contracts import ExecutionIntentEvent, HighDecisionEvent
from phase0.lanes.bus import AsyncEventBus, LaneEvent
from phase0.models.signals import OrderIntent, TradeDecision, UltraSignalEvent
from phase0.state_store import set_runtime_state, upsert_low_analysis_state


def _base_ultra_signal(symbol: str = "AAPL") -> UltraSignalEvent:
    now = datetime.now(tz=timezone.utc)
    return UltraSignalEvent(
        symbol=symbol,
        timestamp=now,
        event_type="price_spike",
        confidence_score=0.95,
        source="rule_engine",
        matched_prototype=None,
        raw_data={
            "side": "buy",
            "price_current": 100.0,
            "strategy": "ultra_event",
            "strategy_confidence": 0.95,
            "authenticity_score": 0.95,
            "quick_filter_score": 0.9,
            "snapshot_id": "snap-sub-001",
            "snapshot_ts": now.isoformat(),
            "allow_opening": True,
            "data_degraded": False,
            "data_quality_errors": [],
        },
    )


def _base_bracket_order(symbol: str = "AAPL", quantity: int = 10) -> dict[str, object]:
    return {
        "parent": {
            "symbol": symbol,
            "client_order_id": f"{symbol}-PARENT",
            "quantity": quantity,
            "limit_price": 100.0,
            "action": "BUY",
            "time_in_force": "DAY",
        },
        "take_profit": {
            "symbol": symbol,
            "client_order_id": f"{symbol}-TAKE-PROFIT",
            "quantity": quantity,
            "limit_price": 110.0,
            "action": "SELL",
            "time_in_force": "GTC",
        },
        "stop_loss": {
            "symbol": symbol,
            "client_order_id": f"{symbol}-STOP-LOSS",
            "quantity": quantity,
            "stop_price": 95.0,
            "action": "SELL",
            "time_in_force": "GTC",
        },
    }


def _execution_ready_high_decision(symbol: str = "AAPL") -> TradeDecision:
    ultra = _base_ultra_signal(symbol)
    ts = ultra.timestamp
    return TradeDecision(
        symbol=symbol,
        approved=True,
        risk_multiplier=1.1,
        stop_loss_pct=0.05,
        reason="APPROVED",
        reject_reasons=[],
        ultra_signal=ultra,
        decision_ts=ts,
        side="buy",
        strategy_id="ultra_event",
        signal_ts=ts,
        snapshot_id="snap-sub-001",
        snapshot_ts=ts,
        quantity=10,
        bracket_order=_base_bracket_order(symbol=symbol, quantity=10),
        estimated_transaction_cost={"slippage_cost": 2.0, "commission_cost": 1.0, "total": 3.0},
        allow_opening=True,
        data_degraded=False,
        data_quality_errors=[],
    )


def _execution_ready_intent(symbol: str = "AAPL") -> OrderIntent:
    now = datetime.now(tz=timezone.utc)
    return OrderIntent(
        symbol=symbol,
        side="buy",
        entry_price=100.0,
        stop_loss=95.0,
        take_profit=110.0,
        equity=100000.0,
        current_symbol_exposure=5000.0,
        last_exit_at=now,
        last_exit_reason="NOT_AVAILABLE_IN_STATE_STORE",
        snapshot_id="snap-intent-001",
        snapshot_ts=now,
        strategy_id="ultra_event",
        risk_multiplier=1.1,
        stop_loss_pct=0.05,
        high_reason="APPROVED",
        ultra_signal=_base_ultra_signal(symbol),
        quantity=10,
        bracket_order=_base_bracket_order(symbol=symbol, quantity=10),
        estimated_transaction_cost={"slippage_cost": 2.0, "commission_cost": 1.0, "total": 3.0},
        allow_opening=True,
        data_degraded=False,
        data_quality_errors=[],
    )


class ExecutionSubscriberTests(unittest.TestCase):
    def test_contract_aliases_remain_available(self) -> None:
        self.assertIs(HighDecisionEvent, TradeDecision)
        self.assertIs(ExecutionIntentEvent, OrderIntent)

    def test_fail_closed_when_high_decision_contract_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "AI_ENABLED": "false"}, clear=False):
                config = load_config()
                set_runtime_state(
                    db_path,
                    drawdown=0.0,
                    day_trade_count=0,
                    cooldown_until="",
                    kill_switch_active=False,
                    equity=100000.0,
                )
                called = asyncio.run(self._run_fail_closed_case(config))
        self.assertFalse(called)

    def test_builds_execution_intent_and_calls_unified_control_plane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "AI_ENABLED": "false"}, clear=False):
                config = load_config()
                set_runtime_state(
                    db_path,
                    drawdown=0.0,
                    day_trade_count=0,
                    cooldown_until="",
                    kill_switch_active=False,
                    equity=100000.0,
                )
                result = asyncio.run(self._run_valid_high_decision_case(config))
        self.assertTrue(result["called"])
        self.assertEqual("AAPL", result["intent_symbol"])

    def test_ultra_to_high_to_execution_intent_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "AI_ENABLED": "false"}, clear=False):
                config = load_config()
                set_runtime_state(
                    db_path,
                    drawdown=0.0,
                    day_trade_count=0,
                    cooldown_until="",
                    kill_switch_active=False,
                    equity=100000.0,
                )
                upsert_low_analysis_state(
                    db_path,
                    symbol="AAPL",
                    analysis={
                        "committee_approved": True,
                        "preferred_sector": "technology",
                        "strategy_fit": {"momentum": 0.8},
                        "sector_allocation": {"technology": 1.0},
                        "committee_votes": [{"model": "m1", "support": True, "score": 0.9}],
                    },
                )
                result = asyncio.run(self._run_full_chain_case(config))
        self.assertTrue(result["execute_called"])
        self.assertEqual("AAPL", result["high_symbol"])
        self.assertEqual("AAPL", result["intent_symbol"])
        self.assertGreater(int(result["high_quantity"]), 0)
        self.assertIn("bracket_order", result["high_payload"])

    def test_execution_subscriber_does_not_re_evaluate_high(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "AI_ENABLED": "false"}, clear=False):
                config = load_config()
                set_runtime_state(
                    db_path,
                    drawdown=0.0,
                    day_trade_count=0,
                    cooldown_until="",
                    kill_switch_active=False,
                    equity=100000.0,
                )
                result = asyncio.run(self._run_execution_intent_only_case(config))
        self.assertTrue(result["execute_called"])
        self.assertFalse(result["evaluate_called"])

    async def _run_fail_closed_case(self, config: object) -> bool:
        bus = AsyncEventBus(max_queue_size=16)
        market_snapshot = {"AAPL": {"reference_price": 100.0}}
        with patch("phase0.execution_subscriber.execute_intents_with_control_plane") as mocked_execute:
            sub_task = asyncio.create_task(
                start_execution_subscriber(
                    bus=bus,
                    config=config,
                    market_snapshot=market_snapshot,
                )
            )
            try:
                await asyncio.sleep(0)
                bus.publish(
                    "high.decision",
                    LaneEvent.from_payload(
                        event_type="decision",
                        source_lane="high",
                        payload={"symbol": "AAPL", "approved": True},
                    ),
                )
                await asyncio.sleep(0.1)
                return mocked_execute.called
            finally:
                sub_task.cancel()
                with suppress(asyncio.CancelledError):
                    await sub_task

    async def _run_execution_intent_only_case(self, config: object) -> dict[str, object]:
        bus = AsyncEventBus(max_queue_size=32)
        execution_intent = _execution_ready_intent("AAPL")
        with patch(
            "phase0.execution_subscriber.evaluate_event",
            create=True,
        ) as mocked_evaluate, patch(
            "phase0.execution_subscriber.execute_intents_with_control_plane",
            return_value={"executions": [{"ok": True}]},
        ) as mocked_execute:
            sub_task = asyncio.create_task(
                start_execution_subscriber(
                    bus=bus,
                    config=config,
                    market_snapshot={"AAPL": {"reference_price": 100.0}},
                )
            )
            try:
                await asyncio.sleep(0)
                bus.publish(
                    "execution.intent",
                    LaneEvent.from_payload(
                        event_type="intent",
                        source_lane="execution",
                        payload=execution_intent.model_dump(mode="json"),
                    ),
                )
                await asyncio.sleep(0.1)
                return {
                    "evaluate_called": mocked_evaluate.called,
                    "execute_called": mocked_execute.called,
                }
            finally:
                sub_task.cancel()
                with suppress(asyncio.CancelledError):
                    await sub_task

    async def _run_valid_high_decision_case(self, config: object) -> dict[str, object]:
        bus = AsyncEventBus(max_queue_size=32)
        market_snapshot = {"AAPL": {"reference_price": 100.0}}
        intent_queue = bus.subscribe("execution.intent")
        high_decision = _execution_ready_high_decision("AAPL")
        with patch(
            "phase0.execution_subscriber.execute_intents_with_control_plane",
            return_value={"executions": [{"ok": True}]},
        ) as mocked_execute:
            sub_task = asyncio.create_task(
                start_execution_subscriber(
                    bus=bus,
                    config=config,
                    market_snapshot=market_snapshot,
                )
            )
            try:
                await asyncio.sleep(0)
                bus.publish(
                    "high.decision",
                    LaneEvent.from_payload(
                        event_type="decision",
                        source_lane="high",
                        payload=high_decision.model_dump(mode="json"),
                    ),
                )
                intent_event = await asyncio.wait_for(intent_queue.get(), timeout=1.0)
                intent_queue.task_done()
                await asyncio.sleep(0.1)
                return {
                    "called": mocked_execute.called,
                    "intent_symbol": intent_event.payload.get("symbol", ""),
                }
            finally:
                sub_task.cancel()
                with suppress(asyncio.CancelledError):
                    await sub_task

    async def _run_full_chain_case(self, config: object) -> dict[str, object]:
        bus = AsyncEventBus(max_queue_size=32)
        market_snapshot = {"AAPL": {"reference_price": 100.0, "volume": 1000.0}}
        high_queue = bus.subscribe("high.decision")
        intent_queue = bus.subscribe("execution.intent")
        with patch(
            "phase0.execution_subscriber.execute_intents_with_control_plane",
            return_value={"executions": [{"ok": True}]},
        ) as mocked_execute:
            high_task = asyncio.create_task(
                start_high_engine(
                    bus=bus,
                    config=config,
                    market_snapshot=market_snapshot,
                )
            )
            sub_task = asyncio.create_task(
                start_execution_subscriber(
                    bus=bus,
                    config=config,
                    market_snapshot=market_snapshot,
                )
            )
            try:
                await asyncio.sleep(0)
                ultra = _base_ultra_signal("AAPL")
                bus.publish(
                    "ultra.signal",
                    LaneEvent.from_payload(
                        event_type="signal",
                        source_lane="ultra",
                        payload=ultra.model_dump(mode="json"),
                    ),
                )
                high_event = await asyncio.wait_for(high_queue.get(), timeout=1.0)
                high_queue.task_done()
                intent_event = await asyncio.wait_for(intent_queue.get(), timeout=1.0)
                intent_queue.task_done()
                await asyncio.sleep(0.1)
                return {
                    "execute_called": mocked_execute.called,
                    "high_symbol": high_event.payload.get("symbol", ""),
                    "high_quantity": high_event.payload.get("quantity", 0),
                    "high_payload": dict(high_event.payload),
                    "intent_symbol": intent_event.payload.get("symbol", ""),
                }
            finally:
                high_task.cancel()
                sub_task.cancel()
                with suppress(asyncio.CancelledError):
                    await high_task
                with suppress(asyncio.CancelledError):
                    await sub_task


if __name__ == "__main__":
    unittest.main()
