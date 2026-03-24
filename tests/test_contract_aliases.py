from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.kernel.contracts import ExecutionIntentEvent, HighDecisionEvent
from phase0.models.signals import OrderIntent, TradeDecision, UltraSignalEvent


class ContractAliasTests(unittest.TestCase):
    def test_alias_identity(self) -> None:
        self.assertIs(HighDecisionEvent, TradeDecision)
        self.assertIs(ExecutionIntentEvent, OrderIntent)

    def test_aliases_validate_same_payload(self) -> None:
        ts = datetime.now(tz=timezone.utc)
        ultra = UltraSignalEvent(
            symbol="AAPL",
            timestamp=ts,
            event_type="price_spike",
            confidence_score=0.9,
            source="rule_engine",
            matched_prototype=None,
            raw_data={"side": "buy", "snapshot_id": "snap-1", "snapshot_ts": ts.isoformat()},
        )
        decision_payload = {
            "symbol": "AAPL",
            "approved": False,
            "risk_multiplier": 1.0,
            "stop_loss_pct": 0.05,
            "reason": "TEST",
            "reject_reasons": ["TEST"],
            "ultra_signal": ultra.model_dump(mode="json"),
            "decision_ts": ts.isoformat(),
            "side": "buy",
            "strategy_id": "ultra_event",
            "signal_ts": ts.isoformat(),
            "snapshot_id": "snap-1",
            "snapshot_ts": ts.isoformat(),
            "allow_opening": True,
            "data_degraded": False,
            "data_quality_errors": [],
        }
        self.assertEqual(
            HighDecisionEvent.model_validate(decision_payload).model_dump(mode="json"),
            TradeDecision.model_validate(decision_payload).model_dump(mode="json"),
        )


if __name__ == "__main__":
    unittest.main()
