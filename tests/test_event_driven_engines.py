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

from phase0.ai.high import HighAdjustmentDecision, HighAssessment, start_high_engine
from phase0.ai.low import start_low_engine
from phase0.ai.ultra import start_ultra_engine
from phase0.config import load_config
from phase0.lanes.bus import AsyncEventBus, LaneEvent
from phase0.models.signals import TradeDecision, UltraSignalEvent
from phase0.state_store import get_latest_low_analysis_state, set_runtime_state, upsert_low_analysis_state


def _ultra_signal_payload(symbol: str = "AAPL") -> dict[str, object]:
    now = datetime.now(tz=timezone.utc)
    event = UltraSignalEvent(
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
            "snapshot_id": "snap-001",
            "snapshot_ts": now.isoformat(),
            "allow_opening": True,
            "data_degraded": False,
            "data_quality_errors": [],
        },
    )
    return event.model_dump(mode="json")


class EventDrivenHighEngineTests(unittest.TestCase):
    def test_high_engine_rejects_when_low_state_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "AI_ENABLED": "false"}, clear=False):
                config = load_config()
                payload = asyncio.run(self._run_high_once(config=config, seed_low=False))
        self.assertFalse(payload["approved"])
        self.assertEqual("LOW_ANALYSIS_UNAVAILABLE", payload["reason"])

    def test_high_engine_reads_low_state_from_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "AI_ENABLED": "false"}, clear=False):
                config = load_config()
                payload = asyncio.run(self._run_high_once(config=config, seed_low=True))
        self.assertNotEqual("LOW_ANALYSIS_UNAVAILABLE", payload["reason"])

    def test_high_engine_emits_execution_ready_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "AI_ENABLED": "false"}, clear=False):
                config = load_config()
                payload = asyncio.run(self._run_high_once(config=config, seed_low=True))
        self.assertTrue(payload["approved"])
        self.assertGreater(int(payload["quantity"]), 0)
        self.assertIn("bracket_order", payload)
        bracket = payload["bracket_order"]
        self.assertEqual("BUY", bracket["parent"]["action"])
        self.assertEqual("SELL", bracket["take_profit"]["action"])
        self.assertEqual("SELL", bracket["stop_loss"]["action"])
        self.assertEqual(payload["quantity"], bracket["parent"]["quantity"])
        self.assertEqual(payload["quantity"], bracket["take_profit"]["quantity"])
        self.assertEqual(payload["quantity"], bracket["stop_loss"]["quantity"])
        self.assertIn("estimated_transaction_cost", payload)
        TradeDecision.model_validate(payload)

    def test_high_engine_uses_governance_snapshot_instead_of_raw_ai_adjustment(self) -> None:
        forced_assessment = HighAssessment(
            decision=HighAdjustmentDecision(
                approved=True,
                risk_multiplier=1.5,
                stop_loss_pct=0.08,
                reason="FORCED_AI_APPROVAL",
            ),
            mode="local",
            committee_votes=[],
            prompt="forced",
        )
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "AI_ENABLED": "true"}, clear=False):
                config = load_config()
                with patch("phase0.ai.high.assess_high_lane_async", return_value=forced_assessment):
                    payload = asyncio.run(self._run_high_once(config=config, seed_low=True))
        self.assertEqual(1.0, float(payload["risk_multiplier"]))
        self.assertEqual(config.ai_stop_loss_default_pct, float(payload["stop_loss_pct"]))

    async def _run_high_once(self, *, config: object, seed_low: bool) -> dict[str, object]:
        cfg = config
        set_runtime_state(
            cfg.ai_state_db_path,
            drawdown=0.0,
            day_trade_count=0,
            cooldown_until="",
            kill_switch_active=False,
            equity=100000.0,
        )
        if seed_low:
            upsert_low_analysis_state(
                cfg.ai_state_db_path,
                symbol="AAPL",
                analysis={
                    "committee_approved": True,
                    "preferred_sector": "technology",
                    "strategy_fit": {"momentum": 0.8},
                    "sector_allocation": {"technology": 1.0},
                    "committee_votes": [{"model": "m1", "support": True, "score": 0.9}],
                },
            )

        bus = AsyncEventBus(max_queue_size=16)
        output_queue = bus.subscribe("high.decision")
        high_task = asyncio.create_task(
            start_high_engine(
                bus=bus,
                config=cfg,
                market_snapshot={"AAPL": {"reference_price": 100.0}},
            )
        )
        try:
            await asyncio.sleep(0)
            bus.publish(
                "ultra.signal",
                LaneEvent.from_payload(
                    event_type="signal",
                    source_lane="ultra",
                    payload=_ultra_signal_payload("AAPL"),
                ),
            )
            result_event = await asyncio.wait_for(output_queue.get(), timeout=1.0)
            output_queue.task_done()
            return dict(result_event.payload)
        finally:
            high_task.cancel()
            with suppress(asyncio.CancelledError):
                await high_task


