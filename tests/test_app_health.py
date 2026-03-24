from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.app import health_check
from phase0.config import load_config


class AppHealthTests(unittest.TestCase):
    def test_health_check_returns_lockdown_when_ibkr_unreachable(self) -> None:
        config = load_config()
        with patch("phase0.app.socket.create_connection", side_effect=OSError("unreachable")), patch(
            "phase0.app._check_llm_connectivity", return_value=True
        ):
            summary = health_check(config)
        self.assertEqual("lockdown", summary["safety_mode"])
        self.assertEqual("false", summary["risk_execution_enabled"])
        self.assertEqual("rejected", summary["execution_status"])

    def test_health_check_returns_normal_when_ibkr_reachable(self) -> None:
        config = load_config()

        class _DummySocket:
            def __enter__(self) -> "_DummySocket":
                return self

            def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
                return None

        with patch("phase0.app.socket.create_connection", return_value=_DummySocket()), patch(
            "phase0.app._check_llm_connectivity", return_value=True
        ):
            summary = health_check(config)
        self.assertEqual("normal", summary["safety_mode"])
        self.assertEqual("true", summary["risk_execution_enabled"])

    def test_health_check_returns_degraded_when_llm_unreachable(self) -> None:
        config = load_config()

        class _DummySocket:
            def __enter__(self) -> "_DummySocket":
                return self

            def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
                return None

        with patch("phase0.app.socket.create_connection", return_value=_DummySocket()), patch(
            "phase0.app._check_llm_connectivity", return_value=False
        ):
            summary = health_check(config)
        self.assertEqual("degraded", summary["safety_mode"])
        self.assertEqual("true", summary["risk_execution_enabled"])

    def test_health_check_treats_unconfigured_ai_as_placeholder(self) -> None:
        class _DummySocket:
            def __enter__(self) -> "_DummySocket":
                return self

            def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
                return None

        with patch.dict(
            "os.environ",
            {
                "LLM_BASE_URL": "",
                "LLM_API_KEY": "",
                "AI_ENABLED": "true",
            },
            clear=False,
        ):
            config = load_config()
        with patch("phase0.app.socket.create_connection", return_value=_DummySocket()):
            summary = health_check(config)
        self.assertEqual("normal", summary["safety_mode"])
        self.assertEqual("placeholder", summary["llm"])
        self.assertEqual("true", summary["risk_execution_enabled"])

    def test_health_check_triggers_lockdown_when_drawdown_equals_limit(self) -> None:
        config = load_config()

        class _DummySocket:
            def __enter__(self) -> "_DummySocket":
                return self

            def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
                return None

        with patch("phase0.app.socket.create_connection", return_value=_DummySocket()), patch(
            "phase0.app._check_llm_connectivity", return_value=True
        ), patch("phase0.app._read_current_drawdown_pct", return_value=config.risk_max_drawdown_pct):
            summary = health_check(config)
        self.assertEqual("lockdown", summary["safety_mode"])


if __name__ == "__main__":
    unittest.main()
