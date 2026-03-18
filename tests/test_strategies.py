from __future__ import annotations

from pathlib import Path
import tempfile
import textwrap
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.strategies import StrategyContext, run_strategies


class StrategyPipelineTests(unittest.TestCase):
    def test_loads_and_runs_multiple_strategies(self) -> None:
        context = StrategyContext(
            watchlist=["AAPL", "NVDA"],
            market_snapshot={
                "AAPL": {
                    "momentum_20d": 0.08,
                    "z_score_5d": -1.4,
                    "relative_strength": 0.25,
                    "volatility": 0.2,
                    "sector": "technology",
                },
                "NVDA": {
                    "momentum_20d": 0.15,
                    "z_score_5d": 1.8,
                    "relative_strength": 0.34,
                    "volatility": 0.35,
                    "sector": "technology",
                },
            },
            headlines=["chipmakers surge after strong growth and upgrade cycle"],
            news_positive_threshold=0.2,
            news_negative_threshold=-0.2,
            rotation_top_k=2,
        )
        signals = run_strategies(["momentum", "mean_reversion", "sector_rotation", "news_sentiment"], context)
        self.assertTrue(signals)
        self.assertIn(signals[0].side, {"buy", "sell"})
        self.assertGreater(signals[0].confidence, 0)

    def test_ignores_unknown_strategy_name(self) -> None:
        context = StrategyContext(
            watchlist=["AAPL"],
            market_snapshot={"AAPL": {"momentum_20d": 0.1, "volatility": 0.2}},
            headlines=[],
            news_positive_threshold=0.2,
            news_negative_threshold=-0.2,
            rotation_top_k=1,
        )
        signals = run_strategies(["unknown"], context)
        self.assertEqual([], signals)

    def test_loads_external_strategy_and_factor_plugins(self) -> None:
        context = StrategyContext(
            watchlist=["AAPL"],
            market_snapshot={"AAPL": {"momentum_20d": 0.1, "volatility": 0.2}},
            headlines=[],
            news_positive_threshold=0.2,
            news_negative_threshold=-0.2,
            rotation_top_k=1,
        )
        plugin_source = textwrap.dedent(
            """
            from phase0.strategies.base import StrategySignal

            def register_factors():
                def quality_factor(context):
                    return {"AAPL": {"quality_score": 0.92}}
                return {"quality_factor": quality_factor}

            def register_strategies():
                def quality_alpha(context):
                    row = context.market_snapshot.get("AAPL", {})
                    score = float(row.get("quality_score", 0.0))
                    if score <= 0:
                        return []
                    return [
                        StrategySignal(
                            strategy="quality_alpha",
                            symbol="AAPL",
                            side="buy",
                            score=score * 10,
                            confidence=0.8,
                            rationale=f"quality_score={score:.2f}",
                        )
                    ]
                return {"quality_alpha": quality_alpha}
            """
        )
        with tempfile.TemporaryDirectory() as tmp:
            plugin_path = Path(tmp) / "community_plugin.py"
            plugin_path.write_text(plugin_source, encoding="utf-8")
            sys.path.insert(0, tmp)
            try:
                signals = run_strategies(
                    ["quality_alpha"],
                    context,
                    strategy_plugin_modules="community_plugin",
                    factor_plugin_modules="community_plugin",
                )
            finally:
                sys.path.remove(tmp)
                sys.modules.pop("community_plugin", None)
        self.assertEqual(1, len(signals))
        self.assertEqual("quality_alpha", signals[0].strategy)
        self.assertIn("quality_score=0.92", signals[0].rationale)


if __name__ == "__main__":
    unittest.main()
