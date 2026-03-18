from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module
from importlib.metadata import entry_points
from typing import Any

from .base import StrategyContext, StrategySignal
from .factors import BUILTIN_FACTOR_REGISTRY, FactorFunc
from .library import (
    StrategyFunc,
    mean_reversion_strategy,
    momentum_strategy,
    news_sentiment_strategy,
    sector_rotation_strategy,
)


STRATEGY_REGISTRY: dict[str, StrategyFunc] = {
    "momentum": momentum_strategy,
    "mean_reversion": mean_reversion_strategy,
    "sector_rotation": sector_rotation_strategy,
    "news_sentiment": news_sentiment_strategy,
}


def run_strategies(
    enabled: list[str],
    context: StrategyContext,
    *,
    strategy_plugin_modules: str = "",
    factor_plugin_modules: str = "",
) -> list[StrategySignal]:
    runtime_context = _enrich_context_with_factors(context, factor_plugin_modules)
    registry = _build_strategy_registry(strategy_plugin_modules)
    signals: list[StrategySignal] = []
    for name in enabled:
        func = registry.get(name)
        if func is None:
            continue
        signals.extend(func(runtime_context))
    return sorted(
        signals,
        key=lambda signal: (signal.score * signal.confidence, signal.confidence, signal.score),
        reverse=True,
    )


def _build_strategy_registry(strategy_plugin_modules: str) -> dict[str, StrategyFunc]:
    registry = dict(STRATEGY_REGISTRY)
    registry.update(_load_entrypoint_strategies())
    for module_name in _parse_csv(strategy_plugin_modules):
        registry.update(_load_module_strategies(module_name))
    return registry


def _enrich_context_with_factors(context: StrategyContext, factor_plugin_modules: str) -> StrategyContext:
    factor_registry: dict[str, FactorFunc] = dict(BUILTIN_FACTOR_REGISTRY)
    factor_registry.update(_load_entrypoint_factors())
    for module_name in _parse_csv(factor_plugin_modules):
        factor_registry.update(_load_module_factors(module_name))
    if not factor_registry:
        return context
    merged_snapshot: dict[str, dict[str, Any]] = {
        symbol: dict(row) for symbol, row in context.market_snapshot.items()
    }
    for factor in factor_registry.values():
        updates = factor(context)
        for symbol, fields in updates.items():
            if symbol not in merged_snapshot:
                merged_snapshot[symbol] = {}
            merged_snapshot[symbol].update(fields)
    return StrategyContext(
        watchlist=list(context.watchlist),
        market_snapshot=merged_snapshot,
        headlines=list(context.headlines),
        news_positive_threshold=context.news_positive_threshold,
        news_negative_threshold=context.news_negative_threshold,
        rotation_top_k=context.rotation_top_k,
    )


def _load_entrypoint_strategies() -> dict[str, StrategyFunc]:
    loaded: dict[str, StrategyFunc] = {}
    for ep in _iter_entry_points("phase0.strategies"):
        candidate = ep.load()
        if callable(candidate):
            loaded[ep.name] = candidate
    return loaded


def _load_entrypoint_factors() -> dict[str, FactorFunc]:
    loaded: dict[str, FactorFunc] = {}
    for ep in _iter_entry_points("phase0.factors"):
        candidate = ep.load()
        if callable(candidate):
            loaded[ep.name] = candidate
    return loaded


def _iter_entry_points(group: str) -> list[Any]:
    try:
        selected = entry_points(group=group)
    except TypeError:
        selected = None
    if selected is not None:
        return list(selected)
    eps = entry_points()
    select = getattr(eps, "select", None)
    if callable(select):
        return list(select(group=group))
    if isinstance(eps, Mapping):
        group_items = eps.get(group, [])
        return list(group_items)
    return []


def _load_module_strategies(module_name: str) -> dict[str, StrategyFunc]:
    module = import_module(module_name)
    register = getattr(module, "register_strategies", None)
    if not callable(register):
        return {}
    loaded = register()
    if not isinstance(loaded, dict):
        return {}
    return {str(name): func for name, func in loaded.items() if callable(func)}


def _load_module_factors(module_name: str) -> dict[str, FactorFunc]:
    module = import_module(module_name)
    register = getattr(module, "register_factors", None)
    if not callable(register):
        return {}
    loaded = register()
    if not isinstance(loaded, dict):
        return {}
    return {str(name): func for name, func in loaded.items() if callable(func)}


def _parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]
