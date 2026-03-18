from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.state_store import get_latest_low_analysis_state, upsert_low_analysis_state


class LowAnalysisStateStoreTests(unittest.TestCase):
    def test_upsert_and_get_latest_for_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            upsert_low_analysis_state(
                db_path,
                symbol="AAPL",
                analysis={"committee_approved": True, "preferred_sector": "technology"},
                analyzed_at="2026-03-18T00:00:00+00:00",
            )
            state = get_latest_low_analysis_state(db_path, symbol="AAPL")
        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual("AAPL", state["symbol"])
        self.assertTrue(state["analysis"]["committee_approved"])

    def test_get_latest_falls_back_to_macro(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "state.db")
            upsert_low_analysis_state(
                db_path,
                symbol="MACRO",
                analysis={"committee_approved": False, "preferred_sector": "energy"},
            )
            state = get_latest_low_analysis_state(db_path, symbol="MSFT")
        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual("MACRO", state["symbol"])
        self.assertFalse(state["analysis"]["committee_approved"])


if __name__ == "__main__":
    unittest.main()
