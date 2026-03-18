from __future__ import annotations


def build_watchlist() -> list[str]:
    market_snapshot = _default_market_snapshot()
    return build_watchlist_with_rotation(market_snapshot, top_k=3)


def build_watchlist_with_rotation(market_snapshot: dict[str, dict[str, float | str]], top_k: int = 3) -> list[str]:
    scored: list[tuple[str, float]] = []
    for symbol, payload in market_snapshot.items():
        momentum = float(payload.get("momentum_20d", 0.0))
        rel_strength = float(payload.get("relative_strength", 0.0))
        z_score = abs(float(payload.get("z_score_5d", 0.0)))
        liquidity = float(payload.get("liquidity_score", 0.5))
        score = momentum * 0.45 + rel_strength * 0.35 + z_score * 0.1 + liquidity * 0.1
        scored.append((symbol, score))
    ranked = sorted(scored, key=lambda row: row[1], reverse=True)
    return [symbol for symbol, _ in ranked[: max(1, top_k)]]


def _default_market_snapshot() -> dict[str, dict[str, float | str]]:
    return {
        "AAPL": {
            "momentum_20d": 0.11,
            "z_score_5d": -0.4,
            "relative_strength": 0.28,
            "volatility": 0.23,
            "liquidity_score": 0.95,
            "sector": "technology",
        },
        "MSFT": {
            "momentum_20d": 0.09,
            "z_score_5d": 0.1,
            "relative_strength": 0.25,
            "volatility": 0.18,
            "liquidity_score": 0.92,
            "sector": "technology",
        },
        "NVDA": {
            "momentum_20d": 0.15,
            "z_score_5d": 1.4,
            "relative_strength": 0.35,
            "volatility": 0.35,
            "liquidity_score": 0.88,
            "sector": "technology",
        },
        "XOM": {
            "momentum_20d": 0.06,
            "z_score_5d": -1.1,
            "relative_strength": 0.2,
            "volatility": 0.2,
            "liquidity_score": 0.8,
            "sector": "energy",
        },
        "JPM": {
            "momentum_20d": 0.05,
            "z_score_5d": -0.9,
            "relative_strength": 0.16,
            "volatility": 0.16,
            "liquidity_score": 0.84,
            "sector": "financial",
        },
    }
