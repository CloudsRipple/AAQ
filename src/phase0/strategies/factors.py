from __future__ import annotations

from typing import Any, Callable

from .base import StrategyContext

FactorFunc = Callable[[StrategyContext], dict[str, dict[str, Any]]]


def volatility_regime_factor(context: StrategyContext) -> dict[str, dict[str, Any]]:
    enriched: dict[str, dict[str, Any]] = {}
    for symbol in context.watchlist:
        row = context.market_snapshot.get(symbol, {})
        volatility = float(row.get("volatility", 0.0))
        if volatility >= 0.4:
            regime = "high"
        elif volatility >= 0.2:
            regime = "medium"
        else:
            regime = "low"
        enriched[symbol] = {"volatility_regime": regime}
    return enriched


BUILTIN_FACTOR_REGISTRY: dict[str, FactorFunc] = {
    "volatility_regime": volatility_regime_factor,
}
