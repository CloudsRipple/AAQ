from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.ai.high import assess_high_lane, evaluate_high_adjustment
from phase0.ai.low import analyze_low_lane
from phase0.ai.memory import LayeredMemoryStore, MemoryRecord, PersistentLayeredMemoryStore
from phase0.ai.ultra import evaluate_ultra_guard


class AILayersTests(unittest.TestCase):
    def test_ultra_guard_rejects_stale_or_unverified_message(self) -> None:
        now = datetime.now(tz=timezone.utc)
        signal = evaluate_ultra_guard(
            headline="unverified rumor suggests sudden takeover",
            published_at=now - timedelta(hours=8),
            now=now,
            max_age_minutes=180,
        )
        self.assertFalse(signal.wake_high)
        self.assertLess(signal.authenticity_score, 0.7)
        self.assertGreaterEqual(signal.quick_filter_score, 0.0)

    def test_ultra_guard_fast_filter_blocks_on_weak_local_metrics(self) -> None:
        now = datetime.now(tz=timezone.utc)
        signal = evaluate_ultra_guard(
            headline="verified update",
            published_at=now - timedelta(minutes=30),
            now=now,
            max_age_minutes=180,
            market_row={"momentum_20d": 0.0, "relative_strength": 0.01, "liquidity_score": 0.2, "volatility": 0.45},
        )
        self.assertEqual("LOCAL_QUICK_FILTER_BLOCKED", signal.reason)
        self.assertFalse(signal.wake_high)

    def test_low_lane_committee_requires_two_of_three(self) -> None:
        snapshot = {
            "AAPL": {"momentum_20d": 0.09, "relative_strength": 0.24, "sector": "technology"},
            "XOM": {"momentum_20d": 0.04, "relative_strength": 0.11, "sector": "energy"},
        }
        analysis = analyze_low_lane(
            market_snapshot=snapshot,
            committee_models=["m1", "m2", "m3"],
            committee_min_support=2,
            strategy_name="sector_rotation",
            strategy_confidence=0.8,
        )
        self.assertEqual("technology", analysis.preferred_sector)
        self.assertTrue(analysis.committee_approved)

    def test_high_adjustment_obeys_single_stoploss_override(self) -> None:
        first = evaluate_high_adjustment(
            strategy_confidence=0.9,
            low_committee_approved=True,
            high_confidence_gate=0.58,
            current_stop_loss_pct=0.02,
            stop_loss_override_used=False,
            default_stop_loss_pct=0.02,
            max_stop_loss_pct=0.05,
        )
        second = evaluate_high_adjustment(
            strategy_confidence=0.9,
            low_committee_approved=True,
            high_confidence_gate=0.58,
            current_stop_loss_pct=first.stop_loss_pct,
            stop_loss_override_used=True,
            default_stop_loss_pct=0.02,
            max_stop_loss_pct=0.05,
        )
        self.assertTrue(first.approved)
        self.assertLessEqual(first.stop_loss_pct, 0.05)
        self.assertEqual(first.stop_loss_pct, second.stop_loss_pct)

    def test_high_assessment_supports_local_or_cloud_mode(self) -> None:
        assessment = assess_high_lane(
            strategy_name="momentum",
            strategy_confidence=0.82,
            low_committee_approved=True,
            ultra_authenticity_score=0.8,
            quick_filter_score=0.74,
            high_confidence_gate=0.58,
            current_stop_loss_pct=0.02,
            stop_loss_override_used=False,
            default_stop_loss_pct=0.02,
            max_stop_loss_pct=0.05,
            mode="cloud",
            committee_models=["local-risk-v1", "gpt-4o-mini"],
            committee_min_support=1,
        )
        self.assertEqual("cloud", assessment.mode)
        self.assertTrue(len(assessment.committee_votes) >= 1)

    def test_high_assessment_uses_cloud_vote_payload(self) -> None:
        def _cloud_vote(prompt: str, model: str) -> str:
            return '{"approve": true, "score": 0.91, "risk_multiplier": 1.2, "stop_loss_pct": 0.032}'

        assessment = assess_high_lane(
            strategy_name="momentum",
            strategy_confidence=0.82,
            low_committee_approved=True,
            ultra_authenticity_score=0.8,
            quick_filter_score=0.74,
            high_confidence_gate=0.58,
            current_stop_loss_pct=0.02,
            stop_loss_override_used=False,
            default_stop_loss_pct=0.02,
            max_stop_loss_pct=0.05,
            mode="cloud",
            committee_models=["gpt-4o-mini"],
            committee_min_support=1,
            cloud_vote_fn=_cloud_vote,
        )
        self.assertTrue(assessment.decision.approved)
        self.assertEqual(1.2, assessment.decision.risk_multiplier)
        self.assertEqual(0.032, assessment.decision.stop_loss_pct)

    def test_high_assessment_falls_back_when_cloud_vote_invalid(self) -> None:
        assessment = assess_high_lane(
            strategy_name="momentum",
            strategy_confidence=0.82,
            low_committee_approved=True,
            ultra_authenticity_score=0.8,
            quick_filter_score=0.74,
            high_confidence_gate=0.58,
            current_stop_loss_pct=0.02,
            stop_loss_override_used=False,
            default_stop_loss_pct=0.02,
            max_stop_loss_pct=0.05,
            mode="cloud",
            committee_models=["gpt-4o-mini"],
            committee_min_support=1,
            cloud_vote_fn=lambda *_: "not-json",
        )
        self.assertTrue(len(assessment.committee_votes) >= 1)
        self.assertTrue(0.8 <= assessment.committee_votes[0].risk_multiplier <= 1.5)

    def test_layered_memory_returns_relevant_records(self) -> None:
        now = datetime.now(tz=timezone.utc)
        store = LayeredMemoryStore(
            [
                MemoryRecord(
                    memory_id="a",
                    tier="short",
                    text="一天前消费电子行业提到小米手机出货恢复",
                    published_at=now - timedelta(days=1),
                    tags=("小米", "消费电子"),
                ),
                MemoryRecord(
                    memory_id="b",
                    tier="long",
                    text="半年前国际油价下跌",
                    published_at=now - timedelta(days=180),
                    tags=("石油", "能源"),
                ),
            ]
        )
        rows = store.query("小米 消费电子", now=now, limit=1)
        self.assertEqual(1, len(rows))
        self.assertEqual("a", rows[0].memory_id)

    def test_persistent_memory_store_loads_from_disk(self) -> None:
        now = datetime.now(tz=timezone.utc)
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "memory.db")
            PersistentLayeredMemoryStore(
                db_path=db_path,
                records=[
                    MemoryRecord(
                        memory_id="persisted-1",
                        tier="short",
                        text="小米消费电子供应链改善",
                        published_at=now - timedelta(days=1),
                        tags=("小米", "消费电子"),
                    )
                ],
            )
            loaded = PersistentLayeredMemoryStore.from_db(db_path)
            rows = loaded.query("小米 消费电子", now=now, limit=1)
            self.assertEqual(1, len(rows))
            self.assertEqual("persisted-1", rows[0].memory_id)


if __name__ == "__main__":
    unittest.main()
