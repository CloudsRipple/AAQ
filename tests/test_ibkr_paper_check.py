from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.ibkr_paper_check import PortStatus, ProbeConfig, run_probe


class FakeClientSuccess:
    def request_l1_snapshot(self, symbol: str) -> dict[str, object]:
        return {"symbol": symbol, "bid": 189.1, "ask": 189.3, "last": 189.2}

    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, object]]:
        return [{"headline": f"{symbol} headline", "provider_code": "BRFG", "article_id": "1", "time": "now"}]

    def close(self) -> None:
        return None


class FakeClientFailure:
    def request_l1_snapshot(self, symbol: str) -> dict[str, object]:
        raise RuntimeError("ibkr request failed")

    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, object]]:
        return []

    def close(self) -> None:
        return None


class FakeClientNoNews:
    def request_l1_snapshot(self, symbol: str) -> dict[str, object]:
        return {"symbol": symbol, "bid": 189.1, "ask": 189.3, "last": 189.2}

    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, object]]:
        return []

    def close(self) -> None:
        return None


class FlakyClient:
    def __init__(self) -> None:
        self.calls = 0

    def request_l1_snapshot(self, symbol: str) -> dict[str, object]:
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("ibkr timeout")
        return {"symbol": symbol, "bid": 189.1, "ask": 189.3, "last": 189.2}

    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, object]]:
        return [{"headline": f"{symbol} headline", "provider_code": "BRFG", "article_id": "1", "time": "now"}]

    def close(self) -> None:
        return None


class IbkrPaperCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = ProbeConfig(symbol="AAPL")

    def test_returns_fallback_when_port_unreachable(self) -> None:
        port_status = PortStatus(ok=False, host="127.0.0.1", port=7497, latency_ms=None, error="connection refused")
        with patch("phase0.ibkr_paper_check.check_port", return_value=port_status), patch(
            "phase0.ibkr_paper_check.fetch_yfinance_snapshot",
            return_value={"ok": True, "source": "yfinance", "symbol": "AAPL", "last": 188.0},
        ):
            report = run_probe(self.config)
        self.assertFalse(report["port_7497"]["ok"])
        self.assertFalse(report["l1_market_data"]["ok"])
        self.assertEqual("7497 unreachable", report["l1_market_data"]["error"])
        self.assertEqual("yfinance", report["fallback_market_data"]["source"])
        self.assertFalse(report["ok"])

    def test_uses_ibkr_data_when_port_ok_and_client_works(self) -> None:
        port_status = PortStatus(ok=True, host="127.0.0.1", port=7497, latency_ms=1.2, error=None)
        with patch("phase0.ibkr_paper_check.check_port", return_value=port_status):
            report = run_probe(self.config, client_factory=lambda _: FakeClientSuccess())
        self.assertTrue(report["port_7497"]["ok"])
        self.assertTrue(report["l1_market_data"]["ok"])
        self.assertEqual("ibkr", report["l1_market_data"]["source"])
        self.assertEqual(1, len(report["news"]))
        self.assertIsNone(report["fallback_market_data"])
        self.assertTrue(report["pass_evidence"]["l1_market_data"]["ok"])
        self.assertTrue(report["pass_evidence"]["news"]["ok"])
        self.assertGreaterEqual(len(report["critical_path_logs"]), 3)
        self.assertEqual(1, report["retry_validation"]["attempts"])
        self.assertTrue(report["ok"])

    def test_falls_back_when_ibkr_client_errors(self) -> None:
        port_status = PortStatus(ok=True, host="127.0.0.1", port=7497, latency_ms=1.2, error=None)
        with patch("phase0.ibkr_paper_check.check_port", return_value=port_status), patch(
            "phase0.ibkr_paper_check.fetch_yfinance_snapshot",
            return_value={"ok": True, "source": "yfinance", "symbol": "AAPL", "last": 187.5},
        ):
            report = run_probe(self.config, client_factory=lambda _: FakeClientFailure())
        self.assertTrue(report["port_7497"]["ok"])
        self.assertFalse(report["l1_market_data"]["ok"])
        self.assertEqual("ibkr request failed", report["l1_market_data"]["error"])
        self.assertEqual("yfinance", report["fallback_market_data"]["source"])
        self.assertGreaterEqual(len(report["alerts"]), 1)
        self.assertFalse(report["ok"])

    def test_retries_on_retryable_error_then_succeeds(self) -> None:
        port_status = PortStatus(ok=True, host="127.0.0.1", port=7497, latency_ms=1.2, error=None)
        flaky_client = FlakyClient()
        with patch("phase0.ibkr_paper_check.check_port", return_value=port_status):
            report = run_probe(ProbeConfig(symbol="AAPL", max_retries=1), client_factory=lambda _: flaky_client)
        self.assertTrue(report["l1_market_data"]["ok"])
        self.assertEqual(2, report["retry_validation"]["attempts"])
        self.assertTrue(report["retry_validation"]["retried"])
        self.assertIn("ibkr timeout", report["retry_validation"]["retryable_errors"][0])
        self.assertTrue(report["ok"])

    def test_marks_probe_not_ok_when_news_evidence_missing(self) -> None:
        port_status = PortStatus(ok=True, host="127.0.0.1", port=7497, latency_ms=1.2, error=None)
        with patch("phase0.ibkr_paper_check.check_port", return_value=port_status):
            report = run_probe(self.config, client_factory=lambda _: FakeClientNoNews())
        self.assertTrue(report["l1_market_data"]["ok"])
        self.assertFalse(report["pass_evidence"]["news"]["ok"])
        self.assertFalse(report["ok"])


if __name__ == "__main__":
    unittest.main()
