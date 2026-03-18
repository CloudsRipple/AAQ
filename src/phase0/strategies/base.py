from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StrategySignal:
    strategy: str
    symbol: str
    side: str
    score: float
    confidence: float
    rationale: str
    risk_multiplier: float = 1.0
    take_profit_boost_pct: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyContext:
    watchlist: list[str]
    market_snapshot: dict[str, dict[str, Any]]
    headlines: list[str]
    news_positive_threshold: float
    news_negative_threshold: float
    rotation_top_k: int
