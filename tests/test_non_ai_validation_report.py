from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.non_ai_validation_report import generate_non_ai_validation_report


class NonAIValidationReportTests(unittest.TestCase):
    def test_generates_non_ai_report(self) -> None:
        report = generate_non_ai_validation_report()
        self.assertEqual("phase0_non_ai_validation_report", report["kind"])
        self.assertEqual("non_ai_bypass", report["mode"])
        self.assertIn("checks", report)
        self.assertIn("components", report)
        self.assertIn("functional", report)
        self.assertTrue(any(item["component"] == "data_transport" for item in report["components"]))


if __name__ == "__main__":
    unittest.main()
