from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.replay import run_replay


class ReplayScriptTests(unittest.TestCase):
    def test_all_mode_runs_fault_injection_matrix(self) -> None:
        report = run_replay(mode="all")
        self.assertEqual("phase0_injection_replay", report["kind"])
        self.assertEqual(5, report["total"])
        self.assertEqual(5, report["passed"])
        scenarios = {item["scenario"]: item for item in report["results"]}
        self.assertIn("breaking_news", scenarios)
        self.assertIn("high_volatility", scenarios)
        self.assertIn("duplicate_event_dedup", scenarios)
        self.assertIn("unverified_stale_message", scenarios)
        self.assertIn("safety_mode_blocked", scenarios)
        self.assertTrue(scenarios["breaking_news"]["ok"])
        self.assertTrue(scenarios["high_volatility"]["ok"])

    def test_single_mode_runs_only_selected_scenario(self) -> None:
        report = run_replay(mode="breaking_news")
        self.assertEqual("breaking_news", report["mode"])
        self.assertEqual(1, report["total"])
        self.assertEqual("breaking_news", report["results"][0]["scenario"])
        self.assertEqual("rejected", report["results"][0]["decision"]["status"])


if __name__ == "__main__":
    unittest.main()
