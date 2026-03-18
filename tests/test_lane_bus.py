from __future__ import annotations

from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import load_config
from phase0.lanes import InMemoryLaneBus, LaneEvent, run_lane_cycle, run_lane_cycle_with_guard


class LaneBusTests(unittest.TestCase):
    def test_deduplicates_same_event(self) -> None:
        bus = InMemoryLaneBus()
        payload = {"symbol": "AAPL", "lane": "ultra", "kind": "signal"}
        event = LaneEvent.from_payload(event_type="signal", source_lane="ultra", payload=payload)
        first_ok = bus.publish("ultra.signal", event)
        second_ok = bus.publish("ultra.signal", event)
        self.assertTrue(first_ok)
        self.assertFalse(second_ok)
        items = bus.consume("ultra.signal")
        self.assertEqual(1, len(items))

    def test_runs_lane_cycle_and_returns_decision(self) -> None:
        config = load_config()
        output = run_lane_cycle("AAPL", config=config)
        self.assertIn("event", output)
        self.assertIn("decisions", output)
        self.assertIn("watchlist", output)
        decisions = output["decisions"]
        self.assertTrue(decisions)
        self.assertEqual("high", decisions[0]["lane"])

    def test_eviction_allows_republish_after_capacity_rollover(self) -> None:
        bus = InMemoryLaneBus(dedup_capacity=2)
        event_a = LaneEvent.from_payload(
            event_type="signal",
            source_lane="ultra",
            payload={"symbol": "AAPL", "seq": 1},
        )
        event_b = LaneEvent.from_payload(
            event_type="signal",
            source_lane="ultra",
            payload={"symbol": "AAPL", "seq": 2},
        )
        event_c = LaneEvent.from_payload(
            event_type="signal",
            source_lane="ultra",
            payload={"symbol": "AAPL", "seq": 3},
        )
        self.assertTrue(bus.publish("ultra.signal", event_a))
        self.assertTrue(bus.publish("ultra.signal", event_b))
        self.assertTrue(bus.publish("ultra.signal", event_c))
        self.assertTrue(bus.publish("ultra.signal", event_a))

    def test_lane_cycle_stays_stable_under_repeated_runs(self) -> None:
        config = load_config()
        accepted = 0
        for _ in range(200):
            output = run_lane_cycle("AAPL", config=config)
            decisions = output["decisions"]
            self.assertTrue(decisions)
            self.assertIn(decisions[0]["status"], {"accepted", "rejected"})
            if decisions[0]["status"] == "accepted":
                accepted += 1
        self.assertGreater(accepted, 0)

    def test_guard_blocks_risk_execution(self) -> None:
        config = load_config()
        output = run_lane_cycle_with_guard("AAPL", config=config, allow_risk_execution=False)
        decisions = output["decisions"]
        self.assertTrue(decisions)
        self.assertEqual("rejected", decisions[0]["status"])
        self.assertIn("SAFETY_MODE_BLOCKED", decisions[0]["reject_reasons"])

    def test_seed_event_boolean_block_is_handled(self) -> None:
        config = load_config()
        output = run_lane_cycle(
            "AAPL",
            config=config,
            seed_event={
                "lane": "ultra",
                "kind": "signal",
                "symbol": "AAPL",
                "side": "buy",
                "entry_price": "100",
                "stop_loss_price": "95",
                "take_profit_price": "110",
                "equity": "100000",
                "current_exposure": "12000",
                "allow_risk_execution": False,
            },
        )
        decisions = output["decisions"]
        self.assertTrue(decisions)
        self.assertEqual("rejected", decisions[0]["status"])
        self.assertIn("SAFETY_MODE_BLOCKED", decisions[0]["reject_reasons"])

    def test_lane_cycle_returns_strategy_signals(self) -> None:
        config = load_config()
        output = run_lane_cycle("AAPL", config=config)
        signals = output["strategy_signals"]
        self.assertTrue(signals)
        self.assertIn("strategy", signals[0])
        self.assertIn("ultra_signal", output)
        self.assertIn("low_analysis", output)
        self.assertIn("memory_context", output)
        self.assertIn("low_async_analysis", output)
        self.assertIn("high_assessment", output)
        self.assertIn("daily_discipline", output)
        self.assertIn("ibkr_order_signals", output)

    def test_lane_cycle_bypasses_ai_when_disabled(self) -> None:
        with patch.dict("os.environ", {"AI_ENABLED": "false"}, clear=False):
            config = load_config()
        output = run_lane_cycle("AAPL", config=config)
        self.assertTrue(output["ai_bypassed"])
        self.assertEqual("AI_BYPASSED", output["ultra_signal"]["reason"])
        self.assertEqual(1.0, output["ultra_signal"]["quick_filter_score"])
        self.assertEqual([], output["memory_context"])
        self.assertEqual(0, output["low_async_processed"])

    def test_lane_cycle_daily_discipline_buy_when_no_position(self) -> None:
        config = load_config()
        output = run_lane_cycle(
            "AAPL",
            config=config,
            daily_state={"actions_today": 0, "has_open_position": False},
        )
        self.assertEqual("buy", output["daily_discipline"]["required_action"])


if __name__ == "__main__":
    unittest.main()
