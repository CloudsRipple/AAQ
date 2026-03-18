from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.lanes.low import build_watchlist_with_rotation


class LowLaneRotationTests(unittest.TestCase):
    def test_build_watchlist_with_rotation_ranks_symbols(self) -> None:
        snapshot = {
            "AAA": {"momentum_20d": 0.12, "relative_strength": 0.3, "z_score_5d": 0.1, "liquidity_score": 0.8},
            "BBB": {"momentum_20d": 0.03, "relative_strength": 0.1, "z_score_5d": 0.2, "liquidity_score": 0.7},
            "CCC": {"momentum_20d": 0.15, "relative_strength": 0.25, "z_score_5d": 1.0, "liquidity_score": 0.9},
        }
        watchlist = build_watchlist_with_rotation(snapshot, top_k=2)
        self.assertEqual(2, len(watchlist))
        self.assertEqual("CCC", watchlist[0])


if __name__ == "__main__":
    unittest.main()
