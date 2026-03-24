from __future__ import annotations

from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.advisory.contracts import AdjustmentProposal
from phase0.advisory.governance import GovernanceOutcome, GovernancePlane
from phase0.config import load_config


def _proposal(*, target_param: str, suggested_value: float, mode: str) -> AdjustmentProposal:
    return AdjustmentProposal(
        proposal_id=f"proposal-{target_param}",
        scope="symbol:AAPL",
        target_param=target_param,
        current_value=1.0,
        suggested_value=suggested_value,
        min_allowed=0.5,
        max_allowed=1.5,
        confidence=0.9,
        reason="test",
        evidence_refs=["unit-test"],
        ttl_seconds=300,
        mode=mode,
    )


class GovernancePlaneTests(unittest.TestCase):
    def test_shadow_mode_audits_but_does_not_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "AI_STATE_DB_PATH": str(Path(tmp) / "state.db"),
                "AI_ENABLED": "true",
                "AI_GOVERNANCE_MODE": "SHADOW",
                "PHASE0_PROFILE": "paper",
            }
            with patch.dict(os.environ, env, clear=False):
                config = load_config()
                plane = GovernancePlane.from_app_config(config)
                baseline = plane.current_snapshot()
                decision = plane.submit_adjustment(
                    _proposal(target_param="high.risk_multiplier", suggested_value=1.4, mode="SHADOW")
                )
        self.assertEqual(GovernanceOutcome.SHADOWED, decision.outcome)
        self.assertEqual(baseline.risk_multiplier, plane.current_snapshot().risk_multiplier)

    def test_bounded_auto_applies_on_paper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "AI_STATE_DB_PATH": str(Path(tmp) / "state.db"),
                "AI_ENABLED": "true",
                "AI_GOVERNANCE_MODE": "BOUNDED_AUTO",
                "PHASE0_PROFILE": "paper",
            }
            with patch.dict(os.environ, env, clear=False):
                config = load_config()
                plane = GovernancePlane.from_app_config(config)
                decision = plane.submit_adjustment(
                    _proposal(target_param="high.risk_multiplier", suggested_value=1.3, mode="BOUNDED_AUTO")
                )
        self.assertEqual(GovernanceOutcome.APPROVED_AUTO, decision.outcome)
        self.assertEqual(1.3, plane.current_snapshot().risk_multiplier)

    def test_bounded_auto_rejected_on_non_paper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                "AI_STATE_DB_PATH": str(Path(tmp) / "state.db"),
                "AI_ENABLED": "true",
                "AI_GOVERNANCE_MODE": "BOUNDED_AUTO",
                "PHASE0_PROFILE": "local",
            }
            with patch.dict(os.environ, env, clear=False):
                config = load_config()
                plane = GovernancePlane.from_app_config(config)
                decision = plane.submit_adjustment(
                    _proposal(target_param="high.risk_multiplier", suggested_value=1.3, mode="BOUNDED_AUTO")
                )
        self.assertEqual(GovernanceOutcome.REJECTED, decision.outcome)
        self.assertEqual(1.0, plane.current_snapshot().risk_multiplier)


if __name__ == "__main__":
    unittest.main()
