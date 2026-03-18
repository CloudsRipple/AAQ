from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.discipline import build_daily_discipline_plan, evaluate_hold_worthiness
from phase0.ibkr_order_adapter import map_decision_to_ibkr_bracket
from phase0.lanes.high import evaluate_event


class DisciplineAndIbkrAdapterTests(unittest.TestCase):
    def test_hold_score_and_daily_plan(self) -> None:
        hold = evaluate_hold_worthiness(
            market_row={"momentum_20d": 0.1, "relative_strength": 0.24, "volatility": 0.2},
            strategy_confidence=0.75,
            ultra_authenticity_score=0.8,
            low_committee_approved=True,
            hold_score_threshold=0.72,
            max_holding_days=3,
        )
        self.assertTrue(hold.score > 0.0)
        plan = build_daily_discipline_plan(
            actions_today=0,
            has_open_position=False,
            min_actions_per_day=1,
            discipline_enabled=True,
            hold=hold,
        )
        self.assertEqual("buy", plan["required_action"])

    def test_ibkr_mapping_uses_stp_and_transmit_chain(self) -> None:
        decision = evaluate_event(
            {
                "lane": "ultra",
                "kind": "signal",
                "symbol": "AAPL",
                "side": "buy",
                "entry_price": "100",
                "stop_loss_price": "95",
                "take_profit_price": "108",
                "equity": "100000",
                "current_exposure": "5000",
            }
        )
        self.assertEqual("accepted", decision["status"])
        payload = map_decision_to_ibkr_bracket(decision)
        self.assertIsNotNone(payload)
        assert payload is not None
        orders = payload["orders"]
        self.assertEqual("LMT", orders[0]["orderType"])
        self.assertEqual("LMT", orders[1]["orderType"])
        self.assertEqual("STP", orders[2]["orderType"])
        self.assertFalse(orders[0]["transmit"])
        self.assertFalse(orders[1]["transmit"])
        self.assertTrue(orders[2]["transmit"])


if __name__ == "__main__":
    unittest.main()
