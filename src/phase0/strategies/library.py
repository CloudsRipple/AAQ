from __future__ import annotations

from collections import defaultdict
import math
from typing import Callable

from .base import StrategyContext, StrategySignal


StrategyFunc = Callable[[StrategyContext], list[StrategySignal]]


def momentum_strategy(context: StrategyContext) -> list[StrategySignal]:
    signals: list[StrategySignal] = []
    for symbol in context.watchlist:
        row = context.market_snapshot.get(symbol, {})
        momentum = row.get("momentum_20d", 0.0)
        volatility = max(row.get("volatility", 0.01), 0.01)
        if momentum <= 0:
            continue
        score = momentum / volatility
        confidence = min(0.95, max(0.2, abs(score) / 5))
        signals.append(
            StrategySignal(
                strategy="momentum",
                symbol=symbol,
                side="buy",
                score=score,
                confidence=confidence,
                rationale=f"momentum={momentum:.3f},volatility={volatility:.3f}",
                risk_multiplier=1.0 + min(0.2, confidence * 0.2),
                take_profit_boost_pct=min(0.1, confidence * 0.1),
            )
        )
    return signals


def mean_reversion_strategy(context: StrategyContext) -> list[StrategySignal]:
    signals: list[StrategySignal] = []
    for symbol in context.watchlist:
        row = context.market_snapshot.get(symbol, {})
        z_score = row.get("z_score_5d", 0.0)
        volatility = max(row.get("volatility", 0.01), 0.01)
        if abs(z_score) < 1.25:
            continue
        side = "buy" if z_score < 0 else "sell"
        score = abs(z_score) / volatility
        confidence = min(0.9, 0.25 + abs(z_score) / 5)
        signals.append(
            StrategySignal(
                strategy="mean_reversion",
                symbol=symbol,
                side=side,
                score=score,
                confidence=confidence,
                rationale=f"z_score_5d={z_score:.3f}",
                risk_multiplier=1.0 - min(0.2, confidence * 0.15),
                take_profit_boost_pct=0.02,
            )
        )
    return signals


def sector_rotation_strategy(context: StrategyContext) -> list[StrategySignal]:
    sector_scores: dict[str, float] = defaultdict(float)
    by_sector: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for symbol in context.watchlist:
        row = context.market_snapshot.get(symbol, {})
        sector = str(row.get("sector", "other"))
        rel_strength = row.get("relative_strength", 0.0)
        sector_scores[sector] += rel_strength
        by_sector[sector].append((symbol, rel_strength))
    if not sector_scores:
        return []
    top_sector = max(sector_scores.items(), key=lambda item: item[1])[0]
    ranked = sorted(by_sector[top_sector], key=lambda item: item[1], reverse=True)
    picked = ranked[: max(1, context.rotation_top_k)]
    signals: list[StrategySignal] = []
    for symbol, rel_strength in picked:
        score = rel_strength + math.log1p(max(rel_strength, 0))
        signals.append(
            StrategySignal(
                strategy="sector_rotation",
                symbol=symbol,
                side="buy",
                score=score,
                confidence=min(0.85, 0.35 + max(0.0, rel_strength)),
                rationale=f"top_sector={top_sector},relative_strength={rel_strength:.3f}",
                risk_multiplier=1.05,
                take_profit_boost_pct=0.04,
                metadata={"sector": top_sector},
            )
        )
    return signals


def news_sentiment_strategy(context: StrategyContext) -> list[StrategySignal]:
    text = " ".join(context.headlines).lower()
    if not text:
        return []
    positive_words = ("beat", "surge", "upgrade", "breakthrough", "strong", "growth")
    negative_words = ("downgrade", "fraud", "lawsuit", "miss", "weak", "plunge")
    pos = sum(text.count(w) for w in positive_words)
    neg = sum(text.count(w) for w in negative_words)
    total = max(1, pos + neg)
    sentiment = (pos - neg) / total
    if sentiment < context.news_positive_threshold and sentiment > context.news_negative_threshold:
        return []
    side = "buy" if sentiment >= context.news_positive_threshold else "sell"
    if not context.watchlist:
        return []
    signals: list[StrategySignal] = []
    for symbol in context.watchlist:
        row = context.market_snapshot.get(symbol, {})
        relative_strength = max(0.0, float(row.get("relative_strength", 0.0)))
        liquidity = max(0.0, min(1.0, float(row.get("liquidity_score", 0.5))))
        symbol_weight = 0.65 + min(0.25, relative_strength) + liquidity * 0.1
        score = abs(sentiment) * 10 * symbol_weight
        confidence = min(0.9, 0.28 + abs(sentiment) * 0.45 + relative_strength * 0.2)
        signals.append(
            StrategySignal(
                strategy="news_sentiment",
                symbol=symbol,
                side=side,
                score=score,
                confidence=confidence,
                rationale=f"news_sentiment={sentiment:.3f},relative_strength={relative_strength:.3f}",
                risk_multiplier=1.0 - min(0.25, abs(sentiment) * 0.2),
                take_profit_boost_pct=0.06 if side == "buy" else 0.03,
                metadata={
                    "sentiment": sentiment,
                    "positive_hits": pos,
                    "negative_hits": neg,
                    "symbol_weight": round(symbol_weight, 4),
                },
            )
        )
    return signals
