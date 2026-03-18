from __future__ import annotations

from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.main import main


class MainRuntimeModeTests(unittest.TestCase):
    def test_default_path_runs_stable_control_plane(self) -> None:
        env = {
            "EVENT_DRIVEN_RUNTIME_ENABLED": "false",
            "LANE_SCHEDULER_CYCLES": "1",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("phase0.main.health_check", return_value={"ok": "true"}) as mocked_health:
                with patch("phase0.main.generate_daily_health_report", return_value={"summary": {}}):
                    with patch("phase0.main.asyncio.run") as mocked_asyncio_run:
                        code = main()
        self.assertEqual(0, code)
        mocked_health.assert_called_once()
        mocked_asyncio_run.assert_not_called()

    def test_event_driven_path_requires_explicit_switch(self) -> None:
        env = {
            "EVENT_DRIVEN_RUNTIME_ENABLED": "true",
        }
        def _close_coro(coro: object) -> None:
            close = getattr(coro, "close", None)
            if callable(close):
                close()
            return None
        with patch.dict(os.environ, env, clear=True):
            with patch("phase0.main.health_check") as mocked_health:
                with patch("phase0.main.asyncio.run", side_effect=_close_coro) as mocked_asyncio_run:
                    code = main()
        self.assertEqual(0, code)
        mocked_health.assert_not_called()
        mocked_asyncio_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
