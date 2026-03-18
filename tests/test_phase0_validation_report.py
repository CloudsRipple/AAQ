from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.phase0_validation_report import generate_phase0_validation_report


class Phase0ValidationReportTests(unittest.TestCase):
    def test_generates_passed_report_when_dynamic_probe_passes(self) -> None:
        def _ok_probe(*args: object, **kwargs: object) -> dict[str, object]:
            return {
                "ok": True,
                "port_7497": {"ok": True},
                "l1_market_data": {"ok": True},
                "news": [{"headline": "ok", "provider_code": "X", "article_id": "1"}],
                "pass_evidence": {"l1_market_data": {"ok": True}, "news": {"ok": True}},
                "critical_path_logs": [{"step": "port_probe"}, {"step": "ibkr_probe"}],
                "retry_validation": {"attempts": 1},
                "alerts": [],
            }

        with patch("phase0.phase0_validation_report.run_probe", side_effect=_ok_probe):
            report = generate_phase0_validation_report()
        self.assertEqual("phase0_validation_report", report["kind"])
        self.assertTrue(report["ok"])
        self.assertTrue(report["ibkr_probe"]["dynamic_probe_ok"])

    def test_generates_failed_report_when_dynamic_probe_fails(self) -> None:
        calls = {"count": 0}

        def _probe(*args: object, **kwargs: object) -> dict[str, object]:
            calls["count"] += 1
            if calls["count"] == 1:
                return {
                    "ok": False,
                    "port_7497": {"ok": False},
                    "l1_market_data": {"ok": False},
                    "news": [],
                    "pass_evidence": {"l1_market_data": {"ok": False}, "news": {"ok": False}},
                    "critical_path_logs": [{"step": "port_probe"}, {"step": "ibkr_probe"}],
                    "retry_validation": {"attempts": 1},
                    "alerts": [{"level": "WARN"}],
                }
            return {
                "ok": True,
                "port_7497": {"ok": True},
                "l1_market_data": {"ok": True},
                "news": [{"headline": "fallback", "provider_code": "X", "article_id": "2"}],
                "pass_evidence": {"l1_market_data": {"ok": True}, "news": {"ok": True}},
                "critical_path_logs": [{"step": "port_probe"}, {"step": "ibkr_probe"}],
                "retry_validation": {"attempts": 1},
                "alerts": [],
            }

        with patch("phase0.phase0_validation_report.run_probe", side_effect=_probe):
            report = generate_phase0_validation_report()
        report = generate_phase0_validation_report()
        self.assertFalse(report["ok"])
        self.assertFalse(report["ibkr_probe"]["dynamic_probe_ok"])
        check_names = {item["name"] for item in report["ibkr_validation_checks"]}
        self.assertIn("dynamic_probe_must_pass", check_names)


if __name__ == "__main__":
    unittest.main()