class EventDrivenLowEngineTests(unittest.TestCase):
    def test_low_engine_persists_low_analysis_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "AI_ENABLED": "false"}, clear=False):
                config = load_config()
                state = asyncio.run(self._run_low_once(config))
        self.assertIsNotNone(state)
        assert state is not None
        self.assertIn("committee_approved", state["analysis"])

    async def _run_low_once(self, config: object) -> dict[str, object] | None:
        bus = AsyncEventBus(max_queue_size=16)
        low_task = asyncio.create_task(
            start_low_engine(
                bus=bus,
                config=config,
                market_snapshot={"AAPL": {"momentum_20d": 0.05, "relative_strength": 0.1, "sector": "technology"}},
                interval_seconds=60.0,
            )
        )
        try:
            await asyncio.sleep(0.1)
            return get_latest_low_analysis_state(config.ai_state_db_path, symbol="AAPL")
        finally:
            low_task.cancel()
            with suppress(asyncio.CancelledError):
                await low_task


class EventDrivenUltraEngineTests(unittest.TestCase):
    def test_ultra_engine_publishes_ultra_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            with patch.dict(os.environ, {"AI_STATE_DB_PATH": db_path, "AI_ENABLED": "false"}, clear=False):
                config = load_config()
                payload = asyncio.run(self._run_ultra_once(config))
        validated = UltraSignalEvent.model_validate(payload)
        self.assertEqual("AAPL", validated.symbol)
        self.assertGreater(validated.confidence_score, 0.0)

    async def _run_ultra_once(self, config: object) -> dict[str, object]:
        class _FakeSentinel:
            async def start(self) -> None:
                return None

            async def stop(self) -> None:
                return None

            async def on_market_tick(self, **kwargs: object) -> UltraSignalEvent | None:
                ts = kwargs.get("timestamp", datetime.now(tz=timezone.utc))
                return UltraSignalEvent(
                    symbol="AAPL",
                    timestamp=ts,
                    event_type="price_spike",
                    confidence_score=0.88,
                    source="rule_engine",
                    matched_prototype=None,
                    raw_data={
                        "side": "buy",
                        "price_current": 100.0,
                        "snapshot_id": "snap-ultra",
                        "snapshot_ts": ts.isoformat(),
                    },
                )

            async def on_news(self, **_: object) -> UltraSignalEvent | None:
                return None

        bus = AsyncEventBus(max_queue_size=16)
        output_queue = bus.subscribe("ultra.signal")
        with patch("phase0.ai.ultra.build_ultra_sentinel", return_value=_FakeSentinel()):
            ultra_task = asyncio.create_task(
                start_ultra_engine(
                    bus=bus,
                    config=config,
                    market_snapshot={"AAPL": {"reference_price": 100.0, "volume": 1000.0}},
                    headlines=[{"headline": "test", "published_at": datetime.now(tz=timezone.utc)}],
                    interval_seconds=0.01,
                )
            )
            try:
                event = await asyncio.wait_for(output_queue.get(), timeout=1.0)
                output_queue.task_done()
                return dict(event.payload)
            finally:
                ultra_task.cancel()
                with suppress(asyncio.CancelledError):
                    await ultra_task


if __name__ == "__main__":
    unittest.main()
