from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import load_config
from phase0.lanes import _build_ultra_signal_snapshot, run_lane_cycle
from phase0.models.signals import UltraSignalEvent


class _FakeSentinel:
    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def on_market_tick(self, **_: object) -> None:
        return None

    async def on_news(self, **kwargs: object) -> UltraSignalEvent:
        ts = kwargs.get("timestamp") or datetime.now(tz=timezone.utc)
        return UltraSignalEvent(
            symbol="AAPL",
            timestamp=ts,
            event_type="composite",
            confidence_score=0.9,
            source="composite",
            matched_prototype="regulatory penalty",
            raw_data={"test": "ok"},
        )

    async def get_signal(self, timeout_seconds: float | None = None) -> UltraSignalEvent:
        _ = timeout_seconds
        return UltraSignalEvent(
            symbol="AAPL",
            timestamp=datetime.now(tz=timezone.utc),
            event_type="news_alert",
            confidence_score=0.8,
            source="vector_match",
            matched_prototype="regulatory penalty",
            raw_data={"test": "ok"},
        )


class UltraQueueWiringTests(unittest.TestCase):
    def test_build_ultra_signal_snapshot_consumes_async_sentinel(self) -> None:
        config = load_config()
        now = datetime.now(tz=timezone.utc)
        with patch("phase0.lanes.build_ultra_sentinel", return_value=_FakeSentinel()):
            snapshot = asyncio.run(
                _build_ultra_signal_snapshot(
                    symbol="AAPL",
                    config=config,
                    lead_headline={"headline": "Regulatory pressure rises", "published_at": now},
                    market_row={"reference_price": 100.0, "momentum_20d": 0.03, "volume": 1000.0},
                    now=now,
                    max_age_minutes=180,
                )
            )
        self.assertTrue(snapshot.wake_high)
        self.assertTrue(snapshot.wake_low)
        self.assertGreater(snapshot.authenticity_score, 0.0)
        self.assertIn("composite", snapshot.reason)

    def test_run_lane_cycle_sync_wrapper_uses_async_implementation(self) -> None:
        mocked = AsyncMock(return_value={"ok": True, "source": "async"})
        with patch("phase0.lanes.run_lane_cycle_async", mocked):
            result = run_lane_cycle(symbol="AAPL", config=object())
        self.assertTrue(result["ok"])
        self.assertEqual("async", result["source"])
        self.assertEqual(1, mocked.await_count)

    def test_run_lane_cycle_sync_wrapper_supports_running_event_loop(self) -> None:
        mocked = AsyncMock(return_value={"ok": True, "source": "thread-bridge"})
        with patch("phase0.lanes.run_lane_cycle_async", mocked):
            result = asyncio.run(self._run_inside_loop())
        self.assertTrue(result["ok"])
        self.assertEqual("thread-bridge", result["source"])
        self.assertEqual(1, mocked.await_count)

    async def _run_inside_loop(self) -> dict[str, object]:
        return run_lane_cycle(symbol="AAPL", config=object())


if __name__ == "__main__":
    unittest.main()
