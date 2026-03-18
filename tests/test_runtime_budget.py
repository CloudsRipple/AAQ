from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import RuntimeMode, load_config
from phase0.runtime_budget import build_runtime_budget


class RuntimeBudgetTests(unittest.TestCase):
    def test_eco_mode_uses_conservative_budget(self) -> None:
        with patch.dict("os.environ", {"RUNTIME_MODE": "eco"}, clear=False):
            config = load_config()
        budget = build_runtime_budget(config)
        self.assertEqual(RuntimeMode.ECO, config.runtime_mode)
        self.assertEqual(1, budget.max_lane_cycles_per_healthcheck)
        self.assertEqual(1, budget.llm_max_parallel_requests)

    def test_perf_mode_uses_higher_parallel_budget(self) -> None:
        with patch.dict("os.environ", {"RUNTIME_MODE": "perf"}, clear=False):
            config = load_config()
        budget = build_runtime_budget(config)
        self.assertEqual(3, budget.max_lane_cycles_per_healthcheck)
        self.assertEqual(3, budget.llm_max_parallel_requests)

    def test_m2_profile_is_detected_on_darwin_arm(self) -> None:
        with patch.dict("os.environ", {"RUNTIME_MODE": "normal"}, clear=False), patch(
            "phase0.runtime_budget.platform.system", return_value="Darwin"
        ), patch("phase0.runtime_budget.platform.machine", return_value="arm64"), patch(
            "phase0.runtime_budget.platform.processor", return_value=""
        ):
            config = load_config()
            budget = build_runtime_budget(config)
        self.assertEqual("macbook_air_m2_16_256", budget.machine_profile)
        self.assertGreaterEqual(budget.lane_loop_interval_ms, 500)


if __name__ == "__main__":
    unittest.main()
