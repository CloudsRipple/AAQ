from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.safety import SafetyMode, assess_safety


class SafetyTests(unittest.TestCase):
    def test_enters_lockdown_when_ibkr_unreachable(self) -> None:
        state = assess_safety(ibkr_reachable=False, llm_reachable=True)
        self.assertEqual(SafetyMode.LOCKDOWN, state.mode)
        self.assertEqual("IBKR_UNREACHABLE", state.reason)
        self.assertFalse(state.allows_risk_execution)

    def test_enters_degraded_when_llm_unreachable(self) -> None:
        state = assess_safety(ibkr_reachable=True, llm_reachable=False)
        self.assertEqual(SafetyMode.DEGRADED, state.mode)
        self.assertEqual("LLM_UNREACHABLE", state.reason)
        self.assertFalse(state.allows_risk_execution)

    def test_enters_normal_when_dependencies_ready(self) -> None:
        state = assess_safety(ibkr_reachable=True, llm_reachable=True)
        self.assertEqual(SafetyMode.NORMAL, state.mode)
        self.assertTrue(state.allows_risk_execution)


if __name__ == "__main__":
    unittest.main()
