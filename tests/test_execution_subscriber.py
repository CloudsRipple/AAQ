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
from phase0.lanes.bus import AsyncEventBus, LaneEvent
from phase0.models.signals import HighDecisionEvent, UltraSignalEvent
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


class ExecutionSubscriberTests(unittest.TestCase):
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

    async def _run_valid_high_decision_case(self, config: object) -> dict[str, object]:
        bus = AsyncEventBus(max_queue_size=32)
        market_snapshot = {"AAPL": {"reference_price": 100.0}}
        intent_queue = bus.subscribe("execution.intent")
        ultra = _base_ultra_signal("AAPL")
        high_decision = HighDecisionEvent(
            symbol="AAPL",
            approved=True,
            risk_multiplier=1.1,
            stop_loss_pct=0.05,
            reason="APPROVED",
            ultra_signal=ultra,
            decision_ts=datetime.now(tz=timezone.utc),
        )
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
