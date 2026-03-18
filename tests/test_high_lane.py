from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.lanes.high import HighLaneSettings, evaluate_event


class HighLaneRuleEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        now = datetime.now(tz=timezone.utc)
        self.base_event = {
            "lane": "ultra",
            "kind": "signal",
            "symbol": "AAPL",
            "side": "buy",
            "entry_price": "100",
            "stop_loss_price": "95",
            "take_profit_price": "108",
            "equity": "100000",
            "current_exposure": "5000",
            "last_exit_at": (now - timedelta(days=3)).isoformat(),
        }

    def test_accepts_and_builds_bracket_order(self) -> None:
        decision = evaluate_event(self.base_event)
        self.assertEqual("accepted", decision["status"])
        self.assertIsInstance(decision["quantity"], int)
        self.assertGreater(decision["quantity"], 0)
        self.assertEqual([], decision["reject_reasons"])
        bracket = decision["bracket_order"]
        self.assertEqual("BUY", bracket["parent"]["action"])
        self.assertEqual("SELL", bracket["take_profit"]["action"])
        self.assertEqual("SELL", bracket["stop_loss"]["action"])
        self.assertEqual(decision["quantity"], bracket["parent"]["quantity"])
        self.assertEqual(decision["quantity"], bracket["take_profit"]["quantity"])
        self.assertEqual(decision["quantity"], bracket["stop_loss"]["quantity"])
        self.assertEqual("LIMIT", bracket["parent"]["order_type"])
        self.assertEqual("LIMIT", bracket["take_profit"]["order_type"])
        self.assertEqual("STOP", bracket["stop_loss"]["order_type"])

    def test_enforces_single_trade_risk_1pct(self) -> None:
        event = dict(self.base_event)
        event["entry_price"] = "100"
        event["stop_loss_price"] = "75"
        decision = evaluate_event(event)
        self.assertEqual("rejected", decision["status"])
        self.assertIn("STOP_LOSS_RANGE_INVALID", decision["reject_reasons"])

    def test_applies_min_trade_unit_when_risk_budget_is_below_one_share(self) -> None:
        event = dict(self.base_event)
        event["equity"] = "100"
        event["current_exposure"] = "0"
        decision = evaluate_event(event, settings=HighLaneSettings(total_exposure_limit_pct=1.0))
        self.assertEqual("accepted", decision["status"])
        self.assertEqual(1, decision["quantity"])
        self.assertTrue(decision["min_trade_units_applied"])

    def test_rejects_with_cooldown_reason(self) -> None:
        event = dict(self.base_event)
        event["last_exit_at"] = (datetime.now(tz=timezone.utc) - timedelta(hours=12)).isoformat()
        decision = evaluate_event(event)
        self.assertEqual("rejected", decision["status"])
        self.assertIn("COOLDOWN_24H_ACTIVE", decision["reject_reasons"])

    def test_rejects_when_holding_period_exceeded(self) -> None:
        event = dict(self.base_event)
        event["position_opened_at"] = (datetime.now(tz=timezone.utc) - timedelta(days=3)).isoformat()
        decision = evaluate_event(event)
        self.assertEqual("rejected", decision["status"])
        self.assertIn("HOLDING_PERIOD_EXCEEDED", decision["reject_reasons"])

    def test_rejects_when_exposure_limit_prevents_integer_shares(self) -> None:
        event = dict(self.base_event)
        event["current_exposure"] = "29999.5"
        event["equity"] = "100000"
        event["entry_price"] = "100"
        decision = evaluate_event(event)
        self.assertEqual("rejected", decision["status"])
        self.assertIn("TOTAL_EXPOSURE_LIMIT", decision["reject_reasons"])

    def test_rejects_when_stop_loss_equals_entry(self) -> None:
        event = dict(self.base_event)
        event["entry_price"] = "100"
        event["stop_loss_price"] = "100"
        decision = evaluate_event(event)
        self.assertEqual("rejected", decision["status"])
        self.assertIn("STOP_LOSS_DIRECTION_INVALID", decision["reject_reasons"])

    def test_rejects_when_source_lane_is_not_ultra(self) -> None:
        event = dict(self.base_event)
        event["lane"] = "low"
        decision = evaluate_event(event)
        self.assertEqual("rejected", decision["status"])
        self.assertIn("SOURCE_LANE_INVALID", decision["reject_reasons"])

    def test_rejects_when_event_kind_is_invalid(self) -> None:
        event = dict(self.base_event)
        event["kind"] = "order"
        decision = evaluate_event(event)
        self.assertEqual("rejected", decision["status"])
        self.assertIn("EVENT_KIND_INVALID", decision["reject_reasons"])

    def test_generates_unique_client_order_id(self) -> None:
        first = evaluate_event(self.base_event)
        second = evaluate_event(self.base_event)
        self.assertEqual("accepted", first["status"])
        self.assertEqual("accepted", second["status"])
        first_parent = first["bracket_order"]["parent"]["client_order_id"]
        second_parent = second["bracket_order"]["parent"]["client_order_id"]
        self.assertNotEqual(first_parent, second_parent)

    def test_supports_adjustable_risk_settings(self) -> None:
        event = dict(self.base_event)
        event["current_exposure"] = "25000"
        settings = HighLaneSettings(total_exposure_limit_pct=0.4)
        decision = evaluate_event(event, settings=settings)
        self.assertEqual("accepted", decision["status"])

    def test_rejects_when_settings_boundary_invalid(self) -> None:
        settings = HighLaneSettings(stop_loss_min_pct=0.09, stop_loss_max_pct=0.08)
        decision = evaluate_event(self.base_event, settings=settings)
        self.assertEqual("rejected", decision["status"])
        self.assertIn("STOP_LOSS_SETTINGS_INVALID", decision["reject_reasons"])

    def test_handles_large_numeric_inputs_stably(self) -> None:
        event = dict(self.base_event)
        event["entry_price"] = "250.5"
        event["stop_loss_price"] = "237.5"
        event["take_profit_price"] = "290.0"
        event["equity"] = "999999999"
        event["current_exposure"] = "120000000"
        decision = evaluate_event(event)
        self.assertEqual("accepted", decision["status"])
        self.assertGreater(decision["quantity"], 0)

    def test_applies_strategy_adjustments_with_bounds(self) -> None:
        settings = HighLaneSettings(risk_multiplier_min=0.6, risk_multiplier_max=1.2, take_profit_boost_max_pct=0.1)
        decision = evaluate_event(
            self.base_event,
            settings=settings,
            strategy_adjustments={"risk_multiplier": 2.0, "take_profit_boost_pct": 0.5},
        )
        self.assertEqual("accepted", decision["status"])
        self.assertEqual(1.2, decision["applied_risk_multiplier"])
        self.assertEqual(0.1, decision["applied_take_profit_boost_pct"])

    def test_respects_configured_holding_days_in_max_hold_until(self) -> None:
        settings = HighLaneSettings(holding_days=3)
        now = datetime.now(tz=timezone.utc)
        decision = evaluate_event(self.base_event, settings=settings)
        self.assertEqual("accepted", decision["status"])
        hold_until = datetime.fromisoformat(decision["bracket_order"]["max_hold_until"])
        delta_days = (hold_until - now).total_seconds() / 86400.0
        self.assertGreater(delta_days, 2.8)


if __name__ == "__main__":
    unittest.main()
