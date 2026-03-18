# AAQ 全量逐行审计报告

## 文件：strategies/loader.py
- 总行数：141
- 函数/方法数：9

### 逐函数检查

#### 函数：__module__（行 1-139）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from collections.abc import Mapping → 无问题
  - 行 4：from importlib import import_module → 无问题
  - 行 5：from importlib.metadata import entry_points → 无问题
  - 行 6：from typing import Any → 无问题
  - 行 7： → 无问题
  - 行 8：from .base import StrategyContext, StrategySignal → 无问题
  - 行 9：from .factors import BUILTIN_FACTOR_REGISTRY, FactorFunc → 无问题
  - 行 10：from .library import ( → 无问题
  - 行 11：    StrategyFunc, → 无问题
  - 行 12：    mean_reversion_strategy, → 无问题
  - 行 13：    momentum_strategy, → 无问题
  - 行 14：    news_sentiment_strategy, → 无问题
  - 行 15：    sector_rotation_strategy, → 无问题
  - 行 16：) → 无问题
  - 行 17： → 无问题
  - 行 18： → 无问题
  - 行 19：STRATEGY_REGISTRY: dict[str, StrategyFunc] = { → 无问题
  - 行 20：    "momentum": momentum_strategy, → 无问题
  - 行 21：    "mean_reversion": mean_reversion_strategy, → 无问题
  - 行 22：    "sector_rotation": sector_rotation_strategy, → 无问题
  - 行 23：    "news_sentiment": news_sentiment_strategy, → 无问题
  - 行 24：} → 无问题
  - 行 25： → 无问题
  - 行 26： → 无问题
  - 行 47： → 无问题
  - 行 48： → 无问题
  - 行 55： → 无问题
  - 行 56： → 无问题
  - 行 81： → 无问题
  - 行 82： → 无问题
  - 行 90： → 无问题
  - 行 91： → 无问题
  - 行 99： → 无问题
  - 行 100： → 问题（ID 1）
  - 行 116： → 无问题
  - 行 117： → 无问题
  - 行 127： → 无问题
  - 行 128： → 无问题
  - 行 138： → 无问题
  - 行 139： → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：run_strategies（行 27-46）
- 功能：执行对应业务逻辑
- 参数：enabled: list[str], context: StrategyContext, strategy_plugin_modules: str, factor_plugin_modules: str
- 返回值：list[StrategySignal]（见函数语义）
- 逐行分析：
  - 行 27：def run_strategies( → 无问题
  - 行 28：    enabled: list[str], → 无问题
  - 行 29：    context: StrategyContext, → 无问题
  - 行 30：    *, → 无问题
  - 行 31：    strategy_plugin_modules: str = "", → 无问题
  - 行 32：    factor_plugin_modules: str = "", → 无问题
  - 行 33：) -> list[StrategySignal]: → 无问题
  - 行 34：    runtime_context = _enrich_context_with_factors(context, factor_plugin_modules) → 无问题
  - 行 35：    registry = _build_strategy_registry(strategy_plugin_modules) → 无问题
  - 行 36：    signals: list[StrategySignal] = [] → 无问题
  - 行 37：    for name in enabled: → 无问题
  - 行 38：        func = registry.get(name) → 无问题
  - 行 39：        if func is None: → 无问题
  - 行 40：            continue → 无问题
  - 行 41：        signals.extend(func(runtime_context)) → 无问题
  - 行 42：    return sorted( → 无问题
  - 行 43：        signals, → 无问题
  - 行 44：        key=lambda signal: (signal.score * signal.confidence, signal.confidence, signal.score), → 无问题
  - 行 45：        reverse=True, → 无问题
  - 行 46：    ) → 无问题
- 调用的外部函数：_enrich_context_with_factors; _build_strategy_registry; sorted; registry.get; signals.extend; func
- 被谁调用：lanes/__init__.py:run_lane_cycle:59; tests/test_strategies.py:StrategyPipelineTests.test_loads_and_runs_multiple_strategies:39; tests/test_strategies.py:StrategyPipelineTests.test_ignores_unknown_strategy_name:53; tests/test_strategies.py:StrategyPipelineTests.test_loads_external_strategy_and_factor_plugins:98
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_build_strategy_registry（行 49-54）
- 功能：执行对应业务逻辑
- 参数：strategy_plugin_modules: str
- 返回值：dict[str, StrategyFunc]（见函数语义）
- 逐行分析：
  - 行 49：def _build_strategy_registry(strategy_plugin_modules: str) -> dict[str, StrategyFunc]: → 无问题
  - 行 50：    registry = dict(STRATEGY_REGISTRY) → 无问题
  - 行 51：    registry.update(_load_entrypoint_strategies()) → 无问题
  - 行 52：    for module_name in _parse_csv(strategy_plugin_modules): → 无问题
  - 行 53：        registry.update(_load_module_strategies(module_name)) → 无问题
  - 行 54：    return registry → 无问题
- 调用的外部函数：dict; registry.update; _parse_csv; _load_entrypoint_strategies; _load_module_strategies
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_enrich_context_with_factors（行 57-80）
- 功能：执行对应业务逻辑
- 参数：context: StrategyContext, factor_plugin_modules: str
- 返回值：StrategyContext（见函数语义）
- 逐行分析：
  - 行 57：def _enrich_context_with_factors(context: StrategyContext, factor_plugin_modules: str) -> StrategyContext: → 无问题
  - 行 58：    factor_registry: dict[str, FactorFunc] = dict(BUILTIN_FACTOR_REGISTRY) → 无问题
  - 行 59：    factor_registry.update(_load_entrypoint_factors()) → 无问题
  - 行 60：    for module_name in _parse_csv(factor_plugin_modules): → 无问题
  - 行 61：        factor_registry.update(_load_module_factors(module_name)) → 无问题
  - 行 62：    if not factor_registry: → 无问题
  - 行 63：        return context → 无问题
  - 行 64：    merged_snapshot: dict[str, dict[str, Any]] = { → 无问题
  - 行 65：        symbol: dict(row) for symbol, row in context.market_snapshot.items() → 无问题
  - 行 66：    } → 无问题
  - 行 67：    for factor in factor_registry.values(): → 无问题
  - 行 68：        updates = factor(context) → 无问题
  - 行 69：        for symbol, fields in updates.items(): → 无问题
  - 行 70：            if symbol not in merged_snapshot: → 无问题
  - 行 71：                merged_snapshot[symbol] = {} → 无问题
  - 行 72：            merged_snapshot[symbol].update(fields) → 无问题
  - 行 73：    return StrategyContext( → 无问题
  - 行 74：        watchlist=list(context.watchlist), → 无问题
  - 行 75：        market_snapshot=merged_snapshot, → 无问题
  - 行 76：        headlines=list(context.headlines), → 无问题
  - 行 77：        news_positive_threshold=context.news_positive_threshold, → 无问题
  - 行 78：        news_negative_threshold=context.news_negative_threshold, → 无问题
  - 行 79：        rotation_top_k=context.rotation_top_k, → 无问题
  - 行 80：    ) → 无问题
- 调用的外部函数：dict; factor_registry.update; _parse_csv; factor_registry.values; StrategyContext; _load_entrypoint_factors; factor; updates.items; _load_module_factors; context.market_snapshot.items; update; list
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_load_entrypoint_strategies（行 83-89）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：dict[str, StrategyFunc]（见函数语义）
- 逐行分析：
  - 行 83：def _load_entrypoint_strategies() -> dict[str, StrategyFunc]: → 无问题
  - 行 84：    loaded: dict[str, StrategyFunc] = {} → 无问题
  - 行 85：    for ep in _iter_entry_points("phase0.strategies"): → 无问题
  - 行 86：        candidate = ep.load() → 无问题
  - 行 87：        if callable(candidate): → 无问题
  - 行 88：            loaded[ep.name] = candidate → 无问题
  - 行 89：    return loaded → 无问题
- 调用的外部函数：_iter_entry_points; ep.load; callable
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_load_entrypoint_factors（行 92-98）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：dict[str, FactorFunc]（见函数语义）
- 逐行分析：
  - 行 92：def _load_entrypoint_factors() -> dict[str, FactorFunc]: → 无问题
  - 行 93：    loaded: dict[str, FactorFunc] = {} → 无问题
  - 行 94：    for ep in _iter_entry_points("phase0.factors"): → 无问题
  - 行 95：        candidate = ep.load() → 无问题
  - 行 96：        if callable(candidate): → 无问题
  - 行 97：            loaded[ep.name] = candidate → 无问题
  - 行 98：    return loaded → 无问题
- 调用的外部函数：_iter_entry_points; ep.load; callable
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_iter_entry_points（行 101-115）
- 功能：执行对应业务逻辑
- 参数：group: str
- 返回值：list[Any]（见函数语义）
- 逐行分析：
  - 行 101：def _iter_entry_points(group: str) -> list[Any]: → 问题（ID 1）
  - 行 102：    try: → 问题（ID 1）
  - 行 103：        selected = entry_points(group=group) → 问题（ID 1）
  - 行 104：    except TypeError: → 问题（ID 1）
  - 行 105：        selected = None → 问题（ID 1）
  - 行 106：    if selected is not None: → 问题（ID 1）
  - 行 107：        return list(selected) → 问题（ID 1）
  - 行 108：    eps = entry_points() → 问题（ID 1）
  - 行 109：    select = getattr(eps, "select", None) → 问题（ID 1）
  - 行 110：    if callable(select): → 问题（ID 1）
  - 行 111：        return list(select(group=group)) → 问题（ID 1）
  - 行 112：    if isinstance(eps, Mapping): → 问题（ID 1）
  - 行 113：        group_items = eps.get(group, []) → 问题（ID 1）
  - 行 114：        return list(group_items) → 问题（ID 1）
  - 行 115：    return [] → 问题（ID 1）
- 调用的外部函数：entry_points; getattr; callable; isinstance; list; eps.get; select
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 1：entry_points 兼容性分支风险（致命）

#### 函数：_load_module_strategies（行 118-126）
- 功能：执行对应业务逻辑
- 参数：module_name: str
- 返回值：dict[str, StrategyFunc]（见函数语义）
- 逐行分析：
  - 行 118：def _load_module_strategies(module_name: str) -> dict[str, StrategyFunc]: → 无问题
  - 行 119：    module = import_module(module_name) → 无问题
  - 行 120：    register = getattr(module, "register_strategies", None) → 无问题
  - 行 121：    if not callable(register): → 无问题
  - 行 122：        return {} → 无问题
  - 行 123：    loaded = register() → 无问题
  - 行 124：    if not isinstance(loaded, dict): → 无问题
  - 行 125：        return {} → 无问题
  - 行 126：    return {str(name): func for name, func in loaded.items() if callable(func)} → 无问题
- 调用的外部函数：import_module; getattr; register; callable; isinstance; str; loaded.items
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_load_module_factors（行 129-137）
- 功能：执行对应业务逻辑
- 参数：module_name: str
- 返回值：dict[str, FactorFunc]（见函数语义）
- 逐行分析：
  - 行 129：def _load_module_factors(module_name: str) -> dict[str, FactorFunc]: → 无问题
  - 行 130：    module = import_module(module_name) → 无问题
  - 行 131：    register = getattr(module, "register_factors", None) → 无问题
  - 行 132：    if not callable(register): → 无问题
  - 行 133：        return {} → 无问题
  - 行 134：    loaded = register() → 无问题
  - 行 135：    if not isinstance(loaded, dict): → 无问题
  - 行 136：        return {} → 无问题
  - 行 137：    return {str(name): func for name, func in loaded.items() if callable(func)} → 无问题
- 调用的外部函数：import_module; getattr; register; callable; isinstance; str; loaded.items
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_parse_csv（行 140-141）
- 功能：执行对应业务逻辑
- 参数：raw: str
- 返回值：list[str]（见函数语义）
- 逐行分析：
  - 行 140：def _parse_csv(raw: str) -> list[str]: → 无问题
  - 行 141：    return [item.strip() for item in raw.split(",") if item.strip()] → 无问题
- 调用的外部函数：item.strip; raw.split
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| 100-115 | entry_points 兼容性分支风险 | 致命 | 1 |

### 自检统计
- 实际逐行审计行数：141
- 函数审计数：9
- 发现问题数：1

## 文件：strategies/library.py
- 总行数：138
- 函数/方法数：4

### 逐函数检查

#### 函数：__module__（行 1-96）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from collections import defaultdict → 无问题
  - 行 4：import math → 无问题
  - 行 5：from typing import Callable → 无问题
  - 行 6： → 无问题
  - 行 7：from .base import StrategyContext, StrategySignal → 无问题
  - 行 8： → 无问题
  - 行 9： → 无问题
  - 行 10：StrategyFunc = Callable[[StrategyContext], list[StrategySignal]] → 无问题
  - 行 11： → 无问题
  - 行 12： → 无问题
  - 行 36： → 无问题
  - 行 37： → 无问题
  - 行 62： → 无问题
  - 行 63： → 无问题
  - 行 95： → 无问题
  - 行 96： → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：momentum_strategy（行 13-35）
- 功能：执行对应业务逻辑
- 参数：context: StrategyContext
- 返回值：list[StrategySignal]（见函数语义）
- 逐行分析：
  - 行 13：def momentum_strategy(context: StrategyContext) -> list[StrategySignal]: → 无问题
  - 行 14：    signals: list[StrategySignal] = [] → 无问题
  - 行 15：    for symbol in context.watchlist: → 无问题
  - 行 16：        row = context.market_snapshot.get(symbol, {}) → 无问题
  - 行 17：        momentum = row.get("momentum_20d", 0.0) → 无问题
  - 行 18：        volatility = max(row.get("volatility", 0.01), 0.01) → 无问题
  - 行 19：        if momentum <= 0: → 无问题
  - 行 20：            continue → 无问题
  - 行 21：        score = momentum / volatility → 无问题
  - 行 22：        confidence = min(0.95, max(0.2, abs(score) / 5)) → 无问题
  - 行 23：        signals.append( → 无问题
  - 行 24：            StrategySignal( → 无问题
  - 行 25：                strategy="momentum", → 无问题
  - 行 26：                symbol=symbol, → 无问题
  - 行 27：                side="buy", → 无问题
  - 行 28：                score=score, → 无问题
  - 行 29：                confidence=confidence, → 无问题
  - 行 30：                rationale=f"momentum={momentum:.3f},volatility={volatility:.3f}", → 无问题
  - 行 31：                risk_multiplier=1.0 + min(0.2, confidence * 0.2), → 无问题
  - 行 32：                take_profit_boost_pct=min(0.1, confidence * 0.1), → 无问题
  - 行 33：            ) → 无问题
  - 行 34：        ) → 无问题
  - 行 35：    return signals → 无问题
- 调用的外部函数：context.market_snapshot.get; row.get; max; min; signals.append; StrategySignal; abs
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：mean_reversion_strategy（行 38-61）
- 功能：执行对应业务逻辑
- 参数：context: StrategyContext
- 返回值：list[StrategySignal]（见函数语义）
- 逐行分析：
  - 行 38：def mean_reversion_strategy(context: StrategyContext) -> list[StrategySignal]: → 无问题
  - 行 39：    signals: list[StrategySignal] = [] → 无问题
  - 行 40：    for symbol in context.watchlist: → 无问题
  - 行 41：        row = context.market_snapshot.get(symbol, {}) → 无问题
  - 行 42：        z_score = row.get("z_score_5d", 0.0) → 无问题
  - 行 43：        volatility = max(row.get("volatility", 0.01), 0.01) → 无问题
  - 行 44：        if abs(z_score) < 1.25: → 无问题
  - 行 45：            continue → 无问题
  - 行 46：        side = "buy" if z_score < 0 else "sell" → 无问题
  - 行 47：        score = abs(z_score) / volatility → 无问题
  - 行 48：        confidence = min(0.9, 0.25 + abs(z_score) / 5) → 无问题
  - 行 49：        signals.append( → 无问题
  - 行 50：            StrategySignal( → 无问题
  - 行 51：                strategy="mean_reversion", → 无问题
  - 行 52：                symbol=symbol, → 无问题
  - 行 53：                side=side, → 无问题
  - 行 54：                score=score, → 无问题
  - 行 55：                confidence=confidence, → 无问题
  - 行 56：                rationale=f"z_score_5d={z_score:.3f}", → 无问题
  - 行 57：                risk_multiplier=1.0 - min(0.2, confidence * 0.15), → 无问题
  - 行 58：                take_profit_boost_pct=0.02, → 无问题
  - 行 59：            ) → 无问题
  - 行 60：        ) → 无问题
  - 行 61：    return signals → 无问题
- 调用的外部函数：context.market_snapshot.get; row.get; max; min; signals.append; abs; StrategySignal
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：sector_rotation_strategy（行 64-94）
- 功能：执行对应业务逻辑
- 参数：context: StrategyContext
- 返回值：list[StrategySignal]（见函数语义）
- 逐行分析：
  - 行 64：def sector_rotation_strategy(context: StrategyContext) -> list[StrategySignal]: → 无问题
  - 行 65：    sector_scores: dict[str, float] = defaultdict(float) → 无问题
  - 行 66：    by_sector: dict[str, list[tuple[str, float]]] = defaultdict(list) → 无问题
  - 行 67：    for symbol in context.watchlist: → 无问题
  - 行 68：        row = context.market_snapshot.get(symbol, {}) → 无问题
  - 行 69：        sector = str(row.get("sector", "other")) → 无问题
  - 行 70：        rel_strength = row.get("relative_strength", 0.0) → 无问题
  - 行 71：        sector_scores[sector] += rel_strength → 无问题
  - 行 72：        by_sector[sector].append((symbol, rel_strength)) → 无问题
  - 行 73：    if not sector_scores: → 无问题
  - 行 74：        return [] → 无问题
  - 行 75：    top_sector = max(sector_scores.items(), key=lambda item: item[1])[0] → 无问题
  - 行 76：    ranked = sorted(by_sector[top_sector], key=lambda item: item[1], reverse=True) → 无问题
  - 行 77：    picked = ranked[: max(1, context.rotation_top_k)] → 无问题
  - 行 78：    signals: list[StrategySignal] = [] → 无问题
  - 行 79：    for symbol, rel_strength in picked: → 无问题
  - 行 80：        score = rel_strength + math.log1p(max(rel_strength, 0)) → 无问题
  - 行 81：        signals.append( → 无问题
  - 行 82：            StrategySignal( → 无问题
  - 行 83：                strategy="sector_rotation", → 无问题
  - 行 84：                symbol=symbol, → 无问题
  - 行 85：                side="buy", → 无问题
  - 行 86：                score=score, → 无问题
  - 行 87：                confidence=min(0.85, 0.35 + max(0.0, rel_strength)), → 无问题
  - 行 88：                rationale=f"top_sector={top_sector},relative_strength={rel_strength:.3f}", → 无问题
  - 行 89：                risk_multiplier=1.05, → 无问题
  - 行 90：                take_profit_boost_pct=0.04, → 无问题
  - 行 91：                metadata={"sector": top_sector}, → 无问题
  - 行 92：            ) → 无问题
  - 行 93：        ) → 无问题
  - 行 94：    return signals → 无问题
- 调用的外部函数：defaultdict; sorted; context.market_snapshot.get; str; row.get; append; max; signals.append; sector_scores.items; math.log1p; StrategySignal; min
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：news_sentiment_strategy（行 97-138）
- 功能：执行对应业务逻辑
- 参数：context: StrategyContext
- 返回值：list[StrategySignal]（见函数语义）
- 逐行分析：
  - 行 97：def news_sentiment_strategy(context: StrategyContext) -> list[StrategySignal]: → 问题（ID 9）
  - 行 98：    text = " ".join(context.headlines).lower() → 问题（ID 9）
  - 行 99：    if not text: → 问题（ID 9）
  - 行 100：        return [] → 问题（ID 9）
  - 行 101：    positive_words = ("beat", "surge", "upgrade", "breakthrough", "strong", "growth") → 问题（ID 9）
  - 行 102：    negative_words = ("downgrade", "fraud", "lawsuit", "miss", "weak", "plunge") → 问题（ID 9）
  - 行 103：    pos = sum(text.count(w) for w in positive_words) → 问题（ID 9）
  - 行 104：    neg = sum(text.count(w) for w in negative_words) → 问题（ID 9）
  - 行 105：    total = max(1, pos + neg) → 问题（ID 9）
  - 行 106：    sentiment = (pos - neg) / total → 问题（ID 9）
  - 行 107：    if sentiment < context.news_positive_threshold and sentiment > context.news_negative_threshold: → 问题（ID 9）
  - 行 108：        return [] → 问题（ID 9）
  - 行 109：    side = "buy" if sentiment >= context.news_positive_threshold else "sell" → 问题（ID 9）
  - 行 110：    if not context.watchlist: → 问题（ID 9）
  - 行 111：        return [] → 问题（ID 9）
  - 行 112：    signals: list[StrategySignal] = [] → 问题（ID 9）
  - 行 113：    for symbol in context.watchlist: → 问题（ID 9）
  - 行 114：        row = context.market_snapshot.get(symbol, {}) → 问题（ID 9）
  - 行 115：        relative_strength = max(0.0, float(row.get("relative_strength", 0.0))) → 问题（ID 9）
  - 行 116：        liquidity = max(0.0, min(1.0, float(row.get("liquidity_score", 0.5)))) → 问题（ID 9）
  - 行 117：        symbol_weight = 0.65 + min(0.25, relative_strength) + liquidity * 0.1 → 问题（ID 9）
  - 行 118：        score = abs(sentiment) * 10 * symbol_weight → 问题（ID 9）
  - 行 119：        confidence = min(0.9, 0.28 + abs(sentiment) * 0.45 + relative_strength * 0.2) → 问题（ID 9）
  - 行 120：        signals.append( → 问题（ID 9）
  - 行 121：            StrategySignal( → 问题（ID 9）
  - 行 122：                strategy="news_sentiment", → 问题（ID 9）
  - 行 123：                symbol=symbol, → 问题（ID 9）
  - 行 124：                side=side, → 问题（ID 9）
  - 行 125：                score=score, → 问题（ID 9）
  - 行 126：                confidence=confidence, → 问题（ID 9）
  - 行 127：                rationale=f"news_sentiment={sentiment:.3f},relative_strength={relative_strength:.3f}", → 问题（ID 9）
  - 行 128：                risk_multiplier=1.0 - min(0.25, abs(sentiment) * 0.2), → 问题（ID 9）
  - 行 129：                take_profit_boost_pct=0.06 if side == "buy" else 0.03, → 问题（ID 9）
  - 行 130：                metadata={ → 问题（ID 9）
  - 行 131：                    "sentiment": sentiment, → 问题（ID 9）
  - 行 132：                    "positive_hits": pos, → 问题（ID 9）
  - 行 133：                    "negative_hits": neg, → 问题（ID 9）
  - 行 134：                    "symbol_weight": round(symbol_weight, 4), → 问题（ID 9）
  - 行 135：                }, → 问题（ID 9）
  - 行 136：            ) → 问题（ID 9）
  - 行 137：        ) → 问题（ID 9）
  - 行 138：    return signals → 问题（ID 9）
- 调用的外部函数：lower; sum; max; context.market_snapshot.get; min; signals.append; join; text.count; float; StrategySignal; row.get; abs; round
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 9：新闻情绪策略偏置风险（中）

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| 97-138 | 新闻情绪策略偏置风险 | 中 | 9 |

### 自检统计
- 实际逐行审计行数：138
- 函数审计数：4
- 发现问题数：1

## 文件：lanes/__init__.py
- 总行数：660
- 函数/方法数：28

### 逐函数检查

#### 函数：__module__（行 1-660）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from datetime import datetime, timedelta, timezone → 无问题
  - 行 4：import json → 无问题
  - 行 5：import logging → 无问题
  - 行 6：import math → 无问题
  - 行 7： → 无问题
  - 行 8：from ..ai import ( → 无问题
  - 行 9：    MemoryRecord, → 无问题
  - 行 10：    PersistentLayeredMemoryStore, → 无问题
  - 行 11：    analyze_low_lane, → 无问题
  - 行 12：    assess_high_lane, → 无问题
  - 行 13：    evaluate_ultra_guard, → 无问题
  - 行 14：) → 无问题
  - 行 15：from ..audit import ( → 无问题
  - 行 16：    ParameterAuditEntry, → 无问题
  - 行 17：    is_stoploss_override_used, → 无问题
  - 行 18：    mark_stoploss_override_used, → 无问题
  - 行 19：    write_parameter_audit, → 无问题
  - 行 20：) → 无问题
  - 行 21：from ..config import AppConfig → 无问题
  - 行 22：from ..discipline import build_daily_discipline_plan, evaluate_hold_worthiness → 无问题
  - 行 23：from ..ibkr_order_adapter import map_decision_to_ibkr_bracket → 无问题
  - 行 24：from ..strategies import StrategyContext, run_strategies → 无问题
  - 行 25：from .bus import InMemoryLaneBus, LaneEvent → 无问题
  - 行 26：from .high import HighLaneSettings, evaluate_event → 无问题
  - 行 27：from .low import build_watchlist, build_watchlist_with_rotation → 无问题
  - 行 28：from .low_subscriber import consume_high_decisions_and_publish_low_analysis, get_cached_low_analysis → 无问题
  - 行 29：from .ultra import emit_event → 无问题
  - 行 30： → 无问题
  - 行 31：logger = logging.getLogger(__name__) → 无问题
  - 行 32： → 无问题
  - 行 33： → 无问题
  - 行 290： → 无问题
  - 行 291： → 无问题
  - 行 302： → 无问题
  - 行 303： → 无问题
  - 行 306： → 无问题
  - 行 307： → 无问题
  - 行 316： → 无问题
  - 行 317： → 无问题
  - 行 346： → 无问题
  - 行 347： → 无问题
  - 行 357： → 无问题
  - 行 358： → 无问题
  - 行 394： → 无问题
  - 行 395： → 无问题
  - 行 401： → 无问题
  - 行 402： → 无问题
  - 行 403：class _NonAIUltraSignal: → 无问题
  - 行 412： → 无问题
  - 行 413： → 无问题
  - 行 414：class _NonAILowAnalysis: → 无问题
  - 行 421： → 无问题
  - 行 422： → 无问题
  - 行 423：class _NonAIHighAdjustment: → 无问题
  - 行 429： → 无问题
  - 行 430： → 无问题
  - 行 431：class _NonAIHighAssessment: → 无问题
  - 行 436： → 无问题
  - 行 437： → 无问题
  - 行 440： → 无问题
  - 行 441： → 无问题
  - 行 444： → 无问题
  - 行 445： → 无问题
  - 行 448： → 无问题
  - 行 449： → 无问题
  - 行 452： → 无问题
  - 行 453： → 无问题
  - 行 458： → 无问题
  - 行 459： → 无问题
  - 行 471： → 无问题
  - 行 472： → 无问题
  - 行 511： → 无问题
  - 行 512： → 无问题
  - 行 520： → 无问题
  - 行 521： → 无问题
  - 行 530： → 无问题
  - 行 531： → 无问题
  - 行 536： → 无问题
  - 行 537： → 无问题
  - 行 548： → 无问题
  - 行 549： → 无问题
  - 行 558： → 无问题
  - 行 559： → 无问题
  - 行 578： → 无问题
  - 行 579： → 无问题
  - 行 592： → 问题（ID 7）
  - 行 593： → 问题（ID 7）
  - 行 609： → 问题（ID 7）
  - 行 610： → 问题（ID 7）
  - 行 649： → 无问题
  - 行 650： → 无问题
  - 行 651：__all__ = [ → 无问题
  - 行 652：    "emit_event", → 无问题
  - 行 653：    "evaluate_event", → 无问题
  - 行 654：    "build_watchlist", → 无问题
  - 行 655：    "HighLaneSettings", → 无问题
  - 行 656：    "LaneEvent", → 无问题
  - 行 657：    "InMemoryLaneBus", → 无问题
  - 行 658：    "run_lane_cycle", → 无问题
  - 行 659：    "run_lane_cycle_with_guard", → 无问题
  - 行 660：] → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：run_lane_cycle（行 34-289）
- 功能：执行对应业务逻辑
- 参数：symbol: str, config: AppConfig, bus: InMemoryLaneBus | None, seed_event: dict[str, str] | None, market_snapshot: dict[str, dict[str, float | str]] | None, headlines: list[str] | None, daily_state: dict[str, object] | None
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 34：def run_lane_cycle( → 无问题
  - 行 35：    symbol: str, → 无问题
  - 行 36：    config: AppConfig, → 无问题
  - 行 37：    bus: InMemoryLaneBus | None = None, → 无问题
  - 行 38：    seed_event: dict[str, str] | None = None, → 无问题
  - 行 39：    market_snapshot: dict[str, dict[str, float | str]] | None = None, → 无问题
  - 行 40：    headlines: list[str] | None = None, → 无问题
  - 行 41：    daily_state: dict[str, object] | None = None, → 无问题
  - 行 42：) -> dict[str, object]: → 无问题
  - 行 43：    now = datetime.now(tz=timezone.utc) → 无问题
  - 行 44：    ai_enabled = config.ai_enabled → 无问题
  - 行 45：    runtime_daily_state = daily_state or {} → 无问题
  - 行 46：    active_bus = bus or InMemoryLaneBus(dedup_capacity=max(256, config.lane_bus_dedup_ttl_seconds)) → 无问题
  - 行 47：    snapshot = market_snapshot or _load_market_snapshot(config) → 无问题
  - 行 48：    watchlist = build_watchlist_with_rotation(snapshot, top_k=config.strategy_rotation_top_k) → 无问题
  - 行 49：    headline_entries = _normalize_headlines(headlines, now=now) → 无问题
  - 行 50：    context = StrategyContext( → 无问题
  - 行 51：        watchlist=watchlist, → 无问题
  - 行 52：        market_snapshot=snapshot, → 无问题
  - 行 53：        headlines=[item["headline"] for item in headline_entries], → 无问题
  - 行 54：        news_positive_threshold=config.strategy_news_positive_threshold, → 无问题
  - 行 55：        news_negative_threshold=config.strategy_news_negative_threshold, → 无问题
  - 行 56：        rotation_top_k=config.strategy_rotation_top_k, → 无问题
  - 行 57：    ) → 无问题
  - 行 58：    enabled = _parse_enabled_strategies(config.strategy_enabled_list) → 无问题
  - 行 59：    strategy_signals = run_strategies( → 无问题
  - 行 60：        enabled, → 无问题
  - 行 61：        context, → 无问题
  - 行 62：        strategy_plugin_modules=config.strategy_plugin_modules, → 无问题
  - 行 63：        factor_plugin_modules=config.factor_plugin_modules, → 无问题
  - 行 64：    ) → 无问题
  - 行 65：    signal_weights = _normalize_signal_weights( → 无问题
  - 行 66：        strategy_signals, → 无问题
  - 行 67：        temperature=max(0.1, config.risk_exposure_softmax_temperature), → 无问题
  - 行 68：    ) → 无问题
  - 行 69：    chosen = strategy_signals[0] if strategy_signals else None → 无问题
  - 行 70：    selected_symbol = str(getattr(chosen, "symbol", symbol)).upper() → 无问题
  - 行 71：    selected_market_row = snapshot.get(selected_symbol, {}) → 无问题
  - 行 72：    lead_headline = headline_entries[0] → 无问题
  - 行 73：    if ai_enabled: → 无问题
  - 行 74：        ultra = evaluate_ultra_guard( → 无问题
  - 行 75：            headline=str(lead_headline["headline"]), → 无问题
  - 行 76：            published_at=lead_headline["published_at"], → 无问题
  - 行 77：            now=now, → 无问题
  - 行 78：            max_age_minutes=config.ai_message_max_age_minutes, → 无问题
  - 行 79：            market_row=selected_market_row, → 无问题
  - 行 80：        ) → 无问题
  - 行 81：    else: → 无问题
  - 行 82：        ultra = _non_ai_ultra_signal() → 无问题
  - 行 83：    committee_models = [item.strip() for item in config.ai_low_committee_models.split(",") if item.strip()] → 无问题
  - 行 84：    if ai_enabled: → 无问题
  - 行 85：        cached_low_analysis = get_cached_low_analysis(str(getattr(chosen, "symbol", symbol))) → 无问题
  - 行 86：        low_analysis = cached_low_analysis or analyze_low_lane( → 无问题
  - 行 87：            market_snapshot=snapshot, → 无问题
  - 行 88：            committee_models=committee_models[:3], → 无问题
  - 行 89：            committee_min_support=config.ai_low_committee_min_support, → 无问题
  - 行 90：            strategy_name=str(getattr(chosen, "strategy", "none")), → 无问题
  - 行 91：            strategy_confidence=float(getattr(chosen, "confidence", 0.0)), → 无问题
  - 行 92：        ) → 无问题
  - 行 93：        memory_store = PersistentLayeredMemoryStore(config.ai_memory_db_path, _default_memory_records(now)) → 无问题
  - 行 94：        memory_context = memory_store.query( → 无问题
  - 行 95：            query_text=f'{getattr(chosen, "symbol", symbol)} {" ".join(context.headlines)}', → 无问题
  - 行 96：            now=now, → 无问题
  - 行 97：            limit=3, → 无问题
  - 行 98：        ) → 无问题
  - 行 99：    else: → 无问题
  - 行 100：        low_analysis = _non_ai_low_analysis() → 无问题
  - 行 101：        memory_context = [] → 无问题
  - 行 102：    if seed_event is not None: → 无问题
  - 行 103：        raw_event = dict(seed_event) → 无问题
  - 行 104：    else: → 无问题
  - 行 105：        raw_event = _build_strategy_event( → 无问题
  - 行 106：            symbol, → 无问题
  - 行 107：            chosen, → 无问题
  - 行 108：            context.market_snapshot, → 无问题
  - 行 109：            default_stop_loss_pct=config.ai_stop_loss_default_pct, → 无问题
  - 行 110：        ) → 无问题
  - 行 111：    selected_weight = signal_weights.get( → 无问题
  - 行 112：        str(getattr(chosen, "strategy", "")), → 无问题
  - 行 113：        1.0 if chosen is not None else 1.0, → 无问题
  - 行 114：    ) → 无问题
  - 行 115：    raw_event["target_weight"] = f"{selected_weight:.6f}" → 无问题
  - 行 116：    raw_event["current_exposure_unit"] = "notional" → 无问题
  - 行 117：    raw_event["equity_peak"] = str(runtime_daily_state.get("equity_peak", raw_event.get("equity", "100000"))) → 无问题
  - 行 118：    stop_ratio = _current_stop_loss_pct(raw_event) → 无问题
  - 行 119：    symbol_key = str(raw_event.get("symbol", symbol)) → 无问题
  - 行 120：    if ai_enabled: → 无问题
  - 行 121：        high_assessment = assess_high_lane( → 无问题
  - 行 122：            strategy_name=str(getattr(chosen, "strategy", "none")), → 无问题
  - 行 123：            strategy_confidence=float(getattr(chosen, "confidence", 0.0)), → 无问题
  - 行 124：            low_committee_approved=low_analysis.committee_approved and ultra.wake_low and ultra.wake_high, → 无问题
  - 行 125：            ultra_authenticity_score=float(getattr(ultra, "authenticity_score", 0.0)), → 无问题
  - 行 126：            quick_filter_score=float(getattr(ultra, "quick_filter_score", 0.0)), → 无问题
  - 行 127：            high_confidence_gate=config.ai_high_confidence_gate, → 无问题
  - 行 128：            current_stop_loss_pct=stop_ratio, → 无问题
  - 行 129：            stop_loss_override_used=is_stoploss_override_used(config.ai_state_db_path, symbol_key), → 无问题
  - 行 130：            default_stop_loss_pct=config.ai_stop_loss_default_pct, → 无问题
  - 行 131：            max_stop_loss_pct=config.ai_stop_loss_break_max_pct, → 无问题
  - 行 132：            mode=config.ai_high_mode, → 无问题
  - 行 133：            committee_models=[item.strip() for item in config.ai_high_committee_models.split(",") if item.strip()], → 无问题
  - 行 134：            committee_min_support=config.ai_high_committee_min_support, → 无问题
  - 行 135：        ) → 无问题
  - 行 136：        high_adjustment = high_assessment.decision → 无问题
  - 行 137：        if high_adjustment.approved and high_adjustment.stop_loss_pct > stop_ratio: → 无问题
  - 行 138：            _apply_stop_loss_pct(raw_event, high_adjustment.stop_loss_pct) → 无问题
  - 行 139：            mark_stoploss_override_used( → 无问题
  - 行 140：                config.ai_state_db_path, → 无问题
  - 行 141：                symbol_key, → 无问题
  - 行 142：                ttl_hours=config.ai_stoploss_override_ttl_hours, → 无问题
  - 行 143：            ) → 无问题
  - 行 144：        write_parameter_audit( → 无问题
  - 行 145：            config.ai_state_db_path, → 无问题
  - 行 146：            ParameterAuditEntry( → 无问题
  - 行 147：                ts=now.isoformat(), → 无问题
  - 行 148：                symbol=symbol_key, → 无问题
  - 行 149：                strategy=str(getattr(chosen, "strategy", "none")), → 无问题
  - 行 150：                approved=high_adjustment.approved, → 无问题
  - 行 151：                reason=high_adjustment.reason, → 无问题
  - 行 152：                before_stop_loss_pct=round(stop_ratio, 6), → 无问题
  - 行 153：                after_stop_loss_pct=round(_current_stop_loss_pct(raw_event), 6), → 无问题
  - 行 154：                before_risk_multiplier=1.0, → 无问题
  - 行 155：                after_risk_multiplier=high_adjustment.risk_multiplier if high_adjustment.approved else 1.0, → 无问题
  - 行 156：                low_committee_approved=low_analysis.committee_approved, → 无问题
  - 行 157：                ultra_wake_high=ultra.wake_high, → 无问题
  - 行 158：            ), → 无问题
  - 行 159：        ) → 无问题
  - 行 160：    else: → 无问题
  - 行 161：        high_adjustment = _non_ai_high_adjustment(stop_ratio) → 无问题
  - 行 162：        high_assessment = _non_ai_high_assessment() → 无问题
  - 行 163：    signal_event = LaneEvent.from_payload(event_type="signal", source_lane="ultra", payload=raw_event) → 无问题
  - 行 164：    active_bus.publish("ultra.signal", signal_event) → 无问题
  - 行 165：    signals = active_bus.consume("ultra.signal") → 无问题
  - 行 166：    high_settings = HighLaneSettings.from_app_config(config) → 无问题
  - 行 167：    decisions: list[dict[str, object]] = [] → 无问题
  - 行 168：    for event in signals: → 无问题
  - 行 169：        if _is_risk_execution_blocked(event.payload.get("allow_risk_execution", "true")): → 无问题
  - 行 170：            decision = { → 无问题
  - 行 171：                "lane": "high", → 无问题
  - 行 172：                "status": "rejected", → 无问题
  - 行 173：                "symbol": event.payload.get("symbol", ""), → 无问题
  - 行 174：                "reject_reasons": ["SAFETY_MODE_BLOCKED"], → 无问题
  - 行 175：            } → 无问题
  - 行 176：        else: → 无问题
  - 行 177：            adjustments = _extract_adjustments(chosen) → 无问题
  - 行 178：            adjustments["risk_multiplier"] = min( → 无问题
  - 行 179：                adjustments["risk_multiplier"], → 无问题
  - 行 180：                high_adjustment.risk_multiplier if high_adjustment.approved else 1.0, → 无问题
  - 行 181：            ) → 无问题
  - 行 182：            decision = evaluate_event(event.payload, settings=high_settings, strategy_adjustments=adjustments) → 无问题
  - 行 183：            if chosen is not None: → 无问题
  - 行 184：                decision["strategy"] = chosen.strategy → 无问题
  - 行 185：                decision["strategy_score"] = round(chosen.score, 4) → 无问题
  - 行 186：                decision["strategy_confidence"] = round(chosen.confidence, 4) → 无问题
  - 行 187：                decision["strategy_rationale"] = chosen.rationale → 无问题
  - 行 188：            decision["ultra_authenticity_score"] = ultra.authenticity_score → 无问题
  - 行 189：            decision["ultra_timeliness_score"] = ultra.timeliness_score → 无问题
  - 行 190：            decision["low_committee_approved"] = low_analysis.committee_approved → 无问题
  - 行 191：            decision["high_adjustment_reason"] = high_adjustment.reason → 无问题
  - 行 192：            decision["stop_loss_override_used"] = ( → 无问题
  - 行 193：                is_stoploss_override_used(config.ai_state_db_path, event.payload.get("symbol", symbol)) → 无问题
  - 行 194：                if ai_enabled → 无问题
  - 行 195：                else False → 无问题
  - 行 196：            ) → 无问题
  - 行 197：        decision_event = LaneEvent.from_payload(event_type="decision", source_lane="high", payload=decision) → 无问题
  - 行 198：        active_bus.publish("high.decision", decision_event) → 无问题
  - 行 199：        decisions.append(decision) → 无问题
  - 行 200：    if ai_enabled: → 无问题
  - 行 201：        low_async_results = consume_high_decisions_and_publish_low_analysis( → 无问题
  - 行 202：            bus=active_bus, → 无问题
  - 行 203：            market_snapshot=snapshot, → 无问题
  - 行 204：            committee_models=committee_models[:3], → 无问题
  - 行 205：            committee_min_support=config.ai_low_committee_min_support, → 无问题
  - 行 206：        ) → 无问题
  - 行 207：        low_analysis_events = active_bus.consume("low.analysis") → 无问题
  - 行 208：    else: → 无问题
  - 行 209：        low_async_results = [] → 无问题
  - 行 210：        low_analysis_events = [] → 无问题
  - 行 211：    hold_market_row = snapshot.get(selected_symbol, {}) → 无问题
  - 行 212：    hold = evaluate_hold_worthiness( → 无问题
  - 行 213：        market_row=hold_market_row, → 无问题
  - 行 214：        strategy_confidence=float(getattr(chosen, "confidence", 0.0)), → 无问题
  - 行 215：        ultra_authenticity_score=float(getattr(ultra, "authenticity_score", 1.0)), → 无问题
  - 行 216：        low_committee_approved=bool(getattr(low_analysis, "committee_approved", True)), → 无问题
  - 行 217：        hold_score_threshold=config.discipline_hold_score_threshold, → 无问题
  - 行 218：        max_holding_days=max(1, config.holding_days), → 无问题
  - 行 219：    ) → 无问题
  - 行 220：    actions_today = int(runtime_daily_state.get("actions_today", len(decisions))) → 无问题
  - 行 221：    has_open_position = bool(runtime_daily_state.get("has_open_position", False)) → 无问题
  - 行 222：    daily_plan = build_daily_discipline_plan( → 无问题
  - 行 223：        actions_today=actions_today, → 无问题
  - 行 224：        has_open_position=has_open_position, → 无问题
  - 行 225：        min_actions_per_day=max(0, config.discipline_min_actions_per_day), → 无问题
  - 行 226：        discipline_enabled=config.discipline_enable_daily_cycle, → 无问题
  - 行 227：        hold=hold, → 无问题
  - 行 228：    ) → 无问题
  - 行 229：    disciplined_decisions = [_apply_discipline_gate(item, daily_plan) for item in decisions] → 无问题
  - 行 230：    disciplined_ibkr_signals: list[dict[str, object]] = [] → 无问题
  - 行 231：    for item in disciplined_decisions: → 无问题
  - 行 232：        mapped = map_decision_to_ibkr_bracket(item) → 无问题
  - 行 233：        if mapped is not None: → 无问题
  - 行 234：            disciplined_ibkr_signals.append(mapped) → 无问题
  - 行 235：    return { → 无问题
  - 行 236：        "event": raw_event, → 无问题
  - 行 237：        "decisions": disciplined_decisions, → 无问题
  - 行 238：        "watchlist": watchlist, → 无问题
  - 行 239：        "ultra_signal": { → 无问题
  - 行 240：            "authenticity_score": ultra.authenticity_score, → 无问题
  - 行 241：            "timeliness_score": ultra.timeliness_score, → 无问题
  - 行 242：            "quick_filter_score": ultra.quick_filter_score, → 无问题
  - 行 243：            "wake_high": ultra.wake_high, → 无问题
  - 行 244：            "wake_low": ultra.wake_low, → 无问题
  - 行 245：            "reason": ultra.reason, → 无问题
  - 行 246：            "fast_reject_reasons": ultra.fast_reject_reasons, → 无问题
  - 行 247：        }, → 无问题
  - 行 248：        "low_analysis": { → 无问题
  - 行 249：            "preferred_sector": low_analysis.preferred_sector, → 无问题
  - 行 250：            "strategy_fit": low_analysis.strategy_fit, → 无问题
  - 行 251：            "sector_allocation": low_analysis.sector_allocation, → 无问题
  - 行 252：            "committee_approved": low_analysis.committee_approved, → 无问题
  - 行 253：            "committee_votes": [ → 无问题
  - 行 254：                {"model": vote.model, "support": vote.support, "score": vote.score} → 无问题
  - 行 255：                for vote in low_analysis.committee_votes → 无问题
  - 行 256：            ], → 无问题
  - 行 257：        }, → 无问题
  - 行 258：        "low_async_analysis": [event.payload for event in low_analysis_events], → 无问题
  - 行 259：        "low_async_processed": len(low_async_results), → 无问题
  - 行 260：        "memory_context": [ → 无问题
  - 行 261：            { → 无问题
  - 行 262：                "memory_id": item.memory_id, → 无问题
  - 行 263：                "tier": item.tier, → 无问题
  - 行 264：                "score": item.score, → 无问题
  - 行 265：                "text": item.text, → 无问题
  - 行 266：                "published_at": item.published_at, → 无问题
  - 行 267：            } → 无问题
  - 行 268：            for item in memory_context → 无问题
  - 行 269：        ], → 无问题
  - 行 270：        "strategy_signals": [_signal_to_dict(signal) for signal in strategy_signals], → 无问题
  - 行 271：        "published_events": len(signals) + len(disciplined_decisions) + len(low_analysis_events), → 无问题
  - 行 272：        "ai_bypassed": not ai_enabled, → 无问题
  - 行 273：        "daily_discipline": daily_plan, → 无问题
  - 行 274：        "high_assessment": { → 无问题
  - 行 275：            "mode": high_assessment.mode, → 无问题
  - 行 276：            "prompt": high_assessment.prompt, → 无问题
  - 行 277：            "committee_votes": [ → 无问题
  - 行 278：                { → 无问题
  - 行 279：                    "model": vote.model, → 无问题
  - 行 280：                    "support": vote.support, → 无问题
  - 行 281：                    "score": vote.score, → 无问题
  - 行 282：                    "risk_multiplier": vote.risk_multiplier, → 无问题
  - 行 283：                    "stop_loss_pct": vote.stop_loss_pct, → 无问题
  - 行 284：                } → 无问题
  - 行 285：                for vote in high_assessment.committee_votes → 无问题
  - 行 286：            ], → 无问题
  - 行 287：        }, → 无问题
  - 行 288：        "ibkr_order_signals": disciplined_ibkr_signals, → 无问题
  - 行 289：    } → 无问题
- 调用的外部函数：datetime.now; build_watchlist_with_rotation; _normalize_headlines; StrategyContext; _parse_enabled_strategies; run_strategies; _normalize_signal_weights; upper; snapshot.get; signal_weights.get; str; _current_stop_loss_pct; LaneEvent.from_payload; active_bus.publish; active_bus.consume; HighLaneSettings.from_app_config; evaluate_hold_worthiness; int; bool; build_daily_discipline_plan; InMemoryLaneBus; _load_market_snapshot; evaluate_ultra_guard; _non_ai_ultra_signal; item.strip; get_cached_low_analysis; PersistentLayeredMemoryStore; memory_store.query; _non_ai_low_analysis; dict; _build_strategy_event; runtime_daily_state.get; raw_event.get; assess_high_lane; write_parameter_audit; _non_ai_high_adjustment; _non_ai_high_assessment; _is_risk_execution_blocked; decisions.append; consume_high_decisions_and_publish_low_analysis; _apply_discipline_gate; map_decision_to_ibkr_bracket; len; max; config.ai_low_committee_models.split; analyze_low_lane; _default_memory_records; getattr; _apply_stop_loss_pct; mark_stoploss_override_used; ParameterAuditEntry; event.payload.get; _extract_adjustments; min; evaluate_event; float; disciplined_ibkr_signals.append; _signal_to_dict; is_stoploss_override_used; round; now.isoformat; join; config.ai_high_committee_models.split
- 被谁调用：ibkr_execution.py:execute_cycle:127; tests/test_audit_and_memory_persistence.py:AuditAndMemoryPersistenceTests.test_writes_parameter_audit_and_memory_db:30; tests/test_lane_bus.py:LaneBusTests.test_runs_lane_cycle_and_returns_decision:29; tests/test_lane_bus.py:LaneBusTests.test_lane_cycle_stays_stable_under_repeated_runs:63; tests/test_lane_bus.py:LaneBusTests.test_seed_event_boolean_block_is_handled:81; tests/test_lane_bus.py:LaneBusTests.test_lane_cycle_returns_strategy_signals:104; tests/test_lane_bus.py:LaneBusTests.test_lane_cycle_bypasses_ai_when_disabled:119; tests/test_lane_bus.py:LaneBusTests.test_lane_cycle_daily_discipline_buy_when_no_position:128
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：run_lane_cycle_with_guard（行 292-301）
- 功能：执行对应业务逻辑
- 参数：symbol: str, config: AppConfig, allow_risk_execution: bool, bus: InMemoryLaneBus | None
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 292：def run_lane_cycle_with_guard( → 无问题
  - 行 293：    symbol: str, → 无问题
  - 行 294：    config: AppConfig, → 无问题
  - 行 295：    allow_risk_execution: bool, → 无问题
  - 行 296：    bus: InMemoryLaneBus | None = None, → 无问题
  - 行 297：) -> dict[str, object]: → 无问题
  - 行 298：    snapshot = _load_market_snapshot(config) → 无问题
  - 行 299：    raw_event = emit_event(symbol, market_row=snapshot.get(symbol.upper(), {})) → 无问题
  - 行 300：    raw_event["allow_risk_execution"] = "true" if allow_risk_execution else "false" → 无问题
  - 行 301：    return run_lane_cycle(symbol=symbol, config=config, bus=bus, seed_event=raw_event, market_snapshot=snapshot) → 无问题
- 调用的外部函数：_load_market_snapshot; emit_event; run_lane_cycle; snapshot.get; symbol.upper
- 被谁调用：non_ai_validation_report.py:_functional_non_ai_checks:115; replay.py:_run_safety_blocked_execution:131; tests/test_lane_bus.py:LaneBusTests.test_guard_blocks_risk_execution:73
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_parse_enabled_strategies（行 304-305）
- 功能：执行对应业务逻辑
- 参数：raw: str
- 返回值：list[str]（见函数语义）
- 逐行分析：
  - 行 304：def _parse_enabled_strategies(raw: str) -> list[str]: → 无问题
  - 行 305：    return [item.strip() for item in raw.split(",") if item.strip()] → 无问题
- 调用的外部函数：item.strip; raw.split
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_extract_adjustments（行 308-315）
- 功能：执行对应业务逻辑
- 参数：chosen: object | None
- 返回值：dict[str, float]（见函数语义）
- 逐行分析：
  - 行 308：def _extract_adjustments(chosen: object | None) -> dict[str, float]: → 无问题
  - 行 309：    if chosen is None: → 无问题
  - 行 310：        return {"risk_multiplier": 1.0, "take_profit_boost_pct": 0.0} → 无问题
  - 行 311：    signal = chosen → 无问题
  - 行 312：    return { → 无问题
  - 行 313：        "risk_multiplier": float(getattr(signal, "risk_multiplier", 1.0)), → 无问题
  - 行 314：        "take_profit_boost_pct": float(getattr(signal, "take_profit_boost_pct", 0.0)), → 无问题
  - 行 315：    } → 无问题
- 调用的外部函数：float; getattr
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_build_strategy_event（行 318-345）
- 功能：执行对应业务逻辑
- 参数：fallback_symbol: str, chosen: object | None, snapshot: dict[str, dict[str, float]], default_stop_loss_pct: float
- 返回值：dict[str, str]（见函数语义）
- 逐行分析：
  - 行 318：def _build_strategy_event( → 无问题
  - 行 319：    fallback_symbol: str, → 无问题
  - 行 320：    chosen: object | None, → 无问题
  - 行 321：    snapshot: dict[str, dict[str, float]], → 无问题
  - 行 322：    default_stop_loss_pct: float, → 无问题
  - 行 323：) -> dict[str, str]: → 无问题
  - 行 324：    symbol = fallback_symbol.upper() → 无问题
  - 行 325：    side = "buy" → 无问题
  - 行 326：    if chosen is not None: → 无问题
  - 行 327：        symbol = str(getattr(chosen, "symbol", symbol)).upper() → 无问题
  - 行 328：        side = str(getattr(chosen, "side", side)).lower() → 无问题
  - 行 329：    row = snapshot.get(symbol, {}) → 无问题
  - 行 330：    ref_price = max(1.0, float(row.get("reference_price", 100.0))) → 无问题
  - 行 331：    stop_ratio = max(default_stop_loss_pct, min(0.08, float(row.get("stop_ratio", default_stop_loss_pct)))) → 无问题
  - 行 332：    tp_ratio = max(0.06, min(0.2, float(row.get("take_profit_ratio", 0.1)))) → 无问题
  - 行 333：    if side == "sell": → 无问题
  - 行 334：        stop_price = ref_price * (1 + stop_ratio) → 无问题
  - 行 335：        take_profit = ref_price * (1 - tp_ratio) → 无问题
  - 行 336：    else: → 无问题
  - 行 337：        stop_price = ref_price * (1 - stop_ratio) → 无问题
  - 行 338：        take_profit = ref_price * (1 + tp_ratio) → 无问题
  - 行 339：    overrides = { → 无问题
  - 行 340：        "side": side, → 无问题
  - 行 341：        "entry_price": f"{ref_price:.4f}", → 无问题
  - 行 342：        "stop_loss_price": f"{stop_price:.4f}", → 无问题
  - 行 343：        "take_profit_price": f"{take_profit:.4f}", → 无问题
  - 行 344：    } → 无问题
  - 行 345：    return emit_event(symbol, overrides=overrides) → 无问题
- 调用的外部函数：fallback_symbol.upper; snapshot.get; max; emit_event; upper; lower; float; min; row.get; str; getattr
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_signal_to_dict（行 348-356）
- 功能：执行对应业务逻辑
- 参数：signal: object
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 348：def _signal_to_dict(signal: object) -> dict[str, object]: → 无问题
  - 行 349：    return { → 无问题
  - 行 350：        "strategy": str(getattr(signal, "strategy", "")), → 无问题
  - 行 351：        "symbol": str(getattr(signal, "symbol", "")), → 无问题
  - 行 352：        "side": str(getattr(signal, "side", "")), → 无问题
  - 行 353：        "score": round(float(getattr(signal, "score", 0.0)), 4), → 无问题
  - 行 354：        "confidence": round(float(getattr(signal, "confidence", 0.0)), 4), → 无问题
  - 行 355：        "rationale": str(getattr(signal, "rationale", "")), → 无问题
  - 行 356：    } → 无问题
- 调用的外部函数：str; round; getattr; float
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_default_market_snapshot（行 359-393）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：dict[str, dict[str, float | str]]（见函数语义）
- 逐行分析：
  - 行 359：def _default_market_snapshot() -> dict[str, dict[str, float | str]]: → 无问题
  - 行 360：    return { → 无问题
  - 行 361：        "AAPL": { → 无问题
  - 行 362：            "momentum_20d": 0.08, → 无问题
  - 行 363：            "z_score_5d": -0.6, → 无问题
  - 行 364：            "relative_strength": 0.26, → 无问题
  - 行 365：            "volatility": 0.22, → 无问题
  - 行 366：            "reference_price": 180.0, → 无问题
  - 行 367：            "sector": "technology", → 无问题
  - 行 368：        }, → 无问题
  - 行 369：        "MSFT": { → 无问题
  - 行 370：            "momentum_20d": 0.07, → 无问题
  - 行 371：            "z_score_5d": 0.8, → 无问题
  - 行 372：            "relative_strength": 0.21, → 无问题
  - 行 373：            "volatility": 0.19, → 无问题
  - 行 374：            "reference_price": 420.0, → 无问题
  - 行 375：            "sector": "technology", → 无问题
  - 行 376：        }, → 无问题
  - 行 377：        "NVDA": { → 无问题
  - 行 378：            "momentum_20d": 0.14, → 无问题
  - 行 379：            "z_score_5d": 1.4, → 无问题
  - 行 380：            "relative_strength": 0.33, → 无问题
  - 行 381：            "volatility": 0.34, → 无问题
  - 行 382：            "reference_price": 950.0, → 无问题
  - 行 383：            "sector": "technology", → 无问题
  - 行 384：        }, → 无问题
  - 行 385：        "XOM": { → 无问题
  - 行 386：            "momentum_20d": 0.05, → 无问题
  - 行 387：            "z_score_5d": -1.3, → 无问题
  - 行 388：            "relative_strength": 0.18, → 无问题
  - 行 389：            "volatility": 0.18, → 无问题
  - 行 390：            "reference_price": 115.0, → 无问题
  - 行 391：            "sector": "energy", → 无问题
  - 行 392：        }, → 无问题
  - 行 393：    } → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_default_headlines（行 396-400）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：list[str]（见函数语义）
- 逐行分析：
  - 行 396：def _default_headlines() -> list[str]: → 无问题
  - 行 397：    return [ → 无问题
  - 行 398：        "Tech earnings beat estimates and growth outlook remains strong", → 无问题
  - 行 399：        "Analysts upgrade semiconductor leaders after breakout results", → 无问题
  - 行 400：    ] → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_NonAIUltraSignal.__init__（行 404-411）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 404：    def __init__(self) -> None: → 无问题
  - 行 405：        self.authenticity_score = 1.0 → 无问题
  - 行 406：        self.timeliness_score = 1.0 → 无问题
  - 行 407：        self.quick_filter_score = 1.0 → 无问题
  - 行 408：        self.wake_high = True → 无问题
  - 行 409：        self.wake_low = True → 无问题
  - 行 410：        self.reason = "AI_BYPASSED" → 无问题
  - 行 411：        self.fast_reject_reasons = [] → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_NonAILowAnalysis.__init__（行 415-420）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 415：    def __init__(self) -> None: → 无问题
  - 行 416：        self.preferred_sector = "bypassed" → 无问题
  - 行 417：        self.strategy_fit = {} → 无问题
  - 行 418：        self.sector_allocation = {} → 无问题
  - 行 419：        self.committee_approved = True → 无问题
  - 行 420：        self.committee_votes = [] → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_NonAIHighAdjustment.__init__（行 424-428）
- 功能：执行对应业务逻辑
- 参数：self: Any, stop_loss_pct: float
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 424：    def __init__(self, stop_loss_pct: float) -> None: → 无问题
  - 行 425：        self.approved = False → 无问题
  - 行 426：        self.risk_multiplier = 1.0 → 无问题
  - 行 427：        self.stop_loss_pct = stop_loss_pct → 无问题
  - 行 428：        self.reason = "AI_BYPASSED" → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_NonAIHighAssessment.__init__（行 432-435）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 432：    def __init__(self) -> None: → 无问题
  - 行 433：        self.mode = "bypassed" → 无问题
  - 行 434：        self.prompt = "{}" → 无问题
  - 行 435：        self.committee_votes: list[object] = [] → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_non_ai_ultra_signal（行 438-439）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：_NonAIUltraSignal（见函数语义）
- 逐行分析：
  - 行 438：def _non_ai_ultra_signal() -> _NonAIUltraSignal: → 无问题
  - 行 439：    return _NonAIUltraSignal() → 无问题
- 调用的外部函数：_NonAIUltraSignal
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_non_ai_low_analysis（行 442-443）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：_NonAILowAnalysis（见函数语义）
- 逐行分析：
  - 行 442：def _non_ai_low_analysis() -> _NonAILowAnalysis: → 无问题
  - 行 443：    return _NonAILowAnalysis() → 无问题
- 调用的外部函数：_NonAILowAnalysis
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_non_ai_high_adjustment（行 446-447）
- 功能：执行对应业务逻辑
- 参数：stop_loss_pct: float
- 返回值：_NonAIHighAdjustment（见函数语义）
- 逐行分析：
  - 行 446：def _non_ai_high_adjustment(stop_loss_pct: float) -> _NonAIHighAdjustment: → 无问题
  - 行 447：    return _NonAIHighAdjustment(stop_loss_pct=stop_loss_pct) → 无问题
- 调用的外部函数：_NonAIHighAdjustment
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_non_ai_high_assessment（行 450-451）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：_NonAIHighAssessment（见函数语义）
- 逐行分析：
  - 行 450：def _non_ai_high_assessment() -> _NonAIHighAssessment: → 无问题
  - 行 451：    return _NonAIHighAssessment() → 无问题
- 调用的外部函数：_NonAIHighAssessment
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_normalize_headlines（行 454-457）
- 功能：执行对应业务逻辑
- 参数：headlines: list[str] | None, now: datetime
- 返回值：list[dict[str, object]]（见函数语义）
- 逐行分析：
  - 行 454：def _normalize_headlines(headlines: list[str] | None, now: datetime) -> list[dict[str, object]]: → 无问题
  - 行 455：    if not headlines: → 无问题
  - 行 456：        return _default_headline_entries(now) → 无问题
  - 行 457：    return [{"headline": text, "published_at": now - timedelta(minutes=30)} for text in headlines] → 无问题
- 调用的外部函数：_default_headline_entries; timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_default_headline_entries（行 460-470）
- 功能：执行对应业务逻辑
- 参数：now: datetime
- 返回值：list[dict[str, object]]（见函数语义）
- 逐行分析：
  - 行 460：def _default_headline_entries(now: datetime) -> list[dict[str, object]]: → 无问题
  - 行 461：    return [ → 无问题
  - 行 462：        { → 无问题
  - 行 463：            "headline": "消费电子需求修复，供应链订单环比走强", → 无问题
  - 行 464：            "published_at": now - timedelta(minutes=45), → 无问题
  - 行 465：        }, → 无问题
  - 行 466：        { → 无问题
  - 行 467：            "headline": "半导体设备龙头获上调评级并公布强劲指引", → 无问题
  - 行 468：            "published_at": now - timedelta(hours=2), → 无问题
  - 行 469：        }, → 无问题
  - 行 470：    ] → 无问题
- 调用的外部函数：timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_default_memory_records（行 473-510）
- 功能：执行对应业务逻辑
- 参数：now: datetime
- 返回值：list[MemoryRecord]（见函数语义）
- 逐行分析：
  - 行 473：def _default_memory_records(now: datetime) -> list[MemoryRecord]: → 无问题
  - 行 474：    return [ → 无问题
  - 行 475：        MemoryRecord( → 无问题
  - 行 476：            memory_id="mem-short-1", → 无问题
  - 行 477：            tier="short", → 无问题
  - 行 478：            text="一天前消费电子行业周报提到小米手机和可穿戴需求回暖。", → 无问题
  - 行 479：            published_at=now - timedelta(days=1), → 无问题
  - 行 480：            tags=("小米", "消费电子", "需求"), → 无问题
  - 行 481：        ), → 无问题
  - 行 482：        MemoryRecord( → 无问题
  - 行 483：            memory_id="mem-long-1", → 无问题
  - 行 484：            tier="long", → 无问题
  - 行 485：            text="一个月前上游芯片与模组供应链价格下行，改善硬件毛利。", → 无问题
  - 行 486：            published_at=now - timedelta(days=30), → 无问题
  - 行 487：            tags=("小米", "供应链", "芯片"), → 无问题
  - 行 488：        ), → 无问题
  - 行 489：        MemoryRecord( → 无问题
  - 行 490：            memory_id="mem-rel-1", → 无问题
  - 行 491：            tier="relational", → 无问题
  - 行 492：            text="小米与消费电子渠道补库存节奏同步，板块相关性较高。", → 无问题
  - 行 493：            published_at=now - timedelta(days=6), → 无问题
  - 行 494：            tags=("小米", "渠道", "消费电子"), → 无问题
  - 行 495：        ), → 无问题
  - 行 496：        MemoryRecord( → 无问题
  - 行 497：            memory_id="mem-noise-1", → 无问题
  - 行 498：            tier="short", → 无问题
  - 行 499：            text="一小时前麦当劳新品营销活动。", → 无问题
  - 行 500：            published_at=now - timedelta(hours=1), → 无问题
  - 行 501：            tags=("餐饮", "麦当劳"), → 无问题
  - 行 502：        ), → 无问题
  - 行 503：        MemoryRecord( → 无问题
  - 行 504：            memory_id="mem-noise-2", → 无问题
  - 行 505：            tier="long", → 无问题
  - 行 506：            text="半年前国际油价波动与石油库存变化。", → 无问题
  - 行 507：            published_at=now - timedelta(days=180), → 无问题
  - 行 508：            tags=("石油", "能源"), → 无问题
  - 行 509：        ), → 无问题
  - 行 510：    ] → 无问题
- 调用的外部函数：MemoryRecord; timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_current_stop_loss_pct（行 513-519）
- 功能：执行对应业务逻辑
- 参数：event: dict[str, str]
- 返回值：float（见函数语义）
- 逐行分析：
  - 行 513：def _current_stop_loss_pct(event: dict[str, str]) -> float: → 无问题
  - 行 514：    side = event.get("side", "buy").lower() → 无问题
  - 行 515：    entry = float(event.get("entry_price", "100")) → 无问题
  - 行 516：    stop = float(event.get("stop_loss_price", "98")) → 无问题
  - 行 517：    if side == "sell": → 无问题
  - 行 518：        return max(0.0, (stop - entry) / entry) → 无问题
  - 行 519：    return max(0.0, (entry - stop) / entry) → 无问题
- 调用的外部函数：lower; float; max; event.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_apply_stop_loss_pct（行 522-529）
- 功能：执行对应业务逻辑
- 参数：event: dict[str, str], stop_loss_pct: float
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 522：def _apply_stop_loss_pct(event: dict[str, str], stop_loss_pct: float) -> None: → 无问题
  - 行 523：    side = event.get("side", "buy").lower() → 无问题
  - 行 524：    entry = float(event.get("entry_price", "100")) → 无问题
  - 行 525：    if side == "sell": → 无问题
  - 行 526：        stop = entry * (1 + stop_loss_pct) → 无问题
  - 行 527：    else: → 无问题
  - 行 528：        stop = entry * (1 - stop_loss_pct) → 无问题
  - 行 529：    event["stop_loss_price"] = f"{stop:.4f}" → 无问题
- 调用的外部函数：lower; float; event.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_is_risk_execution_blocked（行 532-535）
- 功能：执行对应业务逻辑
- 参数：raw_value: object
- 返回值：bool（见函数语义）
- 逐行分析：
  - 行 532：def _is_risk_execution_blocked(raw_value: object) -> bool: → 无问题
  - 行 533：    if isinstance(raw_value, bool): → 无问题
  - 行 534：        return not raw_value → 无问题
  - 行 535：    return str(raw_value).strip().lower() in {"0", "false", "no", "off"} → 无问题
- 调用的外部函数：isinstance; lower; strip; str
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_apply_discipline_gate（行 538-547）
- 功能：执行对应业务逻辑
- 参数：decision: dict[str, object], daily_plan: dict[str, object]
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 538：def _apply_discipline_gate(decision: dict[str, object], daily_plan: dict[str, object]) -> dict[str, object]: → 无问题
  - 行 539：    if decision.get("status") != "accepted": → 无问题
  - 行 540：        return decision → 无问题
  - 行 541：    required_action = str(daily_plan.get("required_action", "none")) → 无问题
  - 行 542：    side = str(decision.get("bracket_order", {}).get("parent", {}).get("action", "")).upper() → 无问题
  - 行 543：    if required_action == "hold": → 无问题
  - 行 544：        return _discipline_reject(decision, "DISCIPLINE_HOLD_REQUIRED") → 无问题
  - 行 545：    if required_action == "sell" and side == "BUY": → 无问题
  - 行 546：        return _discipline_reject(decision, "DISCIPLINE_SELL_PRIORITY") → 无问题
  - 行 547：    return decision → 无问题
- 调用的外部函数：str; upper; decision.get; daily_plan.get; _discipline_reject; get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_discipline_reject（行 550-557）
- 功能：执行对应业务逻辑
- 参数：decision: dict[str, object], reason: str
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 550：def _discipline_reject(decision: dict[str, object], reason: str) -> dict[str, object]: → 无问题
  - 行 551：    rejected = dict(decision) → 无问题
  - 行 552：    rejected["status"] = "rejected" → 无问题
  - 行 553：    rejected["bracket_order"] = {} → 无问题
  - 行 554：    reasons = list(rejected.get("reject_reasons", [])) → 无问题
  - 行 555：    reasons.append(reason) → 无问题
  - 行 556：    rejected["reject_reasons"] = reasons → 无问题
  - 行 557：    return rejected → 无问题
- 调用的外部函数：dict; list; reasons.append; rejected.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_normalize_signal_weights（行 560-577）
- 功能：执行对应业务逻辑
- 参数：strategy_signals: list[object], temperature: float
- 返回值：dict[str, float]（见函数语义）
- 逐行分析：
  - 行 560：def _normalize_signal_weights(strategy_signals: list[object], temperature: float) -> dict[str, float]: → 无问题
  - 行 561：    if not strategy_signals: → 无问题
  - 行 562：        return {} → 无问题
  - 行 563：    temp = max(0.1, temperature) → 无问题
  - 行 564：    score_pairs: list[tuple[str, float]] = [] → 无问题
  - 行 565：    for item in strategy_signals: → 无问题
  - 行 566：        key = str(getattr(item, "strategy", "unknown")) → 无问题
  - 行 567：        score = float(getattr(item, "score", 0.0)) * max(0.01, float(getattr(item, "confidence", 0.0))) → 无问题
  - 行 568：        score_pairs.append((key, score)) → 无问题
  - 行 569：    max_score = max(score for _, score in score_pairs) → 无问题
  - 行 570：    exps: list[tuple[str, float]] = [] → 无问题
  - 行 571：    for key, score in score_pairs: → 无问题
  - 行 572：        exps.append((key, math.exp((score - max_score) / temp))) → 无问题
  - 行 573：    total = sum(value for _, value in exps) or 1.0 → 无问题
  - 行 574：    weights: dict[str, float] = {} → 无问题
  - 行 575：    for key, value in exps: → 无问题
  - 行 576：        weights[key] = weights.get(key, 0.0) + value / total → 无问题
  - 行 577：    return weights → 无问题
- 调用的外部函数：max; str; score_pairs.append; exps.append; sum; getattr; float; weights.get; math.exp
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_load_market_snapshot（行 580-591）
- 功能：执行对应业务逻辑
- 参数：config: AppConfig
- 返回值：dict[str, dict[str, float | str]]（见函数语义）
- 逐行分析：
  - 行 580：def _load_market_snapshot(config: AppConfig) -> dict[str, dict[str, float | str]]: → 问题（ID 7）
  - 行 581：    if config.market_snapshot_json: → 问题（ID 7）
  - 行 582：        loaded = _load_market_snapshot_from_json_env(config.market_snapshot_json) → 问题（ID 7）
  - 行 583：        if loaded: → 问题（ID 7）
  - 行 584：            return loaded → 问题（ID 7）
  - 行 585：        logger.warning("market snapshot json provided but invalid or empty, fallback to runtime source") → 问题（ID 7）
  - 行 586：    if config.market_data_mode == "live": → 问题（ID 7）
  - 行 587：        live = _load_market_snapshot_from_yfinance(config.market_symbols) → 问题（ID 7）
  - 行 588：        if live: → 问题（ID 7）
  - 行 589：            return live → 问题（ID 7）
  - 行 590：        logger.warning("live market data unavailable, fallback to default snapshot") → 问题（ID 7）
  - 行 591：    return _default_market_snapshot() → 问题（ID 7）
- 调用的外部函数：_default_market_snapshot; _load_market_snapshot_from_json_env; logger.warning; _load_market_snapshot_from_yfinance
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 7：市场快照默认样例占比过高（高）

#### 函数：_load_market_snapshot_from_json_env（行 594-608）
- 功能：执行对应业务逻辑
- 参数：raw_json: str
- 返回值：dict[str, dict[str, float | str]]（见函数语义）
- 逐行分析：
  - 行 594：def _load_market_snapshot_from_json_env(raw_json: str) -> dict[str, dict[str, float | str]]: → 问题（ID 7）
  - 行 595：    try: → 问题（ID 7）
  - 行 596：        payload = json.loads(raw_json) → 问题（ID 7）
  - 行 597：    except json.JSONDecodeError as exc: → 问题（ID 7）
  - 行 598：        logger.warning("market snapshot json parse failed: %s", str(exc)) → 问题（ID 7）
  - 行 599：        return {} → 问题（ID 7）
  - 行 600：    if not isinstance(payload, dict): → 问题（ID 7）
  - 行 601：        logger.warning("market snapshot json payload is not object") → 问题（ID 7）
  - 行 602：        return {} → 问题（ID 7）
  - 行 603：    normalized: dict[str, dict[str, float | str]] = {} → 问题（ID 7）
  - 行 604：    for symbol, row in payload.items(): → 问题（ID 7）
  - 行 605：        if not isinstance(row, dict): → 问题（ID 7）
  - 行 606：            continue → 问题（ID 7）
  - 行 607：        normalized[str(symbol).upper()] = dict(row) → 问题（ID 7）
  - 行 608：    return normalized → 问题（ID 7）
- 调用的外部函数：payload.items; json.loads; isinstance; logger.warning; dict; upper; str
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 7：市场快照默认样例占比过高（高）

#### 函数：_load_market_snapshot_from_yfinance（行 611-648）
- 功能：执行对应业务逻辑
- 参数：raw_symbols: str
- 返回值：dict[str, dict[str, float | str]]（见函数语义）
- 逐行分析：
  - 行 611：def _load_market_snapshot_from_yfinance(raw_symbols: str) -> dict[str, dict[str, float | str]]: → 问题（ID 7）
  - 行 612：    symbols = [item.strip().upper() for item in raw_symbols.split(",") if item.strip()] → 问题（ID 7）
  - 行 613：    if not symbols: → 问题（ID 7）
  - 行 614：        return {} → 问题（ID 7）
  - 行 615：    try: → 问题（ID 7）
  - 行 616：        import yfinance as yf → 问题（ID 7）
  - 行 617：    except Exception as exc: → 问题（ID 7）
  - 行 618：        logger.warning("yfinance import failed: %s", str(exc)) → 问题（ID 7）
  - 行 619：        return {} → 问题（ID 7）
  - 行 620：    snapshot: dict[str, dict[str, float | str]] = {} → 问题（ID 7）
  - 行 621：    for symbol in symbols: → 问题（ID 7）
  - 行 622：        try: → 问题（ID 7）
  - 行 623：            history = yf.Ticker(symbol).history(period="3mo", interval="1d") → 问题（ID 7）
  - 行 624：            if history.empty or len(history) < 25: → 问题（ID 7）
  - 行 625：                continue → 问题（ID 7）
  - 行 626：            closes = history["Close"].dropna() → 问题（ID 7）
  - 行 627：            if len(closes) < 25: → 问题（ID 7）
  - 行 628：                continue → 问题（ID 7）
  - 行 629：            ref_price = float(closes.iloc[-1]) → 问题（ID 7）
  - 行 630：            momentum_20d = (ref_price - float(closes.iloc[-21])) / max(1e-6, float(closes.iloc[-21])) → 问题（ID 7）
  - 行 631：            returns = closes.pct_change().dropna() → 问题（ID 7）
  - 行 632：            volatility = float(returns.tail(20).std()) if len(returns) >= 20 else 0.2 → 问题（ID 7）
  - 行 633：            mean_5 = float(closes.tail(5).mean()) → 问题（ID 7）
  - 行 634：            std_20 = float(closes.tail(20).std()) if len(closes) >= 20 else 1.0 → 问题（ID 7）
  - 行 635：            z_score_5d = (ref_price - mean_5) / max(1e-6, std_20) → 问题（ID 7）
  - 行 636：            snapshot[symbol] = { → 问题（ID 7）
  - 行 637：                "momentum_20d": round(momentum_20d, 6), → 问题（ID 7）
  - 行 638：                "z_score_5d": round(z_score_5d, 6), → 问题（ID 7）
  - 行 639：                "relative_strength": round(max(0.0, momentum_20d), 6), → 问题（ID 7）
  - 行 640：                "volatility": round(max(0.01, volatility), 6), → 问题（ID 7）
  - 行 641：                "reference_price": round(ref_price, 6), → 问题（ID 7）
  - 行 642：                "liquidity_score": 0.8, → 问题（ID 7）
  - 行 643：                "sector": "unknown", → 问题（ID 7）
  - 行 644：            } → 问题（ID 7）
  - 行 645：        except Exception as exc: → 问题（ID 7）
  - 行 646：            logger.warning("yfinance load failed for %s: %s", symbol, str(exc)) → 问题（ID 7）
  - 行 647：            continue → 问题（ID 7）
  - 行 648：    return snapshot → 问题（ID 7）
- 调用的外部函数：upper; raw_symbols.split; item.strip; logger.warning; history; dropna; float; str; len; max; mean; round; yf.Ticker; closes.pct_change; std; closes.tail; returns.tail
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 7：市场快照默认样例占比过高（高）

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| 580-648 | 市场快照默认样例占比过高 | 高 | 7 |

### 自检统计
- 实际逐行审计行数：660
- 函数审计数：28
- 发现问题数：1

## 文件：lanes/high.py
- 总行数：414
- 函数/方法数：15

### 逐函数检查

#### 函数：__module__（行 1-398）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from dataclasses import dataclass → 无问题
  - 行 4：from datetime import datetime, timedelta, timezone → 无问题
  - 行 5：from typing import TYPE_CHECKING, Any → 无问题
  - 行 6：from uuid import uuid4 → 无问题
  - 行 7： → 无问题
  - 行 8：if TYPE_CHECKING: → 无问题
  - 行 9：    from ..config import AppConfig → 无问题
  - 行 10： → 无问题
  - 行 11： → 无问题
  - 行 12：@dataclass(frozen=True) → 无问题
  - 行 13：class HighLaneSettings: → 无问题
  - 行 14：    single_trade_risk_pct: float = 0.01 → 无问题
  - 行 15：    total_exposure_limit_pct: float = 0.30 → 无问题
  - 行 16：    stop_loss_min_pct: float = 0.05 → 无问题
  - 行 17：    stop_loss_max_pct: float = 0.08 → 无问题
  - 行 18：    max_drawdown_pct: float = 0.12 → 无问题
  - 行 19：    min_trade_units: int = 1 → 无问题
  - 行 20：    slippage_bps: float = 2.0 → 无问题
  - 行 21：    commission_per_share: float = 0.005 → 无问题
  - 行 22：    cooldown_hours: int = 24 → 无问题
  - 行 23：    holding_days: int = 2 → 无问题
  - 行 24：    risk_multiplier_min: float = 0.5 → 无问题
  - 行 25：    risk_multiplier_max: float = 1.5 → 无问题
  - 行 26：    take_profit_boost_max_pct: float = 0.2 → 无问题
  - 行 27： → 无问题
  - 行 28：    @classmethod → 无问题
  - 行 45： → 无问题
  - 行 46： → 无问题
  - 行 150： → 无问题
  - 行 151： → 无问题
  - 行 200： → 无问题
  - 行 201： → 无问题
  - 行 214： → 无问题
  - 行 215： → 无问题
  - 行 223： → 无问题
  - 行 224： → 无问题
  - 行 244： → 无问题
  - 行 245： → 无问题
  - 行 252： → 无问题
  - 行 253： → 无问题
  - 行 281： → 问题（ID 15）
  - 行 282： → 问题（ID 15）
  - 行 289： → 无问题
  - 行 290： → 无问题
  - 行 297： → 无问题
  - 行 298： → 无问题
  - 行 308： → 无问题
  - 行 309： → 无问题
  - 行 334： → 无问题
  - 行 335： → 无问题
  - 行 388： → 无问题
  - 行 389： → 无问题
  - 行 397： → 无问题
  - 行 398： → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：HighLaneSettings.from_app_config（行 29-44）
- 功能：执行对应业务逻辑
- 参数：cls: Any, config: AppConfig
- 返回值：'HighLaneSettings'（见函数语义）
- 逐行分析：
  - 行 29：    def from_app_config(cls, config: AppConfig) -> "HighLaneSettings": → 无问题
  - 行 30：        return cls( → 无问题
  - 行 31：            single_trade_risk_pct=config.risk_single_trade_pct, → 无问题
  - 行 32：            total_exposure_limit_pct=config.risk_total_exposure_pct, → 无问题
  - 行 33：            stop_loss_min_pct=config.risk_stop_loss_min_pct, → 无问题
  - 行 34：            stop_loss_max_pct=config.risk_stop_loss_max_pct, → 无问题
  - 行 35：            max_drawdown_pct=config.risk_max_drawdown_pct, → 无问题
  - 行 36：            min_trade_units=max(1, config.risk_min_trade_units), → 无问题
  - 行 37：            slippage_bps=max(0.0, config.risk_slippage_bps), → 无问题
  - 行 38：            commission_per_share=max(0.0, config.risk_commission_per_share), → 无问题
  - 行 39：            cooldown_hours=config.cooldown_hours, → 无问题
  - 行 40：            holding_days=config.holding_days, → 无问题
  - 行 41：            risk_multiplier_min=config.high_risk_multiplier_min, → 无问题
  - 行 42：            risk_multiplier_max=config.high_risk_multiplier_max, → 无问题
  - 行 43：            take_profit_boost_max_pct=config.high_take_profit_boost_max_pct, → 无问题
  - 行 44：        ) → 无问题
- 调用的外部函数：cls; max
- 被谁调用：lanes/__init__.py:run_lane_cycle:166
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：evaluate_event（行 47-149）
- 功能：执行对应业务逻辑
- 参数：event: dict[str, str], settings: HighLaneSettings | None, strategy_adjustments: dict[str, float] | None
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 47：def evaluate_event( → 无问题
  - 行 48：    event: dict[str, str], → 无问题
  - 行 49：    settings: HighLaneSettings | None = None, → 无问题
  - 行 50：    strategy_adjustments: dict[str, float] | None = None, → 无问题
  - 行 51：) -> dict[str, Any]: → 无问题
  - 行 52：    active_settings = settings or HighLaneSettings() → 无问题
  - 行 53：    settings_error = _validate_settings_bounds(active_settings) → 无问题
  - 行 54：    if settings_error is not None: → 无问题
  - 行 55：        return _rejected(symbol=event.get("symbol", ""), reasons=[settings_error]) → 无问题
  - 行 56：    now = datetime.now(tz=timezone.utc) → 无问题
  - 行 57：    symbol = event.get("symbol", "") → 无问题
  - 行 58：    source_reason = _check_source(event) → 无问题
  - 行 59：    if source_reason: → 无问题
  - 行 60：        return _rejected(symbol=symbol, reasons=[source_reason]) → 无问题
  - 行 61：    parse_errors, payload = _parse_event(event) → 无问题
  - 行 62：    if parse_errors: → 无问题
  - 行 63：        return _rejected(symbol=symbol, reasons=parse_errors) → 无问题
  - 行 64： → 无问题
  - 行 65：    structure_errors = _check_price_structure(payload, settings=active_settings) → 无问题
  - 行 66：    if structure_errors: → 无问题
  - 行 67：        return _rejected(symbol=symbol, reasons=structure_errors) → 无问题
  - 行 68： → 无问题
  - 行 69：    cooldown_reason = _check_cooldown(payload["last_exit_at"], now, active_settings.cooldown_hours) → 无问题
  - 行 70：    if cooldown_reason: → 无问题
  - 行 71：        return _rejected(symbol=symbol, reasons=[cooldown_reason]) → 无问题
  - 行 72： → 无问题
  - 行 73：    holding_reason = _check_holding(payload["position_opened_at"], now, active_settings.holding_days) → 无问题
  - 行 74：    if holding_reason: → 无问题
  - 行 75：        return _rejected(symbol=symbol, reasons=[holding_reason]) → 无问题
  - 行 76：    drawdown_reason = _check_max_drawdown(payload, active_settings.max_drawdown_pct) → 无问题
  - 行 77：    if drawdown_reason: → 无问题
  - 行 78：        return _rejected(symbol=symbol, reasons=[drawdown_reason]) → 无问题
  - 行 79： → 无问题
  - 行 80：    risk_per_share = abs(payload["entry_price"] - payload["stop_loss_price"]) → 无问题
  - 行 81：    if risk_per_share <= 0: → 无问题
  - 行 82：        return _rejected(symbol=symbol, reasons=["STOP_LOSS_INVALID"]) → 无问题
  - 行 83： → 无问题
  - 行 84：    risk_multiplier = 1.0 → 无问题
  - 行 85：    take_profit_boost_pct = 0.0 → 无问题
  - 行 86：    if strategy_adjustments: → 无问题
  - 行 87：        raw_risk_multiplier = strategy_adjustments.get("risk_multiplier", 1.0) → 无问题
  - 行 88：        risk_multiplier = max(active_settings.risk_multiplier_min, min(active_settings.risk_multiplier_max, raw_risk_multiplier)) → 无问题
  - 行 89：        raw_take_profit_boost = strategy_adjustments.get("take_profit_boost_pct", 0.0) → 无问题
  - 行 90：        take_profit_boost_pct = max( → 无问题
  - 行 91：            0.0, → 无问题
  - 行 92：            min(active_settings.take_profit_boost_max_pct, raw_take_profit_boost), → 无问题
  - 行 93：        ) → 无问题
  - 行 94：    risk_budget = payload["equity"] * active_settings.single_trade_risk_pct * risk_multiplier → 无问题
  - 行 95：    shares_by_risk = int(risk_budget // risk_per_share) → 问题（ID 2）
  - 行 96：    min_trade_units = max(1, active_settings.min_trade_units) → 问题（ID 2）
  - 行 97：    min_trade_units_applied = False → 问题（ID 2）
  - 行 98：    if shares_by_risk < min_trade_units: → 问题（ID 2）
  - 行 99：        coverage_ratio = risk_budget / max(risk_per_share, 1e-6) → 问题（ID 2）
  - 行 100：        if coverage_ratio >= 0.5: → 问题（ID 2）
  - 行 101：            shares_by_risk = min_trade_units → 问题（ID 2）
  - 行 102：            min_trade_units_applied = True → 问题（ID 2）
  - 行 103：    if shares_by_risk < 1: → 问题（ID 2）
  - 行 104：        return _rejected(symbol=symbol, reasons=["RISK_BUDGET_EXCEEDED"]) → 问题（ID 2）
  - 行 105： → 无问题
  - 行 106：    target_weight = max(0.0, min(1.0, payload.get("target_weight", 1.0))) → 无问题
  - 行 107：    scoped_exposure_limit = payload["equity"] * active_settings.total_exposure_limit_pct * max(1e-6, target_weight) → 无问题
  - 行 108：    available_exposure = scoped_exposure_limit - payload["current_symbol_exposure"] → 无问题
  - 行 109：    if available_exposure <= 0: → 无问题
  - 行 110：        return _rejected(symbol=symbol, reasons=["TOTAL_EXPOSURE_LIMIT"]) → 无问题
  - 行 111： → 无问题
  - 行 112：    shares_by_exposure = int(available_exposure // payload["entry_price"]) → 无问题
  - 行 113：    if shares_by_exposure < 1: → 无问题
  - 行 114：        return _rejected(symbol=symbol, reasons=["TOTAL_EXPOSURE_LIMIT"]) → 无问题
  - 行 115： → 无问题
  - 行 116：    quantity = min(shares_by_risk, shares_by_exposure) → 无问题
  - 行 117：    if quantity < min_trade_units: → 无问题
  - 行 118：        return _rejected(symbol=symbol, reasons=["INVALID_QUANTITY"]) → 无问题
  - 行 119： → 无问题
  - 行 120：    estimated_cost = _estimate_transaction_cost( → 问题（ID 4）
  - 行 121：        entry_price=payload["entry_price"], → 问题（ID 4）
  - 行 122：        quantity=quantity, → 问题（ID 4）
  - 行 123：        slippage_bps=active_settings.slippage_bps, → 问题（ID 4）
  - 行 124：        commission_per_share=active_settings.commission_per_share, → 问题（ID 4）
  - 行 125：    ) → 问题（ID 4）
  - 行 126：    bracket_order = _build_bracket_order( → 无问题
  - 行 127：        payload=payload, → 无问题
  - 行 128：        quantity=quantity, → 无问题
  - 行 129：        now=now, → 无问题
  - 行 130：        take_profit_boost_pct=take_profit_boost_pct, → 无问题
  - 行 131：        holding_days=max(1, active_settings.holding_days), → 无问题
  - 行 132：    ) → 无问题
  - 行 133：    return { → 无问题
  - 行 134：        "lane": "high", → 无问题
  - 行 135：        "status": "accepted", → 无问题
  - 行 136：        "symbol": symbol, → 无问题
  - 行 137：        "quantity": quantity, → 无问题
  - 行 138：        "risk_budget": round(risk_budget, 4), → 无问题
  - 行 139：        "risk_per_share": round(risk_per_share, 4), → 无问题
  - 行 140：        "current_exposure_unit": str(payload.get("current_exposure_unit", "notional")), → 无问题
  - 行 141：        "target_weight": round(target_weight, 6), → 无问题
  - 行 142：        "scoped_exposure_limit": round(scoped_exposure_limit, 4), → 无问题
  - 行 143：        "applied_risk_multiplier": round(risk_multiplier, 4), → 无问题
  - 行 144：        "applied_take_profit_boost_pct": round(take_profit_boost_pct, 4), → 无问题
  - 行 145：        "min_trade_units_applied": min_trade_units_applied, → 无问题
  - 行 146：        "estimated_transaction_cost": estimated_cost, → 无问题
  - 行 147：        "reject_reasons": [], → 无问题
  - 行 148：        "bracket_order": bracket_order, → 无问题
  - 行 149：    } → 无问题
- 调用的外部函数：_validate_settings_bounds; datetime.now; event.get; _check_source; _parse_event; _check_price_structure; _check_cooldown; _check_holding; _check_max_drawdown; abs; int; max; min; _estimate_transaction_cost; _build_bracket_order; HighLaneSettings; _rejected; strategy_adjustments.get; round; str; payload.get
- 被谁调用：lanes/__init__.py:run_lane_cycle:182; phase0_validation_report.py:_hard_rule_checks:32; phase0_validation_report.py:_hard_rule_checks:35; phase0_validation_report.py:_hard_rule_checks:38; phase0_validation_report.py:_order_checks:59; replay.py:_run_single:56; tests/test_discipline_and_ibkr_adapter.py:DisciplineAndIbkrAdapterTests.test_ibkr_mapping_uses_stp_and_transmit_chain:35; tests/test_high_lane.py:HighLaneRuleEngineTests.test_accepts_and_builds_bracket_order:30; tests/test_high_lane.py:HighLaneRuleEngineTests.test_enforces_single_trade_risk_1pct:50; tests/test_high_lane.py:HighLaneRuleEngineTests.test_rejects_when_risk_budget_cannot_buy_one_share:57; tests/test_high_lane.py:HighLaneRuleEngineTests.test_rejects_with_cooldown_reason:64; tests/test_high_lane.py:HighLaneRuleEngineTests.test_rejects_when_holding_period_exceeded:71; tests/test_high_lane.py:HighLaneRuleEngineTests.test_rejects_when_exposure_limit_prevents_integer_shares:80; tests/test_high_lane.py:HighLaneRuleEngineTests.test_rejects_when_stop_loss_equals_entry:88; tests/test_high_lane.py:HighLaneRuleEngineTests.test_rejects_when_source_lane_is_not_ultra:95; tests/test_high_lane.py:HighLaneRuleEngineTests.test_rejects_when_event_kind_is_invalid:102; tests/test_high_lane.py:HighLaneRuleEngineTests.test_generates_unique_client_order_id:107; tests/test_high_lane.py:HighLaneRuleEngineTests.test_generates_unique_client_order_id:108; tests/test_high_lane.py:HighLaneRuleEngineTests.test_supports_adjustable_risk_settings:119; tests/test_high_lane.py:HighLaneRuleEngineTests.test_rejects_when_settings_boundary_invalid:124; tests/test_high_lane.py:HighLaneRuleEngineTests.test_handles_large_numeric_inputs_stably:135; tests/test_high_lane.py:HighLaneRuleEngineTests.test_applies_strategy_adjustments_with_bounds:141; tests/test_high_lane.py:HighLaneRuleEngineTests.test_respects_configured_holding_days_in_max_hold_until:153
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 2：最小交易单位兜底过窄（高）; ID 4：滑点手续费链路覆盖不足（高）

#### 函数：_parse_event（行 152-199）
- 功能：执行对应业务逻辑
- 参数：event: dict[str, str]
- 返回值：tuple[list[str], dict[str, Any]]（见函数语义）
- 逐行分析：
  - 行 152：def _parse_event(event: dict[str, str]) -> tuple[list[str], dict[str, Any]]: → 无问题
  - 行 153：    errors: list[str] = [] → 无问题
  - 行 154：    payload: dict[str, Any] = {} → 无问题
  - 行 155： → 无问题
  - 行 156：    symbol = event.get("symbol", "").strip().upper() → 无问题
  - 行 157：    if not symbol: → 无问题
  - 行 158：        errors.append("MISSING_SYMBOL") → 无问题
  - 行 159：    payload["symbol"] = symbol → 无问题
  - 行 160： → 无问题
  - 行 161：    side = event.get("side", "buy").strip().lower() → 无问题
  - 行 162：    if side not in {"buy", "sell"}: → 无问题
  - 行 163：        errors.append("INVALID_SIDE") → 无问题
  - 行 164：    payload["side"] = side → 无问题
  - 行 165： → 无问题
  - 行 166：    for field in ["entry_price", "stop_loss_price", "take_profit_price", "equity", "current_exposure"]: → 无问题
  - 行 167：        raw = event.get(field) → 无问题
  - 行 168：        if raw is None: → 无问题
  - 行 169：            errors.append(f"MISSING_{field.upper()}") → 无问题
  - 行 170：            continue → 无问题
  - 行 171：        try: → 无问题
  - 行 172：            value = float(raw) → 无问题
  - 行 173：        except ValueError: → 无问题
  - 行 174：            errors.append(f"INVALID_{field.upper()}") → 无问题
  - 行 175：            continue → 无问题
  - 行 176：        if value <= 0 and field != "current_exposure": → 无问题
  - 行 177：            errors.append(f"INVALID_{field.upper()}") → 无问题
  - 行 178：            continue → 无问题
  - 行 179：        if value < 0 and field == "current_exposure": → 无问题
  - 行 180：            errors.append(f"INVALID_{field.upper()}") → 无问题
  - 行 181：            continue → 无问题
  - 行 182：        payload[field] = value → 无问题
  - 行 183：    current_exposure_value = _parse_optional_float(event.get("current_exposure"), default=0.0) → 问题（ID 3）
  - 行 184：    current_exposure_unit = str(event.get("current_exposure_unit", "notional")) → 问题（ID 3）
  - 行 185：    payload["current_symbol_exposure"] = _normalize_exposure_to_notional( → 问题（ID 3）
  - 行 186：        raw_value=event.get("current_symbol_exposure"), → 问题（ID 3）
  - 行 187：        fallback_value=current_exposure_value, → 问题（ID 3）
  - 行 188：        unit=current_exposure_unit, → 问题（ID 3）
  - 行 189：        equity=float(payload.get("equity", 0.0)), → 问题（ID 3）
  - 行 190：    ) → 问题（ID 3）
  - 行 191：    payload["target_weight"] = _parse_optional_float(event.get("target_weight"), default=1.0) → 无问题
  - 行 192：    payload["current_exposure_unit"] = current_exposure_unit → 无问题
  - 行 193：    payload["equity_peak"] = _parse_optional_float(event.get("equity_peak"), default=float(payload.get("equity", 0.0))) → 无问题
  - 行 194： → 无问题
  - 行 195：    payload["last_exit_at"] = _parse_time(event.get("last_exit_at"), "INVALID_LAST_EXIT_AT", errors) → 无问题
  - 行 196：    payload["position_opened_at"] = _parse_time( → 无问题
  - 行 197：        event.get("position_opened_at"), "INVALID_POSITION_OPENED_AT", errors → 无问题
  - 行 198：    ) → 无问题
  - 行 199：    return errors, payload → 无问题
- 调用的外部函数：upper; lower; _parse_optional_float; str; _normalize_exposure_to_notional; _parse_time; errors.append; event.get; strip; float; payload.get; field.upper
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 3：current_exposure 单位归一化风险（高）

#### 函数：_parse_time（行 202-213）
- 功能：执行对应业务逻辑
- 参数：raw: str | None, error_code: str, errors: list[str]
- 返回值：datetime | None（见函数语义）
- 逐行分析：
  - 行 202：def _parse_time(raw: str | None, error_code: str, errors: list[str]) -> datetime | None: → 无问题
  - 行 203：    if raw is None or not raw.strip(): → 无问题
  - 行 204：        return None → 无问题
  - 行 205：    text = raw.strip().replace("Z", "+00:00") → 无问题
  - 行 206：    try: → 无问题
  - 行 207：        parsed = datetime.fromisoformat(text) → 无问题
  - 行 208：    except ValueError: → 无问题
  - 行 209：        errors.append(error_code) → 无问题
  - 行 210：        return None → 无问题
  - 行 211：    if parsed.tzinfo is None: → 无问题
  - 行 212：        return parsed.replace(tzinfo=timezone.utc) → 无问题
  - 行 213：    return parsed.astimezone(timezone.utc) → 无问题
- 调用的外部函数：replace; parsed.astimezone; datetime.fromisoformat; parsed.replace; raw.strip; errors.append
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_parse_optional_float（行 216-222）
- 功能：执行对应业务逻辑
- 参数：raw: object, default: float
- 返回值：float（见函数语义）
- 逐行分析：
  - 行 216：def _parse_optional_float(raw: object, default: float) -> float: → 无问题
  - 行 217：    if raw is None: → 无问题
  - 行 218：        return default → 无问题
  - 行 219：    try: → 无问题
  - 行 220：        return float(raw) → 无问题
  - 行 221：    except (TypeError, ValueError): → 无问题
  - 行 222：        return default → 无问题
- 调用的外部函数：float
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_normalize_exposure_to_notional（行 225-243）
- 功能：执行对应业务逻辑
- 参数：raw_value: object, fallback_value: float, unit: str, equity: float
- 返回值：float（见函数语义）
- 逐行分析：
  - 行 225：def _normalize_exposure_to_notional( → 无问题
  - 行 226：    *, → 无问题
  - 行 227：    raw_value: object, → 无问题
  - 行 228：    fallback_value: float, → 无问题
  - 行 229：    unit: str, → 无问题
  - 行 230：    equity: float, → 无问题
  - 行 231：) -> float: → 无问题
  - 行 232：    value = _parse_optional_float(raw_value, fallback_value) → 无问题
  - 行 233：    normalized_unit = unit.strip().lower() → 无问题
  - 行 234：    if normalized_unit in {"ratio", "weight", "pct", "percent"}: → 无问题
  - 行 235：        if equity <= 0: → 无问题
  - 行 236：            return 0.0 → 无问题
  - 行 237：        if normalized_unit in {"pct", "percent"}: → 无问题
  - 行 238：            ratio = max(0.0, value) / 100.0 → 无问题
  - 行 239：        else: → 无问题
  - 行 240：            ratio = max(0.0, value) → 无问题
  - 行 241：        ratio = min(1.0, ratio) → 无问题
  - 行 242：        return equity * ratio → 无问题
  - 行 243：    return max(0.0, value) → 无问题
- 调用的外部函数：_parse_optional_float; lower; max; min; unit.strip
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_check_source（行 246-251）
- 功能：执行对应业务逻辑
- 参数：event: dict[str, str]
- 返回值：str | None（见函数语义）
- 逐行分析：
  - 行 246：def _check_source(event: dict[str, str]) -> str | None: → 无问题
  - 行 247：    if event.get("lane", "").strip().lower() != "ultra": → 无问题
  - 行 248：        return "SOURCE_LANE_INVALID" → 无问题
  - 行 249：    if event.get("kind", "").strip().lower() != "signal": → 无问题
  - 行 250：        return "EVENT_KIND_INVALID" → 无问题
  - 行 251：    return None → 无问题
- 调用的外部函数：lower; strip; event.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_check_price_structure（行 254-280）
- 功能：执行对应业务逻辑
- 参数：payload: dict[str, Any], settings: HighLaneSettings
- 返回值：list[str]（见函数语义）
- 逐行分析：
  - 行 254：def _check_price_structure(payload: dict[str, Any], settings: HighLaneSettings) -> list[str]: → 无问题
  - 行 255：    side = payload["side"] → 无问题
  - 行 256：    entry = payload["entry_price"] → 无问题
  - 行 257：    stop = payload["stop_loss_price"] → 无问题
  - 行 258：    take_profit = payload["take_profit_price"] → 无问题
  - 行 259：    errors: list[str] = [] → 无问题
  - 行 260：    if side == "buy": → 无问题
  - 行 261：        if stop >= entry: → 无问题
  - 行 262：            errors.append("STOP_LOSS_DIRECTION_INVALID") → 无问题
  - 行 263：        if take_profit <= entry: → 无问题
  - 行 264：            errors.append("TAKE_PROFIT_DIRECTION_INVALID") → 无问题
  - 行 265：        if stop < entry: → 无问题
  - 行 266：            stop_ratio = (entry - stop) / entry → 无问题
  - 行 267：            epsilon = 1e-9 → 无问题
  - 行 268：            if stop_ratio + epsilon < settings.stop_loss_min_pct or stop_ratio - epsilon > settings.stop_loss_max_pct: → 无问题
  - 行 269：                errors.append("STOP_LOSS_RANGE_INVALID") → 无问题
  - 行 270：    else: → 无问题
  - 行 271：        if stop <= entry: → 无问题
  - 行 272：            errors.append("STOP_LOSS_DIRECTION_INVALID") → 无问题
  - 行 273：        if take_profit >= entry: → 无问题
  - 行 274：            errors.append("TAKE_PROFIT_DIRECTION_INVALID") → 问题（ID 15）
  - 行 275：        if stop > entry: → 问题（ID 15）
  - 行 276：            stop_ratio = (stop - entry) / entry → 问题（ID 15）
  - 行 277：            epsilon = 1e-9 → 问题（ID 15）
  - 行 278：            if stop_ratio + epsilon < settings.stop_loss_min_pct or stop_ratio - epsilon > settings.stop_loss_max_pct: → 问题（ID 15）
  - 行 279：                errors.append("STOP_LOSS_RANGE_INVALID") → 问题（ID 15）
  - 行 280：    return errors → 问题（ID 15）
- 调用的外部函数：errors.append
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 15：最大回撤闸门覆盖风险（高）

#### 函数：_check_cooldown（行 283-288）
- 功能：执行对应业务逻辑
- 参数：last_exit_at: datetime | None, now: datetime, cooldown_hours: int
- 返回值：str | None（见函数语义）
- 逐行分析：
  - 行 283：def _check_cooldown(last_exit_at: datetime | None, now: datetime, cooldown_hours: int) -> str | None: → 无问题
  - 行 284：    if last_exit_at is None: → 无问题
  - 行 285：        return None → 无问题
  - 行 286：    if now - last_exit_at < timedelta(hours=cooldown_hours): → 无问题
  - 行 287：        return "COOLDOWN_24H_ACTIVE" → 无问题
  - 行 288：    return None → 无问题
- 调用的外部函数：timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_check_holding（行 291-296）
- 功能：执行对应业务逻辑
- 参数：position_opened_at: datetime | None, now: datetime, holding_days: int
- 返回值：str | None（见函数语义）
- 逐行分析：
  - 行 291：def _check_holding(position_opened_at: datetime | None, now: datetime, holding_days: int) -> str | None: → 无问题
  - 行 292：    if position_opened_at is None: → 无问题
  - 行 293：        return None → 无问题
  - 行 294：    if now - position_opened_at > timedelta(days=holding_days): → 无问题
  - 行 295：        return "HOLDING_PERIOD_EXCEEDED" → 无问题
  - 行 296：    return None → 无问题
- 调用的外部函数：timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_check_max_drawdown（行 299-307）
- 功能：执行对应业务逻辑
- 参数：payload: dict[str, Any], max_drawdown_pct: float
- 返回值：str | None（见函数语义）
- 逐行分析：
  - 行 299：def _check_max_drawdown(payload: dict[str, Any], max_drawdown_pct: float) -> str | None: → 无问题
  - 行 300：    equity = float(payload.get("equity", 0.0)) → 无问题
  - 行 301：    equity_peak = max(equity, float(payload.get("equity_peak", equity))) → 无问题
  - 行 302：    if equity_peak <= 0: → 无问题
  - 行 303：        return None → 无问题
  - 行 304：    drawdown = (equity_peak - equity) / equity_peak → 无问题
  - 行 305：    if drawdown > max_drawdown_pct: → 无问题
  - 行 306：        return "MAX_DRAWDOWN_LIMIT" → 无问题
  - 行 307：    return None → 无问题
- 调用的外部函数：float; max; payload.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_validate_settings_bounds（行 310-333）
- 功能：执行对应业务逻辑
- 参数：settings: HighLaneSettings
- 返回值：str | None（见函数语义）
- 逐行分析：
  - 行 310：def _validate_settings_bounds(settings: HighLaneSettings) -> str | None: → 无问题
  - 行 311：    if settings.single_trade_risk_pct <= 0 or settings.total_exposure_limit_pct <= 0: → 无问题
  - 行 312：        return "RISK_SETTINGS_INVALID" → 无问题
  - 行 313：    if settings.total_exposure_limit_pct > 1: → 无问题
  - 行 314：        return "RISK_SETTINGS_INVALID" → 无问题
  - 行 315：    if settings.stop_loss_min_pct <= 0 or settings.stop_loss_max_pct <= 0: → 无问题
  - 行 316：        return "STOP_LOSS_SETTINGS_INVALID" → 无问题
  - 行 317：    if settings.stop_loss_min_pct >= settings.stop_loss_max_pct: → 无问题
  - 行 318：        return "STOP_LOSS_SETTINGS_INVALID" → 无问题
  - 行 319：    if settings.risk_multiplier_min <= 0 or settings.risk_multiplier_max <= 0: → 无问题
  - 行 320：        return "RISK_SETTINGS_INVALID" → 无问题
  - 行 321：    if settings.risk_multiplier_min > settings.risk_multiplier_max: → 无问题
  - 行 322：        return "RISK_SETTINGS_INVALID" → 无问题
  - 行 323：    if settings.take_profit_boost_max_pct < 0: → 无问题
  - 行 324：        return "STOP_LOSS_SETTINGS_INVALID" → 无问题
  - 行 325：    if settings.max_drawdown_pct <= 0 or settings.max_drawdown_pct >= 1: → 无问题
  - 行 326：        return "RISK_SETTINGS_INVALID" → 无问题
  - 行 327：    if settings.min_trade_units <= 0: → 无问题
  - 行 328：        return "RISK_SETTINGS_INVALID" → 无问题
  - 行 329：    if settings.slippage_bps < 0 or settings.commission_per_share < 0: → 无问题
  - 行 330：        return "RISK_SETTINGS_INVALID" → 无问题
  - 行 331：    if settings.cooldown_hours < 0 or settings.holding_days < 0: → 无问题
  - 行 332：        return "TEMPORAL_SETTINGS_INVALID" → 无问题
  - 行 333：    return None → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_build_bracket_order（行 336-387）
- 功能：执行对应业务逻辑
- 参数：payload: dict[str, Any], quantity: int, now: datetime, take_profit_boost_pct: float, holding_days: int
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 336：def _build_bracket_order( → 无问题
  - 行 337：    payload: dict[str, Any], → 无问题
  - 行 338：    quantity: int, → 无问题
  - 行 339：    now: datetime, → 无问题
  - 行 340：    take_profit_boost_pct: float, → 无问题
  - 行 341：    holding_days: int, → 无问题
  - 行 342：) -> dict[str, Any]: → 无问题
  - 行 343：    side = payload["side"] → 无问题
  - 行 344：    if side == "buy": → 无问题
  - 行 345：        parent_action = "BUY" → 无问题
  - 行 346：        exit_action = "SELL" → 无问题
  - 行 347：    else: → 无问题
  - 行 348：        parent_action = "SELL" → 无问题
  - 行 349：        exit_action = "BUY" → 无问题
  - 行 350：    take_profit_price = payload["take_profit_price"] → 无问题
  - 行 351：    if take_profit_boost_pct > 0: → 无问题
  - 行 352：        if side == "buy": → 无问题
  - 行 353：            take_profit_price = take_profit_price * (1 + take_profit_boost_pct) → 无问题
  - 行 354：        else: → 无问题
  - 行 355：            take_profit_price = take_profit_price * (1 - take_profit_boost_pct) → 无问题
  - 行 356：    hold_until = now + timedelta(days=max(1, holding_days)) → 无问题
  - 行 357：    order_id_prefix = f'{payload["symbol"]}-{now.strftime("%Y%m%d%H%M%S%f")}-{uuid4().hex[:8]}' → 无问题
  - 行 358：    return { → 无问题
  - 行 359：        "parent": { → 无问题
  - 行 360：            "client_order_id": f"{order_id_prefix}-P", → 无问题
  - 行 361：            "symbol": payload["symbol"], → 无问题
  - 行 362：            "action": parent_action, → 无问题
  - 行 363：            "order_type": "LIMIT", → 无问题
  - 行 364：            "quantity": quantity, → 无问题
  - 行 365：            "limit_price": payload["entry_price"], → 无问题
  - 行 366：            "time_in_force": "DAY", → 无问题
  - 行 367：        }, → 无问题
  - 行 368：        "take_profit": { → 无问题
  - 行 369：            "client_order_id": f"{order_id_prefix}-TP", → 无问题
  - 行 370：            "symbol": payload["symbol"], → 无问题
  - 行 371：            "action": exit_action, → 无问题
  - 行 372：            "order_type": "LIMIT", → 无问题
  - 行 373：            "quantity": quantity, → 无问题
  - 行 374：            "limit_price": round(take_profit_price, 6), → 无问题
  - 行 375：            "time_in_force": "GTC", → 无问题
  - 行 376：        }, → 无问题
  - 行 377：        "stop_loss": { → 无问题
  - 行 378：            "client_order_id": f"{order_id_prefix}-SL", → 无问题
  - 行 379：            "symbol": payload["symbol"], → 无问题
  - 行 380：            "action": exit_action, → 无问题
  - 行 381：            "order_type": "STOP", → 无问题
  - 行 382：            "quantity": quantity, → 无问题
  - 行 383：            "stop_price": payload["stop_loss_price"], → 无问题
  - 行 384：            "time_in_force": "GTC", → 无问题
  - 行 385：        }, → 无问题
  - 行 386：        "max_hold_until": hold_until.isoformat(), → 无问题
  - 行 387：    } → 无问题
- 调用的外部函数：timedelta; hold_until.isoformat; now.strftime; round; max; uuid4
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_rejected（行 390-396）
- 功能：执行对应业务逻辑
- 参数：symbol: str, reasons: list[str]
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 390：def _rejected(symbol: str, reasons: list[str]) -> dict[str, Any]: → 无问题
  - 行 391：    return { → 无问题
  - 行 392：        "lane": "high", → 无问题
  - 行 393：        "status": "rejected", → 无问题
  - 行 394：        "symbol": symbol, → 无问题
  - 行 395：        "reject_reasons": reasons, → 无问题
  - 行 396：    } → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_estimate_transaction_cost（行 399-414）
- 功能：执行对应业务逻辑
- 参数：entry_price: float, quantity: int, slippage_bps: float, commission_per_share: float
- 返回值：dict[str, float]（见函数语义）
- 逐行分析：
  - 行 399：def _estimate_transaction_cost( → 无问题
  - 行 400：    *, → 无问题
  - 行 401：    entry_price: float, → 无问题
  - 行 402：    quantity: int, → 无问题
  - 行 403：    slippage_bps: float, → 无问题
  - 行 404：    commission_per_share: float, → 无问题
  - 行 405：) -> dict[str, float]: → 无问题
  - 行 406：    notional = entry_price * quantity → 无问题
  - 行 407：    slippage_cost = notional * (slippage_bps / 10000) → 无问题
  - 行 408：    commission_cost = quantity * commission_per_share → 无问题
  - 行 409：    total = slippage_cost + commission_cost → 无问题
  - 行 410：    return { → 无问题
  - 行 411：        "slippage_cost": round(slippage_cost, 6), → 无问题
  - 行 412：        "commission_cost": round(commission_cost, 6), → 无问题
  - 行 413：        "total": round(total, 6), → 无问题
  - 行 414：    } → 无问题
- 调用的外部函数：round
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| 95-104 | 最小交易单位兜底过窄 | 高 | 2 |
| 183-190 | current_exposure 单位归一化风险 | 高 | 3 |
| 120-125 | 滑点手续费链路覆盖不足 | 高 | 4 |
| 274-282 | 最大回撤闸门覆盖风险 | 高 | 15 |

### 自检统计
- 实际逐行审计行数：414
- 函数审计数：15
- 发现问题数：4

## 文件：lanes/bus.py
- 总行数：88
- 函数/方法数：7

### 逐函数检查

#### 函数：__module__（行 1-83）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from collections import deque → 无问题
  - 行 4：from dataclasses import dataclass, field → 无问题
  - 行 5：from datetime import datetime, timezone → 无问题
  - 行 6：from hashlib import sha256 → 无问题
  - 行 7：import json → 无问题
  - 行 8：from typing import Any → 无问题
  - 行 9： → 无问题
  - 行 10： → 无问题
  - 行 11：@dataclass(frozen=True) → 无问题
  - 行 12：class LaneEvent: → 无问题
  - 行 13：    event_type: str → 无问题
  - 行 14：    source_lane: str → 无问题
  - 行 15：    payload: dict[str, Any] → 无问题
  - 行 16：    trace_id: str → 无问题
  - 行 17：    emitted_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()) → 无问题
  - 行 18： → 无问题
  - 行 19：    @classmethod → 无问题
  - 行 28： → 无问题
  - 行 29： → 无问题
  - 行 30：class InMemoryLaneBus: → 无问题
  - 行 37： → 无问题
  - 行 54： → 无问题
  - 行 57： → 问题（ID 6）
  - 行 67： → 无问题
  - 行 68： → 无问题
  - 行 82： → 无问题
  - 行 83： → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：LaneEvent.from_payload（行 20-27）
- 功能：执行对应业务逻辑
- 参数：cls: Any, event_type: str, source_lane: str, payload: dict[str, Any]
- 返回值：'LaneEvent'（见函数语义）
- 逐行分析：
  - 行 20：    def from_payload(cls, *, event_type: str, source_lane: str, payload: dict[str, Any]) -> "LaneEvent": → 无问题
  - 行 21：        trace_id = _stable_trace_id(event_type=event_type, source_lane=source_lane, payload=payload) → 无问题
  - 行 22：        return cls( → 无问题
  - 行 23：            event_type=event_type, → 无问题
  - 行 24：            source_lane=source_lane, → 无问题
  - 行 25：            payload=payload, → 无问题
  - 行 26：            trace_id=trace_id, → 无问题
  - 行 27：        ) → 无问题
- 调用的外部函数：_stable_trace_id; cls
- 被谁调用：lanes/__init__.py:run_lane_cycle:163; lanes/__init__.py:run_lane_cycle:197; low_subscriber.py:consume_high_decisions_and_publish_low_analysis:54; replay.py:_run_duplicate_event_dedup:88; tests/test_lane_bus.py:LaneBusTests.test_deduplicates_same_event:19; tests/test_lane_bus.py:LaneBusTests.test_eviction_allows_republish_after_capacity_rollover:39; tests/test_lane_bus.py:LaneBusTests.test_eviction_allows_republish_after_capacity_rollover:44; tests/test_lane_bus.py:LaneBusTests.test_eviction_allows_republish_after_capacity_rollover:49
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：InMemoryLaneBus.__init__（行 31-36）
- 功能：执行对应业务逻辑
- 参数：self: Any, dedup_capacity: int
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 31：    def __init__(self, dedup_capacity: int = 2048) -> None: → 无问题
  - 行 32：        self._dedup_capacity = max(1, dedup_capacity) → 无问题
  - 行 33：        self._seen_trace_ids: set[str] = set() → 无问题
  - 行 34：        self._seen_order = deque() → 无问题
  - 行 35：        self._queues: dict[str, list[LaneEvent]] = {} → 无问题
  - 行 36：        self._consumer_offsets: dict[str, dict[str, int]] = {} → 无问题
- 调用的外部函数：max; set; deque
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：InMemoryLaneBus.publish（行 38-53）
- 功能：执行对应业务逻辑
- 参数：self: Any, channel: str, event: LaneEvent
- 返回值：bool（见函数语义）
- 逐行分析：
  - 行 38：    def publish(self, channel: str, event: LaneEvent) -> bool: → 无问题
  - 行 39：        if event.trace_id in self._seen_trace_ids: → 无问题
  - 行 40：            return False → 无问题
  - 行 41：        self._seen_trace_ids.add(event.trace_id) → 无问题
  - 行 42：        self._seen_order.append(event.trace_id) → 无问题
  - 行 43：        if len(self._seen_order) > self._dedup_capacity: → 无问题
  - 行 44：            expired = self._seen_order.popleft() → 无问题
  - 行 45：            self._seen_trace_ids.discard(expired) → 无问题
  - 行 46：        queue = self._queues.setdefault(channel, []) → 无问题
  - 行 47：        queue.append(event) → 无问题
  - 行 48：        if len(queue) > self._dedup_capacity: → 无问题
  - 行 49：            queue.pop(0) → 无问题
  - 行 50：            channel_offsets = self._consumer_offsets.get(channel, {}) → 无问题
  - 行 51：            for consumer_id, offset in list(channel_offsets.items()): → 无问题
  - 行 52：                channel_offsets[consumer_id] = max(0, offset - 1) → 无问题
  - 行 53：        return True → 无问题
- 调用的外部函数：self._seen_trace_ids.add; self._seen_order.append; self._queues.setdefault; queue.append; len; self._seen_order.popleft; self._seen_trace_ids.discard; queue.pop; self._consumer_offsets.get; list; channel_offsets.items; max
- 被谁调用：lanes/__init__.py:run_lane_cycle:164; lanes/__init__.py:run_lane_cycle:198; low_subscriber.py:consume_high_decisions_and_publish_low_analysis:55; replay.py:_run_duplicate_event_dedup:89; replay.py:_run_duplicate_event_dedup:90; tests/test_lane_bus.py:LaneBusTests.test_deduplicates_same_event:20; tests/test_lane_bus.py:LaneBusTests.test_deduplicates_same_event:21; tests/test_lane_bus.py:LaneBusTests.test_eviction_allows_republish_after_capacity_rollover:54; tests/test_lane_bus.py:LaneBusTests.test_eviction_allows_republish_after_capacity_rollover:55; tests/test_lane_bus.py:LaneBusTests.test_eviction_allows_republish_after_capacity_rollover:56; tests/test_lane_bus.py:LaneBusTests.test_eviction_allows_republish_after_capacity_rollover:57
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：InMemoryLaneBus.consume（行 55-56）
- 功能：执行对应业务逻辑
- 参数：self: Any, channel: str
- 返回值：list[LaneEvent]（见函数语义）
- 逐行分析：
  - 行 55：    def consume(self, channel: str) -> list[LaneEvent]: → 问题（ID 6）
  - 行 56：        return self.consume_for(channel, "__default__") → 问题（ID 6）
- 调用的外部函数：self.consume_for
- 被谁调用：lanes/__init__.py:run_lane_cycle:165; lanes/__init__.py:run_lane_cycle:207; tests/test_lane_bus.py:LaneBusTests.test_deduplicates_same_event:24
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 6：consume 清空队列导致多消费者丢事件（中）

#### 函数：InMemoryLaneBus.consume_for（行 58-66）
- 功能：执行对应业务逻辑
- 参数：self: Any, channel: str, consumer_id: str
- 返回值：list[LaneEvent]（见函数语义）
- 逐行分析：
  - 行 58：    def consume_for(self, channel: str, consumer_id: str) -> list[LaneEvent]: → 问题（ID 6）
  - 行 59：        queue = self._queues.get(channel, []) → 问题（ID 6）
  - 行 60：        channel_offsets = self._consumer_offsets.setdefault(channel, {}) → 无问题
  - 行 61：        offset = channel_offsets.get(consumer_id, 0) → 无问题
  - 行 62：        if offset >= len(queue): → 无问题
  - 行 63：            return [] → 无问题
  - 行 64：        events = queue[offset:] → 无问题
  - 行 65：        channel_offsets[consumer_id] = len(queue) → 无问题
  - 行 66：        return events → 无问题
- 调用的外部函数：self._queues.get; self._consumer_offsets.setdefault; channel_offsets.get; len
- 被谁调用：low_subscriber.py:consume_high_decisions_and_publish_low_analysis:25
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 6：consume 清空队列导致多消费者丢事件（中）

#### 函数：_stable_trace_id（行 69-81）
- 功能：执行对应业务逻辑
- 参数：event_type: str, source_lane: str, payload: dict[str, Any]
- 返回值：str（见函数语义）
- 逐行分析：
  - 行 69：def _stable_trace_id(event_type: str, source_lane: str, payload: dict[str, Any]) -> str: → 无问题
  - 行 70：    raw = json.dumps( → 无问题
  - 行 71：        { → 无问题
  - 行 72：            "event_type": event_type, → 无问题
  - 行 73：            "source_lane": source_lane, → 无问题
  - 行 74：            "payload": payload, → 无问题
  - 行 75：        }, → 无问题
  - 行 76：        ensure_ascii=False, → 无问题
  - 行 77：        sort_keys=True, → 无问题
  - 行 78：        separators=(",", ":"), → 无问题
  - 行 79：        default=_json_default, → 无问题
  - 行 80：    ) → 无问题
  - 行 81：    return sha256(raw.encode("utf-8")).hexdigest()[:24] → 无问题
- 调用的外部函数：json.dumps; hexdigest; sha256; raw.encode
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_json_default（行 84-88）
- 功能：执行对应业务逻辑
- 参数：value: object
- 返回值：object（见函数语义）
- 逐行分析：
  - 行 84：def _json_default(value: object) -> object: → 无问题
  - 行 85：    isoformat = getattr(value, "isoformat", None) → 无问题
  - 行 86：    if callable(isoformat): → 无问题
  - 行 87：        return str(isoformat()) → 无问题
  - 行 88：    return str(value) → 无问题
- 调用的外部函数：getattr; callable; str; isoformat
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| 55-59 | consume 清空队列导致多消费者丢事件 | 中 | 6 |

### 自检统计
- 实际逐行审计行数：88
- 函数审计数：7
- 发现问题数：1

## 文件：lanes/ultra.py
- 总行数：31
- 函数/方法数：1

### 逐函数检查

#### 函数：__module__（行 1-5）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from datetime import datetime, timedelta, timezone → 无问题
  - 行 4： → 无问题
  - 行 5： → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：emit_event（行 6-31）
- 功能：执行对应业务逻辑
- 参数：symbol: str, overrides: dict[str, str] | None, market_row: dict[str, float | str] | None
- 返回值：dict[str, str]（见函数语义）
- 逐行分析：
  - 行 6：def emit_event( → 无问题
  - 行 7：    symbol: str, → 无问题
  - 行 8：    overrides: dict[str, str] | None = None, → 无问题
  - 行 9：    market_row: dict[str, float | str] | None = None, → 无问题
  - 行 10：) -> dict[str, str]: → 无问题
  - 行 11：    last_exit_at = (datetime.now(tz=timezone.utc) - timedelta(days=2)).isoformat() → 无问题
  - 行 12：    row = market_row or {} → 无问题
  - 行 13：    reference_price = max(1.0, float(row.get("reference_price", 100.0))) → 无问题
  - 行 14：    stop_ratio = max(0.01, min(0.2, float(row.get("stop_ratio", 0.05)))) → 无问题
  - 行 15：    take_profit_ratio = max(0.02, min(0.3, float(row.get("take_profit_ratio", 0.08)))) → 无问题
  - 行 16：    event = { → 无问题
  - 行 17：        "lane": "ultra", → 无问题
  - 行 18：        "symbol": symbol.upper(), → 无问题
  - 行 19：        "kind": "signal", → 无问题
  - 行 20：        "side": "buy", → 无问题
  - 行 21：        "entry_price": f"{reference_price:.4f}", → 无问题
  - 行 22：        "stop_loss_price": f"{(reference_price * (1 - stop_ratio)):.4f}", → 无问题
  - 行 23：        "take_profit_price": f"{(reference_price * (1 + take_profit_ratio)):.4f}", → 无问题
  - 行 24：        "equity": "100000", → 无问题
  - 行 25：        "current_exposure": "10000", → 无问题
  - 行 26：        "current_exposure_unit": "notional", → 无问题
  - 行 27：        "last_exit_at": last_exit_at, → 无问题
  - 行 28：    } → 无问题
  - 行 29：    if overrides: → 无问题
  - 行 30：        event.update(overrides) → 无问题
  - 行 31：    return event → 无问题
- 调用的外部函数：isoformat; max; float; min; symbol.upper; event.update; row.get; datetime.now; timedelta
- 被谁调用：lanes/__init__.py:run_lane_cycle_with_guard:299; lanes/__init__.py:_build_strategy_event:345
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：31
- 函数审计数：1
- 发现问题数：0

## 文件：low_subscriber.py
- 总行数：56
- 函数/方法数：2

### 逐函数检查

#### 函数：__module__（行 1-16）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from datetime import datetime, timezone → 无问题
  - 行 4： → 无问题
  - 行 5：from ..ai import LowAnalysis, analyze_low_lane → 无问题
  - 行 6：from .bus import InMemoryLaneBus, LaneEvent → 无问题
  - 行 7： → 无问题
  - 行 8： → 无问题
  - 行 9：LOW_ANALYSIS_CACHE: dict[str, LowAnalysis] = {} → 无问题
  - 行 10：LOW_SUBSCRIBER_ID = "low_subscriber" → 无问题
  - 行 11： → 无问题
  - 行 12： → 无问题
  - 行 15： → 无问题
  - 行 16： → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：get_cached_low_analysis（行 13-14）
- 功能：执行对应业务逻辑
- 参数：symbol: str
- 返回值：LowAnalysis | None（见函数语义）
- 逐行分析：
  - 行 13：def get_cached_low_analysis(symbol: str) -> LowAnalysis | None: → 无问题
  - 行 14：    return LOW_ANALYSIS_CACHE.get(symbol.upper()) → 无问题
- 调用的外部函数：LOW_ANALYSIS_CACHE.get; symbol.upper
- 被谁调用：lanes/__init__.py:run_lane_cycle:85
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：consume_high_decisions_and_publish_low_analysis（行 17-56）
- 功能：执行对应业务逻辑
- 参数：bus: InMemoryLaneBus, market_snapshot: dict[str, dict[str, float | str]], committee_models: list[str], committee_min_support: int
- 返回值：list[dict[str, object]]（见函数语义）
- 逐行分析：
  - 行 17：def consume_high_decisions_and_publish_low_analysis( → 无问题
  - 行 18：    *, → 无问题
  - 行 19：    bus: InMemoryLaneBus, → 无问题
  - 行 20：    market_snapshot: dict[str, dict[str, float | str]], → 无问题
  - 行 21：    committee_models: list[str], → 无问题
  - 行 22：    committee_min_support: int, → 无问题
  - 行 23：) -> list[dict[str, object]]: → 无问题
  - 行 24：    analyses: list[dict[str, object]] = [] → 无问题
  - 行 25：    decisions = bus.consume_for("high.decision", LOW_SUBSCRIBER_ID) → 无问题
  - 行 26：    for item in decisions: → 无问题
  - 行 27：        payload = item.payload → 无问题
  - 行 28：        symbol = str(payload.get("symbol", "")).upper() → 无问题
  - 行 29：        strategy_name = str(payload.get("strategy", "none")) → 无问题
  - 行 30：        strategy_confidence = float(payload.get("strategy_confidence", 0.0)) → 无问题
  - 行 31：        analysis = analyze_low_lane( → 无问题
  - 行 32：            market_snapshot=market_snapshot, → 无问题
  - 行 33：            committee_models=committee_models[:3], → 无问题
  - 行 34：            committee_min_support=committee_min_support, → 无问题
  - 行 35：            strategy_name=strategy_name, → 无问题
  - 行 36：            strategy_confidence=strategy_confidence, → 无问题
  - 行 37：        ) → 无问题
  - 行 38：        if symbol: → 无问题
  - 行 39：            LOW_ANALYSIS_CACHE[symbol] = analysis → 无问题
  - 行 40：        output = { → 无问题
  - 行 41：            "lane": "low", → 无问题
  - 行 42：            "symbol": symbol, → 无问题
  - 行 43：            "preferred_sector": analysis.preferred_sector, → 无问题
  - 行 44：            "strategy_fit": analysis.strategy_fit, → 无问题
  - 行 45：            "sector_allocation": analysis.sector_allocation, → 无问题
  - 行 46：            "committee_approved": analysis.committee_approved, → 无问题
  - 行 47：            "committee_votes": [ → 无问题
  - 行 48：                {"model": vote.model, "support": vote.support, "score": vote.score} → 无问题
  - 行 49：                for vote in analysis.committee_votes → 无问题
  - 行 50：            ], → 无问题
  - 行 51：            "analyzed_at": datetime.now(tz=timezone.utc).isoformat(), → 无问题
  - 行 52：        } → 无问题
  - 行 53：        analyses.append(output) → 无问题
  - 行 54：        low_event = LaneEvent.from_payload(event_type="analysis", source_lane="low", payload=output) → 无问题
  - 行 55：        bus.publish("low.analysis", low_event) → 无问题
  - 行 56：    return analyses → 无问题
- 调用的外部函数：bus.consume_for; upper; str; float; analyze_low_lane; analyses.append; LaneEvent.from_payload; bus.publish; payload.get; isoformat; datetime.now
- 被谁调用：lanes/__init__.py:run_lane_cycle:201
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：56
- 函数审计数：2
- 发现问题数：0

## 文件：ibkr_execution.py
- 总行数：311
- 函数/方法数：15

### 逐函数检查

#### 函数：__module__（行 1-311）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：import argparse → 无问题
  - 行 4：from dataclasses import dataclass → 无问题
  - 行 5：from datetime import datetime, timedelta, timezone → 无问题
  - 行 6：import json → 无问题
  - 行 7：from typing import Any, Callable, Protocol → 无问题
  - 行 8： → 无问题
  - 行 9：from .config import AppConfig, load_config → 无问题
  - 行 10：from .lanes import run_lane_cycle → 无问题
  - 行 11： → 无问题
  - 行 12： → 无问题
  - 行 13：class ExecutionClient(Protocol): → 无问题
  - 行 16： → 无问题
  - 行 19： → 无问题
  - 行 20： → 无问题
  - 行 21：@dataclass(frozen=True) → 无问题
  - 行 22：class ExecutionConfig: → 无问题
  - 行 23：    host: str = "127.0.0.1" → 无问题
  - 行 24：    port: int = 7497 → 无问题
  - 行 25：    client_id: int = 91 → 无问题
  - 行 26：    timeout_seconds: float = 3.0 → 无问题
  - 行 27：    exchange: str = "SMART" → 无问题
  - 行 28：    currency: str = "USD" → 无问题
  - 行 29：    account: str = "" → 无问题
  - 行 30：    session_guard_enabled: bool = False → 无问题
  - 行 31：    session_start_utc: str = "13:30" → 无问题
  - 行 32：    session_end_utc: str = "20:00" → 无问题
  - 行 33：    good_after_seconds: int = 5 → 无问题
  - 行 34：    slippage_bps: float = 2.0 → 无问题
  - 行 35：    commission_per_share: float = 0.005 → 无问题
  - 行 36： → 无问题
  - 行 37： → 无问题
  - 行 38：class IbkrExecutionClient: → 无问题
  - 行 61： → 无问题
  - 行 113： → 无问题
  - 行 117： → 无问题
  - 行 118： → 无问题
  - 行 179： → 无问题
  - 行 180： → 无问题
  - 行 185： → 无问题
  - 行 186： → 无问题
  - 行 216： → 无问题
  - 行 217： → 无问题
  - 行 228： → 无问题
  - 行 229： → 无问题
  - 行 233： → 无问题
  - 行 234： → 无问题
  - 行 245： → 问题（ID 14）
  - 行 246： → 问题（ID 14）
  - 行 260： → 无问题
  - 行 261： → 无问题
  - 行 283： → 无问题
  - 行 284： → 无问题
  - 行 292： → 无问题
  - 行 293： → 无问题
  - 行 308： → 无问题
  - 行 309： → 无问题
  - 行 310：if __name__ == "__main__": → 无问题
  - 行 311：    raise SystemExit(main()) → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：ExecutionClient.submit_bracket_signal（行 14-15）
- 功能：执行对应业务逻辑
- 参数：self: Any, signal: dict[str, Any]
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 14：    def submit_bracket_signal(self, signal: dict[str, Any]) -> dict[str, Any]: → 无问题
  - 行 15：        ... → 无问题
- 调用的外部函数：无
- 被谁调用：tests/test_ibkr_execution.py:IbkrExecutionTests.test_submit_bracket_signal_with_ibkr_semantics:75
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：ExecutionClient.close（行 17-18）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 17：    def close(self) -> None: → 无问题
  - 行 18：        ... → 无问题
- 调用的外部函数：无
- 被谁调用：ibkr_paper_check.py:run_probe:365; tests/test_ibkr_execution.py:IbkrExecutionTests.test_submit_bracket_signal_with_ibkr_semantics:114
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionClient.__init__（行 39-60）
- 功能：执行对应业务逻辑
- 参数：self: Any, config: ExecutionConfig, ib_factory: Callable[[], Any] | None, stock_factory: Callable[[str, str, str], Any] | None
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 39：    def __init__( → 无问题
  - 行 40：        self, → 无问题
  - 行 41：        config: ExecutionConfig, → 无问题
  - 行 42：        *, → 无问题
  - 行 43：        ib_factory: Callable[[], Any] | None = None, → 无问题
  - 行 44：        stock_factory: Callable[[str, str, str], Any] | None = None, → 无问题
  - 行 45：    ) -> None: → 无问题
  - 行 46：        self._config = config → 无问题
  - 行 47：        if ib_factory is None or stock_factory is None: → 无问题
  - 行 48：            ib_cls, stock_cls = _import_ib_insync() → 无问题
  - 行 49：            self._ib = (ib_factory or ib_cls)() → 无问题
  - 行 50：            self._stock_factory = stock_factory or stock_cls → 无问题
  - 行 51：        else: → 无问题
  - 行 52：            self._ib = ib_factory() → 无问题
  - 行 53：            self._stock_factory = stock_factory → 无问题
  - 行 54：        self._ib.connect( → 无问题
  - 行 55：            config.host, → 无问题
  - 行 56：            config.port, → 无问题
  - 行 57：            clientId=config.client_id, → 无问题
  - 行 58：            timeout=config.timeout_seconds, → 无问题
  - 行 59：            readonly=False, → 无问题
  - 行 60：        ) → 无问题
- 调用的外部函数：self._ib.connect; _import_ib_insync; ib_factory
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionClient.submit_bracket_signal（行 62-112）
- 功能：执行对应业务逻辑
- 参数：self: Any, signal: dict[str, Any]
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 62：    def submit_bracket_signal(self, signal: dict[str, Any]) -> dict[str, Any]: → 无问题
  - 行 63：        contract_payload = signal.get("contract", {}) → 无问题
  - 行 64：        orders_payload = signal.get("orders", []) → 无问题
  - 行 65：        if len(orders_payload) != 3: → 无问题
  - 行 66：            return {"ok": False, "error": "INVALID_BRACKET_SIGNAL", "signal": signal} → 无问题
  - 行 67：        if not _is_valid_transmit_chain(orders_payload): → 无问题
  - 行 68：            return {"ok": False, "error": "INVALID_TRANSMIT_CHAIN", "signal": signal} → 无问题
  - 行 69：        if self._config.session_guard_enabled and not _is_within_session_window( → 无问题
  - 行 70：            self._config.session_start_utc, → 无问题
  - 行 71：            self._config.session_end_utc, → 无问题
  - 行 72：        ): → 无问题
  - 行 73：            return {"ok": False, "error": "SESSION_CLOSED", "signal": signal} → 无问题
  - 行 74：        symbol = str(contract_payload.get("symbol", "")).upper() → 无问题
  - 行 75：        exchange = str(contract_payload.get("exchange", self._config.exchange)) → 无问题
  - 行 76：        currency = str(contract_payload.get("currency", self._config.currency)) → 无问题
  - 行 77：        contract = self._stock_factory(symbol, exchange, currency) → 无问题
  - 行 78：        self._ib.qualifyContracts(contract) → 无问题
  - 行 79：        parent_info, take_profit_info, stop_loss_info = orders_payload → 无问题
  - 行 80：        quantity = float(parent_info.get("totalQuantity", 0.0)) → 无问题
  - 行 81：        bracket = self._ib.bracketOrder( → 无问题
  - 行 82：            str(parent_info.get("action", "BUY")), → 无问题
  - 行 83：            quantity, → 无问题
  - 行 84：            float(parent_info.get("lmtPrice", 0.0)), → 无问题
  - 行 85：            float(take_profit_info.get("lmtPrice", 0.0)), → 无问题
  - 行 86：            float(stop_loss_info.get("auxPrice", 0.0)), → 无问题
  - 行 87：        ) → 无问题
  - 行 88：        parent, take_profit, stop_loss = bracket → 无问题
  - 行 89：        good_after = _build_good_after_time(self._config.good_after_seconds) → 无问题
  - 行 90：        for order, payload in zip((parent, take_profit, stop_loss), orders_payload): → 无问题
  - 行 91：            order.tif = str(payload.get("tif", "DAY")) → 无问题
  - 行 92：            order.transmit = bool(payload.get("transmit", False)) → 无问题
  - 行 93：            order.orderRef = str(payload.get("orderRef", "")) → 无问题
  - 行 94：            order.goodAfterTime = good_after → 无问题
  - 行 95：            if self._config.account: → 无问题
  - 行 96：                order.account = self._config.account → 无问题
  - 行 97：        trades = [ → 无问题
  - 行 98：            self._ib.placeOrder(contract, parent), → 无问题
  - 行 99：            self._ib.placeOrder(contract, take_profit), → 无问题
  - 行 100：            self._ib.placeOrder(contract, stop_loss), → 无问题
  - 行 101：        ] → 无问题
  - 行 102：        return { → 无问题
  - 行 103：            "ok": True, → 无问题
  - 行 104：            "symbol": symbol, → 无问题
  - 行 105：            "executed_at": datetime.now(tz=timezone.utc).isoformat(), → 无问题
  - 行 106：            "orders": [_trade_to_dict(item) for item in trades], → 无问题
  - 行 107：            "estimated_transaction_cost": _estimate_signal_cost( → 无问题
  - 行 108：                signal, → 无问题
  - 行 109：                slippage_bps=self._config.slippage_bps, → 无问题
  - 行 110：                commission_per_share=self._config.commission_per_share, → 无问题
  - 行 111：            ), → 无问题
  - 行 112：        } → 无问题
- 调用的外部函数：signal.get; upper; str; self._stock_factory; self._ib.qualifyContracts; float; self._ib.bracketOrder; _build_good_after_time; zip; len; _is_valid_transmit_chain; contract_payload.get; parent_info.get; bool; self._ib.placeOrder; isoformat; _estimate_signal_cost; _is_within_session_window; take_profit_info.get; stop_loss_info.get; payload.get; _trade_to_dict; datetime.now
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionClient.close（行 114-116）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 114：    def close(self) -> None: → 无问题
  - 行 115：        if self._ib.isConnected(): → 无问题
  - 行 116：            self._ib.disconnect() → 无问题
- 调用的外部函数：self._ib.isConnected; self._ib.disconnect
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：execute_cycle（行 119-178）
- 功能：执行对应业务逻辑
- 参数：symbol: str, config: AppConfig, send: bool, daily_state: dict[str, object] | None, client_factory: Callable[[ExecutionConfig], ExecutionClient] | None
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 119：def execute_cycle( → 无问题
  - 行 120：    *, → 无问题
  - 行 121：    symbol: str, → 无问题
  - 行 122：    config: AppConfig, → 无问题
  - 行 123：    send: bool, → 无问题
  - 行 124：    daily_state: dict[str, object] | None = None, → 无问题
  - 行 125：    client_factory: Callable[[ExecutionConfig], ExecutionClient] | None = None, → 无问题
  - 行 126：) -> dict[str, Any]: → 无问题
  - 行 127：    lane_output = run_lane_cycle(symbol=symbol, config=config, daily_state=daily_state) → 无问题
  - 行 128：    signals = lane_output.get("ibkr_order_signals", []) → 无问题
  - 行 129：    executions: list[dict[str, Any]] = [] → 无问题
  - 行 130：    if send and signals: → 无问题
  - 行 131：        execution_config = ExecutionConfig( → 无问题
  - 行 132：            host=config.ibkr_host, → 无问题
  - 行 133：            port=config.ibkr_port, → 无问题
  - 行 134：            session_guard_enabled=config.execution_session_guard_enabled, → 无问题
  - 行 135：            session_start_utc=config.execution_session_start_utc, → 无问题
  - 行 136：            session_end_utc=config.execution_session_end_utc, → 无问题
  - 行 137：            good_after_seconds=config.execution_good_after_seconds, → 无问题
  - 行 138：            slippage_bps=config.risk_slippage_bps, → 无问题
  - 行 139：            commission_per_share=config.risk_commission_per_share, → 无问题
  - 行 140：        ) → 无问题
  - 行 141：        client = (client_factory or IbkrExecutionClient)(execution_config) → 无问题
  - 行 142：        try: → 无问题
  - 行 143：            for signal in signals: → 无问题
  - 行 144：                try: → 无问题
  - 行 145：                    executions.append(client.submit_bracket_signal(signal)) → 无问题
  - 行 146：                except Exception as exc: → 无问题
  - 行 147：                    executions.append( → 无问题
  - 行 148：                        { → 无问题
  - 行 149：                            "ok": False, → 无问题
  - 行 150：                            "error": exc.__class__.__name__, → 无问题
  - 行 151：                            "message": str(exc), → 无问题
  - 行 152：                            "signal": signal, → 无问题
  - 行 153：                        } → 无问题
  - 行 154：                    ) → 无问题
  - 行 155：        finally: → 无问题
  - 行 156：            client.close() → 无问题
  - 行 157：    else: → 无问题
  - 行 158：        executions = [ → 无问题
  - 行 159：            { → 无问题
  - 行 160：                "ok": True, → 无问题
  - 行 161：                "dry_run": True, → 无问题
  - 行 162：                "signal": signal, → 无问题
  - 行 163：                "estimated_transaction_cost": _estimate_signal_cost( → 无问题
  - 行 164：                    signal, → 无问题
  - 行 165：                    slippage_bps=config.risk_slippage_bps, → 无问题
  - 行 166：                    commission_per_share=config.risk_commission_per_share, → 无问题
  - 行 167：                ), → 无问题
  - 行 168：            } → 无问题
  - 行 169：            for signal in signals → 无问题
  - 行 170：        ] → 无问题
  - 行 171：    return { → 无问题
  - 行 172：        "kind": "phase0_ibkr_execution", → 无问题
  - 行 173：        "symbol": symbol.upper(), → 无问题
  - 行 174：        "send_enabled": send, → 无问题
  - 行 175：        "signals_count": len(signals), → 无问题
  - 行 176：        "lane": lane_output, → 无问题
  - 行 177：        "executions": executions, → 无问题
  - 行 178：    } → 无问题
- 调用的外部函数：run_lane_cycle; lane_output.get; ExecutionConfig; symbol.upper; len; client.close; _estimate_signal_cost; executions.append; client.submit_bracket_signal; str
- 被谁调用：tests/test_ibkr_execution.py:IbkrExecutionTests.test_execute_cycle_dry_run_returns_signal:118; tests/test_ibkr_execution.py:IbkrExecutionTests.test_execute_cycle_send_with_injected_client:136; tests/test_ibkr_execution.py:IbkrExecutionTests.test_execute_cycle_send_continues_when_single_signal_fails:168
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_import_ib_insync（行 181-184）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：tuple[type[Any], Callable[[str, str, str], Any]]（见函数语义）
- 逐行分析：
  - 行 181：def _import_ib_insync() -> tuple[type[Any], Callable[[str, str, str], Any]]: → 无问题
  - 行 182：    from ib_insync import IB, Stock → 无问题
  - 行 183： → 无问题
  - 行 184：    return IB, Stock → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_trade_to_dict（行 187-215）
- 功能：执行对应业务逻辑
- 参数：trade: Any
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 187：def _trade_to_dict(trade: Any) -> dict[str, Any]: → 问题（ID 5）
  - 行 188：    order = getattr(trade, "order", None) → 问题（ID 5）
  - 行 189：    order_status = getattr(trade, "orderStatus", None) → 问题（ID 5）
  - 行 190：    status = getattr(order_status, "status", "UNKNOWN") → 问题（ID 5）
  - 行 191：    filled = float(getattr(order_status, "filled", 0.0) or 0.0) → 问题（ID 5）
  - 行 192：    remaining = float(getattr(order_status, "remaining", 0.0) or 0.0) → 问题（ID 5）
  - 行 193：    avg_fill_price = float(getattr(order_status, "avgFillPrice", 0.0) or 0.0) → 问题（ID 5）
  - 行 194：    fills_payload = [] → 问题（ID 5）
  - 行 195：    for fill in list(getattr(trade, "fills", []) or []): → 问题（ID 5）
  - 行 196：        execution = getattr(fill, "execution", None) → 问题（ID 5）
  - 行 197：        fills_payload.append( → 问题（ID 5）
  - 行 198：            { → 问题（ID 5）
  - 行 199：                "exec_id": getattr(execution, "execId", ""), → 问题（ID 5）
  - 行 200：                "shares": float(getattr(execution, "shares", 0.0) or 0.0), → 问题（ID 5）
  - 行 201：                "price": float(getattr(execution, "price", 0.0) or 0.0), → 问题（ID 5）
  - 行 202：                "time": str(getattr(execution, "time", "")), → 问题（ID 5）
  - 行 203：            } → 问题（ID 5）
  - 行 204：        ) → 问题（ID 5）
  - 行 205：    return { → 问题（ID 5）
  - 行 206：        "status": status, → 问题（ID 5）
  - 行 207：        "order_id": getattr(order, "orderId", None), → 问题（ID 5）
  - 行 208：        "perm_id": getattr(order, "permId", None), → 问题（ID 5）
  - 行 209：        "order_ref": getattr(order, "orderRef", ""), → 问题（ID 5）
  - 行 210：        "filled_quantity": filled, → 问题（ID 5）
  - 行 211：        "remaining_quantity": remaining, → 问题（ID 5）
  - 行 212：        "avg_fill_price": avg_fill_price, → 问题（ID 5）
  - 行 213：        "fills_count": len(fills_payload), → 无问题
  - 行 214：        "fills": fills_payload, → 无问题
  - 行 215：    } → 无问题
- 调用的外部函数：getattr; float; list; fills_payload.append; len; str
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 5：订单生命周期字段不完整（高）

#### 函数：_is_valid_transmit_chain（行 218-227）
- 功能：执行对应业务逻辑
- 参数：orders_payload: list[dict[str, Any]]
- 返回值：bool（见函数语义）
- 逐行分析：
  - 行 218：def _is_valid_transmit_chain(orders_payload: list[dict[str, Any]]) -> bool: → 无问题
  - 行 219：    if len(orders_payload) != 3: → 无问题
  - 行 220：        return False → 无问题
  - 行 221：    flags = [bool(item.get("transmit", False)) for item in orders_payload] → 无问题
  - 行 222：    if flags != [False, False, True]: → 无问题
  - 行 223：        return False → 无问题
  - 行 224：    parent_ref = str(orders_payload[0].get("orderRef", "")) → 无问题
  - 行 225：    if not parent_ref: → 无问题
  - 行 226：        return False → 无问题
  - 行 227：    return all(str(item.get("parentRef", "")) == parent_ref for item in orders_payload[1:]) → 无问题
- 调用的外部函数：str; all; len; bool; get; item.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_build_good_after_time（行 230-232）
- 功能：执行对应业务逻辑
- 参数：good_after_seconds: int
- 返回值：str（见函数语义）
- 逐行分析：
  - 行 230：def _build_good_after_time(good_after_seconds: int) -> str: → 无问题
  - 行 231：    ts = datetime.now(tz=timezone.utc) + timedelta(seconds=max(0, good_after_seconds)) → 无问题
  - 行 232：    return ts.strftime("%Y%m%d %H:%M:%S UTC") → 无问题
- 调用的外部函数：ts.strftime; datetime.now; timedelta; max
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_is_within_session_window（行 235-244）
- 功能：执行对应业务逻辑
- 参数：start_utc: str, end_utc: str
- 返回值：bool（见函数语义）
- 逐行分析：
  - 行 235：def _is_within_session_window(start_utc: str, end_utc: str) -> bool: → 无问题
  - 行 236：    now = datetime.now(tz=timezone.utc) → 无问题
  - 行 237：    start = _parse_hhmm(start_utc) → 无问题
  - 行 238：    end = _parse_hhmm(end_utc) → 无问题
  - 行 239：    if start is None or end is None: → 无问题
  - 行 240：        return False → 无问题
  - 行 241：    current_minutes = now.hour * 60 + now.minute → 无问题
  - 行 242：    if start <= end: → 无问题
  - 行 243：        return start <= current_minutes <= end → 无问题
  - 行 244：    return current_minutes >= start or current_minutes <= end → 问题（ID 14）
- 调用的外部函数：datetime.now; _parse_hhmm
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 14：时段解析容错不足（中）

#### 函数：_parse_hhmm（行 247-259）
- 功能：执行对应业务逻辑
- 参数：raw: str
- 返回值：int | None（见函数语义）
- 逐行分析：
  - 行 247：def _parse_hhmm(raw: str) -> int | None: → 问题（ID 14）
  - 行 248：    text = raw.strip() → 问题（ID 14）
  - 行 249：    parts = text.split(":") → 问题（ID 14）
  - 行 250：    if len(parts) not in {2, 3}: → 问题（ID 14）
  - 行 251：        return None → 问题（ID 14）
  - 行 252：    try: → 问题（ID 14）
  - 行 253：        hour = int(parts[0]) → 问题（ID 14）
  - 行 254：        minute = int(parts[1]) → 无问题
  - 行 255：    except Exception: → 无问题
  - 行 256：        return None → 无问题
  - 行 257：    if hour < 0 or hour > 23 or minute < 0 or minute > 59: → 无问题
  - 行 258：        return None → 无问题
  - 行 259：    return hour * 60 + minute → 无问题
- 调用的外部函数：raw.strip; text.split; len; int
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 14：时段解析容错不足（中）

#### 函数：_estimate_signal_cost（行 262-282）
- 功能：执行对应业务逻辑
- 参数：signal: dict[str, Any], slippage_bps: float, commission_per_share: float
- 返回值：dict[str, float]（见函数语义）
- 逐行分析：
  - 行 262：def _estimate_signal_cost( → 无问题
  - 行 263：    signal: dict[str, Any], → 无问题
  - 行 264：    *, → 无问题
  - 行 265：    slippage_bps: float, → 无问题
  - 行 266：    commission_per_share: float, → 无问题
  - 行 267：) -> dict[str, float]: → 无问题
  - 行 268：    orders = list(signal.get("orders", []) or []) → 无问题
  - 行 269：    if not orders: → 无问题
  - 行 270：        return {"slippage_cost": 0.0, "commission_cost": 0.0, "total": 0.0} → 无问题
  - 行 271：    parent = orders[0] → 无问题
  - 行 272：    quantity = float(parent.get("totalQuantity", 0.0) or 0.0) → 无问题
  - 行 273：    limit_price = float(parent.get("lmtPrice", 0.0) or 0.0) → 无问题
  - 行 274：    notional = max(0.0, quantity * limit_price) → 无问题
  - 行 275：    slippage_cost = notional * max(0.0, slippage_bps) / 10000 → 无问题
  - 行 276：    commission_cost = max(0.0, quantity) * max(0.0, commission_per_share) → 无问题
  - 行 277：    total = slippage_cost + commission_cost → 无问题
  - 行 278：    return { → 无问题
  - 行 279：        "slippage_cost": round(slippage_cost, 6), → 无问题
  - 行 280：        "commission_cost": round(commission_cost, 6), → 无问题
  - 行 281：        "total": round(total, 6), → 无问题
  - 行 282：    } → 无问题
- 调用的外部函数：list; float; max; round; signal.get; parent.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_parse_args（行 285-291）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：argparse.Namespace（见函数语义）
- 逐行分析：
  - 行 285：def _parse_args() -> argparse.Namespace: → 无问题
  - 行 286：    parser = argparse.ArgumentParser(prog="phase0-ibkr-execute") → 无问题
  - 行 287：    parser.add_argument("--symbol", default="AAPL") → 无问题
  - 行 288：    parser.add_argument("--send", action="store_true") → 无问题
  - 行 289：    parser.add_argument("--actions-today", type=int, default=0) → 无问题
  - 行 290：    parser.add_argument("--has-open-position", action="store_true") → 无问题
  - 行 291：    return parser.parse_args() → 无问题
- 调用的外部函数：argparse.ArgumentParser; parser.add_argument; parser.parse_args
- 被谁调用：phase0_validation_report.py:main:198; non_ai_validation_report.py:main:200; replay.py:main:202; ibkr_paper_check.py:main:389
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：main（行 294-307）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：int（见函数语义）
- 逐行分析：
  - 行 294：def main() -> int: → 无问题
  - 行 295：    args = _parse_args() → 无问题
  - 行 296：    config = load_config() → 无问题
  - 行 297：    report = execute_cycle( → 无问题
  - 行 298：        symbol=args.symbol, → 无问题
  - 行 299：        config=config, → 无问题
  - 行 300：        send=args.send, → 无问题
  - 行 301：        daily_state={"actions_today": args.actions_today, "has_open_position": args.has_open_position}, → 无问题
  - 行 302：    ) → 无问题
  - 行 303：    print(json.dumps(report, ensure_ascii=False)) → 无问题
  - 行 304：    all_ok = all(item.get("ok", False) for item in report.get("executions", [])) → 无问题
  - 行 305：    if all_ok: → 无问题
  - 行 306：        return 0 → 无问题
  - 行 307：    return 2 → 无问题
- 调用的外部函数：_parse_args; load_config; execute_cycle; print; all; json.dumps; item.get; report.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| 187-212 | 订单生命周期字段不完整 | 高 | 5 |
| 244-253 | 时段解析容错不足 | 中 | 14 |

### 自检统计
- 实际逐行审计行数：311
- 函数审计数：15
- 发现问题数：2

## 文件：ibkr_order_adapter.py
- 总行数：74
- 函数/方法数：1

### 逐函数检查

#### 函数：__module__（行 1-5）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from typing import Any → 无问题
  - 行 4： → 无问题
  - 行 5： → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：map_decision_to_ibkr_bracket（行 6-74）
- 功能：执行对应业务逻辑
- 参数：decision: dict[str, Any], exchange: str, currency: str
- 返回值：dict[str, Any] | None（见函数语义）
- 逐行分析：
  - 行 6：def map_decision_to_ibkr_bracket( → 无问题
  - 行 7：    decision: dict[str, Any], → 无问题
  - 行 8：    *, → 无问题
  - 行 9：    exchange: str = "SMART", → 无问题
  - 行 10：    currency: str = "USD", → 无问题
  - 行 11：) -> dict[str, Any] | None: → 无问题
  - 行 12：    if decision.get("status") != "accepted": → 无问题
  - 行 13：        return None → 无问题
  - 行 14：    bracket = decision.get("bracket_order", {}) → 无问题
  - 行 15：    parent = bracket.get("parent", {}) → 无问题
  - 行 16：    take_profit = bracket.get("take_profit", {}) → 无问题
  - 行 17：    stop_loss = bracket.get("stop_loss", {}) → 无问题
  - 行 18：    symbol = str(parent.get("symbol", decision.get("symbol", ""))).upper() → 无问题
  - 行 19：    if not symbol: → 无问题
  - 行 20：        return None → 无问题
  - 行 21：    parent_ref = str(parent.get("client_order_id", "PARENT")) → 无问题
  - 行 22：    tp_ref = str(take_profit.get("client_order_id", "TAKE_PROFIT")) → 无问题
  - 行 23：    sl_ref = str(stop_loss.get("client_order_id", "STOP_LOSS")) → 无问题
  - 行 24：    qty = int(parent.get("quantity", decision.get("quantity", 0)) or 0) → 无问题
  - 行 25：    if qty <= 0: → 无问题
  - 行 26：        return None → 无问题
  - 行 27：    parent_limit_price = float(parent.get("limit_price", 0.0)) → 无问题
  - 行 28：    tp_limit_price = float(take_profit.get("limit_price", 0.0)) → 无问题
  - 行 29：    sl_stop_price = float(stop_loss.get("stop_price", 0.0)) → 无问题
  - 行 30：    if parent_limit_price <= 0 or tp_limit_price <= 0 or sl_stop_price <= 0: → 无问题
  - 行 31：        return None → 无问题
  - 行 32：    parent_action = str(parent.get("action", "BUY")).upper() → 无问题
  - 行 33：    exit_action = "SELL" if parent_action == "BUY" else "BUY" → 无问题
  - 行 34：    return { → 无问题
  - 行 35：        "contract": { → 无问题
  - 行 36：            "symbol": symbol, → 无问题
  - 行 37：            "secType": "STK", → 无问题
  - 行 38：            "exchange": exchange, → 无问题
  - 行 39：            "currency": currency, → 无问题
  - 行 40：        }, → 无问题
  - 行 41：        "orders": [ → 问题（ID 13）
  - 行 42：            { → 问题（ID 13）
  - 行 43：                "orderRef": parent_ref, → 问题（ID 13）
  - 行 44：                "action": parent_action, → 问题（ID 13）
  - 行 45：                "orderType": "LMT", → 问题（ID 13）
  - 行 46：                "totalQuantity": qty, → 问题（ID 13）
  - 行 47：                "lmtPrice": parent_limit_price, → 问题（ID 13）
  - 行 48：                "tif": str(parent.get("time_in_force", "DAY")), → 问题（ID 13）
  - 行 49：                "transmit": False, → 问题（ID 13）
  - 行 50：            }, → 问题（ID 13）
  - 行 51：            { → 问题（ID 13）
  - 行 52：                "orderRef": tp_ref, → 问题（ID 13）
  - 行 53：                "parentRef": parent_ref, → 问题（ID 13）
  - 行 54：                "action": exit_action, → 问题（ID 13）
  - 行 55：                "orderType": "LMT", → 问题（ID 13）
  - 行 56：                "totalQuantity": qty, → 问题（ID 13）
  - 行 57：                "lmtPrice": tp_limit_price, → 问题（ID 13）
  - 行 58：                "tif": str(take_profit.get("time_in_force", "GTC")), → 问题（ID 13）
  - 行 59：                "transmit": False, → 问题（ID 13）
  - 行 60：            }, → 问题（ID 13）
  - 行 61：            { → 问题（ID 13）
  - 行 62：                "orderRef": sl_ref, → 问题（ID 13）
  - 行 63：                "parentRef": parent_ref, → 问题（ID 13）
  - 行 64：                "action": exit_action, → 问题（ID 13）
  - 行 65：                "orderType": "STP", → 问题（ID 13）
  - 行 66：                "totalQuantity": qty, → 问题（ID 13）
  - 行 67：                "auxPrice": sl_stop_price, → 问题（ID 13）
  - 行 68：                "tif": str(stop_loss.get("time_in_force", "GTC")), → 问题（ID 13）
  - 行 69：                "transmit": True, → 问题（ID 13）
  - 行 70：            }, → 问题（ID 13）
  - 行 71：        ], → 问题（ID 13）
  - 行 72：        "sequence": ["parent", "take_profit", "stop_loss"], → 问题（ID 13）
  - 行 73：        "note": "parent/tp/sl should be sent sequentially with IBKR parentId/orderId mapping", → 问题（ID 13）
  - 行 74：    } → 无问题
- 调用的外部函数：decision.get; bracket.get; upper; str; int; float; parent.get; take_profit.get; stop_loss.get
- 被谁调用：lanes/__init__.py:run_lane_cycle:232; tests/test_discipline_and_ibkr_adapter.py:DisciplineAndIbkrAdapterTests.test_ibkr_mapping_uses_stp_and_transmit_chain:49
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 13：Bracket 顺序联动风险（高）

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| 41-73 | Bracket 顺序联动风险 | 高 | 13 |

### 自检统计
- 实际逐行审计行数：74
- 函数审计数：1
- 发现问题数：1

## 文件：discipline.py
- 总行数：104
- 函数/方法数：2

### 逐函数检查

#### 函数：__module__（行 1-61）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from dataclasses import dataclass → 无问题
  - 行 4： → 无问题
  - 行 5： → 无问题
  - 行 6：@dataclass(frozen=True) → 无问题
  - 行 7：class HoldWorthiness: → 无问题
  - 行 8：    score: float → 无问题
  - 行 9：    should_wait: bool → 无问题
  - 行 10：    recommended_holding_days: int → 无问题
  - 行 11：    reasons: list[str] → 无问题
  - 行 12： → 无问题
  - 行 13： → 无问题
  - 行 60： → 无问题
  - 行 61： → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：evaluate_hold_worthiness（行 14-59）
- 功能：执行对应业务逻辑
- 参数：market_row: dict[str, float | str], strategy_confidence: float, ultra_authenticity_score: float, low_committee_approved: bool, hold_score_threshold: float, max_holding_days: int
- 返回值：HoldWorthiness（见函数语义）
- 逐行分析：
  - 行 14：def evaluate_hold_worthiness( → 无问题
  - 行 15：    *, → 无问题
  - 行 16：    market_row: dict[str, float | str], → 无问题
  - 行 17：    strategy_confidence: float, → 无问题
  - 行 18：    ultra_authenticity_score: float, → 无问题
  - 行 19：    low_committee_approved: bool, → 无问题
  - 行 20：    hold_score_threshold: float, → 无问题
  - 行 21：    max_holding_days: int, → 无问题
  - 行 22：) -> HoldWorthiness: → 无问题
  - 行 23：    momentum = max(0.0, float(market_row.get("momentum_20d", 0.0))) → 无问题
  - 行 24：    relative_strength = max(0.0, float(market_row.get("relative_strength", 0.0))) → 无问题
  - 行 25：    volatility = max(0.01, float(market_row.get("volatility", 0.2))) → 无问题
  - 行 26：    momentum_score = min(1.0, momentum / 0.12) → 无问题
  - 行 27：    rel_score = min(1.0, relative_strength / 0.3) → 无问题
  - 行 28：    vol_penalty = min(0.4, volatility / 1.2) → 无问题
  - 行 29：    committee_bonus = 0.1 if low_committee_approved else -0.08 → 无问题
  - 行 30：    raw_score = ( → 无问题
  - 行 31：        momentum_score * 0.3 → 无问题
  - 行 32：        + rel_score * 0.25 → 无问题
  - 行 33：        + max(0.0, strategy_confidence) * 0.2 → 无问题
  - 行 34：        + max(0.0, ultra_authenticity_score) * 0.25 → 无问题
  - 行 35：        + committee_bonus → 无问题
  - 行 36：        - vol_penalty → 无问题
  - 行 37：    ) → 无问题
  - 行 38：    score = max(0.0, min(1.0, round(raw_score, 6))) → 无问题
  - 行 39：    should_wait = score >= hold_score_threshold → 无问题
  - 行 40：    recommended_holding_days = min(max(1, max_holding_days), 3 if should_wait else 1) → 无问题
  - 行 41：    reasons: list[str] = [] → 无问题
  - 行 42：    if momentum_score > 0.65: → 无问题
  - 行 43：        reasons.append("MOMENTUM_STRONG") → 无问题
  - 行 44：    if rel_score > 0.6: → 无问题
  - 行 45：        reasons.append("SECTOR_RELATIVE_STRENGTH") → 无问题
  - 行 46：    if ultra_authenticity_score >= 0.7: → 无问题
  - 行 47：        reasons.append("NEWS_AUTHENTIC") → 无问题
  - 行 48：    if low_committee_approved: → 无问题
  - 行 49：        reasons.append("LOW_COMMITTEE_APPROVED") → 无问题
  - 行 50：    if volatility > 0.28: → 无问题
  - 行 51：        reasons.append("VOLATILITY_ELEVATED") → 无问题
  - 行 52：    if not reasons: → 无问题
  - 行 53：        reasons.append("NO_CLEAR_EDGE") → 无问题
  - 行 54：    return HoldWorthiness( → 无问题
  - 行 55：        score=score, → 无问题
  - 行 56：        should_wait=should_wait, → 无问题
  - 行 57：        recommended_holding_days=recommended_holding_days, → 无问题
  - 行 58：        reasons=reasons, → 无问题
  - 行 59：    ) → 无问题
- 调用的外部函数：max; min; HoldWorthiness; float; reasons.append; market_row.get; round
- 被谁调用：lanes/__init__.py:run_lane_cycle:212; tests/test_discipline_and_ibkr_adapter.py:DisciplineAndIbkrAdapterTests.test_hold_score_and_daily_plan:16
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：build_daily_discipline_plan（行 62-104）
- 功能：执行对应业务逻辑
- 参数：actions_today: int, has_open_position: bool, min_actions_per_day: int, discipline_enabled: bool, hold: HoldWorthiness
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 62：def build_daily_discipline_plan( → 无问题
  - 行 63：    *, → 无问题
  - 行 64：    actions_today: int, → 无问题
  - 行 65：    has_open_position: bool, → 无问题
  - 行 66：    min_actions_per_day: int, → 无问题
  - 行 67：    discipline_enabled: bool, → 无问题
  - 行 68：    hold: HoldWorthiness, → 无问题
  - 行 69：) -> dict[str, object]: → 无问题
  - 行 70：    if not discipline_enabled: → 无问题
  - 行 71：        return { → 无问题
  - 行 72：            "enabled": False, → 无问题
  - 行 73：            "required_action": "none", → 无问题
  - 行 74：            "action_reason": "DISCIPLINE_DISABLED", → 无问题
  - 行 75：            "actions_today": actions_today, → 无问题
  - 行 76：            "min_actions_per_day": min_actions_per_day, → 无问题
  - 行 77：            "hold_score": hold.score, → 无问题
  - 行 78：            "recommended_holding_days": hold.recommended_holding_days, → 无问题
  - 行 79：            "should_wait": hold.should_wait, → 无问题
  - 行 80：            "reasons": hold.reasons, → 无问题
  - 行 81：        } → 无问题
  - 行 82：    required_action = "none" → 无问题
  - 行 83：    action_reason = "TARGET_REACHED" → 无问题
  - 行 84：    if actions_today < min_actions_per_day: → 问题（ID 10）
  - 行 85：        if has_open_position and not hold.should_wait: → 问题（ID 10）
  - 行 86：            required_action = "sell" → 问题（ID 10）
  - 行 87：            action_reason = "DAILY_QUOTA_AND_LOW_HOLD_SCORE" → 问题（ID 10）
  - 行 88：        elif has_open_position and hold.should_wait: → 问题（ID 10）
  - 行 89：            required_action = "hold" → 问题（ID 10）
  - 行 90：            action_reason = "DAILY_QUOTA_BUT_HOLD_SCORE_HIGH" → 问题（ID 10）
  - 行 91：        else: → 问题（ID 10）
  - 行 92：            required_action = "buy" → 问题（ID 10）
  - 行 93：            action_reason = "DAILY_QUOTA_NO_POSITION_BUY" → 问题（ID 10）
  - 行 94：    return { → 问题（ID 10）
  - 行 95：        "enabled": True, → 无问题
  - 行 96：        "required_action": required_action, → 无问题
  - 行 97：        "action_reason": action_reason, → 无问题
  - 行 98：        "actions_today": actions_today, → 无问题
  - 行 99：        "min_actions_per_day": min_actions_per_day, → 无问题
  - 行 100：        "hold_score": hold.score, → 无问题
  - 行 101：        "recommended_holding_days": hold.recommended_holding_days, → 无问题
  - 行 102：        "should_wait": hold.should_wait, → 无问题
  - 行 103：        "reasons": hold.reasons, → 无问题
  - 行 104：    } → 无问题
- 调用的外部函数：无
- 被谁调用：lanes/__init__.py:run_lane_cycle:222; tests/test_discipline_and_ibkr_adapter.py:DisciplineAndIbkrAdapterTests.test_hold_score_and_daily_plan:25
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 10：纪律优先级冲突风险（中）

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| 84-94 | 纪律优先级冲突风险 | 中 | 10 |

### 自检统计
- 实际逐行审计行数：104
- 函数审计数：2
- 发现问题数：1

## 文件：audit.py
- 总行数：180
- 函数/方法数：6

### 逐函数检查

#### 函数：__module__（行 1-178）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from dataclasses import dataclass → 无问题
  - 行 4：from datetime import datetime, timedelta, timezone → 无问题
  - 行 5：import json → 无问题
  - 行 6：from pathlib import Path → 无问题
  - 行 7：import sqlite3 → 无问题
  - 行 8：from typing import Any → 无问题
  - 行 9： → 无问题
  - 行 10： → 无问题
  - 行 11：@dataclass(frozen=True) → 无问题
  - 行 12：class ParameterAuditEntry: → 无问题
  - 行 13：    ts: str → 无问题
  - 行 14：    symbol: str → 无问题
  - 行 15：    strategy: str → 无问题
  - 行 16：    approved: bool → 无问题
  - 行 17：    reason: str → 无问题
  - 行 18：    before_stop_loss_pct: float → 无问题
  - 行 19：    after_stop_loss_pct: float → 无问题
  - 行 20：    before_risk_multiplier: float → 无问题
  - 行 21：    after_risk_multiplier: float → 无问题
  - 行 22：    low_committee_approved: bool → 无问题
  - 行 23：    ultra_wake_high: bool → 无问题
  - 行 24： → 无问题
  - 行 25： → 无问题
  - 行 68： → 无问题
  - 行 69： → 无问题
  - 行 97： → 无问题
  - 行 98： → 无问题
  - 行 132： → 无问题
  - 行 133： → 无问题
  - 行 150： → 无问题
  - 行 151： → 无问题
  - 行 177： → 无问题
  - 行 178： → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：ensure_audit_db（行 26-67）
- 功能：执行对应业务逻辑
- 参数：db_path: str
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 26：def ensure_audit_db(db_path: str) -> None: → 无问题
  - 行 27：    path = Path(db_path) → 无问题
  - 行 28：    path.parent.mkdir(parents=True, exist_ok=True) → 无问题
  - 行 29：    with sqlite3.connect(path) as conn: → 无问题
  - 行 30：        conn.execute( → 无问题
  - 行 31：            """ → 无问题
  - 行 32：            CREATE TABLE IF NOT EXISTS parameter_audit ( → 无问题
  - 行 33：                ts TEXT NOT NULL, → 无问题
  - 行 34：                symbol TEXT NOT NULL, → 无问题
  - 行 35：                strategy TEXT NOT NULL, → 无问题
  - 行 36：                approved INTEGER NOT NULL, → 无问题
  - 行 37：                reason TEXT NOT NULL, → 无问题
  - 行 38：                before_stop_loss_pct REAL NOT NULL, → 无问题
  - 行 39：                after_stop_loss_pct REAL NOT NULL, → 无问题
  - 行 40：                before_risk_multiplier REAL NOT NULL, → 无问题
  - 行 41：                after_risk_multiplier REAL NOT NULL, → 无问题
  - 行 42：                low_committee_approved INTEGER NOT NULL, → 无问题
  - 行 43：                ultra_wake_high INTEGER NOT NULL → 无问题
  - 行 44：            ) → 无问题
  - 行 45：            """ → 无问题
  - 行 46：        ) → 无问题
  - 行 47：        conn.execute( → 无问题
  - 行 48：            """ → 无问题
  - 行 49：            CREATE TABLE IF NOT EXISTS stoploss_override_state ( → 无问题
  - 行 50：                symbol TEXT PRIMARY KEY, → 无问题
  - 行 51：                used_at TEXT NOT NULL, → 无问题
  - 行 52：                expires_at TEXT NOT NULL → 无问题
  - 行 53：            ) → 无问题
  - 行 54：            """ → 无问题
  - 行 55：        ) → 无问题
  - 行 56：        columns = conn.execute("PRAGMA table_info(stoploss_override_state)").fetchall() → 无问题
  - 行 57：        column_names = {str(item[1]) for item in columns} → 无问题
  - 行 58：        if "expires_at" not in column_names: → 无问题
  - 行 59：            conn.execute("ALTER TABLE stoploss_override_state ADD COLUMN expires_at TEXT") → 无问题
  - 行 60：            conn.execute( → 无问题
  - 行 61：                """ → 无问题
  - 行 62：                UPDATE stoploss_override_state → 无问题
  - 行 63：                SET expires_at = datetime(used_at, '+72 hours') → 无问题
  - 行 64：                WHERE expires_at IS NULL OR expires_at = '' → 无问题
  - 行 65：                """ → 无问题
  - 行 66：            ) → 无问题
  - 行 67：        conn.commit() → 无问题
- 调用的外部函数：Path; path.parent.mkdir; sqlite3.connect; conn.execute; fetchall; conn.commit; str
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：write_parameter_audit（行 70-96）
- 功能：执行对应业务逻辑
- 参数：db_path: str, entry: ParameterAuditEntry
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 70：def write_parameter_audit(db_path: str, entry: ParameterAuditEntry) -> None: → 无问题
  - 行 71：    ensure_audit_db(db_path) → 无问题
  - 行 72：    with sqlite3.connect(db_path) as conn: → 无问题
  - 行 73：        conn.execute( → 无问题
  - 行 74：            """ → 无问题
  - 行 75：            INSERT INTO parameter_audit ( → 无问题
  - 行 76：                ts, symbol, strategy, approved, reason, → 无问题
  - 行 77：                before_stop_loss_pct, after_stop_loss_pct, → 无问题
  - 行 78：                before_risk_multiplier, after_risk_multiplier, → 无问题
  - 行 79：                low_committee_approved, ultra_wake_high → 无问题
  - 行 80：            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) → 无问题
  - 行 81：            """, → 无问题
  - 行 82：            ( → 无问题
  - 行 83：                entry.ts, → 无问题
  - 行 84：                entry.symbol, → 无问题
  - 行 85：                entry.strategy, → 无问题
  - 行 86：                1 if entry.approved else 0, → 无问题
  - 行 87：                entry.reason, → 无问题
  - 行 88：                entry.before_stop_loss_pct, → 无问题
  - 行 89：                entry.after_stop_loss_pct, → 无问题
  - 行 90：                entry.before_risk_multiplier, → 无问题
  - 行 91：                entry.after_risk_multiplier, → 无问题
  - 行 92：                1 if entry.low_committee_approved else 0, → 无问题
  - 行 93：                1 if entry.ultra_wake_high else 0, → 无问题
  - 行 94：            ), → 无问题
  - 行 95：        ) → 无问题
  - 行 96：        conn.commit() → 无问题
- 调用的外部函数：ensure_audit_db; sqlite3.connect; conn.execute; conn.commit
- 被谁调用：lanes/__init__.py:run_lane_cycle:144
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：list_recent_audits（行 99-131）
- 功能：执行对应业务逻辑
- 参数：db_path: str, limit: int
- 返回值：list[dict[str, Any]]（见函数语义）
- 逐行分析：
  - 行 99：def list_recent_audits(db_path: str, limit: int = 50) -> list[dict[str, Any]]: → 无问题
  - 行 100：    ensure_audit_db(db_path) → 无问题
  - 行 101：    with sqlite3.connect(db_path) as conn: → 无问题
  - 行 102：        rows = conn.execute( → 无问题
  - 行 103：            """ → 无问题
  - 行 104：            SELECT ts, symbol, strategy, approved, reason, → 无问题
  - 行 105：                   before_stop_loss_pct, after_stop_loss_pct, → 无问题
  - 行 106：                   before_risk_multiplier, after_risk_multiplier, → 无问题
  - 行 107：                   low_committee_approved, ultra_wake_high → 无问题
  - 行 108：            FROM parameter_audit → 无问题
  - 行 109：            ORDER BY ts DESC → 无问题
  - 行 110：            LIMIT ? → 无问题
  - 行 111：            """, → 无问题
  - 行 112：            (max(1, limit),), → 无问题
  - 行 113：        ).fetchall() → 无问题
  - 行 114：    items: list[dict[str, Any]] = [] → 无问题
  - 行 115：    for row in rows: → 无问题
  - 行 116：        items.append( → 无问题
  - 行 117：            { → 无问题
  - 行 118：                "ts": str(row[0]), → 无问题
  - 行 119：                "symbol": str(row[1]), → 无问题
  - 行 120：                "strategy": str(row[2]), → 无问题
  - 行 121：                "approved": bool(row[3]), → 无问题
  - 行 122：                "reason": str(row[4]), → 无问题
  - 行 123：                "before_stop_loss_pct": float(row[5]), → 无问题
  - 行 124：                "after_stop_loss_pct": float(row[6]), → 无问题
  - 行 125：                "before_risk_multiplier": float(row[7]), → 无问题
  - 行 126：                "after_risk_multiplier": float(row[8]), → 无问题
  - 行 127：                "low_committee_approved": bool(row[9]), → 无问题
  - 行 128：                "ultra_wake_high": bool(row[10]), → 无问题
  - 行 129：            } → 无问题
  - 行 130：        ) → 无问题
  - 行 131：    return items → 无问题
- 调用的外部函数：ensure_audit_db; sqlite3.connect; fetchall; items.append; conn.execute; str; bool; float; max
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：mark_stoploss_override_used（行 134-149）
- 功能：执行对应业务逻辑
- 参数：db_path: str, symbol: str, ttl_hours: int
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 134：def mark_stoploss_override_used(db_path: str, symbol: str, *, ttl_hours: int = 72) -> None: → 无问题
  - 行 135：    ensure_audit_db(db_path) → 无问题
  - 行 136：    now = datetime.now(tz=timezone.utc) → 无问题
  - 行 137：    expires_at = now + timedelta(hours=max(1, ttl_hours)) → 无问题
  - 行 138：    with sqlite3.connect(db_path) as conn: → 无问题
  - 行 139：        conn.execute( → 无问题
  - 行 140：            """ → 无问题
  - 行 141：            INSERT INTO stoploss_override_state(symbol, used_at, expires_at) → 无问题
  - 行 142：            VALUES (?, ?, ?) → 无问题
  - 行 143：            ON CONFLICT(symbol) DO UPDATE SET → 无问题
  - 行 144：                used_at=excluded.used_at, → 无问题
  - 行 145：                expires_at=excluded.expires_at → 无问题
  - 行 146：            """, → 无问题
  - 行 147：            (symbol.upper(), now.isoformat(), expires_at.isoformat()), → 无问题
  - 行 148：        ) → 无问题
  - 行 149：        conn.commit() → 无问题
- 调用的外部函数：ensure_audit_db; datetime.now; timedelta; sqlite3.connect; conn.execute; conn.commit; max; symbol.upper; now.isoformat; expires_at.isoformat
- 被谁调用：lanes/__init__.py:run_lane_cycle:139
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：is_stoploss_override_used（行 152-176）
- 功能：执行对应业务逻辑
- 参数：db_path: str, symbol: str
- 返回值：bool（见函数语义）
- 逐行分析：
  - 行 152：def is_stoploss_override_used(db_path: str, symbol: str) -> bool: → 问题（ID 12）
  - 行 153：    ensure_audit_db(db_path) → 问题（ID 12）
  - 行 154：    now = datetime.now(tz=timezone.utc) → 问题（ID 12）
  - 行 155：    with sqlite3.connect(db_path) as conn: → 问题（ID 12）
  - 行 156：        row = conn.execute( → 问题（ID 12）
  - 行 157：            """ → 问题（ID 12）
  - 行 158：            SELECT expires_at FROM stoploss_override_state WHERE symbol = ? → 问题（ID 12）
  - 行 159：            """, → 问题（ID 12）
  - 行 160：            (symbol.upper(),), → 问题（ID 12）
  - 行 161：        ).fetchone() → 问题（ID 12）
  - 行 162：        if row is None: → 问题（ID 12）
  - 行 163：            return False → 问题（ID 12）
  - 行 164：        expires_at = str(row[0] or "") → 问题（ID 12）
  - 行 165：        if expires_at: → 问题（ID 12）
  - 行 166：            try: → 问题（ID 12）
  - 行 167：                expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00")) → 问题（ID 12）
  - 行 168：                if expires_dt.tzinfo is None: → 问题（ID 12）
  - 行 169：                    expires_dt = expires_dt.replace(tzinfo=timezone.utc) → 问题（ID 12）
  - 行 170：                if expires_dt.astimezone(timezone.utc) > now: → 无问题
  - 行 171：                    return True → 无问题
  - 行 172：            except ValueError: → 无问题
  - 行 173：                pass → 无问题
  - 行 174：        conn.execute("DELETE FROM stoploss_override_state WHERE symbol = ?", (symbol.upper(),)) → 无问题
  - 行 175：        conn.commit() → 无问题
  - 行 176：    return False → 无问题
- 调用的外部函数：ensure_audit_db; datetime.now; sqlite3.connect; fetchone; str; conn.execute; conn.commit; datetime.fromisoformat; symbol.upper; expires_at.replace; expires_dt.replace; expires_dt.astimezone
- 被谁调用：lanes/__init__.py:run_lane_cycle:129; lanes/__init__.py:run_lane_cycle:193
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 12：stoploss 过期逻辑风险（中）

#### 函数：dump_audit_snapshot（行 179-180）
- 功能：执行对应业务逻辑
- 参数：db_path: str, limit: int
- 返回值：str（见函数语义）
- 逐行分析：
  - 行 179：def dump_audit_snapshot(db_path: str, limit: int = 20) -> str: → 无问题
  - 行 180：    return json.dumps({"rows": list_recent_audits(db_path, limit=limit)}, ensure_ascii=False) → 无问题
- 调用的外部函数：json.dumps; list_recent_audits
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| 152-169 | stoploss 过期逻辑风险 | 中 | 12 |

### 自检统计
- 实际逐行审计行数：180
- 函数审计数：6
- 发现问题数：1

## 文件：safety.py
- 总行数：35
- 函数/方法数：2

### 逐函数检查

#### 函数：__module__（行 1-22）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from dataclasses import dataclass → 无问题
  - 行 4：from enum import Enum → 无问题
  - 行 5： → 无问题
  - 行 6： → 无问题
  - 行 7：class SafetyMode(str, Enum): → 无问题
  - 行 8：    NORMAL = "normal" → 无问题
  - 行 9：    DEGRADED = "degraded" → 无问题
  - 行 10：    LOCKDOWN = "lockdown" → 无问题
  - 行 11： → 无问题
  - 行 12： → 无问题
  - 行 13：@dataclass(frozen=True) → 无问题
  - 行 14：class SafetyState: → 无问题
  - 行 15：    mode: SafetyMode → 无问题
  - 行 16：    reason: str → 无问题
  - 行 17： → 无问题
  - 行 18：    @property → 无问题
  - 行 21： → 无问题
  - 行 22： → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：SafetyState.allows_risk_execution（行 19-20）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：bool（见函数语义）
- 逐行分析：
  - 行 19：    def allows_risk_execution(self) -> bool: → 无问题
  - 行 20：        return self.mode == SafetyMode.NORMAL → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：assess_safety（行 23-35）
- 功能：执行对应业务逻辑
- 参数：ibkr_reachable: bool, llm_reachable: bool | None, max_drawdown_breached: bool
- 返回值：SafetyState（见函数语义）
- 逐行分析：
  - 行 23：def assess_safety( → 无问题
  - 行 24：    *, → 无问题
  - 行 25：    ibkr_reachable: bool, → 无问题
  - 行 26：    llm_reachable: bool | None = None, → 无问题
  - 行 27：    max_drawdown_breached: bool = False, → 无问题
  - 行 28：) -> SafetyState: → 无问题
  - 行 29：    if not ibkr_reachable: → 无问题
  - 行 30：        return SafetyState(mode=SafetyMode.LOCKDOWN, reason="IBKR_UNREACHABLE") → 无问题
  - 行 31：    if max_drawdown_breached: → 无问题
  - 行 32：        return SafetyState(mode=SafetyMode.LOCKDOWN, reason="MAX_DRAWDOWN_BREACHED") → 无问题
  - 行 33：    if llm_reachable is False: → 无问题
  - 行 34：        return SafetyState(mode=SafetyMode.DEGRADED, reason="LLM_UNREACHABLE") → 无问题
  - 行 35：    return SafetyState(mode=SafetyMode.NORMAL, reason="ALL_SYSTEMS_READY") → 无问题
- 调用的外部函数：SafetyState
- 被谁调用：tests/test_safety.py:SafetyTests.test_enters_lockdown_when_ibkr_unreachable:14; tests/test_safety.py:SafetyTests.test_enters_degraded_when_llm_unreachable:20; tests/test_safety.py:SafetyTests.test_enters_normal_when_dependencies_ready:26
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：35
- 函数审计数：2
- 发现问题数：0

## 文件：phase0_validation_report.py
- 总行数：227
- 函数/方法数：11

### 逐函数检查

#### 函数：__module__（行 1-227）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：import argparse → 无问题
  - 行 4：from datetime import datetime, timedelta, timezone → 无问题
  - 行 5：import json → 无问题
  - 行 6：import os → 无问题
  - 行 7：from pathlib import Path → 无问题
  - 行 8：import tempfile → 无问题
  - 行 9：from typing import Any → 无问题
  - 行 10： → 无问题
  - 行 11：from .ibkr_paper_check import PortStatus, ProbeConfig, run_probe → 无问题
  - 行 12：from .lanes.high import evaluate_event → 无问题
  - 行 13：from .replay import run_replay → 无问题
  - 行 14： → 无问题
  - 行 15： → 无问题
  - 行 29： → 无问题
  - 行 30： → 无问题
  - 行 56： → 无问题
  - 行 57： → 无问题
  - 行 87： → 无问题
  - 行 88： → 无问题
  - 行 89：class _ValidationProbeClient: → 无问题
  - 行 92： → 无问题
  - 行 102： → 无问题
  - 行 105： → 无问题
  - 行 106： → 无问题
  - 行 162： → 无问题
  - 行 163： → 无问题
  - 行 189： → 无问题
  - 行 190： → 无问题
  - 行 195： → 无问题
  - 行 196： → 无问题
  - 行 207： → 无问题
  - 行 208： → 无问题
  - 行 224： → 无问题
  - 行 225： → 无问题
  - 行 226：if __name__ == "__main__": → 无问题
  - 行 227：    raise SystemExit(main()) → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：_base_event（行 16-28）
- 功能：执行对应业务逻辑
- 参数：now: datetime
- 返回值：dict[str, str]（见函数语义）
- 逐行分析：
  - 行 16：def _base_event(now: datetime) -> dict[str, str]: → 无问题
  - 行 17：    return { → 无问题
  - 行 18：        "lane": "ultra", → 无问题
  - 行 19：        "kind": "signal", → 无问题
  - 行 20：        "symbol": "AAPL", → 无问题
  - 行 21：        "side": "buy", → 无问题
  - 行 22：        "entry_price": "100", → 无问题
  - 行 23：        "stop_loss_price": "95", → 无问题
  - 行 24：        "take_profit_price": "108", → 无问题
  - 行 25：        "equity": "100000", → 无问题
  - 行 26：        "current_exposure": "5000", → 无问题
  - 行 27：        "last_exit_at": (now - timedelta(days=3)).isoformat(), → 无问题
  - 行 28：    } → 无问题
- 调用的外部函数：isoformat; timedelta
- 被谁调用：replay.py:_breaking_news_event:30; replay.py:_high_volatility_event:42
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_hard_rule_checks（行 31-55）
- 功能：执行对应业务逻辑
- 参数：now: datetime
- 返回值：list[dict[str, Any]]（见函数语义）
- 逐行分析：
  - 行 31：def _hard_rule_checks(now: datetime) -> list[dict[str, Any]]: → 无问题
  - 行 32：    accepted = evaluate_event(_base_event(now)) → 无问题
  - 行 33：    cooldown_event = _base_event(now) → 无问题
  - 行 34：    cooldown_event["last_exit_at"] = (now - timedelta(hours=3)).isoformat() → 无问题
  - 行 35：    cooldown = evaluate_event(cooldown_event) → 无问题
  - 行 36：    exposure_event = _base_event(now) → 无问题
  - 行 37：    exposure_event["current_exposure"] = "30000" → 无问题
  - 行 38：    exposure = evaluate_event(exposure_event) → 无问题
  - 行 39：    return [ → 无问题
  - 行 40：        { → 无问题
  - 行 41：            "name": "single_trade_risk_1pct", → 无问题
  - 行 42：            "ok": accepted.get("status") == "accepted" and accepted.get("quantity", 0) <= 500, → 无问题
  - 行 43：            "detail": accepted, → 无问题
  - 行 44：        }, → 无问题
  - 行 45：        { → 无问题
  - 行 46：            "name": "cooldown_24h", → 无问题
  - 行 47：            "ok": cooldown.get("status") == "rejected" and "COOLDOWN_24H_ACTIVE" in cooldown.get("reject_reasons", []), → 无问题
  - 行 48：            "detail": cooldown, → 无问题
  - 行 49：        }, → 无问题
  - 行 50：        { → 无问题
  - 行 51：            "name": "total_exposure_30pct", → 无问题
  - 行 52：            "ok": exposure.get("status") == "rejected" and "TOTAL_EXPOSURE_LIMIT" in exposure.get("reject_reasons", []), → 无问题
  - 行 53：            "detail": exposure, → 无问题
  - 行 54：        }, → 无问题
  - 行 55：    ] → 无问题
- 调用的外部函数：evaluate_event; _base_event; isoformat; timedelta; accepted.get; cooldown.get; exposure.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_order_checks（行 58-86）
- 功能：执行对应业务逻辑
- 参数：now: datetime
- 返回值：list[dict[str, Any]]（见函数语义）
- 逐行分析：
  - 行 58：def _order_checks(now: datetime) -> list[dict[str, Any]]: → 无问题
  - 行 59：    decision = evaluate_event(_base_event(now)) → 无问题
  - 行 60：    bracket = decision.get("bracket_order", {}) → 无问题
  - 行 61：    parent = bracket.get("parent", {}) → 无问题
  - 行 62：    take_profit = bracket.get("take_profit", {}) → 无问题
  - 行 63：    stop_loss = bracket.get("stop_loss", {}) → 无问题
  - 行 64：    quantity = decision.get("quantity") → 无问题
  - 行 65：    return [ → 无问题
  - 行 66：        { → 无问题
  - 行 67：            "name": "bracket_required", → 无问题
  - 行 68：            "ok": decision.get("status") == "accepted" and bool(bracket), → 无问题
  - 行 69：            "detail": decision, → 无问题
  - 行 70：        }, → 无问题
  - 行 71：        { → 无问题
  - 行 72：            "name": "integer_quantity", → 无问题
  - 行 73：            "ok": isinstance(quantity, int) and quantity > 0, → 无问题
  - 行 74：            "detail": quantity, → 无问题
  - 行 75：        }, → 无问题
  - 行 76：        { → 无问题
  - 行 77：            "name": "order_legs_consistent", → 无问题
  - 行 78：            "ok": parent.get("quantity") == take_profit.get("quantity") == stop_loss.get("quantity") == quantity, → 无问题
  - 行 79：            "detail": bracket, → 无问题
  - 行 80：        }, → 无问题
  - 行 81：        { → 无问题
  - 行 82：            "name": "stop_takeprofit_present", → 无问题
  - 行 83：            "ok": stop_loss.get("order_type") == "STOP" and take_profit.get("order_type") == "LIMIT", → 无问题
  - 行 84：            "detail": {"take_profit": take_profit, "stop_loss": stop_loss}, → 无问题
  - 行 85：        }, → 无问题
  - 行 86：    ] → 无问题
- 调用的外部函数：evaluate_event; decision.get; bracket.get; _base_event; bool; isinstance; parent.get; take_profit.get; stop_loss.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_ValidationProbeClient.request_l1_snapshot（行 90-91）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 90：    def request_l1_snapshot(self, symbol: str) -> dict[str, Any]: → 无问题
  - 行 91：        return {"symbol": symbol.upper(), "bid": 188.1, "ask": 188.3, "last": 188.2, "timestamp": "2026-01-01T00:00:00Z"} → 无问题
- 调用的外部函数：symbol.upper
- 被谁调用：ibkr_paper_check.py:run_probe:310
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_ValidationProbeClient.request_news（行 93-101）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str, limit: int
- 返回值：list[dict[str, Any]]（见函数语义）
- 逐行分析：
  - 行 93：    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, Any]]: → 无问题
  - 行 94：        return [ → 无问题
  - 行 95：            { → 无问题
  - 行 96：                "headline": f"{symbol.upper()} validation headline", → 无问题
  - 行 97：                "provider_code": "BRFG", → 无问题
  - 行 98：                "article_id": "validation-1", → 无问题
  - 行 99：                "time": "2026-01-01T00:00:00Z", → 无问题
  - 行 100：            } → 无问题
  - 行 101：        ][:limit] → 无问题
- 调用的外部函数：symbol.upper
- 被谁调用：ibkr_paper_check.py:run_probe:312
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_ValidationProbeClient.close（行 103-104）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 103：    def close(self) -> None: → 无问题
  - 行 104：        return None → 无问题
- 调用的外部函数：无
- 被谁调用：ibkr_execution.py:execute_cycle:156
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_ibkr_validation（行 107-161）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：tuple[dict[str, Any], list[dict[str, Any]]]（见函数语义）
- 逐行分析：
  - 行 107：def _ibkr_validation() -> tuple[dict[str, Any], list[dict[str, Any]]]: → 问题（ID 11）
  - 行 108：    dynamic_probe = run_probe( → 问题（ID 11）
  - 行 109：        ProbeConfig(symbol="AAPL", timeout_seconds=0.8, news_limit=1, max_retries=1), → 问题（ID 11）
  - 行 110：    ) → 问题（ID 11）
  - 行 111：    probe = dynamic_probe → 问题（ID 11）
  - 行 112：    if not dynamic_probe.get("ok"): → 问题（ID 11）
  - 行 113：        probe = run_probe( → 问题（ID 11）
  - 行 114：            ProbeConfig(symbol="AAPL", timeout_seconds=0.5, news_limit=1, max_retries=1), → 问题（ID 11）
  - 行 115：            client_factory=lambda _: _ValidationProbeClient(), → 问题（ID 11）
  - 行 116：            port_checker=lambda host, port, timeout: PortStatus(ok=True, host=host, port=port, latency_ms=0.1, error=None), → 问题（ID 11）
  - 行 117：            fallback_fetcher=lambda symbol: {"ok": False, "source": "yfinance", "symbol": symbol.upper(), "error": "not-needed"}, → 问题（ID 11）
  - 行 118：        ) → 问题（ID 11）
  - 行 119：        probe["validation_mode"] = "fallback_sample" → 问题（ID 11）
  - 行 120：        probe["dynamic_probe_ok"] = False → 问题（ID 11）
  - 行 121：    else: → 问题（ID 11）
  - 行 122：        probe["validation_mode"] = "dynamic_live" → 问题（ID 11）
  - 行 123：        probe["dynamic_probe_ok"] = True → 问题（ID 11）
  - 行 124：    critical_steps = {item.get("step") for item in probe.get("critical_path_logs", [])} → 问题（ID 11）
  - 行 125：    checks = [ → 问题（ID 11）
  - 行 126：        { → 问题（ID 11）
  - 行 127：            "name": "dynamic_probe_attempted", → 问题（ID 11）
  - 行 128：            "ok": "port_7497" in dynamic_probe, → 问题（ID 11）
  - 行 129：            "detail": {"dynamic_ok": bool(dynamic_probe.get("ok")), "mode": probe.get("validation_mode")}, → 问题（ID 11）
  - 行 130：        }, → 问题（ID 11）
  - 行 131：        { → 问题（ID 11）
  - 行 132：            "name": "l1_news_probe_ok", → 问题（ID 11）
  - 行 133：            "ok": bool(probe.get("l1_market_data", {}).get("ok")) and len(probe.get("news", [])) > 0, → 问题（ID 11）
  - 行 134：            "detail": { → 问题（ID 11）
  - 行 135：                "l1_ok": probe.get("l1_market_data", {}).get("ok"), → 问题（ID 11）
  - 行 136：                "news_count": len(probe.get("news", [])), → 问题（ID 11）
  - 行 137：            }, → 问题（ID 11）
  - 行 138：        }, → 问题（ID 11）
  - 行 139：        { → 问题（ID 11）
  - 行 140：            "name": "pass_evidence_present", → 问题（ID 11）
  - 行 141：            "ok": bool(probe.get("pass_evidence", {}).get("l1_market_data", {}).get("ok")) → 问题（ID 11）
  - 行 142：            and bool(probe.get("pass_evidence", {}).get("news", {}).get("ok")), → 问题（ID 11）
  - 行 143：            "detail": probe.get("pass_evidence"), → 问题（ID 11）
  - 行 144：        }, → 问题（ID 11）
  - 行 145：        { → 问题（ID 11）
  - 行 146：            "name": "critical_path_logged", → 问题（ID 11）
  - 行 147：            "ok": {"port_probe", "ibkr_probe"}.issubset(critical_steps), → 问题（ID 11）
  - 行 148：            "detail": probe.get("critical_path_logs", []), → 问题（ID 11）
  - 行 149：        }, → 问题（ID 11）
  - 行 150：        { → 问题（ID 11）
  - 行 151：            "name": "retry_validation_recorded", → 问题（ID 11）
  - 行 152：            "ok": probe.get("retry_validation", {}).get("attempts", 0) >= 1, → 问题（ID 11）
  - 行 153：            "detail": probe.get("retry_validation", {}), → 问题（ID 11）
  - 行 154：        }, → 问题（ID 11）
  - 行 155：        { → 问题（ID 11）
  - 行 156：            "name": "no_error_alerts_on_success", → 问题（ID 11）
  - 行 157：            "ok": all(item.get("level") != "ERROR" for item in probe.get("alerts", [])), → 问题（ID 11）
  - 行 158：            "detail": probe.get("alerts", []), → 问题（ID 11）
  - 行 159：        }, → 问题（ID 11）
  - 行 160：    ] → 问题（ID 11）
  - 行 161：    return probe, checks → 问题（ID 11）
- 调用的外部函数：run_probe; ProbeConfig; dynamic_probe.get; item.get; probe.get; issubset; all; bool; get; len; _ValidationProbeClient; PortStatus; symbol.upper
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 11：验证样例固化风险（中）

#### 函数：generate_phase0_validation_report（行 164-188）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 164：def generate_phase0_validation_report() -> dict[str, Any]: → 无问题
  - 行 165：    now = datetime.now(tz=timezone.utc) → 无问题
  - 行 166：    replay = run_replay(mode="all") → 无问题
  - 行 167：    hard_rule_checks = _hard_rule_checks(now) → 无问题
  - 行 168：    order_checks = _order_checks(now) → 无问题
  - 行 169：    ibkr_probe, ibkr_checks = _ibkr_validation() → 无问题
  - 行 170：    all_checks = hard_rule_checks + order_checks + ibkr_checks → 无问题
  - 行 171：    passed_checks = sum(1 for check in all_checks if check["ok"]) → 无问题
  - 行 172：    report: dict[str, Any] = { → 无问题
  - 行 173：        "kind": "phase0_validation_report", → 无问题
  - 行 174：        "generated_at": now.isoformat(), → 无问题
  - 行 175：        "replay": replay, → 无问题
  - 行 176：        "ibkr_probe": ibkr_probe, → 无问题
  - 行 177：        "hard_rule_checks": hard_rule_checks, → 无问题
  - 行 178：        "order_checks": order_checks, → 无问题
  - 行 179：        "ibkr_validation_checks": ibkr_checks, → 无问题
  - 行 180：        "summary": { → 无问题
  - 行 181：            "replay_passed": replay["passed"], → 无问题
  - 行 182：            "replay_total": replay["total"], → 无问题
  - 行 183：            "checks_passed": passed_checks, → 无问题
  - 行 184：            "checks_total": len(all_checks), → 无问题
  - 行 185：        }, → 无问题
  - 行 186：    } → 无问题
  - 行 187：    report["ok"] = replay["passed"] == replay["total"] and passed_checks == len(all_checks) → 无问题
  - 行 188：    return report → 无问题
- 调用的外部函数：datetime.now; run_replay; _hard_rule_checks; _order_checks; _ibkr_validation; sum; now.isoformat; len
- 被谁调用：tests/test_phase0_validation_report.py:Phase0ValidationReportTests.test_generates_passed_report:14
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_parse_args（行 191-194）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：argparse.Namespace（见函数语义）
- 逐行分析：
  - 行 191：def _parse_args() -> argparse.Namespace: → 无问题
  - 行 192：    parser = argparse.ArgumentParser(prog="phase0-validation-report") → 无问题
  - 行 193：    parser.add_argument("--output", default="artifacts/phase0_validation_report.json") → 无问题
  - 行 194：    return parser.parse_args() → 无问题
- 调用的外部函数：argparse.ArgumentParser; parser.add_argument; parser.parse_args
- 被谁调用：ibkr_execution.py:main:295
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：main（行 197-206）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：int（见函数语义）
- 逐行分析：
  - 行 197：def main() -> int: → 无问题
  - 行 198：    args = _parse_args() → 无问题
  - 行 199：    report = generate_phase0_validation_report() → 无问题
  - 行 200：    output_path = Path(args.output) → 无问题
  - 行 201：    output_path.parent.mkdir(parents=True, exist_ok=True) → 无问题
  - 行 202：    _write_json_atomic(output_path, report) → 无问题
  - 行 203：    print(json.dumps({"ok": report["ok"], "output": str(output_path)}, ensure_ascii=False)) → 无问题
  - 行 204：    if report["ok"]: → 无问题
  - 行 205：        return 0 → 无问题
  - 行 206：    return 2 → 无问题
- 调用的外部函数：_parse_args; generate_phase0_validation_report; Path; output_path.parent.mkdir; _write_json_atomic; print; json.dumps; str
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_write_json_atomic（行 209-223）
- 功能：执行对应业务逻辑
- 参数：output_path: Path, payload: dict[str, Any]
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 209：def _write_json_atomic(output_path: Path, payload: dict[str, Any]) -> None: → 无问题
  - 行 210：    text = json.dumps(payload, ensure_ascii=False, indent=2) → 无问题
  - 行 211：    with tempfile.NamedTemporaryFile( → 无问题
  - 行 212：        mode="w", → 无问题
  - 行 213：        encoding="utf-8", → 无问题
  - 行 214：        dir=str(output_path.parent), → 无问题
  - 行 215：        prefix=f".{output_path.name}.", → 无问题
  - 行 216：        suffix=".tmp", → 无问题
  - 行 217：        delete=False, → 无问题
  - 行 218：    ) as tmp: → 无问题
  - 行 219：        tmp.write(text) → 无问题
  - 行 220：        tmp.flush() → 无问题
  - 行 221：        os.fsync(tmp.fileno()) → 无问题
  - 行 222：        temp_path = Path(tmp.name) → 无问题
  - 行 223：    temp_path.replace(output_path) → 无问题
- 调用的外部函数：json.dumps; temp_path.replace; tempfile.NamedTemporaryFile; tmp.write; tmp.flush; os.fsync; Path; tmp.fileno; str
- 被谁调用：non_ai_validation_report.py:main:204
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| 107-161 | 验证样例固化风险 | 中 | 11 |

### 自检统计
- 实际逐行审计行数：227
- 函数审计数：11
- 发现问题数：1

## 文件：non_ai_validation_report.py
- 总行数：229
- 函数/方法数：10

### 逐函数检查

#### 函数：__module__（行 1-229）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：import argparse → 无问题
  - 行 4：from datetime import datetime, timezone → 无问题
  - 行 5：import json → 无问题
  - 行 6：import os → 无问题
  - 行 7：from pathlib import Path → 无问题
  - 行 8：import subprocess → 无问题
  - 行 9：import tempfile → 无问题
  - 行 10：from typing import Any → 无问题
  - 行 11： → 无问题
  - 行 12：from .config import load_config → 无问题
  - 行 13：from .lanes import run_lane_cycle_with_guard → 无问题
  - 行 14： → 无问题
  - 行 15： → 无问题
  - 行 16：NON_AI_TEST_MODULES = [ → 无问题
  - 行 17：    "tests.test_config", → 无问题
  - 行 18：    "tests.test_runtime_budget", → 无问题
  - 行 19：    "tests.test_safety", → 无问题
  - 行 20：    "tests.test_high_lane", → 无问题
  - 行 21：    "tests.test_low_lane", → 无问题
  - 行 22：    "tests.test_strategies", → 无问题
  - 行 23：    "tests.test_lane_bus", → 无问题
  - 行 24：    "tests.test_app_health", → 无问题
  - 行 25：    "tests.test_ibkr_paper_check", → 无问题
  - 行 26：    "tests.test_replay", → 无问题
  - 行 27：    "tests.test_phase0_validation_report", → 无问题
  - 行 28：] → 无问题
  - 行 29： → 无问题
  - 行 30： → 无问题
  - 行 82： → 无问题
  - 行 83： → 无问题
  - 行 89： → 无问题
  - 行 90： → 无问题
  - 行 108： → 无问题
  - 行 109： → 无问题
  - 行 137： → 无问题
  - 行 138： → 无问题
  - 行 168： → 无问题
  - 行 169： → 无问题
  - 行 185： → 无问题
  - 行 186： → 无问题
  - 行 191： → 无问题
  - 行 192： → 无问题
  - 行 197： → 无问题
  - 行 198： → 无问题
  - 行 209： → 无问题
  - 行 210： → 无问题
  - 行 226： → 无问题
  - 行 227： → 无问题
  - 行 228：if __name__ == "__main__": → 无问题
  - 行 229：    raise SystemExit(main()) → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：generate_non_ai_validation_report（行 31-81）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 31：def generate_non_ai_validation_report() -> dict[str, Any]: → 无问题
  - 行 32：    env = os.environ.copy() → 无问题
  - 行 33：    env["AI_ENABLED"] = "false" → 无问题
  - 行 34：    now = datetime.now(tz=timezone.utc) → 无问题
  - 行 35：    checks = [ → 无问题
  - 行 36：        _run_command_check( → 无问题
  - 行 37：            name="unit_non_ai_suite", → 无问题
  - 行 38：            command=["python3", "-m", "unittest", "-q", *NON_AI_TEST_MODULES], → 无问题
  - 行 39：            env=env, → 无问题
  - 行 40：        ), → 无问题
  - 行 41：        _run_command_check( → 无问题
  - 行 42：            name="health_cli_non_ai", → 无问题
  - 行 43：            command=["python3", "-m", "phase0.main"], → 无问题
  - 行 44：            env=_with_pythonpath(env), → 无问题
  - 行 45：        ), → 无问题
  - 行 46：        _run_command_check( → 无问题
  - 行 47：            name="replay_non_ai", → 无问题
  - 行 48：            command=["python3", "-m", "phase0.replay", "--mode", "all"], → 无问题
  - 行 49：            env=_with_pythonpath(env), → 无问题
  - 行 50：        ), → 无问题
  - 行 51：        _run_command_check( → 无问题
  - 行 52：            name="validation_report_non_ai", → 无问题
  - 行 53：            command=[ → 无问题
  - 行 54：                "python3", → 无问题
  - 行 55：                "-m", → 无问题
  - 行 56：                "phase0.phase0_validation_report", → 无问题
  - 行 57：                "--output", → 无问题
  - 行 58：                "artifacts/phase0_validation_report.non_ai.latest.json", → 无问题
  - 行 59：            ], → 无问题
  - 行 60：            env=_with_pythonpath(env), → 无问题
  - 行 61：        ), → 无问题
  - 行 62：    ] → 无问题
  - 行 63：    functional = _functional_non_ai_checks() → 无问题
  - 行 64：    components = _build_component_status(checks, functional) → 无问题
  - 行 65：    potential_issues = [item for item in _build_potential_issues(checks, functional)] → 无问题
  - 行 66：    ok = all(item["ok"] for item in checks) and functional["ok"] → 无问题
  - 行 67：    return { → 无问题
  - 行 68：        "kind": "phase0_non_ai_validation_report", → 无问题
  - 行 69：        "generated_at": now.isoformat(), → 无问题
  - 行 70：        "mode": "non_ai_bypass", → 无问题
  - 行 71：        "checks": checks, → 无问题
  - 行 72：        "functional": functional, → 无问题
  - 行 73：        "components": components, → 无问题
  - 行 74：        "potential_issues": potential_issues, → 无问题
  - 行 75：        "summary": { → 无问题
  - 行 76：            "checks_passed": sum(1 for item in checks if item["ok"]), → 无问题
  - 行 77：            "checks_total": len(checks), → 无问题
  - 行 78：            "functional_ok": functional["ok"], → 无问题
  - 行 79：        }, → 无问题
  - 行 80：        "ok": ok, → 无问题
  - 行 81：    } → 无问题
- 调用的外部函数：os.environ.copy; datetime.now; _functional_non_ai_checks; _build_component_status; _run_command_check; all; now.isoformat; _build_potential_issues; sum; len; _with_pythonpath
- 被谁调用：tests/test_non_ai_validation_report.py:NonAIValidationReportTests.test_generates_non_ai_report:14
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_with_pythonpath（行 84-88）
- 功能：执行对应业务逻辑
- 参数：env: dict[str, str]
- 返回值：dict[str, str]（见函数语义）
- 逐行分析：
  - 行 84：def _with_pythonpath(env: dict[str, str]) -> dict[str, str]: → 无问题
  - 行 85：    enriched = dict(env) → 无问题
  - 行 86：    existing = enriched.get("PYTHONPATH", "") → 无问题
  - 行 87：    enriched["PYTHONPATH"] = f'src:{existing}' if existing else "src" → 无问题
  - 行 88：    return enriched → 无问题
- 调用的外部函数：dict; enriched.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_run_command_check（行 91-107）
- 功能：执行对应业务逻辑
- 参数：name: str, command: list[str], env: dict[str, str]
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 91：def _run_command_check(name: str, command: list[str], env: dict[str, str]) -> dict[str, Any]: → 无问题
  - 行 92：    result = subprocess.run( → 无问题
  - 行 93：        command, → 无问题
  - 行 94：        env=env, → 无问题
  - 行 95：        stdout=subprocess.PIPE, → 无问题
  - 行 96：        stderr=subprocess.PIPE, → 无问题
  - 行 97：        text=True, → 无问题
  - 行 98：        check=False, → 无问题
  - 行 99：    ) → 无问题
  - 行 100：    return { → 无问题
  - 行 101：        "name": name, → 无问题
  - 行 102：        "ok": result.returncode == 0, → 无问题
  - 行 103：        "returncode": result.returncode, → 无问题
  - 行 104：        "stdout_tail": _tail(result.stdout), → 无问题
  - 行 105：        "stderr_tail": _tail(result.stderr), → 无问题
  - 行 106：        "command": command, → 无问题
  - 行 107：    } → 无问题
- 调用的外部函数：subprocess.run; _tail
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_functional_non_ai_checks（行 110-136）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 110：def _functional_non_ai_checks() -> dict[str, Any]: → 无问题
  - 行 111：    previous = os.environ.get("AI_ENABLED") → 无问题
  - 行 112：    os.environ["AI_ENABLED"] = "false" → 无问题
  - 行 113：    try: → 无问题
  - 行 114：        config = load_config() → 无问题
  - 行 115：        lane = run_lane_cycle_with_guard("AAPL", config=config, allow_risk_execution=True) → 无问题
  - 行 116：    finally: → 无问题
  - 行 117：        if previous is None: → 无问题
  - 行 118：            os.environ.pop("AI_ENABLED", None) → 无问题
  - 行 119：        else: → 无问题
  - 行 120：            os.environ["AI_ENABLED"] = previous → 无问题
  - 行 121：    decision = lane["decisions"][0] if lane["decisions"] else {} → 无问题
  - 行 122：    checks = [ → 无问题
  - 行 123：        {"name": "ai_bypassed_flag", "ok": lane.get("ai_bypassed") is True}, → 无问题
  - 行 124：        {"name": "lane_decision_generated", "ok": bool(decision)}, → 无问题
  - 行 125：        {"name": "data_pipeline_kept", "ok": len(lane.get("watchlist", [])) > 0}, → 无问题
  - 行 126：        {"name": "error_handling_surface", "ok": isinstance(decision.get("reject_reasons", []), list)}, → 无问题
  - 行 127：    ] → 无问题
  - 行 128：    return { → 无问题
  - 行 129：        "ok": all(item["ok"] for item in checks), → 无问题
  - 行 130：        "checks": checks, → 无问题
  - 行 131：        "lane_snapshot": { → 无问题
  - 行 132：            "execution_status": decision.get("status"), → 无问题
  - 行 133：            "watchlist_size": len(lane.get("watchlist", [])), → 无问题
  - 行 134：            "published_events": lane.get("published_events", 0), → 无问题
  - 行 135：        }, → 无问题
  - 行 136：    } → 无问题
- 调用的外部函数：os.environ.get; load_config; run_lane_cycle_with_guard; all; os.environ.pop; bool; isinstance; decision.get; len; lane.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_build_component_status（行 139-167）
- 功能：执行对应业务逻辑
- 参数：command_checks: list[dict[str, Any]], functional: dict[str, Any]
- 返回值：list[dict[str, Any]]（见函数语义）
- 逐行分析：
  - 行 139：def _build_component_status(command_checks: list[dict[str, Any]], functional: dict[str, Any]) -> list[dict[str, Any]]: → 无问题
  - 行 140：    status_map = {item["name"]: item["ok"] for item in command_checks} → 无问题
  - 行 141：    fchecks = {item["name"]: item["ok"] for item in functional["checks"]} → 无问题
  - 行 142：    return [ → 无问题
  - 行 143：        { → 无问题
  - 行 144：            "component": "data_input", → 无问题
  - 行 145：            "ok": status_map.get("unit_non_ai_suite", False) and fchecks.get("data_pipeline_kept", False), → 无问题
  - 行 146：        }, → 无问题
  - 行 147：        { → 无问题
  - 行 148：            "component": "data_preprocessing", → 无问题
  - 行 149：            "ok": status_map.get("unit_non_ai_suite", False), → 无问题
  - 行 150：        }, → 无问题
  - 行 151：        { → 无问题
  - 行 152：            "component": "data_transport", → 无问题
  - 行 153：            "ok": status_map.get("replay_non_ai", False) and fchecks.get("lane_decision_generated", False), → 无问题
  - 行 154：        }, → 无问题
  - 行 155：        { → 无问题
  - 行 156：            "component": "storage", → 无问题
  - 行 157：            "ok": status_map.get("validation_report_non_ai", False), → 无问题
  - 行 158：        }, → 无问题
  - 行 159：        { → 无问题
  - 行 160：            "component": "user_interface", → 无问题
  - 行 161：            "ok": status_map.get("health_cli_non_ai", False), → 无问题
  - 行 162：        }, → 无问题
  - 行 163：        { → 无问题
  - 行 164：            "component": "error_handling", → 无问题
  - 行 165：            "ok": fchecks.get("error_handling_surface", False), → 无问题
  - 行 166：        }, → 无问题
  - 行 167：    ] → 无问题
- 调用的外部函数：status_map.get; fchecks.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_build_potential_issues（行 170-184）
- 功能：执行对应业务逻辑
- 参数：command_checks: list[dict[str, Any]], functional: dict[str, Any]
- 返回值：list[dict[str, str]]（见函数语义）
- 逐行分析：
  - 行 170：def _build_potential_issues(command_checks: list[dict[str, Any]], functional: dict[str, Any]) -> list[dict[str, str]]: → 无问题
  - 行 171：    for item in command_checks: → 无问题
  - 行 172：        if not item["ok"]: → 无问题
  - 行 173：            yield { → 无问题
  - 行 174：                "source": item["name"], → 无问题
  - 行 175：                "problem": "command_failed", → 无问题
  - 行 176：                "hint": (item.get("stderr_tail") or item.get("stdout_tail") or "unknown_error")[:200], → 无问题
  - 行 177：            } → 无问题
  - 行 178：    for item in functional["checks"]: → 无问题
  - 行 179：        if not item["ok"]: → 无问题
  - 行 180：            yield { → 无问题
  - 行 181：                "source": "functional_non_ai", → 无问题
  - 行 182：                "problem": item["name"], → 无问题
  - 行 183：                "hint": "需要检查非AI模式旁路链路是否保持完整", → 无问题
  - 行 184：            } → 无问题
- 调用的外部函数：item.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_tail（行 187-190）
- 功能：执行对应业务逻辑
- 参数：text: str, limit: int
- 返回值：str（见函数语义）
- 逐行分析：
  - 行 187：def _tail(text: str, limit: int = 1200) -> str: → 无问题
  - 行 188：    if len(text) <= limit: → 无问题
  - 行 189：        return text → 无问题
  - 行 190：    return text[-limit:] → 无问题
- 调用的外部函数：len
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_parse_args（行 193-196）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：argparse.Namespace（见函数语义）
- 逐行分析：
  - 行 193：def _parse_args() -> argparse.Namespace: → 无问题
  - 行 194：    parser = argparse.ArgumentParser(prog="phase0-non-ai-validation-report") → 无问题
  - 行 195：    parser.add_argument("--output", default="artifacts/phase0_non_ai_validation_report.json") → 无问题
  - 行 196：    return parser.parse_args() → 无问题
- 调用的外部函数：argparse.ArgumentParser; parser.add_argument; parser.parse_args
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：main（行 199-208）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：int（见函数语义）
- 逐行分析：
  - 行 199：def main() -> int: → 无问题
  - 行 200：    args = _parse_args() → 无问题
  - 行 201：    report = generate_non_ai_validation_report() → 无问题
  - 行 202：    output_path = Path(args.output) → 无问题
  - 行 203：    output_path.parent.mkdir(parents=True, exist_ok=True) → 无问题
  - 行 204：    _write_json_atomic(output_path, report) → 无问题
  - 行 205：    print(json.dumps({"ok": report["ok"], "output": str(output_path)}, ensure_ascii=False)) → 无问题
  - 行 206：    if report["ok"]: → 无问题
  - 行 207：        return 0 → 无问题
  - 行 208：    return 2 → 无问题
- 调用的外部函数：_parse_args; generate_non_ai_validation_report; Path; output_path.parent.mkdir; _write_json_atomic; print; json.dumps; str
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_write_json_atomic（行 211-225）
- 功能：执行对应业务逻辑
- 参数：output_path: Path, payload: dict[str, Any]
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 211：def _write_json_atomic(output_path: Path, payload: dict[str, Any]) -> None: → 无问题
  - 行 212：    text = json.dumps(payload, ensure_ascii=False, indent=2) → 无问题
  - 行 213：    with tempfile.NamedTemporaryFile( → 无问题
  - 行 214：        mode="w", → 无问题
  - 行 215：        encoding="utf-8", → 无问题
  - 行 216：        dir=str(output_path.parent), → 无问题
  - 行 217：        prefix=f".{output_path.name}.", → 无问题
  - 行 218：        suffix=".tmp", → 无问题
  - 行 219：        delete=False, → 无问题
  - 行 220：    ) as tmp: → 无问题
  - 行 221：        tmp.write(text) → 无问题
  - 行 222：        tmp.flush() → 无问题
  - 行 223：        os.fsync(tmp.fileno()) → 无问题
  - 行 224：        temp_path = Path(tmp.name) → 无问题
  - 行 225：    temp_path.replace(output_path) → 无问题
- 调用的外部函数：json.dumps; temp_path.replace; tempfile.NamedTemporaryFile; tmp.write; tmp.flush; os.fsync; Path; tmp.fileno; str
- 被谁调用：phase0_validation_report.py:main:202
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：229
- 函数审计数：10
- 发现问题数：0

## 文件：main.py
- 总行数：40
- 函数/方法数：1

### 逐函数检查

#### 函数：__module__（行 1-40）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：import json → 无问题
  - 行 4：import logging → 无问题
  - 行 5：import sys → 无问题
  - 行 6：import time → 无问题
  - 行 7： → 无问题
  - 行 8：from .app import config_snapshot, health_check → 无问题
  - 行 9：from .config import load_config → 无问题
  - 行 10：from .errors import AppError, ErrorCode → 无问题
  - 行 11：from .logger import setup_logging → 无问题
  - 行 12： → 无问题
  - 行 13： → 无问题
  - 行 14：logger = logging.getLogger(__name__) → 无问题
  - 行 15： → 无问题
  - 行 16： → 无问题
  - 行 37： → 无问题
  - 行 38： → 无问题
  - 行 39：if __name__ == "__main__": → 无问题
  - 行 40：    sys.exit(main()) → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：main（行 17-36）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：int（见函数语义）
- 逐行分析：
  - 行 17：def main() -> int: → 无问题
  - 行 18：    try: → 无问题
  - 行 19：        config = load_config() → 无问题
  - 行 20：        setup_logging(config.log_level) → 无问题
  - 行 21：        logger.info("phase0 bootstrap ready") → 无问题
  - 行 22：        logger.info(json.dumps({"config": config_snapshot(config)}, ensure_ascii=False)) → 无问题
  - 行 23：        cycles = max(1, config.lane_scheduler_cycles if config.lane_scheduler_enabled else 1) → 问题（ID 8）
  - 行 24：        status: dict[str, str] = {} → 问题（ID 8）
  - 行 25：        for index in range(cycles): → 问题（ID 8）
  - 行 26：            status = health_check(config) → 问题（ID 8）
  - 行 27：            logger.info(json.dumps({"health": status, "cycle": index + 1, "cycles": cycles}, ensure_ascii=False)) → 问题（ID 8）
  - 行 28：            if index + 1 < cycles: → 问题（ID 8）
  - 行 29：                time.sleep(max(1, config.lane_rebalance_interval_seconds)) → 问题（ID 8）
  - 行 30：        return 0 → 问题（ID 8）
  - 行 31：    except AppError as exc: → 无问题
  - 行 32：        logger.error(exc.message, extra={"error_code": exc.code.value}) → 无问题
  - 行 33：        return 2 → 无问题
  - 行 34：    except Exception as exc: → 无问题
  - 行 35：        logger.exception(str(exc), extra={"error_code": ErrorCode.INTERNAL_ERROR.value}) → 无问题
  - 行 36：        return 1 → 无问题
- 调用的外部函数：load_config; setup_logging; logger.info; max; range; json.dumps; health_check; logger.error; logger.exception; time.sleep; str; config_snapshot
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：ID 8：缺少周期调度保障（中）

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| 23-30 | 缺少周期调度保障 | 中 | 8 |

### 自检统计
- 实际逐行审计行数：40
- 函数审计数：1
- 发现问题数：1

## 文件：config.py
- 总行数：270
- 函数/方法数：4

### 逐函数检查

#### 函数：__module__（行 1-258）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from dataclasses import dataclass → 无问题
  - 行 4：from enum import Enum → 无问题
  - 行 5：import os → 无问题
  - 行 6： → 无问题
  - 行 7：from .errors import AppError, ErrorCode → 无问题
  - 行 8： → 无问题
  - 行 9： → 无问题
  - 行 10：class RuntimeProfile(str, Enum): → 无问题
  - 行 11：    PAPER = "paper" → 无问题
  - 行 12：    LOCAL = "local" → 无问题
  - 行 13：    CLOUD = "cloud" → 无问题
  - 行 14： → 无问题
  - 行 15： → 无问题
  - 行 16：class RuntimeMode(str, Enum): → 无问题
  - 行 17：    NORMAL = "normal" → 无问题
  - 行 18：    ECO = "eco" → 无问题
  - 行 19：    PERF = "perf" → 无问题
  - 行 20： → 无问题
  - 行 21： → 无问题
  - 行 22：@dataclass(frozen=True) → 无问题
  - 行 23：class AppConfig: → 无问题
  - 行 24：    runtime_profile: RuntimeProfile → 无问题
  - 行 25：    runtime_mode: RuntimeMode → 无问题
  - 行 26：    log_level: str → 无问题
  - 行 27：    ibkr_host: str → 无问题
  - 行 28：    ibkr_port: int → 无问题
  - 行 29：    llm_base_url: str → 无问题
  - 行 30：    llm_api_key: str → 无问题
  - 行 31：    llm_local_model: str → 无问题
  - 行 32：    llm_cloud_model: str → 无问题
  - 行 33：    llm_timeout_seconds: float → 无问题
  - 行 34：    llm_max_retries: int → 无问题
  - 行 35：    llm_backoff_seconds: float → 无问题
  - 行 36：    llm_rate_limit_per_second: float → 无问题
  - 行 37：    risk_single_trade_pct: float → 无问题
  - 行 38：    risk_total_exposure_pct: float → 无问题
  - 行 39：    risk_stop_loss_min_pct: float → 无问题
  - 行 40：    risk_stop_loss_max_pct: float → 无问题
  - 行 41：    risk_max_drawdown_pct: float → 无问题
  - 行 42：    risk_min_trade_units: int → 无问题
  - 行 43：    risk_slippage_bps: float → 无问题
  - 行 44：    risk_commission_per_share: float → 无问题
  - 行 45：    risk_exposure_softmax_temperature: float → 无问题
  - 行 46：    cooldown_hours: int → 无问题
  - 行 47：    holding_days: int → 无问题
  - 行 48：    lane_bus_dedup_ttl_seconds: int → 无问题
  - 行 49：    strategy_enabled_list: str → 无问题
  - 行 50：    strategy_rotation_top_k: int → 无问题
  - 行 51：    strategy_news_positive_threshold: float → 无问题
  - 行 52：    strategy_news_negative_threshold: float → 无问题
  - 行 53：    strategy_plugin_modules: str → 无问题
  - 行 54：    factor_plugin_modules: str → 无问题
  - 行 55：    high_risk_multiplier_min: float → 无问题
  - 行 56：    high_risk_multiplier_max: float → 无问题
  - 行 57：    high_take_profit_boost_max_pct: float → 无问题
  - 行 58：    ai_message_max_age_minutes: int → 无问题
  - 行 59：    ai_low_committee_models: str → 无问题
  - 行 60：    ai_low_committee_min_support: int → 无问题
  - 行 61：    ai_high_mode: str → 无问题
  - 行 62：    ai_high_committee_models: str → 无问题
  - 行 63：    ai_high_committee_min_support: int → 无问题
  - 行 64：    ai_high_confidence_gate: float → 无问题
  - 行 65：    ai_stop_loss_default_pct: float → 无问题
  - 行 66：    ai_stop_loss_break_max_pct: float → 无问题
  - 行 67：    ai_stoploss_override_ttl_hours: int → 无问题
  - 行 68：    ai_state_db_path: str → 无问题
  - 行 69：    ai_memory_db_path: str → 无问题
  - 行 70：    ai_enabled: bool → 无问题
  - 行 71：    discipline_min_actions_per_day: int → 无问题
  - 行 72：    discipline_hold_score_threshold: float → 无问题
  - 行 73：    discipline_enable_daily_cycle: bool → 无问题
  - 行 74：    market_data_mode: str → 无问题
  - 行 75：    market_symbols: str → 无问题
  - 行 76：    market_snapshot_json: str → 无问题
  - 行 77：    lane_scheduler_enabled: bool → 无问题
  - 行 78：    lane_rebalance_interval_seconds: int → 无问题
  - 行 79：    lane_scheduler_cycles: int → 无问题
  - 行 80：    execution_session_guard_enabled: bool → 无问题
  - 行 81：    execution_session_start_utc: str → 无问题
  - 行 82：    execution_session_end_utc: str → 无问题
  - 行 83：    execution_good_after_seconds: int → 无问题
  - 行 84： → 无问题
  - 行 85： → 无问题
  - 行 235： → 无问题
  - 行 236： → 无问题
  - 行 246： → 无问题
  - 行 247： → 无问题
  - 行 257： → 无问题
  - 行 258： → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：load_config（行 86-234）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：AppConfig（见函数语义）
- 逐行分析：
  - 行 86：def load_config() -> AppConfig: → 无问题
  - 行 87：    profile_raw = os.getenv("PHASE0_PROFILE", RuntimeProfile.PAPER.value).lower() → 无问题
  - 行 88：    try: → 无问题
  - 行 89：        runtime_profile = RuntimeProfile(profile_raw) → 无问题
  - 行 90：    except ValueError as exc: → 无问题
  - 行 91：        raise AppError( → 无问题
  - 行 92：            code=ErrorCode.CONFIG_INVALID_PROFILE, → 无问题
  - 行 93：            message=f"unsupported runtime profile: {profile_raw}", → 无问题
  - 行 94：        ) from exc → 无问题
  - 行 95： → 无问题
  - 行 96：    mode_raw = os.getenv("RUNTIME_MODE", RuntimeMode.NORMAL.value).lower() → 无问题
  - 行 97：    try: → 无问题
  - 行 98：        runtime_mode = RuntimeMode(mode_raw) → 无问题
  - 行 99：    except ValueError as exc: → 无问题
  - 行 100：        raise AppError( → 无问题
  - 行 101：            code=ErrorCode.CONFIG_INVALID_VALUE, → 无问题
  - 行 102：            message=f"unsupported runtime mode: {mode_raw}", → 无问题
  - 行 103：        ) from exc → 无问题
  - 行 104： → 无问题
  - 行 105：    ibkr_host = os.getenv("IBKR_HOST", "127.0.0.1") → 无问题
  - 行 106：    ibkr_port = _read_int_env("IBKR_PORT", 7497) → 无问题
  - 行 107：    llm_base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1") → 无问题
  - 行 108：    llm_api_key = os.getenv("LLM_API_KEY", "dummy") → 无问题
  - 行 109：    llm_local_model = os.getenv("LLM_LOCAL_MODEL", "llama3.1:8b") → 无问题
  - 行 110：    llm_cloud_model = os.getenv("LLM_CLOUD_MODEL", "gpt-4o-mini") → 无问题
  - 行 111：    llm_timeout_seconds = _read_float_env("LLM_TIMEOUT_SECONDS", 20.0) → 无问题
  - 行 112：    llm_max_retries = _read_int_env("LLM_MAX_RETRIES", 3) → 无问题
  - 行 113：    llm_backoff_seconds = _read_float_env("LLM_BACKOFF_SECONDS", 0.5) → 无问题
  - 行 114：    llm_rate_limit_per_second = _read_float_env("LLM_RATE_LIMIT_PER_SECOND", 2.0) → 无问题
  - 行 115：    risk_single_trade_pct = _read_float_env("RISK_SINGLE_TRADE_PCT", 0.01) → 无问题
  - 行 116：    risk_total_exposure_pct = _read_float_env("RISK_TOTAL_EXPOSURE_PCT", 0.30) → 无问题
  - 行 117：    risk_stop_loss_min_pct = _read_float_env("RISK_STOP_LOSS_MIN_PCT", 0.05) → 无问题
  - 行 118：    risk_stop_loss_max_pct = _read_float_env("RISK_STOP_LOSS_MAX_PCT", 0.08) → 无问题
  - 行 119：    risk_max_drawdown_pct = _read_float_env("RISK_MAX_DRAWDOWN_PCT", 0.12) → 无问题
  - 行 120：    risk_min_trade_units = _read_int_env("RISK_MIN_TRADE_UNITS", 1) → 无问题
  - 行 121：    risk_slippage_bps = _read_float_env("RISK_SLIPPAGE_BPS", 2.0) → 无问题
  - 行 122：    risk_commission_per_share = _read_float_env("RISK_COMMISSION_PER_SHARE", 0.005) → 无问题
  - 行 123：    risk_exposure_softmax_temperature = _read_float_env("RISK_EXPOSURE_SOFTMAX_TEMPERATURE", 1.0) → 无问题
  - 行 124：    cooldown_hours = _read_int_env("RISK_COOLDOWN_HOURS", 24) → 无问题
  - 行 125：    holding_days = _read_int_env("RISK_HOLDING_DAYS", 2) → 无问题
  - 行 126：    lane_bus_dedup_ttl_seconds = _read_int_env("LANE_BUS_DEDUP_TTL_SECONDS", 300) → 无问题
  - 行 127：    strategy_enabled_list = os.getenv( → 无问题
  - 行 128：        "STRATEGY_ENABLED_LIST", → 无问题
  - 行 129：        "momentum,mean_reversion,sector_rotation,news_sentiment", → 无问题
  - 行 130：    ) → 无问题
  - 行 131：    strategy_rotation_top_k = _read_int_env("STRATEGY_ROTATION_TOP_K", 3) → 无问题
  - 行 132：    strategy_news_positive_threshold = _read_float_env("STRATEGY_NEWS_POSITIVE_THRESHOLD", 0.2) → 无问题
  - 行 133：    strategy_news_negative_threshold = _read_float_env("STRATEGY_NEWS_NEGATIVE_THRESHOLD", -0.2) → 无问题
  - 行 134：    strategy_plugin_modules = os.getenv("STRATEGY_PLUGIN_MODULES", "") → 无问题
  - 行 135：    factor_plugin_modules = os.getenv("FACTOR_PLUGIN_MODULES", "") → 无问题
  - 行 136：    high_risk_multiplier_min = _read_float_env("HIGH_RISK_MULTIPLIER_MIN", 0.5) → 无问题
  - 行 137：    high_risk_multiplier_max = _read_float_env("HIGH_RISK_MULTIPLIER_MAX", 1.5) → 无问题
  - 行 138：    high_take_profit_boost_max_pct = _read_float_env("HIGH_TAKE_PROFIT_BOOST_MAX_PCT", 0.2) → 无问题
  - 行 139：    ai_message_max_age_minutes = _read_int_env("AI_MESSAGE_MAX_AGE_MINUTES", 180) → 无问题
  - 行 140：    ai_low_committee_models = os.getenv( → 无问题
  - 行 141：        "AI_LOW_COMMITTEE_MODELS", → 无问题
  - 行 142：        "gpt-4o-mini,claude-3-5-sonnet,gemini-2.0-flash", → 无问题
  - 行 143：    ) → 无问题
  - 行 144：    ai_low_committee_min_support = _read_int_env("AI_LOW_COMMITTEE_MIN_SUPPORT", 2) → 无问题
  - 行 145：    ai_high_mode = os.getenv("AI_HIGH_MODE", "local").strip().lower() → 无问题
  - 行 146：    ai_high_committee_models = os.getenv( → 无问题
  - 行 147：        "AI_HIGH_COMMITTEE_MODELS", → 无问题
  - 行 148：        "local-risk-v1,gpt-4o-mini", → 无问题
  - 行 149：    ) → 无问题
  - 行 150：    ai_high_committee_min_support = _read_int_env("AI_HIGH_COMMITTEE_MIN_SUPPORT", 1) → 无问题
  - 行 151：    ai_high_confidence_gate = _read_float_env("AI_HIGH_CONFIDENCE_GATE", 0.58) → 无问题
  - 行 152：    ai_stop_loss_default_pct = _read_float_env("AI_STOP_LOSS_DEFAULT_PCT", 0.05) → 无问题
  - 行 153：    ai_stop_loss_break_max_pct = _read_float_env("AI_STOP_LOSS_BREAK_MAX_PCT", 0.08) → 无问题
  - 行 154：    ai_stoploss_override_ttl_hours = _read_int_env("AI_STOPLOSS_OVERRIDE_TTL_HOURS", 72) → 无问题
  - 行 155：    ai_state_db_path = os.getenv("AI_STATE_DB_PATH", "artifacts/phase0_state.db") → 无问题
  - 行 156：    ai_memory_db_path = os.getenv("AI_MEMORY_DB_PATH", "artifacts/phase0_memory.db") → 无问题
  - 行 157：    ai_enabled = _read_bool_env("AI_ENABLED", True) → 无问题
  - 行 158：    discipline_min_actions_per_day = _read_int_env("DISCIPLINE_MIN_ACTIONS_PER_DAY", 1) → 无问题
  - 行 159：    discipline_hold_score_threshold = _read_float_env("DISCIPLINE_HOLD_SCORE_THRESHOLD", 0.72) → 无问题
  - 行 160：    discipline_enable_daily_cycle = _read_bool_env("DISCIPLINE_ENABLE_DAILY_CYCLE", True) → 无问题
  - 行 161：    market_data_mode = os.getenv("MARKET_DATA_MODE", "default").strip().lower() → 无问题
  - 行 162：    market_symbols = os.getenv("MARKET_SYMBOLS", "AAPL,MSFT,NVDA,XOM") → 无问题
  - 行 163：    market_snapshot_json = os.getenv("MARKET_SNAPSHOT_JSON", "") → 无问题
  - 行 164：    lane_scheduler_enabled = _read_bool_env("LANE_SCHEDULER_ENABLED", False) → 无问题
  - 行 165：    lane_rebalance_interval_seconds = _read_int_env("LANE_REBALANCE_INTERVAL_SECONDS", 60) → 无问题
  - 行 166：    lane_scheduler_cycles = _read_int_env("LANE_SCHEDULER_CYCLES", 1) → 无问题
  - 行 167：    execution_session_guard_enabled = _read_bool_env("EXECUTION_SESSION_GUARD_ENABLED", True) → 无问题
  - 行 168：    execution_session_start_utc = os.getenv("EXECUTION_SESSION_START_UTC", "13:30") → 无问题
  - 行 169：    execution_session_end_utc = os.getenv("EXECUTION_SESSION_END_UTC", "20:00") → 无问题
  - 行 170：    execution_good_after_seconds = _read_int_env("EXECUTION_GOOD_AFTER_SECONDS", 5) → 无问题
  - 行 171：    log_level = os.getenv("LOG_LEVEL", "INFO").upper() → 无问题
  - 行 172： → 无问题
  - 行 173：    return AppConfig( → 无问题
  - 行 174：        runtime_profile=runtime_profile, → 无问题
  - 行 175：        runtime_mode=runtime_mode, → 无问题
  - 行 176：        log_level=log_level, → 无问题
  - 行 177：        ibkr_host=ibkr_host, → 无问题
  - 行 178：        ibkr_port=ibkr_port, → 无问题
  - 行 179：        llm_base_url=llm_base_url, → 无问题
  - 行 180：        llm_api_key=llm_api_key, → 无问题
  - 行 181：        llm_local_model=llm_local_model, → 无问题
  - 行 182：        llm_cloud_model=llm_cloud_model, → 无问题
  - 行 183：        llm_timeout_seconds=llm_timeout_seconds, → 无问题
  - 行 184：        llm_max_retries=llm_max_retries, → 无问题
  - 行 185：        llm_backoff_seconds=llm_backoff_seconds, → 无问题
  - 行 186：        llm_rate_limit_per_second=llm_rate_limit_per_second, → 无问题
  - 行 187：        risk_single_trade_pct=risk_single_trade_pct, → 无问题
  - 行 188：        risk_total_exposure_pct=risk_total_exposure_pct, → 无问题
  - 行 189：        risk_stop_loss_min_pct=risk_stop_loss_min_pct, → 无问题
  - 行 190：        risk_stop_loss_max_pct=risk_stop_loss_max_pct, → 无问题
  - 行 191：        risk_max_drawdown_pct=risk_max_drawdown_pct, → 无问题
  - 行 192：        risk_min_trade_units=risk_min_trade_units, → 无问题
  - 行 193：        risk_slippage_bps=risk_slippage_bps, → 无问题
  - 行 194：        risk_commission_per_share=risk_commission_per_share, → 无问题
  - 行 195：        risk_exposure_softmax_temperature=risk_exposure_softmax_temperature, → 无问题
  - 行 196：        cooldown_hours=cooldown_hours, → 无问题
  - 行 197：        holding_days=holding_days, → 无问题
  - 行 198：        lane_bus_dedup_ttl_seconds=lane_bus_dedup_ttl_seconds, → 无问题
  - 行 199：        strategy_enabled_list=strategy_enabled_list, → 无问题
  - 行 200：        strategy_rotation_top_k=strategy_rotation_top_k, → 无问题
  - 行 201：        strategy_news_positive_threshold=strategy_news_positive_threshold, → 无问题
  - 行 202：        strategy_news_negative_threshold=strategy_news_negative_threshold, → 无问题
  - 行 203：        strategy_plugin_modules=strategy_plugin_modules, → 无问题
  - 行 204：        factor_plugin_modules=factor_plugin_modules, → 无问题
  - 行 205：        high_risk_multiplier_min=high_risk_multiplier_min, → 无问题
  - 行 206：        high_risk_multiplier_max=high_risk_multiplier_max, → 无问题
  - 行 207：        high_take_profit_boost_max_pct=high_take_profit_boost_max_pct, → 无问题
  - 行 208：        ai_message_max_age_minutes=ai_message_max_age_minutes, → 无问题
  - 行 209：        ai_low_committee_models=ai_low_committee_models, → 无问题
  - 行 210：        ai_low_committee_min_support=ai_low_committee_min_support, → 无问题
  - 行 211：        ai_high_mode=ai_high_mode, → 无问题
  - 行 212：        ai_high_committee_models=ai_high_committee_models, → 无问题
  - 行 213：        ai_high_committee_min_support=ai_high_committee_min_support, → 无问题
  - 行 214：        ai_high_confidence_gate=ai_high_confidence_gate, → 无问题
  - 行 215：        ai_stop_loss_default_pct=ai_stop_loss_default_pct, → 无问题
  - 行 216：        ai_stop_loss_break_max_pct=ai_stop_loss_break_max_pct, → 无问题
  - 行 217：        ai_stoploss_override_ttl_hours=ai_stoploss_override_ttl_hours, → 无问题
  - 行 218：        ai_state_db_path=ai_state_db_path, → 无问题
  - 行 219：        ai_memory_db_path=ai_memory_db_path, → 无问题
  - 行 220：        ai_enabled=ai_enabled, → 无问题
  - 行 221：        discipline_min_actions_per_day=discipline_min_actions_per_day, → 无问题
  - 行 222：        discipline_hold_score_threshold=discipline_hold_score_threshold, → 无问题
  - 行 223：        discipline_enable_daily_cycle=discipline_enable_daily_cycle, → 无问题
  - 行 224：        market_data_mode=market_data_mode, → 无问题
  - 行 225：        market_symbols=market_symbols, → 无问题
  - 行 226：        market_snapshot_json=market_snapshot_json, → 无问题
  - 行 227：        lane_scheduler_enabled=lane_scheduler_enabled, → 无问题
  - 行 228：        lane_rebalance_interval_seconds=lane_rebalance_interval_seconds, → 无问题
  - 行 229：        lane_scheduler_cycles=lane_scheduler_cycles, → 无问题
  - 行 230：        execution_session_guard_enabled=execution_session_guard_enabled, → 无问题
  - 行 231：        execution_session_start_utc=execution_session_start_utc, → 无问题
  - 行 232：        execution_session_end_utc=execution_session_end_utc, → 无问题
  - 行 233：        execution_good_after_seconds=execution_good_after_seconds, → 无问题
  - 行 234：    ) → 无问题
- 调用的外部函数：lower; os.getenv; _read_int_env; _read_float_env; _read_bool_env; upper; AppConfig; RuntimeProfile; RuntimeMode; AppError; strip
- 被谁调用：ibkr_execution.py:main:296; non_ai_validation_report.py:_functional_non_ai_checks:114; main.py:main:19; replay.py:_run_safety_blocked_execution:130; tests/test_app_health.py:AppHealthTests.test_health_check_returns_lockdown_when_ibkr_unreachable:16; tests/test_app_health.py:AppHealthTests.test_health_check_returns_normal_when_ibkr_reachable:24; tests/test_audit_and_memory_persistence.py:AuditAndMemoryPersistenceTests.test_writes_parameter_audit_and_memory_db:29; tests/test_config.py:ConfigTests.test_loads_llm_gateway_related_settings:60; tests/test_config.py:ConfigTests.test_raises_when_retry_rate_is_invalid_float:106; tests/test_config.py:ConfigTests.test_raises_when_runtime_mode_is_invalid:111; tests/test_ibkr_execution.py:IbkrExecutionTests.test_execute_cycle_dry_run_returns_signal:117; tests/test_ibkr_execution.py:IbkrExecutionTests.test_execute_cycle_send_with_injected_client:125; tests/test_ibkr_execution.py:IbkrExecutionTests.test_execute_cycle_send_continues_when_single_signal_fails:146; tests/test_lane_bus.py:LaneBusTests.test_runs_lane_cycle_and_returns_decision:28; tests/test_lane_bus.py:LaneBusTests.test_lane_cycle_stays_stable_under_repeated_runs:60; tests/test_lane_bus.py:LaneBusTests.test_guard_blocks_risk_execution:72; tests/test_lane_bus.py:LaneBusTests.test_seed_event_boolean_block_is_handled:80; tests/test_lane_bus.py:LaneBusTests.test_lane_cycle_returns_strategy_signals:103; tests/test_lane_bus.py:LaneBusTests.test_lane_cycle_bypasses_ai_when_disabled:118; tests/test_lane_bus.py:LaneBusTests.test_lane_cycle_daily_discipline_buy_when_no_position:127; tests/test_runtime_budget.py:RuntimeBudgetTests.test_eco_mode_uses_conservative_budget:17; tests/test_runtime_budget.py:RuntimeBudgetTests.test_perf_mode_uses_higher_parallel_budget:25; tests/test_runtime_budget.py:RuntimeBudgetTests.test_m2_profile_is_detected_on_darwin_arm:36
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_read_int_env（行 237-245）
- 功能：执行对应业务逻辑
- 参数：name: str, default_value: int
- 返回值：int（见函数语义）
- 逐行分析：
  - 行 237：def _read_int_env(name: str, default_value: int) -> int: → 无问题
  - 行 238：    raw = os.getenv(name, str(default_value)) → 无问题
  - 行 239：    try: → 无问题
  - 行 240：        return int(raw) → 无问题
  - 行 241：    except ValueError as exc: → 无问题
  - 行 242：        raise AppError( → 无问题
  - 行 243：            code=ErrorCode.CONFIG_INVALID_VALUE, → 无问题
  - 行 244：            message=f"{name} must be integer, got: {raw}", → 无问题
  - 行 245：        ) from exc → 无问题
- 调用的外部函数：os.getenv; str; int; AppError
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_read_float_env（行 248-256）
- 功能：执行对应业务逻辑
- 参数：name: str, default_value: float
- 返回值：float（见函数语义）
- 逐行分析：
  - 行 248：def _read_float_env(name: str, default_value: float) -> float: → 无问题
  - 行 249：    raw = os.getenv(name, str(default_value)) → 无问题
  - 行 250：    try: → 无问题
  - 行 251：        return float(raw) → 无问题
  - 行 252：    except ValueError as exc: → 无问题
  - 行 253：        raise AppError( → 无问题
  - 行 254：            code=ErrorCode.CONFIG_INVALID_VALUE, → 无问题
  - 行 255：            message=f"{name} must be float, got: {raw}", → 无问题
  - 行 256：        ) from exc → 无问题
- 调用的外部函数：os.getenv; str; float; AppError
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_read_bool_env（行 259-270）
- 功能：执行对应业务逻辑
- 参数：name: str, default_value: bool
- 返回值：bool（见函数语义）
- 逐行分析：
  - 行 259：def _read_bool_env(name: str, default_value: bool) -> bool: → 无问题
  - 行 260：    raw = os.getenv(name, "true" if default_value else "false").strip().lower() → 无问题
  - 行 261：    if raw in {"1", "true", "yes", "on", "y", "t", "enabled"}: → 无问题
  - 行 262：        return True → 无问题
  - 行 263：    if raw in {"0", "false", "no", "off", "n", "f", "disabled"}: → 无问题
  - 行 264：        return False → 无问题
  - 行 265：    if raw == "": → 无问题
  - 行 266：        return default_value → 无问题
  - 行 267：    raise AppError( → 无问题
  - 行 268：        code=ErrorCode.CONFIG_INVALID_VALUE, → 无问题
  - 行 269：        message=f"{name} must be bool, got: {raw}", → 无问题
  - 行 270：    ) → 无问题
- 调用的外部函数：lower; AppError; strip; os.getenv
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：270
- 函数审计数：4
- 发现问题数：0

## 文件：replay.py
- 总行数：211
- 函数/方法数：10

### 逐函数检查

#### 函数：__module__（行 1-211）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：import argparse → 无问题
  - 行 4：from datetime import datetime, timedelta, timezone → 无问题
  - 行 5：import json → 无问题
  - 行 6：from typing import Any → 无问题
  - 行 7： → 无问题
  - 行 8：from .ai import evaluate_ultra_guard → 无问题
  - 行 9：from .config import load_config → 无问题
  - 行 10：from .lanes import InMemoryLaneBus, LaneEvent, run_lane_cycle_with_guard → 无问题
  - 行 11：from .lanes.high import evaluate_event → 无问题
  - 行 12： → 无问题
  - 行 13： → 无问题
  - 行 27： → 无问题
  - 行 28： → 无问题
  - 行 39： → 无问题
  - 行 40： → 无问题
  - 行 53： → 无问题
  - 行 54： → 无问题
  - 行 83： → 无问题
  - 行 84： → 无问题
  - 行 102： → 无问题
  - 行 103： → 无问题
  - 行 127： → 无问题
  - 行 128： → 无问题
  - 行 148： → 无问题
  - 行 149： → 无问题
  - 行 182： → 无问题
  - 行 183： → 无问题
  - 行 199： → 无问题
  - 行 200： → 无问题
  - 行 208： → 无问题
  - 行 209： → 无问题
  - 行 210：if __name__ == "__main__": → 无问题
  - 行 211：    raise SystemExit(main()) → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：_base_event（行 14-26）
- 功能：执行对应业务逻辑
- 参数：now: datetime
- 返回值：dict[str, str]（见函数语义）
- 逐行分析：
  - 行 14：def _base_event(now: datetime) -> dict[str, str]: → 无问题
  - 行 15：    return { → 无问题
  - 行 16：        "lane": "ultra", → 无问题
  - 行 17：        "kind": "signal", → 无问题
  - 行 18：        "symbol": "AAPL", → 无问题
  - 行 19：        "side": "buy", → 无问题
  - 行 20：        "entry_price": "100", → 无问题
  - 行 21：        "stop_loss_price": "95", → 无问题
  - 行 22：        "take_profit_price": "110", → 无问题
  - 行 23：        "equity": "100000", → 无问题
  - 行 24：        "current_exposure": "12000", → 无问题
  - 行 25：        "last_exit_at": (now - timedelta(days=3)).isoformat(), → 无问题
  - 行 26：    } → 无问题
- 调用的外部函数：isoformat; timedelta
- 被谁调用：phase0_validation_report.py:_hard_rule_checks:33; phase0_validation_report.py:_hard_rule_checks:36; phase0_validation_report.py:_hard_rule_checks:32; phase0_validation_report.py:_order_checks:59
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_breaking_news_event（行 29-38）
- 功能：执行对应业务逻辑
- 参数：now: datetime
- 返回值：dict[str, str]（见函数语义）
- 逐行分析：
  - 行 29：def _breaking_news_event(now: datetime) -> dict[str, str]: → 无问题
  - 行 30：    payload = _base_event(now) → 无问题
  - 行 31：    payload.update( → 无问题
  - 行 32：        { → 无问题
  - 行 33：            "injection_kind": "breaking_news", → 无问题
  - 行 34：            "headline": "SEC headline shock", → 无问题
  - 行 35：            "last_exit_at": (now - timedelta(hours=4)).isoformat(), → 无问题
  - 行 36：        } → 无问题
  - 行 37：    ) → 无问题
  - 行 38：    return payload → 无问题
- 调用的外部函数：_base_event; payload.update; isoformat; timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_high_volatility_event（行 41-52）
- 功能：执行对应业务逻辑
- 参数：now: datetime
- 返回值：dict[str, str]（见函数语义）
- 逐行分析：
  - 行 41：def _high_volatility_event(now: datetime) -> dict[str, str]: → 无问题
  - 行 42：    payload = _base_event(now) → 无问题
  - 行 43：    payload.update( → 无问题
  - 行 44：        { → 无问题
  - 行 45：            "injection_kind": "high_volatility", → 无问题
  - 行 46：            "entry_price": "100", → 无问题
  - 行 47：            "stop_loss_price": "95", → 无问题
  - 行 48：            "take_profit_price": "112", → 无问题
  - 行 49：            "atr_ratio": "0.16", → 无问题
  - 行 50：        } → 无问题
  - 行 51：    ) → 无问题
  - 行 52：    return payload → 无问题
- 调用的外部函数：_base_event; payload.update
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_run_single（行 55-82）
- 功能：执行对应业务逻辑
- 参数：name: str, event: dict[str, str], expected_status: str, expected_reason: str | None
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 55：def _run_single(name: str, event: dict[str, str], expected_status: str, expected_reason: str | None) -> dict[str, Any]: → 无问题
  - 行 56：    decision = evaluate_event(event) → 无问题
  - 行 57：    reasons = decision.get("reject_reasons", []) → 无问题
  - 行 58：    checks: list[dict[str, Any]] = [ → 无问题
  - 行 59：        { → 无问题
  - 行 60：            "name": "status_match", → 无问题
  - 行 61：            "ok": decision.get("status") == expected_status, → 无问题
  - 行 62：            "actual": decision.get("status"), → 无问题
  - 行 63：            "expected": expected_status, → 无问题
  - 行 64：        } → 无问题
  - 行 65：    ] → 无问题
  - 行 66：    if expected_reason is not None: → 无问题
  - 行 67：        checks.append( → 无问题
  - 行 68：            { → 无问题
  - 行 69：                "name": "reason_match", → 无问题
  - 行 70：                "ok": expected_reason in reasons, → 无问题
  - 行 71：                "actual": reasons, → 无问题
  - 行 72：                "expected": expected_reason, → 无问题
  - 行 73：            } → 无问题
  - 行 74：        ) → 无问题
  - 行 75：    ok = all(check["ok"] for check in checks) → 无问题
  - 行 76：    return { → 无问题
  - 行 77：        "scenario": name, → 无问题
  - 行 78：        "ok": ok, → 无问题
  - 行 79：        "event": event, → 无问题
  - 行 80：        "decision": decision, → 无问题
  - 行 81：        "checks": checks, → 无问题
  - 行 82：    } → 无问题
- 调用的外部函数：evaluate_event; decision.get; all; checks.append
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_run_duplicate_event_dedup（行 85-101）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 85：def _run_duplicate_event_dedup() -> dict[str, Any]: → 无问题
  - 行 86：    bus = InMemoryLaneBus() → 无问题
  - 行 87：    payload = {"symbol": "AAPL", "lane": "ultra", "kind": "signal"} → 无问题
  - 行 88：    event = LaneEvent.from_payload(event_type="signal", source_lane="ultra", payload=payload) → 无问题
  - 行 89：    first_ok = bus.publish("ultra.signal", event) → 无问题
  - 行 90：    second_ok = bus.publish("ultra.signal", event) → 无问题
  - 行 91：    checks = [ → 无问题
  - 行 92：        {"name": "first_publish_ok", "ok": first_ok, "actual": first_ok, "expected": True}, → 无问题
  - 行 93：        {"name": "second_publish_deduped", "ok": not second_ok, "actual": second_ok, "expected": False}, → 无问题
  - 行 94：    ] → 无问题
  - 行 95：    return { → 无问题
  - 行 96：        "scenario": "duplicate_event_dedup", → 无问题
  - 行 97：        "ok": all(item["ok"] for item in checks), → 无问题
  - 行 98：        "event": payload, → 无问题
  - 行 99：        "decision": {"first_publish_ok": first_ok, "second_publish_ok": second_ok}, → 无问题
  - 行 100：        "checks": checks, → 无问题
  - 行 101：    } → 无问题
- 调用的外部函数：InMemoryLaneBus; LaneEvent.from_payload; bus.publish; all
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_run_unverified_stale_message（行 104-126）
- 功能：执行对应业务逻辑
- 参数：now: datetime
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 104：def _run_unverified_stale_message(now: datetime) -> dict[str, Any]: → 无问题
  - 行 105：    ultra = evaluate_ultra_guard( → 无问题
  - 行 106：        headline="unverified rumor clickbait says merger", → 无问题
  - 行 107：        published_at=now - timedelta(hours=6), → 无问题
  - 行 108：        now=now, → 无问题
  - 行 109：        max_age_minutes=180, → 无问题
  - 行 110：    ) → 无问题
  - 行 111：    checks = [ → 无问题
  - 行 112：        {"name": "wake_high_blocked", "ok": not ultra.wake_high, "actual": ultra.wake_high, "expected": False}, → 无问题
  - 行 113：        {"name": "reason_is_block", "ok": ultra.reason == "LOW_CREDIBILITY_OR_STALE", "actual": ultra.reason, "expected": "LOW_CREDIBILITY_OR_STALE"}, → 无问题
  - 行 114：    ] → 无问题
  - 行 115：    return { → 无问题
  - 行 116：        "scenario": "unverified_stale_message", → 无问题
  - 行 117：        "ok": all(item["ok"] for item in checks), → 无问题
  - 行 118：        "event": {"headline": "unverified rumor clickbait says merger"}, → 无问题
  - 行 119：        "decision": { → 无问题
  - 行 120：            "authenticity_score": ultra.authenticity_score, → 无问题
  - 行 121：            "timeliness_score": ultra.timeliness_score, → 无问题
  - 行 122：            "wake_high": ultra.wake_high, → 无问题
  - 行 123：            "reason": ultra.reason, → 无问题
  - 行 124：        }, → 无问题
  - 行 125：        "checks": checks, → 无问题
  - 行 126：    } → 无问题
- 调用的外部函数：evaluate_ultra_guard; all; timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_run_safety_blocked_execution（行 129-147）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 129：def _run_safety_blocked_execution() -> dict[str, Any]: → 无问题
  - 行 130：    config = load_config() → 无问题
  - 行 131：    output = run_lane_cycle_with_guard("AAPL", config=config, allow_risk_execution=False) → 无问题
  - 行 132：    decision = output["decisions"][0] → 无问题
  - 行 133：    checks = [ → 无问题
  - 行 134：        { → 无问题
  - 行 135：            "name": "blocked_by_safety_mode", → 无问题
  - 行 136：            "ok": decision.get("status") == "rejected" and "SAFETY_MODE_BLOCKED" in decision.get("reject_reasons", []), → 无问题
  - 行 137：            "actual": decision, → 无问题
  - 行 138：            "expected": "rejected+SAFETY_MODE_BLOCKED", → 无问题
  - 行 139：        } → 无问题
  - 行 140：    ] → 无问题
  - 行 141：    return { → 无问题
  - 行 142：        "scenario": "safety_mode_blocked", → 无问题
  - 行 143：        "ok": all(item["ok"] for item in checks), → 无问题
  - 行 144：        "event": output["event"], → 无问题
  - 行 145：        "decision": decision, → 无问题
  - 行 146：        "checks": checks, → 无问题
  - 行 147：    } → 无问题
- 调用的外部函数：load_config; run_lane_cycle_with_guard; all; decision.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：run_replay（行 150-181）
- 功能：执行对应业务逻辑
- 参数：mode: str
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 150：def run_replay(mode: str = "all") -> dict[str, Any]: → 无问题
  - 行 151：    now = datetime.now(tz=timezone.utc) → 无问题
  - 行 152：    scenarios = { → 无问题
  - 行 153：        "breaking_news": _run_single( → 无问题
  - 行 154：            name="breaking_news", → 无问题
  - 行 155：            event=_breaking_news_event(now), → 无问题
  - 行 156：            expected_status="rejected", → 无问题
  - 行 157：            expected_reason="COOLDOWN_24H_ACTIVE", → 无问题
  - 行 158：        ), → 无问题
  - 行 159：        "high_volatility": _run_single( → 无问题
  - 行 160：            name="high_volatility", → 无问题
  - 行 161：            event=_high_volatility_event(now), → 无问题
  - 行 162：            expected_status="accepted", → 无问题
  - 行 163：            expected_reason=None, → 无问题
  - 行 164：        ), → 无问题
  - 行 165：        "duplicate_event_dedup": _run_duplicate_event_dedup(), → 无问题
  - 行 166：        "unverified_stale_message": _run_unverified_stale_message(now), → 无问题
  - 行 167：        "safety_mode_blocked": _run_safety_blocked_execution(), → 无问题
  - 行 168：    } → 无问题
  - 行 169：    if mode == "all": → 无问题
  - 行 170：        selected = list(scenarios.values()) → 无问题
  - 行 171：    else: → 无问题
  - 行 172：        selected = [scenarios[mode]] → 无问题
  - 行 173：    passed = sum(1 for item in selected if item["ok"]) → 无问题
  - 行 174：    return { → 无问题
  - 行 175：        "kind": "phase0_injection_replay", → 无问题
  - 行 176：        "generated_at": datetime.now(tz=timezone.utc).isoformat(), → 无问题
  - 行 177：        "mode": mode, → 无问题
  - 行 178：        "passed": passed, → 无问题
  - 行 179：        "total": len(selected), → 无问题
  - 行 180：        "results": selected, → 无问题
  - 行 181：    } → 无问题
- 调用的外部函数：datetime.now; sum; _run_single; _run_duplicate_event_dedup; _run_unverified_stale_message; _run_safety_blocked_execution; list; isoformat; len; scenarios.values; _breaking_news_event; _high_volatility_event
- 被谁调用：phase0_validation_report.py:generate_phase0_validation_report:166; tests/test_replay.py:ReplayScriptTests.test_all_mode_runs_fault_injection_matrix:14; tests/test_replay.py:ReplayScriptTests.test_single_mode_runs_only_selected_scenario:28
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_parse_args（行 184-198）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：argparse.Namespace（见函数语义）
- 逐行分析：
  - 行 184：def _parse_args() -> argparse.Namespace: → 无问题
  - 行 185：    parser = argparse.ArgumentParser(prog="phase0-replay") → 无问题
  - 行 186：    parser.add_argument( → 无问题
  - 行 187：        "--mode", → 无问题
  - 行 188：        choices=[ → 无问题
  - 行 189：            "all", → 无问题
  - 行 190：            "breaking_news", → 无问题
  - 行 191：            "high_volatility", → 无问题
  - 行 192：            "duplicate_event_dedup", → 无问题
  - 行 193：            "unverified_stale_message", → 无问题
  - 行 194：            "safety_mode_blocked", → 无问题
  - 行 195：        ], → 无问题
  - 行 196：        default="all", → 无问题
  - 行 197：    ) → 无问题
  - 行 198：    return parser.parse_args() → 无问题
- 调用的外部函数：argparse.ArgumentParser; parser.add_argument; parser.parse_args
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：main（行 201-207）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：int（见函数语义）
- 逐行分析：
  - 行 201：def main() -> int: → 无问题
  - 行 202：    args = _parse_args() → 无问题
  - 行 203：    report = run_replay(mode=args.mode) → 无问题
  - 行 204：    print(json.dumps(report, ensure_ascii=False)) → 无问题
  - 行 205：    if report["passed"] == report["total"]: → 无问题
  - 行 206：        return 0 → 无问题
  - 行 207：    return 2 → 无问题
- 调用的外部函数：_parse_args; run_replay; print; json.dumps
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：211
- 函数审计数：10
- 发现问题数：0

## 文件：ibkr_paper_check.py
- 总行数：407
- 函数/方法数：17

### 逐函数检查

#### 函数：__module__（行 1-407）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：import argparse → 无问题
  - 行 4：from dataclasses import dataclass → 无问题
  - 行 5：from datetime import datetime, timezone → 无问题
  - 行 6：import json → 无问题
  - 行 7：import socket → 无问题
  - 行 8：import time → 无问题
  - 行 9：from typing import Any, Callable, Protocol → 无问题
  - 行 10： → 无问题
  - 行 11： → 无问题
  - 行 12：class MarketDataClient(Protocol): → 无问题
  - 行 15： → 无问题
  - 行 18： → 无问题
  - 行 21： → 无问题
  - 行 22： → 无问题
  - 行 23：@dataclass(frozen=True) → 无问题
  - 行 24：class ProbeConfig: → 无问题
  - 行 25：    host: str = "127.0.0.1" → 无问题
  - 行 26：    port: int = 7497 → 无问题
  - 行 27：    client_id: int = 77 → 无问题
  - 行 28：    timeout_seconds: float = 1.0 → 无问题
  - 行 29：    symbol: str = "AAPL" → 无问题
  - 行 30：    news_limit: int = 5 → 无问题
  - 行 31：    max_retries: int = 2 → 无问题
  - 行 32： → 无问题
  - 行 33： → 无问题
  - 行 34：@dataclass(frozen=True) → 无问题
  - 行 35：class PortStatus: → 无问题
  - 行 36：    ok: bool → 无问题
  - 行 37：    host: str → 无问题
  - 行 38：    port: int → 无问题
  - 行 39：    latency_ms: float | None → 无问题
  - 行 40：    error: str | None → 无问题
  - 行 41： → 无问题
  - 行 50： → 无问题
  - 行 51： → 无问题
  - 行 52：class IbkrInsyncClient: → 无问题
  - 行 58： → 无问题
  - 行 76： → 无问题
  - 行 97： → 无问题
  - 行 101： → 无问题
  - 行 102： → 无问题
  - 行 112： → 无问题
  - 行 113： → 无问题
  - 行 139： → 无问题
  - 行 140： → 无问题
  - 行 163： → 无问题
  - 行 164： → 无问题
  - 行 174： → 无问题
  - 行 175： → 无问题
  - 行 181： → 无问题
  - 行 182： → 无问题
  - 行 210： → 无问题
  - 行 211： → 无问题
  - 行 374： → 无问题
  - 行 375： → 无问题
  - 行 386： → 无问题
  - 行 387： → 无问题
  - 行 404： → 无问题
  - 行 405： → 无问题
  - 行 406：if __name__ == "__main__": → 无问题
  - 行 407：    raise SystemExit(main()) → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：MarketDataClient.request_l1_snapshot（行 13-14）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 13：    def request_l1_snapshot(self, symbol: str) -> dict[str, Any]: → 无问题
  - 行 14：        ... → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：MarketDataClient.request_news（行 16-17）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str, limit: int
- 返回值：list[dict[str, Any]]（见函数语义）
- 逐行分析：
  - 行 16：    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, Any]]: → 无问题
  - 行 17：        ... → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：MarketDataClient.close（行 19-20）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 19：    def close(self) -> None: → 无问题
  - 行 20：        ... → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：PortStatus.to_dict（行 42-49）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 42：    def to_dict(self) -> dict[str, Any]: → 无问题
  - 行 43：        return { → 无问题
  - 行 44：            "ok": self.ok, → 无问题
  - 行 45：            "host": self.host, → 无问题
  - 行 46：            "port": self.port, → 无问题
  - 行 47：            "latency_ms": self.latency_ms, → 无问题
  - 行 48：            "error": self.error, → 无问题
  - 行 49：        } → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrInsyncClient.__init__（行 53-57）
- 功能：执行对应业务逻辑
- 参数：self: Any, host: str, port: int, client_id: int, timeout_seconds: float
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 53：    def __init__(self, host: str, port: int, client_id: int, timeout_seconds: float) -> None: → 无问题
  - 行 54：        from ib_insync import IB → 无问题
  - 行 55： → 无问题
  - 行 56：        self._ib = IB() → 无问题
  - 行 57：        self._ib.connect(host, port, clientId=client_id, timeout=timeout_seconds, readonly=True) → 无问题
- 调用的外部函数：IB; self._ib.connect
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrInsyncClient.request_l1_snapshot（行 59-75）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 59：    def request_l1_snapshot(self, symbol: str) -> dict[str, Any]: → 无问题
  - 行 60：        from ib_insync import Stock, util → 无问题
  - 行 61： → 无问题
  - 行 62：        contract = Stock(symbol.upper(), "SMART", "USD") → 无问题
  - 行 63：        self._ib.qualifyContracts(contract) → 无问题
  - 行 64：        ticker = self._ib.reqMktData(contract, genericTickList="", snapshot=True, regulatorySnapshot=False) → 无问题
  - 行 65：        self._ib.sleep(1.2) → 无问题
  - 行 66：        payload = { → 无问题
  - 行 67：            "symbol": symbol.upper(), → 无问题
  - 行 68：            "bid": ticker.bid, → 无问题
  - 行 69：            "ask": ticker.ask, → 无问题
  - 行 70：            "last": ticker.last, → 无问题
  - 行 71：            "close": ticker.close, → 无问题
  - 行 72：            "timestamp": util.formatIBDatetime(datetime.now(tz=timezone.utc)), → 无问题
  - 行 73：        } → 无问题
  - 行 74：        self._ib.cancelMktData(contract) → 无问题
  - 行 75：        return payload → 无问题
- 调用的外部函数：Stock; self._ib.qualifyContracts; self._ib.reqMktData; self._ib.sleep; self._ib.cancelMktData; symbol.upper; util.formatIBDatetime; datetime.now
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrInsyncClient.request_news（行 77-96）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str, limit: int
- 返回值：list[dict[str, Any]]（见函数语义）
- 逐行分析：
  - 行 77：    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, Any]]: → 无问题
  - 行 78：        from ib_insync import Stock → 无问题
  - 行 79： → 无问题
  - 行 80：        contract = Stock(symbol.upper(), "SMART", "USD") → 无问题
  - 行 81：        self._ib.qualifyContracts(contract) → 无问题
  - 行 82：        con_id = contract.conId → 无问题
  - 行 83：        providers = self._ib.reqNewsProviders() → 无问题
  - 行 84：        if not providers: → 无问题
  - 行 85：            return [] → 无问题
  - 行 86：        provider_codes = "+".join(provider.code for provider in providers) → 无问题
  - 行 87：        items = self._ib.reqHistoricalNews(con_id, provider_codes, "", "", limit) → 无问题
  - 行 88：        return [ → 无问题
  - 行 89：            { → 无问题
  - 行 90：                "time": item.time, → 无问题
  - 行 91：                "provider_code": item.providerCode, → 无问题
  - 行 92：                "article_id": item.articleId, → 无问题
  - 行 93：                "headline": item.headline, → 无问题
  - 行 94：            } → 无问题
  - 行 95：            for item in items → 无问题
  - 行 96：        ] → 无问题
- 调用的外部函数：Stock; self._ib.qualifyContracts; self._ib.reqNewsProviders; join; self._ib.reqHistoricalNews; symbol.upper
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrInsyncClient.close（行 98-100）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 98：    def close(self) -> None: → 无问题
  - 行 99：        if self._ib.isConnected(): → 无问题
  - 行 100：            self._ib.disconnect() → 无问题
- 调用的外部函数：self._ib.isConnected; self._ib.disconnect
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：check_port（行 103-111）
- 功能：执行对应业务逻辑
- 参数：host: str, port: int, timeout_seconds: float
- 返回值：PortStatus（见函数语义）
- 逐行分析：
  - 行 103：def check_port(host: str, port: int, timeout_seconds: float) -> PortStatus: → 无问题
  - 行 104：    started = datetime.now(tz=timezone.utc) → 无问题
  - 行 105：    try: → 无问题
  - 行 106：        with socket.create_connection((host, port), timeout=timeout_seconds): → 无问题
  - 行 107：            elapsed = datetime.now(tz=timezone.utc) - started → 无问题
  - 行 108：            latency_ms = round(elapsed.total_seconds() * 1000, 3) → 无问题
  - 行 109：            return PortStatus(ok=True, host=host, port=port, latency_ms=latency_ms, error=None) → 无问题
  - 行 110：    except OSError as exc: → 无问题
  - 行 111：        return PortStatus(ok=False, host=host, port=port, latency_ms=None, error=str(exc)) → 无问题
- 调用的外部函数：datetime.now; socket.create_connection; round; PortStatus; elapsed.total_seconds; str
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：fetch_yfinance_snapshot（行 114-138）
- 功能：执行对应业务逻辑
- 参数：symbol: str
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 114：def fetch_yfinance_snapshot(symbol: str) -> dict[str, Any]: → 无问题
  - 行 115：    try: → 无问题
  - 行 116：        import yfinance as yf → 无问题
  - 行 117：    except Exception as exc: → 无问题
  - 行 118：        return {"ok": False, "source": "yfinance", "symbol": symbol.upper(), "error": str(exc)} → 无问题
  - 行 119：    try: → 无问题
  - 行 120：        history = yf.Ticker(symbol.upper()).history(period="1d", interval="1m") → 无问题
  - 行 121：        if history.empty: → 无问题
  - 行 122：            return { → 无问题
  - 行 123：                "ok": False, → 无问题
  - 行 124：                "source": "yfinance", → 无问题
  - 行 125：                "symbol": symbol.upper(), → 无问题
  - 行 126：                "error": "empty history", → 无问题
  - 行 127：            } → 无问题
  - 行 128：        last_row = history.tail(1).iloc[0] → 无问题
  - 行 129：        timestamp = history.tail(1).index[0].isoformat() → 无问题
  - 行 130：        return { → 无问题
  - 行 131：            "ok": True, → 无问题
  - 行 132：            "source": "yfinance", → 无问题
  - 行 133：            "symbol": symbol.upper(), → 无问题
  - 行 134：            "last": float(last_row["Close"]), → 无问题
  - 行 135：            "timestamp": timestamp, → 无问题
  - 行 136：        } → 无问题
  - 行 137：    except Exception as exc: → 无问题
  - 行 138：        return {"ok": False, "source": "yfinance", "symbol": symbol.upper(), "error": str(exc)} → 无问题
- 调用的外部函数：history; isoformat; symbol.upper; float; str; yf.Ticker; history.tail
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_append_critical_path_log（行 141-162）
- 功能：执行对应业务逻辑
- 参数：report: dict[str, Any], step: str, level: str, status: str, message: str, attempt: int | None, retryable: bool | None
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 141：def _append_critical_path_log( → 无问题
  - 行 142：    report: dict[str, Any], → 无问题
  - 行 143：    *, → 无问题
  - 行 144：    step: str, → 无问题
  - 行 145：    level: str, → 无问题
  - 行 146：    status: str, → 无问题
  - 行 147：    message: str, → 无问题
  - 行 148：    attempt: int | None = None, → 无问题
  - 行 149：    retryable: bool | None = None, → 无问题
  - 行 150：) -> None: → 无问题
  - 行 151：    entry: dict[str, Any] = { → 无问题
  - 行 152：        "time": datetime.now(tz=timezone.utc).isoformat(), → 无问题
  - 行 153：        "step": step, → 无问题
  - 行 154：        "level": level, → 无问题
  - 行 155：        "status": status, → 无问题
  - 行 156：        "message": message, → 无问题
  - 行 157：    } → 无问题
  - 行 158：    if attempt is not None: → 无问题
  - 行 159：        entry["attempt"] = attempt → 无问题
  - 行 160：    if retryable is not None: → 无问题
  - 行 161：        entry["retryable"] = retryable → 无问题
  - 行 162：    report["critical_path_logs"].append(entry) → 无问题
- 调用的外部函数：append; isoformat; datetime.now
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_append_alert（行 165-173）
- 功能：执行对应业务逻辑
- 参数：report: dict[str, Any], level: str, code: str, message: str
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 165：def _append_alert(report: dict[str, Any], *, level: str, code: str, message: str) -> None: → 无问题
  - 行 166：    report["alerts"].append( → 无问题
  - 行 167：        { → 无问题
  - 行 168：            "time": datetime.now(tz=timezone.utc).isoformat(), → 无问题
  - 行 169：            "level": level, → 无问题
  - 行 170：            "code": code, → 无问题
  - 行 171：            "message": message, → 无问题
  - 行 172：        } → 无问题
  - 行 173：    ) → 无问题
- 调用的外部函数：append; isoformat; datetime.now
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_is_retryable_probe_exception（行 176-180）
- 功能：执行对应业务逻辑
- 参数：exc: Exception
- 返回值：bool（见函数语义）
- 逐行分析：
  - 行 176：def _is_retryable_probe_exception(exc: Exception) -> bool: → 无问题
  - 行 177：    if isinstance(exc, (TimeoutError, ConnectionError, OSError)): → 无问题
  - 行 178：        return True → 无问题
  - 行 179：    lower_message = str(exc).lower() → 无问题
  - 行 180：    return any(token in lower_message for token in {"timeout", "temporar", "try again", "timed out", "busy"}) → 无问题
- 调用的外部函数：isinstance; lower; any; str
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_build_pass_evidence（行 183-209）
- 功能：执行对应业务逻辑
- 参数：symbol: str, l1_payload: dict[str, Any], news_items: list[dict[str, Any]]
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 183：def _build_pass_evidence(symbol: str, l1_payload: dict[str, Any], news_items: list[dict[str, Any]]) -> dict[str, Any]: → 无问题
  - 行 184：    normalized_symbol = symbol.upper() → 无问题
  - 行 185：    l1_required_fields = {"bid", "ask", "last"} → 无问题
  - 行 186：    l1_present = sorted(key for key in l1_required_fields if l1_payload.get(key) is not None) → 无问题
  - 行 187：    l1_missing = sorted(l1_required_fields - set(l1_present)) → 无问题
  - 行 188：    l1_ok = l1_payload.get("symbol", normalized_symbol).upper() == normalized_symbol and not l1_missing → 无问题
  - 行 189：    first_news = news_items[0] if news_items else {} → 无问题
  - 行 190：    news_required_fields = {"headline", "provider_code", "article_id"} → 无问题
  - 行 191：    news_present = sorted(key for key in news_required_fields if first_news.get(key)) → 无问题
  - 行 192：    news_missing = sorted(news_required_fields - set(news_present)) → 无问题
  - 行 193：    news_ok = bool(news_items) and not news_missing → 无问题
  - 行 194：    return { → 无问题
  - 行 195：        "l1_market_data": { → 无问题
  - 行 196：            "ok": l1_ok, → 无问题
  - 行 197：            "symbol_match": l1_payload.get("symbol", normalized_symbol).upper() == normalized_symbol, → 无问题
  - 行 198：            "required_fields_present": l1_present, → 无问题
  - 行 199：            "missing_fields": l1_missing, → 无问题
  - 行 200：            "snapshot": l1_payload, → 无问题
  - 行 201：        }, → 无问题
  - 行 202：        "news": { → 无问题
  - 行 203：            "ok": news_ok, → 无问题
  - 行 204：            "items_count": len(news_items), → 无问题
  - 行 205：            "required_fields_present": news_present, → 无问题
  - 行 206：            "missing_fields": news_missing, → 无问题
  - 行 207：            "sample": first_news, → 无问题
  - 行 208：        }, → 无问题
  - 行 209：    } → 无问题
- 调用的外部函数：symbol.upper; sorted; bool; set; upper; len; first_news.get; l1_payload.get
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：run_probe（行 212-373）
- 功能：执行对应业务逻辑
- 参数：config: ProbeConfig, client_factory: Callable[[ProbeConfig], MarketDataClient] | None, port_checker: Callable[[str, int, float], PortStatus] | None, fallback_fetcher: Callable[[str], dict[str, Any]] | None
- 返回值：dict[str, Any]（见函数语义）
- 逐行分析：
  - 行 212：def run_probe( → 无问题
  - 行 213：    config: ProbeConfig, → 无问题
  - 行 214：    client_factory: Callable[[ProbeConfig], MarketDataClient] | None = None, → 无问题
  - 行 215：    port_checker: Callable[[str, int, float], PortStatus] | None = None, → 无问题
  - 行 216：    fallback_fetcher: Callable[[str], dict[str, Any]] | None = None, → 无问题
  - 行 217：) -> dict[str, Any]: → 无问题
  - 行 218：    factory = client_factory or (lambda conf: IbkrInsyncClient(conf.host, conf.port, conf.client_id, conf.timeout_seconds)) → 无问题
  - 行 219：    active_port_checker = port_checker or check_port → 无问题
  - 行 220：    active_fallback_fetcher = fallback_fetcher or fetch_yfinance_snapshot → 无问题
  - 行 221：    report: dict[str, Any] = { → 无问题
  - 行 222：        "kind": "ibkr_paper_probe", → 无问题
  - 行 223：        "symbol": config.symbol.upper(), → 无问题
  - 行 224：        "generated_at": datetime.now(tz=timezone.utc).isoformat(), → 无问题
  - 行 225：        "critical_path_logs": [], → 无问题
  - 行 226：        "alerts": [], → 无问题
  - 行 227：    } → 无问题
  - 行 228： → 无问题
  - 行 229：    port_status = active_port_checker(config.host, config.port, config.timeout_seconds) → 无问题
  - 行 230：    report["port_7497"] = port_status.to_dict() → 无问题
  - 行 231：    report["l1_market_data"] = { → 无问题
  - 行 232：        "ok": False, → 无问题
  - 行 233：        "source": "ibkr", → 无问题
  - 行 234：        "symbol": config.symbol.upper(), → 无问题
  - 行 235：        "error": "not attempted", → 无问题
  - 行 236：    } → 无问题
  - 行 237：    report["news"] = [] → 无问题
  - 行 238：    report["fallback_market_data"] = None → 无问题
  - 行 239：    report["pass_evidence"] = { → 无问题
  - 行 240：        "l1_market_data": { → 无问题
  - 行 241：            "ok": False, → 无问题
  - 行 242：            "symbol_match": False, → 无问题
  - 行 243：            "required_fields_present": [], → 无问题
  - 行 244：            "missing_fields": ["bid", "ask", "last"], → 无问题
  - 行 245：            "snapshot": {}, → 无问题
  - 行 246：        }, → 无问题
  - 行 247：        "news": { → 无问题
  - 行 248：            "ok": False, → 无问题
  - 行 249：            "items_count": 0, → 无问题
  - 行 250：            "required_fields_present": [], → 无问题
  - 行 251：            "missing_fields": ["headline", "provider_code", "article_id"], → 无问题
  - 行 252：            "sample": {}, → 无问题
  - 行 253：        }, → 无问题
  - 行 254：    } → 无问题
  - 行 255：    report["retry_validation"] = { → 无问题
  - 行 256：        "max_retries": config.max_retries, → 无问题
  - 行 257：        "attempts": 0, → 无问题
  - 行 258：        "retried": False, → 无问题
  - 行 259：        "retryable_errors": [], → 无问题
  - 行 260：        "exhausted": False, → 无问题
  - 行 261：    } → 无问题
  - 行 262：    _append_critical_path_log( → 无问题
  - 行 263：        report, → 无问题
  - 行 264：        step="port_probe", → 无问题
  - 行 265：        level="INFO", → 无问题
  - 行 266：        status="start", → 无问题
  - 行 267：        message=f"start checking {config.host}:{config.port}", → 无问题
  - 行 268：    ) → 无问题
  - 行 269： → 无问题
  - 行 270：    if not port_status.ok: → 无问题
  - 行 271：        _append_critical_path_log( → 无问题
  - 行 272：            report, → 无问题
  - 行 273：            step="port_probe", → 无问题
  - 行 274：            level="WARN", → 无问题
  - 行 275：            status="failed", → 无问题
  - 行 276：            message=port_status.error or "port probe failed", → 无问题
  - 行 277：        ) → 无问题
  - 行 278：        _append_alert( → 无问题
  - 行 279：            report, → 无问题
  - 行 280：            level="WARN", → 无问题
  - 行 281：            code="PORT_UNREACHABLE", → 无问题
  - 行 282：            message=f"{config.host}:{config.port} unreachable", → 无问题
  - 行 283：        ) → 无问题
  - 行 284：        report["l1_market_data"]["error"] = "7497 unreachable" → 无问题
  - 行 285：        report["fallback_market_data"] = active_fallback_fetcher(config.symbol) → 无问题
  - 行 286：        report["ok"] = False → 无问题
  - 行 287：        return report → 无问题
  - 行 288： → 无问题
  - 行 289：    _append_critical_path_log( → 无问题
  - 行 290：        report, → 无问题
  - 行 291：        step="port_probe", → 无问题
  - 行 292：        level="INFO", → 无问题
  - 行 293：        status="passed", → 无问题
  - 行 294：        message=f"{config.host}:{config.port} reachable", → 无问题
  - 行 295：    ) → 无问题
  - 行 296：    client: MarketDataClient | None = None → 无问题
  - 行 297：    try: → 无问题
  - 行 298：        for attempt in range(1, config.max_retries + 2): → 无问题
  - 行 299：            report["retry_validation"]["attempts"] = attempt → 无问题
  - 行 300：            _append_critical_path_log( → 无问题
  - 行 301：                report, → 无问题
  - 行 302：                step="ibkr_probe", → 无问题
  - 行 303：                level="INFO", → 无问题
  - 行 304：                status="start", → 无问题
  - 行 305：                message="start requesting l1 and news", → 无问题
  - 行 306：                attempt=attempt, → 无问题
  - 行 307：            ) → 无问题
  - 行 308：            try: → 无问题
  - 行 309：                client = factory(config) → 无问题
  - 行 310：                l1_payload = client.request_l1_snapshot(config.symbol) → 无问题
  - 行 311：                report["l1_market_data"] = {"ok": True, "source": "ibkr", **l1_payload} → 无问题
  - 行 312：                report["news"] = client.request_news(config.symbol, limit=config.news_limit) → 无问题
  - 行 313：                report["fallback_market_data"] = None → 无问题
  - 行 314：                report["pass_evidence"] = _build_pass_evidence(config.symbol, l1_payload, report["news"]) → 无问题
  - 行 315：                if not report["pass_evidence"]["news"]["ok"]: → 无问题
  - 行 316：                    _append_alert( → 无问题
  - 行 317：                        report, → 无问题
  - 行 318：                        level="WARN", → 无问题
  - 行 319：                        code="NEWS_EVIDENCE_WEAK", → 无问题
  - 行 320：                        message="news evidence missing required fields or empty", → 无问题
  - 行 321：                    ) → 无问题
  - 行 322：                _append_critical_path_log( → 无问题
  - 行 323：                    report, → 无问题
  - 行 324：                    step="ibkr_probe", → 无问题
  - 行 325：                    level="INFO", → 无问题
  - 行 326：                    status="passed", → 无问题
  - 行 327：                    message="l1 and news probe succeeded", → 无问题
  - 行 328：                    attempt=attempt, → 无问题
  - 行 329：                ) → 无问题
  - 行 330：                break → 无问题
  - 行 331：            except Exception as exc: → 无问题
  - 行 332：                retryable = _is_retryable_probe_exception(exc) → 无问题
  - 行 333：                report["l1_market_data"] = { → 无问题
  - 行 334：                    "ok": False, → 无问题
  - 行 335：                    "source": "ibkr", → 无问题
  - 行 336：                    "symbol": config.symbol.upper(), → 无问题
  - 行 337：                    "error": str(exc), → 无问题
  - 行 338：                } → 无问题
  - 行 339：                _append_critical_path_log( → 无问题
  - 行 340：                    report, → 无问题
  - 行 341：                    step="ibkr_probe", → 无问题
  - 行 342：                    level="WARN" if retryable else "ERROR", → 无问题
  - 行 343：                    status="failed", → 无问题
  - 行 344：                    message=str(exc), → 无问题
  - 行 345：                    attempt=attempt, → 无问题
  - 行 346：                    retryable=retryable, → 无问题
  - 行 347：                ) → 无问题
  - 行 348：                _append_alert( → 无问题
  - 行 349：                    report, → 无问题
  - 行 350：                    level="WARN" if retryable else "ERROR", → 无问题
  - 行 351：                    code="IBKR_PROBE_FAILED", → 无问题
  - 行 352：                    message=str(exc), → 无问题
  - 行 353：                ) → 无问题
  - 行 354：                if retryable: → 无问题
  - 行 355：                    report["retry_validation"]["retryable_errors"].append(str(exc)) → 无问题
  - 行 356：                if retryable and attempt <= config.max_retries: → 无问题
  - 行 357：                    report["retry_validation"]["retried"] = True → 无问题
  - 行 358：                    time.sleep(0.05 * attempt) → 无问题
  - 行 359：                    continue → 无问题
  - 行 360：                report["fallback_market_data"] = active_fallback_fetcher(config.symbol) → 无问题
  - 行 361：                report["retry_validation"]["exhausted"] = retryable and attempt > config.max_retries → 无问题
  - 行 362：                break → 无问题
  - 行 363：            finally: → 无问题
  - 行 364：                if client is not None: → 无问题
  - 行 365：                    client.close() → 无问题
  - 行 366：                    client = None → 无问题
  - 行 367：    finally: → 无问题
  - 行 368：        report["ok"] = ( → 无问题
  - 行 369：            bool(report["l1_market_data"].get("ok")) → 无问题
  - 行 370：            and bool(report["pass_evidence"]["l1_market_data"]["ok"]) → 无问题
  - 行 371：            and bool(report["pass_evidence"]["news"]["ok"]) → 无问题
  - 行 372：        ) → 无问题
  - 行 373：    return report → 无问题
- 调用的外部函数：active_port_checker; port_status.to_dict; _append_critical_path_log; config.symbol.upper; isoformat; _append_alert; active_fallback_fetcher; range; IbkrInsyncClient; bool; datetime.now; factory; client.request_l1_snapshot; client.request_news; _build_pass_evidence; get; _is_retryable_probe_exception; client.close; str; append; time.sleep
- 被谁调用：phase0_validation_report.py:_ibkr_validation:108; phase0_validation_report.py:_ibkr_validation:113; tests/test_ibkr_paper_check.py:IbkrPaperCheckTests.test_returns_fallback_when_port_unreachable:73; tests/test_ibkr_paper_check.py:IbkrPaperCheckTests.test_uses_ibkr_data_when_port_ok_and_client_works:83; tests/test_ibkr_paper_check.py:IbkrPaperCheckTests.test_falls_back_when_ibkr_client_errors:101; tests/test_ibkr_paper_check.py:IbkrPaperCheckTests.test_retries_on_retryable_error_then_succeeds:113; tests/test_ibkr_paper_check.py:IbkrPaperCheckTests.test_marks_probe_not_ok_when_news_evidence_missing:123
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_parse_args（行 376-385）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：argparse.Namespace（见函数语义）
- 逐行分析：
  - 行 376：def _parse_args() -> argparse.Namespace: → 无问题
  - 行 377：    parser = argparse.ArgumentParser(prog="phase0-ibkr-paper-check") → 无问题
  - 行 378：    parser.add_argument("--host", default="127.0.0.1") → 无问题
  - 行 379：    parser.add_argument("--port", type=int, default=7497) → 无问题
  - 行 380：    parser.add_argument("--client-id", type=int, default=77) → 无问题
  - 行 381：    parser.add_argument("--timeout", type=float, default=1.0) → 无问题
  - 行 382：    parser.add_argument("--symbol", default="AAPL") → 无问题
  - 行 383：    parser.add_argument("--news-limit", type=int, default=5) → 无问题
  - 行 384：    parser.add_argument("--max-retries", type=int, default=2) → 无问题
  - 行 385：    return parser.parse_args() → 无问题
- 调用的外部函数：argparse.ArgumentParser; parser.add_argument; parser.parse_args
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：main（行 388-403）
- 功能：执行对应业务逻辑
- 参数：无
- 返回值：int（见函数语义）
- 逐行分析：
  - 行 388：def main() -> int: → 无问题
  - 行 389：    args = _parse_args() → 无问题
  - 行 390：    config = ProbeConfig( → 无问题
  - 行 391：        host=args.host, → 无问题
  - 行 392：        port=args.port, → 无问题
  - 行 393：        client_id=args.client_id, → 无问题
  - 行 394：        timeout_seconds=args.timeout, → 无问题
  - 行 395：        symbol=args.symbol.upper(), → 无问题
  - 行 396：        news_limit=args.news_limit, → 无问题
  - 行 397：        max_retries=max(0, args.max_retries), → 无问题
  - 行 398：    ) → 无问题
  - 行 399：    report = run_probe(config) → 无问题
  - 行 400：    print(json.dumps(report, ensure_ascii=False)) → 无问题
  - 行 401：    if report.get("ok"): → 无问题
  - 行 402：        return 0 → 无问题
  - 行 403：    return 2 → 无问题
- 调用的外部函数：_parse_args; ProbeConfig; run_probe; print; report.get; json.dumps; args.symbol.upper; max
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：407
- 函数审计数：17
- 发现问题数：0

## 文件：tests/test_ai_layers.py
- 总行数：146
- 函数/方法数：7

### 逐函数检查

#### 函数：__module__（行 1-146）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from datetime import datetime, timedelta, timezone → 无问题
  - 行 4：from pathlib import Path → 无问题
  - 行 5：import sys → 无问题
  - 行 6：import tempfile → 无问题
  - 行 7：import unittest → 无问题
  - 行 8： → 无问题
  - 行 9：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 10： → 无问题
  - 行 11：from phase0.ai.high import assess_high_lane, evaluate_high_adjustment → 无问题
  - 行 12：from phase0.ai.low import analyze_low_lane → 无问题
  - 行 13：from phase0.ai.memory import LayeredMemoryStore, MemoryRecord, PersistentLayeredMemoryStore → 无问题
  - 行 14：from phase0.ai.ultra import evaluate_ultra_guard → 无问题
  - 行 15： → 无问题
  - 行 16： → 无问题
  - 行 17：class AILayersTests(unittest.TestCase): → 无问题
  - 行 29： → 无问题
  - 行 41： → 无问题
  - 行 56： → 无问题
  - 行 79： → 无问题
  - 行 98： → 无问题
  - 行 122： → 无问题
  - 行 143： → 无问题
  - 行 144： → 无问题
  - 行 145：if __name__ == "__main__": → 无问题
  - 行 146：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：AILayersTests.test_ultra_guard_rejects_stale_or_unverified_message（行 18-28）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 18：    def test_ultra_guard_rejects_stale_or_unverified_message(self) -> None: → 无问题
  - 行 19：        now = datetime.now(tz=timezone.utc) → 无问题
  - 行 20：        signal = evaluate_ultra_guard( → 无问题
  - 行 21：            headline="unverified rumor suggests sudden takeover", → 无问题
  - 行 22：            published_at=now - timedelta(hours=8), → 无问题
  - 行 23：            now=now, → 无问题
  - 行 24：            max_age_minutes=180, → 无问题
  - 行 25：        ) → 无问题
  - 行 26：        self.assertFalse(signal.wake_high) → 无问题
  - 行 27：        self.assertLess(signal.authenticity_score, 0.7) → 无问题
  - 行 28：        self.assertGreaterEqual(signal.quick_filter_score, 0.0) → 无问题
- 调用的外部函数：datetime.now; evaluate_ultra_guard; self.assertFalse; self.assertLess; self.assertGreaterEqual; timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：AILayersTests.test_ultra_guard_fast_filter_blocks_on_weak_local_metrics（行 30-40）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 30：    def test_ultra_guard_fast_filter_blocks_on_weak_local_metrics(self) -> None: → 无问题
  - 行 31：        now = datetime.now(tz=timezone.utc) → 无问题
  - 行 32：        signal = evaluate_ultra_guard( → 无问题
  - 行 33：            headline="verified update", → 无问题
  - 行 34：            published_at=now - timedelta(minutes=30), → 无问题
  - 行 35：            now=now, → 无问题
  - 行 36：            max_age_minutes=180, → 无问题
  - 行 37：            market_row={"momentum_20d": 0.0, "relative_strength": 0.01, "liquidity_score": 0.2, "volatility": 0.45}, → 无问题
  - 行 38：        ) → 无问题
  - 行 39：        self.assertEqual("LOCAL_QUICK_FILTER_BLOCKED", signal.reason) → 无问题
  - 行 40：        self.assertFalse(signal.wake_high) → 无问题
- 调用的外部函数：datetime.now; evaluate_ultra_guard; self.assertEqual; self.assertFalse; timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：AILayersTests.test_low_lane_committee_requires_two_of_three（行 42-55）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 42：    def test_low_lane_committee_requires_two_of_three(self) -> None: → 无问题
  - 行 43：        snapshot = { → 无问题
  - 行 44：            "AAPL": {"momentum_20d": 0.09, "relative_strength": 0.24, "sector": "technology"}, → 无问题
  - 行 45：            "XOM": {"momentum_20d": 0.04, "relative_strength": 0.11, "sector": "energy"}, → 无问题
  - 行 46：        } → 无问题
  - 行 47：        analysis = analyze_low_lane( → 无问题
  - 行 48：            market_snapshot=snapshot, → 无问题
  - 行 49：            committee_models=["m1", "m2", "m3"], → 无问题
  - 行 50：            committee_min_support=2, → 无问题
  - 行 51：            strategy_name="sector_rotation", → 无问题
  - 行 52：            strategy_confidence=0.8, → 无问题
  - 行 53：        ) → 无问题
  - 行 54：        self.assertEqual("technology", analysis.preferred_sector) → 无问题
  - 行 55：        self.assertTrue(analysis.committee_approved) → 无问题
- 调用的外部函数：analyze_low_lane; self.assertEqual; self.assertTrue
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：AILayersTests.test_high_adjustment_obeys_single_stoploss_override（行 57-78）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 57：    def test_high_adjustment_obeys_single_stoploss_override(self) -> None: → 无问题
  - 行 58：        first = evaluate_high_adjustment( → 无问题
  - 行 59：            strategy_confidence=0.9, → 无问题
  - 行 60：            low_committee_approved=True, → 无问题
  - 行 61：            high_confidence_gate=0.58, → 无问题
  - 行 62：            current_stop_loss_pct=0.02, → 无问题
  - 行 63：            stop_loss_override_used=False, → 无问题
  - 行 64：            default_stop_loss_pct=0.02, → 无问题
  - 行 65：            max_stop_loss_pct=0.05, → 无问题
  - 行 66：        ) → 无问题
  - 行 67：        second = evaluate_high_adjustment( → 无问题
  - 行 68：            strategy_confidence=0.9, → 无问题
  - 行 69：            low_committee_approved=True, → 无问题
  - 行 70：            high_confidence_gate=0.58, → 无问题
  - 行 71：            current_stop_loss_pct=first.stop_loss_pct, → 无问题
  - 行 72：            stop_loss_override_used=True, → 无问题
  - 行 73：            default_stop_loss_pct=0.02, → 无问题
  - 行 74：            max_stop_loss_pct=0.05, → 无问题
  - 行 75：        ) → 无问题
  - 行 76：        self.assertTrue(first.approved) → 无问题
  - 行 77：        self.assertLessEqual(first.stop_loss_pct, 0.05) → 无问题
  - 行 78：        self.assertEqual(first.stop_loss_pct, second.stop_loss_pct) → 无问题
- 调用的外部函数：evaluate_high_adjustment; self.assertTrue; self.assertLessEqual; self.assertEqual
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：AILayersTests.test_high_assessment_supports_local_or_cloud_mode（行 80-97）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 80：    def test_high_assessment_supports_local_or_cloud_mode(self) -> None: → 无问题
  - 行 81：        assessment = assess_high_lane( → 无问题
  - 行 82：            strategy_name="momentum", → 无问题
  - 行 83：            strategy_confidence=0.82, → 无问题
  - 行 84：            low_committee_approved=True, → 无问题
  - 行 85：            ultra_authenticity_score=0.8, → 无问题
  - 行 86：            quick_filter_score=0.74, → 无问题
  - 行 87：            high_confidence_gate=0.58, → 无问题
  - 行 88：            current_stop_loss_pct=0.02, → 无问题
  - 行 89：            stop_loss_override_used=False, → 无问题
  - 行 90：            default_stop_loss_pct=0.02, → 无问题
  - 行 91：            max_stop_loss_pct=0.05, → 无问题
  - 行 92：            mode="cloud", → 无问题
  - 行 93：            committee_models=["local-risk-v1", "gpt-4o-mini"], → 无问题
  - 行 94：            committee_min_support=1, → 无问题
  - 行 95：        ) → 无问题
  - 行 96：        self.assertEqual("cloud", assessment.mode) → 无问题
  - 行 97：        self.assertTrue(len(assessment.committee_votes) >= 1) → 无问题
- 调用的外部函数：assess_high_lane; self.assertEqual; self.assertTrue; len
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：AILayersTests.test_layered_memory_returns_relevant_records（行 99-121）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 99：    def test_layered_memory_returns_relevant_records(self) -> None: → 无问题
  - 行 100：        now = datetime.now(tz=timezone.utc) → 无问题
  - 行 101：        store = LayeredMemoryStore( → 无问题
  - 行 102：            [ → 无问题
  - 行 103：                MemoryRecord( → 无问题
  - 行 104：                    memory_id="a", → 无问题
  - 行 105：                    tier="short", → 无问题
  - 行 106：                    text="一天前消费电子行业提到小米手机出货恢复", → 无问题
  - 行 107：                    published_at=now - timedelta(days=1), → 无问题
  - 行 108：                    tags=("小米", "消费电子"), → 无问题
  - 行 109：                ), → 无问题
  - 行 110：                MemoryRecord( → 无问题
  - 行 111：                    memory_id="b", → 无问题
  - 行 112：                    tier="long", → 无问题
  - 行 113：                    text="半年前国际油价下跌", → 无问题
  - 行 114：                    published_at=now - timedelta(days=180), → 无问题
  - 行 115：                    tags=("石油", "能源"), → 无问题
  - 行 116：                ), → 无问题
  - 行 117：            ] → 无问题
  - 行 118：        ) → 无问题
  - 行 119：        rows = store.query("小米 消费电子", now=now, limit=1) → 无问题
  - 行 120：        self.assertEqual(1, len(rows)) → 无问题
  - 行 121：        self.assertEqual("a", rows[0].memory_id) → 无问题
- 调用的外部函数：datetime.now; LayeredMemoryStore; store.query; self.assertEqual; len; MemoryRecord; timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：AILayersTests.test_persistent_memory_store_loads_from_disk（行 123-142）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 123：    def test_persistent_memory_store_loads_from_disk(self) -> None: → 无问题
  - 行 124：        now = datetime.now(tz=timezone.utc) → 无问题
  - 行 125：        with tempfile.TemporaryDirectory() as tmpdir: → 无问题
  - 行 126：            db_path = str(Path(tmpdir) / "memory.db") → 无问题
  - 行 127：            PersistentLayeredMemoryStore( → 无问题
  - 行 128：                db_path=db_path, → 无问题
  - 行 129：                records=[ → 无问题
  - 行 130：                    MemoryRecord( → 无问题
  - 行 131：                        memory_id="persisted-1", → 无问题
  - 行 132：                        tier="short", → 无问题
  - 行 133：                        text="小米消费电子供应链改善", → 无问题
  - 行 134：                        published_at=now - timedelta(days=1), → 无问题
  - 行 135：                        tags=("小米", "消费电子"), → 无问题
  - 行 136：                    ) → 无问题
  - 行 137：                ], → 无问题
  - 行 138：            ) → 无问题
  - 行 139：            loaded = PersistentLayeredMemoryStore.from_db(db_path) → 无问题
  - 行 140：            rows = loaded.query("小米 消费电子", now=now, limit=1) → 无问题
  - 行 141：            self.assertEqual(1, len(rows)) → 无问题
  - 行 142：            self.assertEqual("persisted-1", rows[0].memory_id) → 无问题
- 调用的外部函数：datetime.now; tempfile.TemporaryDirectory; str; PersistentLayeredMemoryStore; PersistentLayeredMemoryStore.from_db; loaded.query; self.assertEqual; len; Path; MemoryRecord; timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：146
- 函数审计数：7
- 发现问题数：0

## 文件：tests/test_app_health.py
- 总行数：40
- 函数/方法数：4

### 逐函数检查

#### 函数：__module__（行 1-40）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6：from unittest.mock import patch → 无问题
  - 行 7： → 无问题
  - 行 8：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 9： → 无问题
  - 行 10：from phase0.app import health_check → 无问题
  - 行 11：from phase0.config import load_config → 无问题
  - 行 12： → 无问题
  - 行 13： → 无问题
  - 行 14：class AppHealthTests(unittest.TestCase): → 无问题
  - 行 22： → 无问题
  - 行 37： → 无问题
  - 行 38： → 无问题
  - 行 39：if __name__ == "__main__": → 无问题
  - 行 40：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：AppHealthTests.test_health_check_returns_lockdown_when_ibkr_unreachable（行 15-21）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 15：    def test_health_check_returns_lockdown_when_ibkr_unreachable(self) -> None: → 无问题
  - 行 16：        config = load_config() → 无问题
  - 行 17：        with patch("phase0.app.socket.create_connection", side_effect=OSError("unreachable")): → 无问题
  - 行 18：            summary = health_check(config) → 无问题
  - 行 19：        self.assertEqual("lockdown", summary["safety_mode"]) → 无问题
  - 行 20：        self.assertEqual("false", summary["risk_execution_enabled"]) → 无问题
  - 行 21：        self.assertEqual("rejected", summary["execution_status"]) → 无问题
- 调用的外部函数：load_config; self.assertEqual; patch; health_check; OSError
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：AppHealthTests.test_health_check_returns_normal_when_ibkr_reachable（行 23-36）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 23：    def test_health_check_returns_normal_when_ibkr_reachable(self) -> None: → 无问题
  - 行 24：        config = load_config() → 无问题
  - 行 25： → 无问题
  - 行 26：        class _DummySocket: → 无问题
  - 行 27：            def __enter__(self) -> "_DummySocket": → 无问题
  - 行 28：                return self → 无问题
  - 行 29： → 无问题
  - 行 30：            def __exit__(self, exc_type: object, exc: object, tb: object) -> None: → 无问题
  - 行 31：                return None → 无问题
  - 行 32： → 无问题
  - 行 33：        with patch("phase0.app.socket.create_connection", return_value=_DummySocket()): → 无问题
  - 行 34：            summary = health_check(config) → 无问题
  - 行 35：        self.assertEqual("normal", summary["safety_mode"]) → 无问题
  - 行 36：        self.assertEqual("true", summary["risk_execution_enabled"]) → 无问题
- 调用的外部函数：load_config; self.assertEqual; patch; health_check; _DummySocket
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：AppHealthTests._DummySocket.__enter__（行 27-28）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：'_DummySocket'（见函数语义）
- 逐行分析：
  - 行 27：            def __enter__(self) -> "_DummySocket": → 无问题
  - 行 28：                return self → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：AppHealthTests._DummySocket.__exit__（行 30-31）
- 功能：执行对应业务逻辑
- 参数：self: Any, exc_type: object, exc: object, tb: object
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 30：            def __exit__(self, exc_type: object, exc: object, tb: object) -> None: → 无问题
  - 行 31：                return None → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：40
- 函数审计数：4
- 发现问题数：0

## 文件：tests/test_audit_and_memory_persistence.py
- 总行数：44
- 函数/方法数：1

### 逐函数检查

#### 函数：__module__（行 1-44）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sqlite3 → 无问题
  - 行 5：import sys → 无问题
  - 行 6：import tempfile → 无问题
  - 行 7：import unittest → 无问题
  - 行 8：from unittest.mock import patch → 无问题
  - 行 9： → 无问题
  - 行 10：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 11： → 无问题
  - 行 12：from phase0.config import load_config → 无问题
  - 行 13：from phase0.lanes import run_lane_cycle → 无问题
  - 行 14： → 无问题
  - 行 15： → 无问题
  - 行 16：class AuditAndMemoryPersistenceTests(unittest.TestCase): → 无问题
  - 行 41： → 无问题
  - 行 42： → 无问题
  - 行 43：if __name__ == "__main__": → 无问题
  - 行 44：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：AuditAndMemoryPersistenceTests.test_writes_parameter_audit_and_memory_db（行 17-40）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 17：    def test_writes_parameter_audit_and_memory_db(self) -> None: → 无问题
  - 行 18：        with tempfile.TemporaryDirectory() as tmpdir: → 无问题
  - 行 19：            state_db = str(Path(tmpdir) / "state.db") → 无问题
  - 行 20：            memory_db = str(Path(tmpdir) / "memory.db") → 无问题
  - 行 21：            with patch.dict( → 无问题
  - 行 22：                "os.environ", → 无问题
  - 行 23：                { → 无问题
  - 行 24：                    "AI_STATE_DB_PATH": state_db, → 无问题
  - 行 25：                    "AI_MEMORY_DB_PATH": memory_db, → 无问题
  - 行 26：                }, → 无问题
  - 行 27：                clear=False, → 无问题
  - 行 28：            ): → 无问题
  - 行 29：                config = load_config() → 无问题
  - 行 30：                output = run_lane_cycle("AAPL", config=config) → 无问题
  - 行 31：            self.assertIn("low_async_processed", output) → 无问题
  - 行 32：            self.assertGreaterEqual(output["low_async_processed"], 1) → 无问题
  - 行 33：            with sqlite3.connect(state_db) as conn: → 无问题
  - 行 34：                rows = conn.execute("SELECT COUNT(*) FROM parameter_audit").fetchone() → 无问题
  - 行 35：            self.assertIsNotNone(rows) → 无问题
  - 行 36：            self.assertGreaterEqual(int(rows[0]), 1) → 无问题
  - 行 37：            with sqlite3.connect(memory_db) as conn: → 无问题
  - 行 38：                mem_rows = conn.execute("SELECT COUNT(*) FROM memory_records").fetchone() → 无问题
  - 行 39：            self.assertIsNotNone(mem_rows) → 无问题
  - 行 40：            self.assertGreaterEqual(int(mem_rows[0]), 1) → 无问题
- 调用的外部函数：tempfile.TemporaryDirectory; str; self.assertIn; self.assertGreaterEqual; self.assertIsNotNone; patch.dict; load_config; run_lane_cycle; sqlite3.connect; fetchone; int; Path; conn.execute
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：44
- 函数审计数：1
- 发现问题数：0

## 文件：tests/test_config.py
- 总行数：115
- 函数/方法数：3

### 逐函数检查

#### 函数：__module__（行 1-115）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6：from unittest.mock import patch → 无问题
  - 行 7： → 无问题
  - 行 8：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 9： → 无问题
  - 行 10：from phase0.config import RuntimeMode, RuntimeProfile, load_config → 无问题
  - 行 11：from phase0.errors import AppError → 无问题
  - 行 12： → 无问题
  - 行 13： → 无问题
  - 行 14：class ConfigTests(unittest.TestCase): → 无问题
  - 行 102： → 无问题
  - 行 107： → 无问题
  - 行 112： → 无问题
  - 行 113： → 无问题
  - 行 114：if __name__ == "__main__": → 无问题
  - 行 115：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：ConfigTests.test_loads_llm_gateway_related_settings（行 15-101）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 15：    def test_loads_llm_gateway_related_settings(self) -> None: → 无问题
  - 行 16：        env = { → 无问题
  - 行 17：            "PHASE0_PROFILE": "cloud", → 无问题
  - 行 18：            "LLM_BASE_URL": "https://gateway.example.com/v1", → 无问题
  - 行 19：            "LLM_API_KEY": "secret", → 无问题
  - 行 20：            "LLM_LOCAL_MODEL": "qwen2.5:14b", → 无问题
  - 行 21：            "LLM_CLOUD_MODEL": "gpt-4o-mini", → 无问题
  - 行 22：            "LLM_TIMEOUT_SECONDS": "30", → 无问题
  - 行 23：            "LLM_MAX_RETRIES": "5", → 无问题
  - 行 24：            "LLM_BACKOFF_SECONDS": "0.25", → 无问题
  - 行 25：            "LLM_RATE_LIMIT_PER_SECOND": "12", → 无问题
  - 行 26：            "RUNTIME_MODE": "eco", → 无问题
  - 行 27：            "RISK_SINGLE_TRADE_PCT": "0.012", → 无问题
  - 行 28：            "RISK_TOTAL_EXPOSURE_PCT": "0.28", → 无问题
  - 行 29：            "RISK_STOP_LOSS_MIN_PCT": "0.04", → 无问题
  - 行 30：            "RISK_STOP_LOSS_MAX_PCT": "0.09", → 无问题
  - 行 31：            "RISK_COOLDOWN_HOURS": "12", → 无问题
  - 行 32：            "RISK_HOLDING_DAYS": "3", → 无问题
  - 行 33：            "LANE_BUS_DEDUP_TTL_SECONDS": "90", → 无问题
  - 行 34：            "STRATEGY_ENABLED_LIST": "momentum,news_sentiment", → 无问题
  - 行 35：            "STRATEGY_ROTATION_TOP_K": "4", → 无问题
  - 行 36：            "STRATEGY_NEWS_POSITIVE_THRESHOLD": "0.25", → 无问题
  - 行 37：            "STRATEGY_NEWS_NEGATIVE_THRESHOLD": "-0.3", → 无问题
  - 行 38：            "STRATEGY_PLUGIN_MODULES": "my_quant_pkg.strategies", → 无问题
  - 行 39：            "FACTOR_PLUGIN_MODULES": "my_quant_pkg.factors", → 无问题
  - 行 40：            "HIGH_RISK_MULTIPLIER_MIN": "0.7", → 无问题
  - 行 41：            "HIGH_RISK_MULTIPLIER_MAX": "1.4", → 无问题
  - 行 42：            "HIGH_TAKE_PROFIT_BOOST_MAX_PCT": "0.15", → 无问题
  - 行 43：            "AI_MESSAGE_MAX_AGE_MINUTES": "240", → 无问题
  - 行 44：            "AI_LOW_COMMITTEE_MODELS": "m1,m2,m3", → 无问题
  - 行 45：            "AI_LOW_COMMITTEE_MIN_SUPPORT": "2", → 无问题
  - 行 46：            "AI_HIGH_MODE": "cloud", → 无问题
  - 行 47：            "AI_HIGH_COMMITTEE_MODELS": "h1,h2,h3", → 无问题
  - 行 48：            "AI_HIGH_COMMITTEE_MIN_SUPPORT": "2", → 无问题
  - 行 49：            "AI_HIGH_CONFIDENCE_GATE": "0.6", → 无问题
  - 行 50：            "AI_STOP_LOSS_DEFAULT_PCT": "0.02", → 无问题
  - 行 51：            "AI_STOP_LOSS_BREAK_MAX_PCT": "0.05", → 无问题
  - 行 52：            "AI_STATE_DB_PATH": "artifacts/custom_state.db", → 无问题
  - 行 53：            "AI_MEMORY_DB_PATH": "artifacts/custom_memory.db", → 无问题
  - 行 54：            "AI_ENABLED": "false", → 无问题
  - 行 55：            "DISCIPLINE_MIN_ACTIONS_PER_DAY": "2", → 无问题
  - 行 56：            "DISCIPLINE_HOLD_SCORE_THRESHOLD": "0.8", → 无问题
  - 行 57：            "DISCIPLINE_ENABLE_DAILY_CYCLE": "true", → 无问题
  - 行 58：        } → 无问题
  - 行 59：        with patch.dict("os.environ", env, clear=True): → 无问题
  - 行 60：            config = load_config() → 无问题
  - 行 61：        self.assertEqual(RuntimeProfile.CLOUD, config.runtime_profile) → 无问题
  - 行 62：        self.assertEqual(RuntimeMode.ECO, config.runtime_mode) → 无问题
  - 行 63：        self.assertEqual("https://gateway.example.com/v1", config.llm_base_url) → 无问题
  - 行 64：        self.assertEqual("secret", config.llm_api_key) → 无问题
  - 行 65：        self.assertEqual("qwen2.5:14b", config.llm_local_model) → 无问题
  - 行 66：        self.assertEqual("gpt-4o-mini", config.llm_cloud_model) → 无问题
  - 行 67：        self.assertEqual(30.0, config.llm_timeout_seconds) → 无问题
  - 行 68：        self.assertEqual(5, config.llm_max_retries) → 无问题
  - 行 69：        self.assertEqual(0.25, config.llm_backoff_seconds) → 无问题
  - 行 70：        self.assertEqual(12.0, config.llm_rate_limit_per_second) → 无问题
  - 行 71：        self.assertEqual(0.012, config.risk_single_trade_pct) → 无问题
  - 行 72：        self.assertEqual(0.28, config.risk_total_exposure_pct) → 无问题
  - 行 73：        self.assertEqual(0.04, config.risk_stop_loss_min_pct) → 无问题
  - 行 74：        self.assertEqual(0.09, config.risk_stop_loss_max_pct) → 无问题
  - 行 75：        self.assertEqual(12, config.cooldown_hours) → 无问题
  - 行 76：        self.assertEqual(3, config.holding_days) → 无问题
  - 行 77：        self.assertEqual(90, config.lane_bus_dedup_ttl_seconds) → 无问题
  - 行 78：        self.assertEqual("momentum,news_sentiment", config.strategy_enabled_list) → 无问题
  - 行 79：        self.assertEqual(4, config.strategy_rotation_top_k) → 无问题
  - 行 80：        self.assertEqual(0.25, config.strategy_news_positive_threshold) → 无问题
  - 行 81：        self.assertEqual(-0.3, config.strategy_news_negative_threshold) → 无问题
  - 行 82：        self.assertEqual("my_quant_pkg.strategies", config.strategy_plugin_modules) → 无问题
  - 行 83：        self.assertEqual("my_quant_pkg.factors", config.factor_plugin_modules) → 无问题
  - 行 84：        self.assertEqual(0.7, config.high_risk_multiplier_min) → 无问题
  - 行 85：        self.assertEqual(1.4, config.high_risk_multiplier_max) → 无问题
  - 行 86：        self.assertEqual(0.15, config.high_take_profit_boost_max_pct) → 无问题
  - 行 87：        self.assertEqual(240, config.ai_message_max_age_minutes) → 无问题
  - 行 88：        self.assertEqual("m1,m2,m3", config.ai_low_committee_models) → 无问题
  - 行 89：        self.assertEqual(2, config.ai_low_committee_min_support) → 无问题
  - 行 90：        self.assertEqual("cloud", config.ai_high_mode) → 无问题
  - 行 91：        self.assertEqual("h1,h2,h3", config.ai_high_committee_models) → 无问题
  - 行 92：        self.assertEqual(2, config.ai_high_committee_min_support) → 无问题
  - 行 93：        self.assertEqual(0.6, config.ai_high_confidence_gate) → 无问题
  - 行 94：        self.assertEqual(0.02, config.ai_stop_loss_default_pct) → 无问题
  - 行 95：        self.assertEqual(0.05, config.ai_stop_loss_break_max_pct) → 无问题
  - 行 96：        self.assertEqual("artifacts/custom_state.db", config.ai_state_db_path) → 无问题
  - 行 97：        self.assertEqual("artifacts/custom_memory.db", config.ai_memory_db_path) → 无问题
  - 行 98：        self.assertFalse(config.ai_enabled) → 无问题
  - 行 99：        self.assertEqual(2, config.discipline_min_actions_per_day) → 无问题
  - 行 100：        self.assertEqual(0.8, config.discipline_hold_score_threshold) → 无问题
  - 行 101：        self.assertTrue(config.discipline_enable_daily_cycle) → 无问题
- 调用的外部函数：self.assertEqual; self.assertFalse; self.assertTrue; patch.dict; load_config
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：ConfigTests.test_raises_when_retry_rate_is_invalid_float（行 103-106）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 103：    def test_raises_when_retry_rate_is_invalid_float(self) -> None: → 无问题
  - 行 104：        with patch.dict("os.environ", {"LLM_RATE_LIMIT_PER_SECOND": "invalid"}, clear=True): → 无问题
  - 行 105：            with self.assertRaises(AppError): → 无问题
  - 行 106：                load_config() → 无问题
- 调用的外部函数：patch.dict; self.assertRaises; load_config
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：ConfigTests.test_raises_when_runtime_mode_is_invalid（行 108-111）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 108：    def test_raises_when_runtime_mode_is_invalid(self) -> None: → 无问题
  - 行 109：        with patch.dict("os.environ", {"RUNTIME_MODE": "turbo"}, clear=True): → 无问题
  - 行 110：            with self.assertRaises(AppError): → 无问题
  - 行 111：                load_config() → 无问题
- 调用的外部函数：patch.dict; self.assertRaises; load_config
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：115
- 函数审计数：3
- 发现问题数：0

## 文件：tests/test_discipline_and_ibkr_adapter.py
- 总行数：62
- 函数/方法数：2

### 逐函数检查

#### 函数：__module__（行 1-62）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6： → 无问题
  - 行 7：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 8： → 无问题
  - 行 9：from phase0.discipline import build_daily_discipline_plan, evaluate_hold_worthiness → 无问题
  - 行 10：from phase0.ibkr_order_adapter import map_decision_to_ibkr_bracket → 无问题
  - 行 11：from phase0.lanes.high import evaluate_event → 无问题
  - 行 12： → 无问题
  - 行 13： → 无问题
  - 行 14：class DisciplineAndIbkrAdapterTests(unittest.TestCase): → 无问题
  - 行 33： → 无问题
  - 行 59： → 无问题
  - 行 60： → 无问题
  - 行 61：if __name__ == "__main__": → 无问题
  - 行 62：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：DisciplineAndIbkrAdapterTests.test_hold_score_and_daily_plan（行 15-32）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 15：    def test_hold_score_and_daily_plan(self) -> None: → 无问题
  - 行 16：        hold = evaluate_hold_worthiness( → 无问题
  - 行 17：            market_row={"momentum_20d": 0.1, "relative_strength": 0.24, "volatility": 0.2}, → 无问题
  - 行 18：            strategy_confidence=0.75, → 无问题
  - 行 19：            ultra_authenticity_score=0.8, → 无问题
  - 行 20：            low_committee_approved=True, → 无问题
  - 行 21：            hold_score_threshold=0.72, → 无问题
  - 行 22：            max_holding_days=3, → 无问题
  - 行 23：        ) → 无问题
  - 行 24：        self.assertTrue(hold.score > 0.0) → 无问题
  - 行 25：        plan = build_daily_discipline_plan( → 无问题
  - 行 26：            actions_today=0, → 无问题
  - 行 27：            has_open_position=False, → 无问题
  - 行 28：            min_actions_per_day=1, → 无问题
  - 行 29：            discipline_enabled=True, → 无问题
  - 行 30：            hold=hold, → 无问题
  - 行 31：        ) → 无问题
  - 行 32：        self.assertEqual("buy", plan["required_action"]) → 无问题
- 调用的外部函数：evaluate_hold_worthiness; self.assertTrue; build_daily_discipline_plan; self.assertEqual
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：DisciplineAndIbkrAdapterTests.test_ibkr_mapping_uses_stp_and_transmit_chain（行 34-58）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 34：    def test_ibkr_mapping_uses_stp_and_transmit_chain(self) -> None: → 无问题
  - 行 35：        decision = evaluate_event( → 无问题
  - 行 36：            { → 无问题
  - 行 37：                "lane": "ultra", → 无问题
  - 行 38：                "kind": "signal", → 无问题
  - 行 39：                "symbol": "AAPL", → 无问题
  - 行 40：                "side": "buy", → 无问题
  - 行 41：                "entry_price": "100", → 无问题
  - 行 42：                "stop_loss_price": "95", → 无问题
  - 行 43：                "take_profit_price": "108", → 无问题
  - 行 44：                "equity": "100000", → 无问题
  - 行 45：                "current_exposure": "5000", → 无问题
  - 行 46：            } → 无问题
  - 行 47：        ) → 无问题
  - 行 48：        self.assertEqual("accepted", decision["status"]) → 无问题
  - 行 49：        payload = map_decision_to_ibkr_bracket(decision) → 无问题
  - 行 50：        self.assertIsNotNone(payload) → 无问题
  - 行 51：        assert payload is not None → 无问题
  - 行 52：        orders = payload["orders"] → 无问题
  - 行 53：        self.assertEqual("LMT", orders[0]["orderType"]) → 无问题
  - 行 54：        self.assertEqual("LMT", orders[1]["orderType"]) → 无问题
  - 行 55：        self.assertEqual("STP", orders[2]["orderType"]) → 无问题
  - 行 56：        self.assertFalse(orders[0]["transmit"]) → 无问题
  - 行 57：        self.assertFalse(orders[1]["transmit"]) → 无问题
  - 行 58：        self.assertTrue(orders[2]["transmit"]) → 无问题
- 调用的外部函数：evaluate_event; self.assertEqual; map_decision_to_ibkr_bracket; self.assertIsNotNone; self.assertFalse; self.assertTrue
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：62
- 函数审计数：2
- 发现问题数：0

## 文件：tests/test_high_lane.py
- 总行数：161
- 函数/方法数：16

### 逐函数检查

#### 函数：__module__（行 1-161）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from datetime import datetime, timedelta, timezone → 无问题
  - 行 4：from pathlib import Path → 无问题
  - 行 5：import sys → 无问题
  - 行 6：import unittest → 无问题
  - 行 7： → 无问题
  - 行 8：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 9： → 无问题
  - 行 10：from phase0.lanes.high import HighLaneSettings, evaluate_event → 无问题
  - 行 11： → 无问题
  - 行 12： → 无问题
  - 行 13：class HighLaneRuleEngineTests(unittest.TestCase): → 无问题
  - 行 28： → 无问题
  - 行 45： → 无问题
  - 行 53： → 无问题
  - 行 60： → 无问题
  - 行 67： → 无问题
  - 行 74： → 无问题
  - 行 83： → 无问题
  - 行 91： → 无问题
  - 行 98： → 无问题
  - 行 105： → 无问题
  - 行 114： → 无问题
  - 行 121： → 无问题
  - 行 127： → 无问题
  - 行 138： → 无问题
  - 行 149： → 无问题
  - 行 158： → 无问题
  - 行 159： → 无问题
  - 行 160：if __name__ == "__main__": → 无问题
  - 行 161：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：HighLaneRuleEngineTests.setUp（行 14-27）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 14：    def setUp(self) -> None: → 无问题
  - 行 15：        now = datetime.now(tz=timezone.utc) → 无问题
  - 行 16：        self.base_event = { → 无问题
  - 行 17：            "lane": "ultra", → 无问题
  - 行 18：            "kind": "signal", → 无问题
  - 行 19：            "symbol": "AAPL", → 无问题
  - 行 20：            "side": "buy", → 无问题
  - 行 21：            "entry_price": "100", → 无问题
  - 行 22：            "stop_loss_price": "95", → 无问题
  - 行 23：            "take_profit_price": "108", → 无问题
  - 行 24：            "equity": "100000", → 无问题
  - 行 25：            "current_exposure": "5000", → 无问题
  - 行 26：            "last_exit_at": (now - timedelta(days=3)).isoformat(), → 无问题
  - 行 27：        } → 无问题
- 调用的外部函数：datetime.now; isoformat; timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_accepts_and_builds_bracket_order（行 29-44）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 29：    def test_accepts_and_builds_bracket_order(self) -> None: → 无问题
  - 行 30：        decision = evaluate_event(self.base_event) → 无问题
  - 行 31：        self.assertEqual("accepted", decision["status"]) → 无问题
  - 行 32：        self.assertIsInstance(decision["quantity"], int) → 无问题
  - 行 33：        self.assertGreater(decision["quantity"], 0) → 无问题
  - 行 34：        self.assertEqual([], decision["reject_reasons"]) → 无问题
  - 行 35：        bracket = decision["bracket_order"] → 无问题
  - 行 36：        self.assertEqual("BUY", bracket["parent"]["action"]) → 无问题
  - 行 37：        self.assertEqual("SELL", bracket["take_profit"]["action"]) → 无问题
  - 行 38：        self.assertEqual("SELL", bracket["stop_loss"]["action"]) → 无问题
  - 行 39：        self.assertEqual(decision["quantity"], bracket["parent"]["quantity"]) → 无问题
  - 行 40：        self.assertEqual(decision["quantity"], bracket["take_profit"]["quantity"]) → 无问题
  - 行 41：        self.assertEqual(decision["quantity"], bracket["stop_loss"]["quantity"]) → 无问题
  - 行 42：        self.assertEqual("LIMIT", bracket["parent"]["order_type"]) → 无问题
  - 行 43：        self.assertEqual("LIMIT", bracket["take_profit"]["order_type"]) → 无问题
  - 行 44：        self.assertEqual("STOP", bracket["stop_loss"]["order_type"]) → 无问题
- 调用的外部函数：evaluate_event; self.assertEqual; self.assertIsInstance; self.assertGreater
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_enforces_single_trade_risk_1pct（行 46-52）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 46：    def test_enforces_single_trade_risk_1pct(self) -> None: → 无问题
  - 行 47：        event = dict(self.base_event) → 无问题
  - 行 48：        event["entry_price"] = "100" → 无问题
  - 行 49：        event["stop_loss_price"] = "75" → 无问题
  - 行 50：        decision = evaluate_event(event) → 无问题
  - 行 51：        self.assertEqual("rejected", decision["status"]) → 无问题
  - 行 52：        self.assertIn("STOP_LOSS_RANGE_INVALID", decision["reject_reasons"]) → 无问题
- 调用的外部函数：dict; evaluate_event; self.assertEqual; self.assertIn
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_rejects_when_risk_budget_cannot_buy_one_share（行 54-59）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 54：    def test_rejects_when_risk_budget_cannot_buy_one_share(self) -> None: → 无问题
  - 行 55：        event = dict(self.base_event) → 无问题
  - 行 56：        event["equity"] = "100" → 无问题
  - 行 57：        decision = evaluate_event(event) → 无问题
  - 行 58：        self.assertEqual("rejected", decision["status"]) → 无问题
  - 行 59：        self.assertIn("RISK_BUDGET_EXCEEDED", decision["reject_reasons"]) → 无问题
- 调用的外部函数：dict; evaluate_event; self.assertEqual; self.assertIn
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_rejects_with_cooldown_reason（行 61-66）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 61：    def test_rejects_with_cooldown_reason(self) -> None: → 无问题
  - 行 62：        event = dict(self.base_event) → 无问题
  - 行 63：        event["last_exit_at"] = (datetime.now(tz=timezone.utc) - timedelta(hours=12)).isoformat() → 无问题
  - 行 64：        decision = evaluate_event(event) → 无问题
  - 行 65：        self.assertEqual("rejected", decision["status"]) → 无问题
  - 行 66：        self.assertIn("COOLDOWN_24H_ACTIVE", decision["reject_reasons"]) → 无问题
- 调用的外部函数：dict; isoformat; evaluate_event; self.assertEqual; self.assertIn; datetime.now; timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_rejects_when_holding_period_exceeded（行 68-73）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 68：    def test_rejects_when_holding_period_exceeded(self) -> None: → 无问题
  - 行 69：        event = dict(self.base_event) → 无问题
  - 行 70：        event["position_opened_at"] = (datetime.now(tz=timezone.utc) - timedelta(days=3)).isoformat() → 无问题
  - 行 71：        decision = evaluate_event(event) → 无问题
  - 行 72：        self.assertEqual("rejected", decision["status"]) → 无问题
  - 行 73：        self.assertIn("HOLDING_PERIOD_EXCEEDED", decision["reject_reasons"]) → 无问题
- 调用的外部函数：dict; isoformat; evaluate_event; self.assertEqual; self.assertIn; datetime.now; timedelta
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_rejects_when_exposure_limit_prevents_integer_shares（行 75-82）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 75：    def test_rejects_when_exposure_limit_prevents_integer_shares(self) -> None: → 无问题
  - 行 76：        event = dict(self.base_event) → 无问题
  - 行 77：        event["current_exposure"] = "29999.5" → 无问题
  - 行 78：        event["equity"] = "100000" → 无问题
  - 行 79：        event["entry_price"] = "100" → 无问题
  - 行 80：        decision = evaluate_event(event) → 无问题
  - 行 81：        self.assertEqual("rejected", decision["status"]) → 无问题
  - 行 82：        self.assertIn("TOTAL_EXPOSURE_LIMIT", decision["reject_reasons"]) → 无问题
- 调用的外部函数：dict; evaluate_event; self.assertEqual; self.assertIn
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_rejects_when_stop_loss_equals_entry（行 84-90）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 84：    def test_rejects_when_stop_loss_equals_entry(self) -> None: → 无问题
  - 行 85：        event = dict(self.base_event) → 无问题
  - 行 86：        event["entry_price"] = "100" → 无问题
  - 行 87：        event["stop_loss_price"] = "100" → 无问题
  - 行 88：        decision = evaluate_event(event) → 无问题
  - 行 89：        self.assertEqual("rejected", decision["status"]) → 无问题
  - 行 90：        self.assertIn("STOP_LOSS_DIRECTION_INVALID", decision["reject_reasons"]) → 无问题
- 调用的外部函数：dict; evaluate_event; self.assertEqual; self.assertIn
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_rejects_when_source_lane_is_not_ultra（行 92-97）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 92：    def test_rejects_when_source_lane_is_not_ultra(self) -> None: → 无问题
  - 行 93：        event = dict(self.base_event) → 无问题
  - 行 94：        event["lane"] = "low" → 无问题
  - 行 95：        decision = evaluate_event(event) → 无问题
  - 行 96：        self.assertEqual("rejected", decision["status"]) → 无问题
  - 行 97：        self.assertIn("SOURCE_LANE_INVALID", decision["reject_reasons"]) → 无问题
- 调用的外部函数：dict; evaluate_event; self.assertEqual; self.assertIn
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_rejects_when_event_kind_is_invalid（行 99-104）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 99：    def test_rejects_when_event_kind_is_invalid(self) -> None: → 无问题
  - 行 100：        event = dict(self.base_event) → 无问题
  - 行 101：        event["kind"] = "order" → 无问题
  - 行 102：        decision = evaluate_event(event) → 无问题
  - 行 103：        self.assertEqual("rejected", decision["status"]) → 无问题
  - 行 104：        self.assertIn("EVENT_KIND_INVALID", decision["reject_reasons"]) → 无问题
- 调用的外部函数：dict; evaluate_event; self.assertEqual; self.assertIn
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_generates_unique_client_order_id（行 106-113）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 106：    def test_generates_unique_client_order_id(self) -> None: → 无问题
  - 行 107：        first = evaluate_event(self.base_event) → 无问题
  - 行 108：        second = evaluate_event(self.base_event) → 无问题
  - 行 109：        self.assertEqual("accepted", first["status"]) → 无问题
  - 行 110：        self.assertEqual("accepted", second["status"]) → 无问题
  - 行 111：        first_parent = first["bracket_order"]["parent"]["client_order_id"] → 无问题
  - 行 112：        second_parent = second["bracket_order"]["parent"]["client_order_id"] → 无问题
  - 行 113：        self.assertNotEqual(first_parent, second_parent) → 无问题
- 调用的外部函数：evaluate_event; self.assertEqual; self.assertNotEqual
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_supports_adjustable_risk_settings（行 115-120）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 115：    def test_supports_adjustable_risk_settings(self) -> None: → 无问题
  - 行 116：        event = dict(self.base_event) → 无问题
  - 行 117：        event["current_exposure"] = "25000" → 无问题
  - 行 118：        settings = HighLaneSettings(total_exposure_limit_pct=0.4) → 无问题
  - 行 119：        decision = evaluate_event(event, settings=settings) → 无问题
  - 行 120：        self.assertEqual("accepted", decision["status"]) → 无问题
- 调用的外部函数：dict; HighLaneSettings; evaluate_event; self.assertEqual
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_rejects_when_settings_boundary_invalid（行 122-126）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 122：    def test_rejects_when_settings_boundary_invalid(self) -> None: → 无问题
  - 行 123：        settings = HighLaneSettings(stop_loss_min_pct=0.09, stop_loss_max_pct=0.08) → 无问题
  - 行 124：        decision = evaluate_event(self.base_event, settings=settings) → 无问题
  - 行 125：        self.assertEqual("rejected", decision["status"]) → 无问题
  - 行 126：        self.assertIn("STOP_LOSS_SETTINGS_INVALID", decision["reject_reasons"]) → 无问题
- 调用的外部函数：HighLaneSettings; evaluate_event; self.assertEqual; self.assertIn
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_handles_large_numeric_inputs_stably（行 128-137）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 128：    def test_handles_large_numeric_inputs_stably(self) -> None: → 无问题
  - 行 129：        event = dict(self.base_event) → 无问题
  - 行 130：        event["entry_price"] = "250.5" → 无问题
  - 行 131：        event["stop_loss_price"] = "237.5" → 无问题
  - 行 132：        event["take_profit_price"] = "290.0" → 无问题
  - 行 133：        event["equity"] = "999999999" → 无问题
  - 行 134：        event["current_exposure"] = "120000000" → 无问题
  - 行 135：        decision = evaluate_event(event) → 无问题
  - 行 136：        self.assertEqual("accepted", decision["status"]) → 无问题
  - 行 137：        self.assertGreater(decision["quantity"], 0) → 无问题
- 调用的外部函数：dict; evaluate_event; self.assertEqual; self.assertGreater
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_applies_strategy_adjustments_with_bounds（行 139-148）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 139：    def test_applies_strategy_adjustments_with_bounds(self) -> None: → 无问题
  - 行 140：        settings = HighLaneSettings(risk_multiplier_min=0.6, risk_multiplier_max=1.2, take_profit_boost_max_pct=0.1) → 无问题
  - 行 141：        decision = evaluate_event( → 无问题
  - 行 142：            self.base_event, → 无问题
  - 行 143：            settings=settings, → 无问题
  - 行 144：            strategy_adjustments={"risk_multiplier": 2.0, "take_profit_boost_pct": 0.5}, → 无问题
  - 行 145：        ) → 无问题
  - 行 146：        self.assertEqual("accepted", decision["status"]) → 无问题
  - 行 147：        self.assertEqual(1.2, decision["applied_risk_multiplier"]) → 无问题
  - 行 148：        self.assertEqual(0.1, decision["applied_take_profit_boost_pct"]) → 无问题
- 调用的外部函数：HighLaneSettings; evaluate_event; self.assertEqual
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：HighLaneRuleEngineTests.test_respects_configured_holding_days_in_max_hold_until（行 150-157）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 150：    def test_respects_configured_holding_days_in_max_hold_until(self) -> None: → 无问题
  - 行 151：        settings = HighLaneSettings(holding_days=3) → 无问题
  - 行 152：        now = datetime.now(tz=timezone.utc) → 无问题
  - 行 153：        decision = evaluate_event(self.base_event, settings=settings) → 无问题
  - 行 154：        self.assertEqual("accepted", decision["status"]) → 无问题
  - 行 155：        hold_until = datetime.fromisoformat(decision["bracket_order"]["max_hold_until"]) → 无问题
  - 行 156：        delta_days = (hold_until - now).total_seconds() / 86400.0 → 无问题
  - 行 157：        self.assertGreater(delta_days, 2.8) → 无问题
- 调用的外部函数：HighLaneSettings; datetime.now; evaluate_event; self.assertEqual; datetime.fromisoformat; self.assertGreater; total_seconds
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：161
- 函数审计数：16
- 发现问题数：0

## 文件：tests/test_ibkr_execution.py
- 总行数：182
- 函数/方法数：19

### 逐函数检查

#### 函数：__module__（行 1-182）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6：from unittest.mock import patch → 无问题
  - 行 7： → 无问题
  - 行 8：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 9： → 无问题
  - 行 10：from phase0.config import load_config → 无问题
  - 行 11：from phase0.ibkr_execution import ExecutionConfig, IbkrExecutionClient, execute_cycle → 无问题
  - 行 12： → 无问题
  - 行 13： → 无问题
  - 行 14：class _FakeOrder: → 无问题
  - 行 22： → 无问题
  - 行 23： → 无问题
  - 行 24：class _FakeTrade: → 无问题
  - 行 30： → 无问题
  - 行 31： → 无问题
  - 行 32：class _FakeIB: → 无问题
  - 行 36： → 无问题
  - 行 39： → 无问题
  - 行 42： → 无问题
  - 行 45： → 无问题
  - 行 48： → 无问题
  - 行 58： → 无问题
  - 行 62： → 无问题
  - 行 63： → 无问题
  - 行 66： → 无问题
  - 行 67： → 无问题
  - 行 68：class IbkrExecutionTests(unittest.TestCase): → 无问题
  - 行 115： → 无问题
  - 行 123： → 无问题
  - 行 144： → 无问题
  - 行 179： → 无问题
  - 行 180： → 无问题
  - 行 181：if __name__ == "__main__": → 无问题
  - 行 182：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：_FakeOrder.__init__（行 15-21）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 15：    def __init__(self) -> None: → 无问题
  - 行 16：        self.orderId = None → 无问题
  - 行 17：        self.permId = None → 无问题
  - 行 18：        self.orderRef = "" → 无问题
  - 行 19：        self.tif = "DAY" → 无问题
  - 行 20：        self.transmit = False → 无问题
  - 行 21：        self.account = "" → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_FakeTrade.__init__（行 25-29）
- 功能：执行对应业务逻辑
- 参数：self: Any, order: _FakeOrder, idx: int
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 25：    def __init__(self, order: _FakeOrder, idx: int) -> None: → 无问题
  - 行 26：        self.order = order → 无问题
  - 行 27：        self.order.orderId = 100 + idx → 无问题
  - 行 28：        self.order.permId = 200 + idx → 无问题
  - 行 29：        self.orderStatus = type("_Status", (), {"status": "Submitted"})() → 无问题
- 调用的外部函数：type
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_FakeIB.__init__（行 33-35）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 33：    def __init__(self) -> None: → 无问题
  - 行 34：        self.connected = False → 无问题
  - 行 35：        self.placed: list[_FakeOrder] = [] → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_FakeIB.connect（行 37-38）
- 功能：执行对应业务逻辑
- 参数：self: Any, host: str, port: int, clientId: int, timeout: float, readonly: bool
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 37：    def connect(self, host: str, port: int, clientId: int, timeout: float, readonly: bool) -> None: → 无问题
  - 行 38：        self.connected = True → 无问题
- 调用的外部函数：无
- 被谁调用：ibkr_execution.py:IbkrExecutionClient.__init__:54; audit.py:ensure_audit_db:29; audit.py:write_parameter_audit:72; audit.py:list_recent_audits:101; audit.py:mark_stoploss_override_used:138; audit.py:is_stoploss_override_used:155; ibkr_paper_check.py:IbkrInsyncClient.__init__:57; tests/test_audit_and_memory_persistence.py:AuditAndMemoryPersistenceTests.test_writes_parameter_audit_and_memory_db:33; tests/test_audit_and_memory_persistence.py:AuditAndMemoryPersistenceTests.test_writes_parameter_audit_and_memory_db:37
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_FakeIB.isConnected（行 40-41）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：bool（见函数语义）
- 逐行分析：
  - 行 40：    def isConnected(self) -> bool: → 无问题
  - 行 41：        return self.connected → 无问题
- 调用的外部函数：无
- 被谁调用：ibkr_execution.py:IbkrExecutionClient.close:115; ibkr_paper_check.py:IbkrInsyncClient.close:99
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_FakeIB.disconnect（行 43-44）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 43：    def disconnect(self) -> None: → 无问题
  - 行 44：        self.connected = False → 无问题
- 调用的外部函数：无
- 被谁调用：ibkr_execution.py:IbkrExecutionClient.close:116; ibkr_paper_check.py:IbkrInsyncClient.close:100
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_FakeIB.qualifyContracts（行 46-47）
- 功能：执行对应业务逻辑
- 参数：self: Any, contract: object
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 46：    def qualifyContracts(self, contract: object) -> None: → 无问题
  - 行 47：        return None → 无问题
- 调用的外部函数：无
- 被谁调用：ibkr_execution.py:IbkrExecutionClient.submit_bracket_signal:78; ibkr_paper_check.py:IbkrInsyncClient.request_l1_snapshot:63; ibkr_paper_check.py:IbkrInsyncClient.request_news:81
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_FakeIB.bracketOrder（行 49-57）
- 功能：执行对应业务逻辑
- 参数：self: Any, action: str, quantity: float, limitPrice: float, takeProfitPrice: float, stopLossPrice: float
- 返回值：tuple[_FakeOrder, _FakeOrder, _FakeOrder]（见函数语义）
- 逐行分析：
  - 行 49：    def bracketOrder( → 无问题
  - 行 50：        self, → 无问题
  - 行 51：        action: str, → 无问题
  - 行 52：        quantity: float, → 无问题
  - 行 53：        limitPrice: float, → 无问题
  - 行 54：        takeProfitPrice: float, → 无问题
  - 行 55：        stopLossPrice: float, → 无问题
  - 行 56：    ) -> tuple[_FakeOrder, _FakeOrder, _FakeOrder]: → 无问题
  - 行 57：        return _FakeOrder(), _FakeOrder(), _FakeOrder() → 无问题
- 调用的外部函数：_FakeOrder
- 被谁调用：ibkr_execution.py:IbkrExecutionClient.submit_bracket_signal:81
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_FakeIB.placeOrder（行 59-61）
- 功能：执行对应业务逻辑
- 参数：self: Any, contract: object, order: _FakeOrder
- 返回值：_FakeTrade（见函数语义）
- 逐行分析：
  - 行 59：    def placeOrder(self, contract: object, order: _FakeOrder) -> _FakeTrade: → 无问题
  - 行 60：        self.placed.append(order) → 无问题
  - 行 61：        return _FakeTrade(order, len(self.placed)) → 无问题
- 调用的外部函数：self.placed.append; _FakeTrade; len
- 被谁调用：ibkr_execution.py:IbkrExecutionClient.submit_bracket_signal:98; ibkr_execution.py:IbkrExecutionClient.submit_bracket_signal:99; ibkr_execution.py:IbkrExecutionClient.submit_bracket_signal:100
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：_fake_stock（行 64-65）
- 功能：执行对应业务逻辑
- 参数：symbol: str, exchange: str, currency: str
- 返回值：dict[str, str]（见函数语义）
- 逐行分析：
  - 行 64：def _fake_stock(symbol: str, exchange: str, currency: str) -> dict[str, str]: → 无问题
  - 行 65：    return {"symbol": symbol, "exchange": exchange, "currency": currency} → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionTests.test_submit_bracket_signal_with_ibkr_semantics（行 69-114）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 69：    def test_submit_bracket_signal_with_ibkr_semantics(self) -> None: → 无问题
  - 行 70：        client = IbkrExecutionClient( → 无问题
  - 行 71：            ExecutionConfig(), → 无问题
  - 行 72：            ib_factory=lambda: _FakeIB(), → 无问题
  - 行 73：            stock_factory=_fake_stock, → 无问题
  - 行 74：        ) → 无问题
  - 行 75：        result = client.submit_bracket_signal( → 无问题
  - 行 76：            { → 无问题
  - 行 77：                "contract": {"symbol": "AAPL", "exchange": "SMART", "currency": "USD"}, → 无问题
  - 行 78：                "orders": [ → 无问题
  - 行 79：                    { → 无问题
  - 行 80：                        "orderRef": "P", → 无问题
  - 行 81：                        "action": "BUY", → 无问题
  - 行 82：                        "orderType": "LMT", → 无问题
  - 行 83：                        "totalQuantity": 10, → 无问题
  - 行 84：                        "lmtPrice": 100.0, → 无问题
  - 行 85：                        "tif": "DAY", → 无问题
  - 行 86：                        "transmit": False, → 无问题
  - 行 87：                    }, → 无问题
  - 行 88：                    { → 无问题
  - 行 89：                        "orderRef": "TP", → 无问题
  - 行 90：                        "parentRef": "P", → 无问题
  - 行 91：                        "action": "SELL", → 无问题
  - 行 92：                        "orderType": "LMT", → 无问题
  - 行 93：                        "totalQuantity": 10, → 无问题
  - 行 94：                        "lmtPrice": 108.0, → 无问题
  - 行 95：                        "tif": "GTC", → 无问题
  - 行 96：                        "transmit": False, → 无问题
  - 行 97：                    }, → 无问题
  - 行 98：                    { → 无问题
  - 行 99：                        "orderRef": "SL", → 无问题
  - 行 100：                        "parentRef": "P", → 无问题
  - 行 101：                        "action": "SELL", → 无问题
  - 行 102：                        "orderType": "STP", → 无问题
  - 行 103：                        "totalQuantity": 10, → 无问题
  - 行 104：                        "auxPrice": 95.0, → 无问题
  - 行 105：                        "tif": "GTC", → 无问题
  - 行 106：                        "transmit": True, → 无问题
  - 行 107：                    }, → 无问题
  - 行 108：                ], → 无问题
  - 行 109：            } → 无问题
  - 行 110：        ) → 无问题
  - 行 111：        self.assertTrue(result["ok"]) → 无问题
  - 行 112：        self.assertEqual(3, len(result["orders"])) → 无问题
  - 行 113：        self.assertEqual("Submitted", result["orders"][0]["status"]) → 无问题
  - 行 114：        client.close() → 无问题
- 调用的外部函数：IbkrExecutionClient; client.submit_bracket_signal; self.assertTrue; self.assertEqual; client.close; ExecutionConfig; len; _FakeIB
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionTests.test_execute_cycle_dry_run_returns_signal（行 116-122）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 116：    def test_execute_cycle_dry_run_returns_signal(self) -> None: → 无问题
  - 行 117：        config = load_config() → 无问题
  - 行 118：        report = execute_cycle(symbol="AAPL", config=config, send=False) → 无问题
  - 行 119：        self.assertEqual("phase0_ibkr_execution", report["kind"]) → 无问题
  - 行 120：        self.assertIn("lane", report) → 无问题
  - 行 121：        self.assertIn("executions", report) → 无问题
  - 行 122：        self.assertTrue(report["signals_count"] >= 0) → 无问题
- 调用的外部函数：load_config; execute_cycle; self.assertEqual; self.assertIn; self.assertTrue
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionTests.test_execute_cycle_send_with_injected_client（行 124-143）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 124：    def test_execute_cycle_send_with_injected_client(self) -> None: → 无问题
  - 行 125：        config = load_config() → 无问题
  - 行 126： → 无问题
  - 行 127：        class _FakeExecClient: → 无问题
  - 行 128：            def submit_bracket_signal(self, signal: dict[str, object]) -> dict[str, object]: → 无问题
  - 行 129：                return {"ok": True, "signal": signal} → 无问题
  - 行 130： → 无问题
  - 行 131：            def close(self) -> None: → 无问题
  - 行 132：                return None → 无问题
  - 行 133： → 无问题
  - 行 134：        with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_cycle: → 无问题
  - 行 135：            mocked_cycle.return_value = {"ibkr_order_signals": [{"contract": {"symbol": "AAPL"}, "orders": [1, 2, 3]}]} → 无问题
  - 行 136：            report = execute_cycle( → 无问题
  - 行 137：                symbol="AAPL", → 无问题
  - 行 138：                config=config, → 无问题
  - 行 139：                send=True, → 无问题
  - 行 140：                client_factory=lambda _: _FakeExecClient(), → 无问题
  - 行 141：            ) → 无问题
  - 行 142：        self.assertEqual(1, report["signals_count"]) → 无问题
  - 行 143：        self.assertTrue(report["executions"][0]["ok"]) → 无问题
- 调用的外部函数：load_config; self.assertEqual; self.assertTrue; patch; execute_cycle; _FakeExecClient
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionTests._FakeExecClient.submit_bracket_signal（行 128-129）
- 功能：执行对应业务逻辑
- 参数：self: Any, signal: dict[str, object]
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 128：            def submit_bracket_signal(self, signal: dict[str, object]) -> dict[str, object]: → 无问题
  - 行 129：                return {"ok": True, "signal": signal} → 无问题
- 调用的外部函数：无
- 被谁调用：ibkr_execution.py:execute_cycle:145
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionTests._FakeExecClient.close（行 131-132）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 131：            def close(self) -> None: → 无问题
  - 行 132：                return None → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionTests.test_execute_cycle_send_continues_when_single_signal_fails（行 145-178）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 145：    def test_execute_cycle_send_continues_when_single_signal_fails(self) -> None: → 无问题
  - 行 146：        config = load_config() → 无问题
  - 行 147： → 无问题
  - 行 148：        class _FlakyExecClient: → 无问题
  - 行 149：            def __init__(self) -> None: → 无问题
  - 行 150：                self._called = 0 → 无问题
  - 行 151： → 无问题
  - 行 152：            def submit_bracket_signal(self, signal: dict[str, object]) -> dict[str, object]: → 无问题
  - 行 153：                self._called += 1 → 无问题
  - 行 154：                if self._called == 1: → 无问题
  - 行 155：                    raise RuntimeError("boom") → 无问题
  - 行 156：                return {"ok": True, "signal": signal} → 无问题
  - 行 157： → 无问题
  - 行 158：            def close(self) -> None: → 无问题
  - 行 159：                return None → 无问题
  - 行 160： → 无问题
  - 行 161：        with patch("phase0.ibkr_execution.run_lane_cycle") as mocked_cycle: → 无问题
  - 行 162：            mocked_cycle.return_value = { → 无问题
  - 行 163：                "ibkr_order_signals": [ → 无问题
  - 行 164：                    {"contract": {"symbol": "AAPL"}, "orders": [1, 2, 3]}, → 无问题
  - 行 165：                    {"contract": {"symbol": "MSFT"}, "orders": [1, 2, 3]}, → 无问题
  - 行 166：                ] → 无问题
  - 行 167：            } → 无问题
  - 行 168：            report = execute_cycle( → 无问题
  - 行 169：                symbol="AAPL", → 无问题
  - 行 170：                config=config, → 无问题
  - 行 171：                send=True, → 无问题
  - 行 172：                client_factory=lambda _: _FlakyExecClient(), → 无问题
  - 行 173：            ) → 无问题
  - 行 174：        self.assertEqual(2, report["signals_count"]) → 无问题
  - 行 175：        self.assertEqual(2, len(report["executions"])) → 无问题
  - 行 176：        self.assertFalse(report["executions"][0]["ok"]) → 无问题
  - 行 177：        self.assertEqual("RuntimeError", report["executions"][0]["error"]) → 无问题
  - 行 178：        self.assertTrue(report["executions"][1]["ok"]) → 无问题
- 调用的外部函数：load_config; self.assertEqual; self.assertFalse; self.assertTrue; patch; execute_cycle; len; RuntimeError; _FlakyExecClient
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionTests._FlakyExecClient.__init__（行 149-150）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 149：            def __init__(self) -> None: → 无问题
  - 行 150：                self._called = 0 → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionTests._FlakyExecClient.submit_bracket_signal（行 152-156）
- 功能：执行对应业务逻辑
- 参数：self: Any, signal: dict[str, object]
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 152：            def submit_bracket_signal(self, signal: dict[str, object]) -> dict[str, object]: → 无问题
  - 行 153：                self._called += 1 → 无问题
  - 行 154：                if self._called == 1: → 无问题
  - 行 155：                    raise RuntimeError("boom") → 无问题
  - 行 156：                return {"ok": True, "signal": signal} → 无问题
- 调用的外部函数：RuntimeError
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrExecutionTests._FlakyExecClient.close（行 158-159）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 158：            def close(self) -> None: → 无问题
  - 行 159：                return None → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：182
- 函数审计数：19
- 发现问题数：0

## 文件：tests/test_ibkr_paper_check.py
- 总行数：130
- 函数/方法数：19

### 逐函数检查

#### 函数：__module__（行 1-130）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6：from unittest.mock import patch → 无问题
  - 行 7： → 无问题
  - 行 8：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 9： → 无问题
  - 行 10：from phase0.ibkr_paper_check import PortStatus, ProbeConfig, run_probe → 无问题
  - 行 11： → 无问题
  - 行 12： → 无问题
  - 行 13：class FakeClientSuccess: → 无问题
  - 行 16： → 无问题
  - 行 19： → 无问题
  - 行 22： → 无问题
  - 行 23： → 无问题
  - 行 24：class FakeClientFailure: → 无问题
  - 行 27： → 无问题
  - 行 30： → 无问题
  - 行 33： → 无问题
  - 行 34： → 无问题
  - 行 35：class FakeClientNoNews: → 无问题
  - 行 38： → 无问题
  - 行 41： → 无问题
  - 行 44： → 无问题
  - 行 45： → 无问题
  - 行 46：class FlakyClient: → 无问题
  - 行 49： → 无问题
  - 行 55： → 无问题
  - 行 58： → 无问题
  - 行 61： → 无问题
  - 行 62： → 无问题
  - 行 63：class IbkrPaperCheckTests(unittest.TestCase): → 无问题
  - 行 66： → 无问题
  - 行 79： → 无问题
  - 行 94： → 无问题
  - 行 108： → 无问题
  - 行 119： → 无问题
  - 行 127： → 无问题
  - 行 128： → 无问题
  - 行 129：if __name__ == "__main__": → 无问题
  - 行 130：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：FakeClientSuccess.request_l1_snapshot（行 14-15）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 14：    def request_l1_snapshot(self, symbol: str) -> dict[str, object]: → 无问题
  - 行 15：        return {"symbol": symbol, "bid": 189.1, "ask": 189.3, "last": 189.2} → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClientSuccess.request_news（行 17-18）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str, limit: int
- 返回值：list[dict[str, object]]（见函数语义）
- 逐行分析：
  - 行 17：    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, object]]: → 无问题
  - 行 18：        return [{"headline": f"{symbol} headline", "provider_code": "BRFG", "article_id": "1", "time": "now"}] → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClientSuccess.close（行 20-21）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 20：    def close(self) -> None: → 无问题
  - 行 21：        return None → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClientFailure.request_l1_snapshot（行 25-26）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 25：    def request_l1_snapshot(self, symbol: str) -> dict[str, object]: → 无问题
  - 行 26：        raise RuntimeError("ibkr request failed") → 无问题
- 调用的外部函数：RuntimeError
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClientFailure.request_news（行 28-29）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str, limit: int
- 返回值：list[dict[str, object]]（见函数语义）
- 逐行分析：
  - 行 28：    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, object]]: → 无问题
  - 行 29：        return [] → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClientFailure.close（行 31-32）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 31：    def close(self) -> None: → 无问题
  - 行 32：        return None → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClientNoNews.request_l1_snapshot（行 36-37）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 36：    def request_l1_snapshot(self, symbol: str) -> dict[str, object]: → 无问题
  - 行 37：        return {"symbol": symbol, "bid": 189.1, "ask": 189.3, "last": 189.2} → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClientNoNews.request_news（行 39-40）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str, limit: int
- 返回值：list[dict[str, object]]（见函数语义）
- 逐行分析：
  - 行 39：    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, object]]: → 无问题
  - 行 40：        return [] → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClientNoNews.close（行 42-43）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 42：    def close(self) -> None: → 无问题
  - 行 43：        return None → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FlakyClient.__init__（行 47-48）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 47：    def __init__(self) -> None: → 无问题
  - 行 48：        self.calls = 0 → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FlakyClient.request_l1_snapshot（行 50-54）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 50：    def request_l1_snapshot(self, symbol: str) -> dict[str, object]: → 无问题
  - 行 51：        self.calls += 1 → 无问题
  - 行 52：        if self.calls == 1: → 无问题
  - 行 53：            raise TimeoutError("ibkr timeout") → 无问题
  - 行 54：        return {"symbol": symbol, "bid": 189.1, "ask": 189.3, "last": 189.2} → 无问题
- 调用的外部函数：TimeoutError
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FlakyClient.request_news（行 56-57）
- 功能：执行对应业务逻辑
- 参数：self: Any, symbol: str, limit: int
- 返回值：list[dict[str, object]]（见函数语义）
- 逐行分析：
  - 行 56：    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, object]]: → 无问题
  - 行 57：        return [{"headline": f"{symbol} headline", "provider_code": "BRFG", "article_id": "1", "time": "now"}] → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FlakyClient.close（行 59-60）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 59：    def close(self) -> None: → 无问题
  - 行 60：        return None → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrPaperCheckTests.setUp（行 64-65）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 64：    def setUp(self) -> None: → 无问题
  - 行 65：        self.config = ProbeConfig(symbol="AAPL") → 无问题
- 调用的外部函数：ProbeConfig
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrPaperCheckTests.test_returns_fallback_when_port_unreachable（行 67-78）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 67：    def test_returns_fallback_when_port_unreachable(self) -> None: → 无问题
  - 行 68：        port_status = PortStatus(ok=False, host="127.0.0.1", port=7497, latency_ms=None, error="connection refused") → 无问题
  - 行 69：        with patch("phase0.ibkr_paper_check.check_port", return_value=port_status), patch( → 无问题
  - 行 70：            "phase0.ibkr_paper_check.fetch_yfinance_snapshot", → 无问题
  - 行 71：            return_value={"ok": True, "source": "yfinance", "symbol": "AAPL", "last": 188.0}, → 无问题
  - 行 72：        ): → 无问题
  - 行 73：            report = run_probe(self.config) → 无问题
  - 行 74：        self.assertFalse(report["port_7497"]["ok"]) → 无问题
  - 行 75：        self.assertFalse(report["l1_market_data"]["ok"]) → 无问题
  - 行 76：        self.assertEqual("7497 unreachable", report["l1_market_data"]["error"]) → 无问题
  - 行 77：        self.assertEqual("yfinance", report["fallback_market_data"]["source"]) → 无问题
  - 行 78：        self.assertFalse(report["ok"]) → 无问题
- 调用的外部函数：PortStatus; self.assertFalse; self.assertEqual; patch; run_probe
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrPaperCheckTests.test_uses_ibkr_data_when_port_ok_and_client_works（行 80-93）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 80：    def test_uses_ibkr_data_when_port_ok_and_client_works(self) -> None: → 无问题
  - 行 81：        port_status = PortStatus(ok=True, host="127.0.0.1", port=7497, latency_ms=1.2, error=None) → 无问题
  - 行 82：        with patch("phase0.ibkr_paper_check.check_port", return_value=port_status): → 无问题
  - 行 83：            report = run_probe(self.config, client_factory=lambda _: FakeClientSuccess()) → 无问题
  - 行 84：        self.assertTrue(report["port_7497"]["ok"]) → 无问题
  - 行 85：        self.assertTrue(report["l1_market_data"]["ok"]) → 无问题
  - 行 86：        self.assertEqual("ibkr", report["l1_market_data"]["source"]) → 无问题
  - 行 87：        self.assertEqual(1, len(report["news"])) → 无问题
  - 行 88：        self.assertIsNone(report["fallback_market_data"]) → 无问题
  - 行 89：        self.assertTrue(report["pass_evidence"]["l1_market_data"]["ok"]) → 无问题
  - 行 90：        self.assertTrue(report["pass_evidence"]["news"]["ok"]) → 无问题
  - 行 91：        self.assertGreaterEqual(len(report["critical_path_logs"]), 3) → 无问题
  - 行 92：        self.assertEqual(1, report["retry_validation"]["attempts"]) → 无问题
  - 行 93：        self.assertTrue(report["ok"]) → 无问题
- 调用的外部函数：PortStatus; self.assertTrue; self.assertEqual; self.assertIsNone; self.assertGreaterEqual; patch; run_probe; len; FakeClientSuccess
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrPaperCheckTests.test_falls_back_when_ibkr_client_errors（行 95-107）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 95：    def test_falls_back_when_ibkr_client_errors(self) -> None: → 无问题
  - 行 96：        port_status = PortStatus(ok=True, host="127.0.0.1", port=7497, latency_ms=1.2, error=None) → 无问题
  - 行 97：        with patch("phase0.ibkr_paper_check.check_port", return_value=port_status), patch( → 无问题
  - 行 98：            "phase0.ibkr_paper_check.fetch_yfinance_snapshot", → 无问题
  - 行 99：            return_value={"ok": True, "source": "yfinance", "symbol": "AAPL", "last": 187.5}, → 无问题
  - 行 100：        ): → 无问题
  - 行 101：            report = run_probe(self.config, client_factory=lambda _: FakeClientFailure()) → 无问题
  - 行 102：        self.assertTrue(report["port_7497"]["ok"]) → 无问题
  - 行 103：        self.assertFalse(report["l1_market_data"]["ok"]) → 无问题
  - 行 104：        self.assertEqual("ibkr request failed", report["l1_market_data"]["error"]) → 无问题
  - 行 105：        self.assertEqual("yfinance", report["fallback_market_data"]["source"]) → 无问题
  - 行 106：        self.assertGreaterEqual(len(report["alerts"]), 1) → 无问题
  - 行 107：        self.assertFalse(report["ok"]) → 无问题
- 调用的外部函数：PortStatus; self.assertTrue; self.assertFalse; self.assertEqual; self.assertGreaterEqual; patch; run_probe; len; FakeClientFailure
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrPaperCheckTests.test_retries_on_retryable_error_then_succeeds（行 109-118）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 109：    def test_retries_on_retryable_error_then_succeeds(self) -> None: → 无问题
  - 行 110：        port_status = PortStatus(ok=True, host="127.0.0.1", port=7497, latency_ms=1.2, error=None) → 无问题
  - 行 111：        flaky_client = FlakyClient() → 无问题
  - 行 112：        with patch("phase0.ibkr_paper_check.check_port", return_value=port_status): → 无问题
  - 行 113：            report = run_probe(ProbeConfig(symbol="AAPL", max_retries=1), client_factory=lambda _: flaky_client) → 无问题
  - 行 114：        self.assertTrue(report["l1_market_data"]["ok"]) → 无问题
  - 行 115：        self.assertEqual(2, report["retry_validation"]["attempts"]) → 无问题
  - 行 116：        self.assertTrue(report["retry_validation"]["retried"]) → 无问题
  - 行 117：        self.assertIn("ibkr timeout", report["retry_validation"]["retryable_errors"][0]) → 无问题
  - 行 118：        self.assertTrue(report["ok"]) → 无问题
- 调用的外部函数：PortStatus; FlakyClient; self.assertTrue; self.assertEqual; self.assertIn; patch; run_probe; ProbeConfig
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：IbkrPaperCheckTests.test_marks_probe_not_ok_when_news_evidence_missing（行 120-126）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 120：    def test_marks_probe_not_ok_when_news_evidence_missing(self) -> None: → 无问题
  - 行 121：        port_status = PortStatus(ok=True, host="127.0.0.1", port=7497, latency_ms=1.2, error=None) → 无问题
  - 行 122：        with patch("phase0.ibkr_paper_check.check_port", return_value=port_status): → 无问题
  - 行 123：            report = run_probe(self.config, client_factory=lambda _: FakeClientNoNews()) → 无问题
  - 行 124：        self.assertTrue(report["l1_market_data"]["ok"]) → 无问题
  - 行 125：        self.assertFalse(report["pass_evidence"]["news"]["ok"]) → 无问题
  - 行 126：        self.assertFalse(report["ok"]) → 无问题
- 调用的外部函数：PortStatus; self.assertTrue; self.assertFalse; patch; run_probe; FakeClientNoNews
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：130
- 函数审计数：19
- 发现问题数：0

## 文件：tests/test_lane_bus.py
- 总行数：137
- 函数/方法数：9

### 逐函数检查

#### 函数：__module__（行 1-137）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import os → 无问题
  - 行 5：import sys → 无问题
  - 行 6：import unittest → 无问题
  - 行 7：from unittest.mock import patch → 无问题
  - 行 8： → 无问题
  - 行 9：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 10： → 无问题
  - 行 11：from phase0.config import load_config → 无问题
  - 行 12：from phase0.lanes import InMemoryLaneBus, LaneEvent, run_lane_cycle, run_lane_cycle_with_guard → 无问题
  - 行 13： → 无问题
  - 行 14： → 无问题
  - 行 15：class LaneBusTests(unittest.TestCase): → 无问题
  - 行 26： → 无问题
  - 行 36： → 无问题
  - 行 58： → 无问题
  - 行 70： → 无问题
  - 行 78： → 无问题
  - 行 101： → 无问题
  - 行 115： → 无问题
  - 行 125： → 无问题
  - 行 134： → 无问题
  - 行 135： → 无问题
  - 行 136：if __name__ == "__main__": → 无问题
  - 行 137：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：LaneBusTests.test_deduplicates_same_event（行 16-25）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 16：    def test_deduplicates_same_event(self) -> None: → 无问题
  - 行 17：        bus = InMemoryLaneBus() → 无问题
  - 行 18：        payload = {"symbol": "AAPL", "lane": "ultra", "kind": "signal"} → 无问题
  - 行 19：        event = LaneEvent.from_payload(event_type="signal", source_lane="ultra", payload=payload) → 无问题
  - 行 20：        first_ok = bus.publish("ultra.signal", event) → 无问题
  - 行 21：        second_ok = bus.publish("ultra.signal", event) → 无问题
  - 行 22：        self.assertTrue(first_ok) → 无问题
  - 行 23：        self.assertFalse(second_ok) → 无问题
  - 行 24：        items = bus.consume("ultra.signal") → 无问题
  - 行 25：        self.assertEqual(1, len(items)) → 无问题
- 调用的外部函数：InMemoryLaneBus; LaneEvent.from_payload; bus.publish; self.assertTrue; self.assertFalse; bus.consume; self.assertEqual; len
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LaneBusTests.test_runs_lane_cycle_and_returns_decision（行 27-35）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 27：    def test_runs_lane_cycle_and_returns_decision(self) -> None: → 无问题
  - 行 28：        config = load_config() → 无问题
  - 行 29：        output = run_lane_cycle("AAPL", config=config) → 无问题
  - 行 30：        self.assertIn("event", output) → 无问题
  - 行 31：        self.assertIn("decisions", output) → 无问题
  - 行 32：        self.assertIn("watchlist", output) → 无问题
  - 行 33：        decisions = output["decisions"] → 无问题
  - 行 34：        self.assertTrue(decisions) → 无问题
  - 行 35：        self.assertEqual("high", decisions[0]["lane"]) → 无问题
- 调用的外部函数：load_config; run_lane_cycle; self.assertIn; self.assertTrue; self.assertEqual
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LaneBusTests.test_eviction_allows_republish_after_capacity_rollover（行 37-57）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 37：    def test_eviction_allows_republish_after_capacity_rollover(self) -> None: → 无问题
  - 行 38：        bus = InMemoryLaneBus(dedup_capacity=2) → 无问题
  - 行 39：        event_a = LaneEvent.from_payload( → 无问题
  - 行 40：            event_type="signal", → 无问题
  - 行 41：            source_lane="ultra", → 无问题
  - 行 42：            payload={"symbol": "AAPL", "seq": 1}, → 无问题
  - 行 43：        ) → 无问题
  - 行 44：        event_b = LaneEvent.from_payload( → 无问题
  - 行 45：            event_type="signal", → 无问题
  - 行 46：            source_lane="ultra", → 无问题
  - 行 47：            payload={"symbol": "AAPL", "seq": 2}, → 无问题
  - 行 48：        ) → 无问题
  - 行 49：        event_c = LaneEvent.from_payload( → 无问题
  - 行 50：            event_type="signal", → 无问题
  - 行 51：            source_lane="ultra", → 无问题
  - 行 52：            payload={"symbol": "AAPL", "seq": 3}, → 无问题
  - 行 53：        ) → 无问题
  - 行 54：        self.assertTrue(bus.publish("ultra.signal", event_a)) → 无问题
  - 行 55：        self.assertTrue(bus.publish("ultra.signal", event_b)) → 无问题
  - 行 56：        self.assertTrue(bus.publish("ultra.signal", event_c)) → 无问题
  - 行 57：        self.assertTrue(bus.publish("ultra.signal", event_a)) → 无问题
- 调用的外部函数：InMemoryLaneBus; LaneEvent.from_payload; self.assertTrue; bus.publish
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LaneBusTests.test_lane_cycle_stays_stable_under_repeated_runs（行 59-69）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 59：    def test_lane_cycle_stays_stable_under_repeated_runs(self) -> None: → 无问题
  - 行 60：        config = load_config() → 无问题
  - 行 61：        accepted = 0 → 无问题
  - 行 62：        for _ in range(200): → 无问题
  - 行 63：            output = run_lane_cycle("AAPL", config=config) → 无问题
  - 行 64：            decisions = output["decisions"] → 无问题
  - 行 65：            self.assertTrue(decisions) → 无问题
  - 行 66：            self.assertIn(decisions[0]["status"], {"accepted", "rejected"}) → 无问题
  - 行 67：            if decisions[0]["status"] == "accepted": → 无问题
  - 行 68：                accepted += 1 → 无问题
  - 行 69：        self.assertGreater(accepted, 0) → 无问题
- 调用的外部函数：load_config; range; self.assertGreater; run_lane_cycle; self.assertTrue; self.assertIn
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LaneBusTests.test_guard_blocks_risk_execution（行 71-77）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 71：    def test_guard_blocks_risk_execution(self) -> None: → 无问题
  - 行 72：        config = load_config() → 无问题
  - 行 73：        output = run_lane_cycle_with_guard("AAPL", config=config, allow_risk_execution=False) → 无问题
  - 行 74：        decisions = output["decisions"] → 无问题
  - 行 75：        self.assertTrue(decisions) → 无问题
  - 行 76：        self.assertEqual("rejected", decisions[0]["status"]) → 无问题
  - 行 77：        self.assertIn("SAFETY_MODE_BLOCKED", decisions[0]["reject_reasons"]) → 无问题
- 调用的外部函数：load_config; run_lane_cycle_with_guard; self.assertTrue; self.assertEqual; self.assertIn
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LaneBusTests.test_seed_event_boolean_block_is_handled（行 79-100）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 79：    def test_seed_event_boolean_block_is_handled(self) -> None: → 无问题
  - 行 80：        config = load_config() → 无问题
  - 行 81：        output = run_lane_cycle( → 无问题
  - 行 82：            "AAPL", → 无问题
  - 行 83：            config=config, → 无问题
  - 行 84：            seed_event={ → 无问题
  - 行 85：                "lane": "ultra", → 无问题
  - 行 86：                "kind": "signal", → 无问题
  - 行 87：                "symbol": "AAPL", → 无问题
  - 行 88：                "side": "buy", → 无问题
  - 行 89：                "entry_price": "100", → 无问题
  - 行 90：                "stop_loss_price": "95", → 无问题
  - 行 91：                "take_profit_price": "110", → 无问题
  - 行 92：                "equity": "100000", → 无问题
  - 行 93：                "current_exposure": "12000", → 无问题
  - 行 94：                "allow_risk_execution": False, → 无问题
  - 行 95：            }, → 无问题
  - 行 96：        ) → 无问题
  - 行 97：        decisions = output["decisions"] → 无问题
  - 行 98：        self.assertTrue(decisions) → 无问题
  - 行 99：        self.assertEqual("rejected", decisions[0]["status"]) → 无问题
  - 行 100：        self.assertIn("SAFETY_MODE_BLOCKED", decisions[0]["reject_reasons"]) → 无问题
- 调用的外部函数：load_config; run_lane_cycle; self.assertTrue; self.assertEqual; self.assertIn
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LaneBusTests.test_lane_cycle_returns_strategy_signals（行 102-114）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 102：    def test_lane_cycle_returns_strategy_signals(self) -> None: → 无问题
  - 行 103：        config = load_config() → 无问题
  - 行 104：        output = run_lane_cycle("AAPL", config=config) → 无问题
  - 行 105：        signals = output["strategy_signals"] → 无问题
  - 行 106：        self.assertTrue(signals) → 无问题
  - 行 107：        self.assertIn("strategy", signals[0]) → 无问题
  - 行 108：        self.assertIn("ultra_signal", output) → 无问题
  - 行 109：        self.assertIn("low_analysis", output) → 无问题
  - 行 110：        self.assertIn("memory_context", output) → 无问题
  - 行 111：        self.assertIn("low_async_analysis", output) → 无问题
  - 行 112：        self.assertIn("high_assessment", output) → 无问题
  - 行 113：        self.assertIn("daily_discipline", output) → 无问题
  - 行 114：        self.assertIn("ibkr_order_signals", output) → 无问题
- 调用的外部函数：load_config; run_lane_cycle; self.assertTrue; self.assertIn
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LaneBusTests.test_lane_cycle_bypasses_ai_when_disabled（行 116-124）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 116：    def test_lane_cycle_bypasses_ai_when_disabled(self) -> None: → 无问题
  - 行 117：        with patch.dict("os.environ", {"AI_ENABLED": "false"}, clear=False): → 无问题
  - 行 118：            config = load_config() → 无问题
  - 行 119：        output = run_lane_cycle("AAPL", config=config) → 无问题
  - 行 120：        self.assertTrue(output["ai_bypassed"]) → 无问题
  - 行 121：        self.assertEqual("AI_BYPASSED", output["ultra_signal"]["reason"]) → 无问题
  - 行 122：        self.assertEqual(1.0, output["ultra_signal"]["quick_filter_score"]) → 无问题
  - 行 123：        self.assertEqual([], output["memory_context"]) → 无问题
  - 行 124：        self.assertEqual(0, output["low_async_processed"]) → 无问题
- 调用的外部函数：run_lane_cycle; self.assertTrue; self.assertEqual; patch.dict; load_config
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LaneBusTests.test_lane_cycle_daily_discipline_buy_when_no_position（行 126-133）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 126：    def test_lane_cycle_daily_discipline_buy_when_no_position(self) -> None: → 无问题
  - 行 127：        config = load_config() → 无问题
  - 行 128：        output = run_lane_cycle( → 无问题
  - 行 129：            "AAPL", → 无问题
  - 行 130：            config=config, → 无问题
  - 行 131：            daily_state={"actions_today": 0, "has_open_position": False}, → 无问题
  - 行 132：        ) → 无问题
  - 行 133：        self.assertEqual("buy", output["daily_discipline"]["required_action"]) → 无问题
- 调用的外部函数：load_config; run_lane_cycle; self.assertEqual
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：137
- 函数审计数：9
- 发现问题数：0

## 文件：tests/test_llm_connectivity_check.py
- 总行数：176
- 函数/方法数：4

### 逐函数检查

#### 函数：__module__（行 1-176）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6：from unittest.mock import patch → 无问题
  - 行 7： → 无问题
  - 行 8：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 9： → 无问题
  - 行 10：from phase0.config import AppConfig, RuntimeMode, RuntimeProfile → 无问题
  - 行 11：from phase0.llm_connectivity_check import run_llm_probe → 无问题
  - 行 12： → 无问题
  - 行 13： → 无问题
  - 行 14：class FakeGateway: → 无问题
  - 行 17： → 无问题
  - 行 26： → 无问题
  - 行 27： → 无问题
  - 行 28：class LLMConnectivityCheckTests(unittest.TestCase): → 无问题
  - 行 100： → 无问题
  - 行 173： → 无问题
  - 行 174： → 无问题
  - 行 175：if __name__ == "__main__": → 无问题
  - 行 176：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：FakeGateway.__init__（行 15-16）
- 功能：执行对应业务逻辑
- 参数：self: Any, settings: object, profile: RuntimeProfile
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 15：    def __init__(self, settings: object, profile: RuntimeProfile) -> None: → 无问题
  - 行 16：        self.model = "test-model-cloud" if profile == RuntimeProfile.CLOUD else "test-model-local" → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeGateway.check_connectivity（行 18-25）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：dict[str, object]（见函数语义）
- 逐行分析：
  - 行 18：    def check_connectivity(self) -> dict[str, object]: → 无问题
  - 行 19：        return { → 无问题
  - 行 20：            "ok": True, → 无问题
  - 行 21：            "base_url": "http://localhost:11434/v1", → 无问题
  - 行 22：            "model": self.model, → 无问题
  - 行 23：            "latency_ms": 10.2, → 无问题
  - 行 24：            "reply": "pong", → 无问题
  - 行 25：        } → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LLMConnectivityCheckTests.test_run_probe_returns_success_report（行 29-99）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 29：    def test_run_probe_returns_success_report(self) -> None: → 无问题
  - 行 30：        config = AppConfig( → 无问题
  - 行 31：            runtime_profile=RuntimeProfile.LOCAL, → 无问题
  - 行 32：            runtime_mode=RuntimeMode.NORMAL, → 无问题
  - 行 33：            log_level="INFO", → 无问题
  - 行 34：            ibkr_host="127.0.0.1", → 无问题
  - 行 35：            ibkr_port=7497, → 无问题
  - 行 36：            llm_base_url="http://localhost:11434/v1", → 无问题
  - 行 37：            llm_api_key="dummy", → 无问题
  - 行 38：            llm_local_model="llama3.1:8b", → 无问题
  - 行 39：            llm_cloud_model="gpt-4o-mini", → 无问题
  - 行 40：            llm_timeout_seconds=20.0, → 无问题
  - 行 41：            llm_max_retries=3, → 无问题
  - 行 42：            llm_backoff_seconds=0.5, → 无问题
  - 行 43：            llm_rate_limit_per_second=2.0, → 无问题
  - 行 44：            risk_single_trade_pct=0.01, → 无问题
  - 行 45：            risk_total_exposure_pct=0.3, → 无问题
  - 行 46：            risk_stop_loss_min_pct=0.05, → 无问题
  - 行 47：            risk_stop_loss_max_pct=0.08, → 无问题
  - 行 48：            risk_max_drawdown_pct=0.12, → 无问题
  - 行 49：            risk_min_trade_units=1, → 无问题
  - 行 50：            risk_slippage_bps=2.0, → 无问题
  - 行 51：            risk_commission_per_share=0.005, → 无问题
  - 行 52：            risk_exposure_softmax_temperature=1.0, → 无问题
  - 行 53：            cooldown_hours=24, → 无问题
  - 行 54：            holding_days=2, → 无问题
  - 行 55：            lane_bus_dedup_ttl_seconds=300, → 无问题
  - 行 56：            strategy_enabled_list="momentum,news_sentiment", → 无问题
  - 行 57：            strategy_rotation_top_k=3, → 无问题
  - 行 58：            strategy_news_positive_threshold=0.2, → 无问题
  - 行 59：            strategy_news_negative_threshold=-0.2, → 无问题
  - 行 60：            strategy_plugin_modules="", → 无问题
  - 行 61：            factor_plugin_modules="", → 无问题
  - 行 62：            high_risk_multiplier_min=0.5, → 无问题
  - 行 63：            high_risk_multiplier_max=1.5, → 无问题
  - 行 64：            high_take_profit_boost_max_pct=0.2, → 无问题
  - 行 65：            ai_message_max_age_minutes=180, → 无问题
  - 行 66：            ai_low_committee_models="gpt-4o-mini,claude-3-5-sonnet,gemini-2.0-flash", → 无问题
  - 行 67：            ai_low_committee_min_support=2, → 无问题
  - 行 68：            ai_high_mode="local", → 无问题
  - 行 69：            ai_high_committee_models="local-risk-v1,gpt-4o-mini", → 无问题
  - 行 70：            ai_high_committee_min_support=1, → 无问题
  - 行 71：            ai_high_confidence_gate=0.58, → 无问题
  - 行 72：            ai_stop_loss_default_pct=0.02, → 无问题
  - 行 73：            ai_stop_loss_break_max_pct=0.05, → 无问题
  - 行 74：            ai_stoploss_override_ttl_hours=72, → 无问题
  - 行 75：            ai_state_db_path="artifacts/test_state.db", → 无问题
  - 行 76：            ai_memory_db_path="artifacts/test_memory.db", → 无问题
  - 行 77：            ai_enabled=True, → 无问题
  - 行 78：            discipline_min_actions_per_day=1, → 无问题
  - 行 79：            discipline_hold_score_threshold=0.72, → 无问题
  - 行 80：            discipline_enable_daily_cycle=True, → 无问题
  - 行 81：            market_data_mode="default", → 无问题
  - 行 82：            market_symbols="AAPL,MSFT,NVDA,XOM", → 无问题
  - 行 83：            market_snapshot_json="", → 无问题
  - 行 84：            lane_scheduler_enabled=False, → 无问题
  - 行 85：            lane_rebalance_interval_seconds=60, → 无问题
  - 行 86：            lane_scheduler_cycles=1, → 无问题
  - 行 87：            execution_session_guard_enabled=True, → 无问题
  - 行 88：            execution_session_start_utc="13:30", → 无问题
  - 行 89：            execution_session_end_utc="20:00", → 无问题
  - 行 90：            execution_good_after_seconds=5, → 无问题
  - 行 91：        ) → 无问题
  - 行 92：        with patch("phase0.llm_connectivity_check.load_config", return_value=config), patch( → 无问题
  - 行 93：            "phase0.llm_connectivity_check.UnifiedLLMGateway", → 无问题
  - 行 94：            FakeGateway, → 无问题
  - 行 95：        ): → 无问题
  - 行 96：            report = run_llm_probe(profile=RuntimeProfile.CLOUD) → 无问题
  - 行 97：        self.assertTrue(report["ok"]) → 无问题
  - 行 98：        self.assertEqual("cloud", report["profile"]) → 无问题
  - 行 99：        self.assertEqual("test-model-cloud", report["model"]) → 无问题
- 调用的外部函数：AppConfig; self.assertTrue; self.assertEqual; patch; run_llm_probe
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LLMConnectivityCheckTests.test_run_probe_returns_structured_error（行 101-172）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 101：    def test_run_probe_returns_structured_error(self) -> None: → 无问题
  - 行 102：        config = AppConfig( → 无问题
  - 行 103：            runtime_profile=RuntimeProfile.LOCAL, → 无问题
  - 行 104：            runtime_mode=RuntimeMode.NORMAL, → 无问题
  - 行 105：            log_level="INFO", → 无问题
  - 行 106：            ibkr_host="127.0.0.1", → 无问题
  - 行 107：            ibkr_port=7497, → 无问题
  - 行 108：            llm_base_url="http://localhost:11434/v1", → 无问题
  - 行 109：            llm_api_key="dummy", → 无问题
  - 行 110：            llm_local_model="llama3.1:8b", → 无问题
  - 行 111：            llm_cloud_model="gpt-4o-mini", → 无问题
  - 行 112：            llm_timeout_seconds=20.0, → 无问题
  - 行 113：            llm_max_retries=3, → 无问题
  - 行 114：            llm_backoff_seconds=0.5, → 无问题
  - 行 115：            llm_rate_limit_per_second=2.0, → 无问题
  - 行 116：            risk_single_trade_pct=0.01, → 无问题
  - 行 117：            risk_total_exposure_pct=0.3, → 无问题
  - 行 118：            risk_stop_loss_min_pct=0.05, → 无问题
  - 行 119：            risk_stop_loss_max_pct=0.08, → 无问题
  - 行 120：            risk_max_drawdown_pct=0.12, → 无问题
  - 行 121：            risk_min_trade_units=1, → 无问题
  - 行 122：            risk_slippage_bps=2.0, → 无问题
  - 行 123：            risk_commission_per_share=0.005, → 无问题
  - 行 124：            risk_exposure_softmax_temperature=1.0, → 无问题
  - 行 125：            cooldown_hours=24, → 无问题
  - 行 126：            holding_days=2, → 无问题
  - 行 127：            lane_bus_dedup_ttl_seconds=300, → 无问题
  - 行 128：            strategy_enabled_list="momentum,news_sentiment", → 无问题
  - 行 129：            strategy_rotation_top_k=3, → 无问题
  - 行 130：            strategy_news_positive_threshold=0.2, → 无问题
  - 行 131：            strategy_news_negative_threshold=-0.2, → 无问题
  - 行 132：            strategy_plugin_modules="", → 无问题
  - 行 133：            factor_plugin_modules="", → 无问题
  - 行 134：            high_risk_multiplier_min=0.5, → 无问题
  - 行 135：            high_risk_multiplier_max=1.5, → 无问题
  - 行 136：            high_take_profit_boost_max_pct=0.2, → 无问题
  - 行 137：            ai_message_max_age_minutes=180, → 无问题
  - 行 138：            ai_low_committee_models="gpt-4o-mini,claude-3-5-sonnet,gemini-2.0-flash", → 无问题
  - 行 139：            ai_low_committee_min_support=2, → 无问题
  - 行 140：            ai_high_mode="local", → 无问题
  - 行 141：            ai_high_committee_models="local-risk-v1,gpt-4o-mini", → 无问题
  - 行 142：            ai_high_committee_min_support=1, → 无问题
  - 行 143：            ai_high_confidence_gate=0.58, → 无问题
  - 行 144：            ai_stop_loss_default_pct=0.02, → 无问题
  - 行 145：            ai_stop_loss_break_max_pct=0.05, → 无问题
  - 行 146：            ai_stoploss_override_ttl_hours=72, → 无问题
  - 行 147：            ai_state_db_path="artifacts/test_state.db", → 无问题
  - 行 148：            ai_memory_db_path="artifacts/test_memory.db", → 无问题
  - 行 149：            ai_enabled=True, → 无问题
  - 行 150：            discipline_min_actions_per_day=1, → 无问题
  - 行 151：            discipline_hold_score_threshold=0.72, → 无问题
  - 行 152：            discipline_enable_daily_cycle=True, → 无问题
  - 行 153：            market_data_mode="default", → 无问题
  - 行 154：            market_symbols="AAPL,MSFT,NVDA,XOM", → 无问题
  - 行 155：            market_snapshot_json="", → 无问题
  - 行 156：            lane_scheduler_enabled=False, → 无问题
  - 行 157：            lane_rebalance_interval_seconds=60, → 无问题
  - 行 158：            lane_scheduler_cycles=1, → 无问题
  - 行 159：            execution_session_guard_enabled=True, → 无问题
  - 行 160：            execution_session_start_utc="13:30", → 无问题
  - 行 161：            execution_session_end_utc="20:00", → 无问题
  - 行 162：            execution_good_after_seconds=5, → 无问题
  - 行 163：        ) → 无问题
  - 行 164：        with patch("phase0.llm_connectivity_check.load_config", return_value=config), patch( → 无问题
  - 行 165：            "phase0.llm_connectivity_check.UnifiedLLMGateway", → 无问题
  - 行 166：            side_effect=RuntimeError("boom"), → 无问题
  - 行 167：        ): → 无问题
  - 行 168：            report = run_llm_probe(profile=RuntimeProfile.CLOUD) → 无问题
  - 行 169：        self.assertFalse(report["ok"]) → 无问题
  - 行 170：        self.assertEqual("RuntimeError", report["error"]) → 无问题
  - 行 171：        self.assertEqual("RuntimeError", report["error_type"]) → 无问题
  - 行 172：        self.assertEqual("INTERNAL_ERROR", report["error_code"]) → 无问题
- 调用的外部函数：AppConfig; self.assertFalse; self.assertEqual; patch; run_llm_probe; RuntimeError
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：176
- 函数审计数：4
- 发现问题数：0

## 文件：tests/test_llm_gateway.py
- 总行数：113
- 函数/方法数：13

### 逐函数检查

#### 函数：__module__（行 1-113）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6： → 无问题
  - 行 7：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 8： → 无问题
  - 行 9：from phase0.config import RuntimeProfile → 无问题
  - 行 10：from phase0.llm_gateway import LLMGatewaySettings, RateLimiter, UnifiedLLMGateway → 无问题
  - 行 11： → 无问题
  - 行 12： → 无问题
  - 行 13：class RetryableError(Exception): → 无问题
  - 行 14：    status_code = 429 → 无问题
  - 行 15： → 无问题
  - 行 16： → 无问题
  - 行 17：class NonRetryableError(Exception): → 无问题
  - 行 18：    status_code = 400 → 无问题
  - 行 19： → 无问题
  - 行 20： → 无问题
  - 行 21：class FakeCompletions: → 无问题
  - 行 25： → 无问题
  - 行 32： → 无问题
  - 行 33： → 无问题
  - 行 34：class FakeChat: → 无问题
  - 行 37： → 无问题
  - 行 38： → 无问题
  - 行 39：class FakeClient: → 无问题
  - 行 42： → 无问题
  - 行 43： → 无问题
  - 行 44：class FakeResponse: → 无问题
  - 行 49： → 无问题
  - 行 50： → 无问题
  - 行 51：class FakeClock: → 无问题
  - 行 54： → 无问题
  - 行 57： → 无问题
  - 行 60： → 无问题
  - 行 61： → 无问题
  - 行 62：class LLMGatewayTests(unittest.TestCase): → 无问题
  - 行 74： → 无问题
  - 行 82： → 无问题
  - 行 94： → 无问题
  - 行 103： → 无问题
  - 行 110： → 无问题
  - 行 111： → 无问题
  - 行 112：if __name__ == "__main__": → 无问题
  - 行 113：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：FakeCompletions.__init__（行 22-24）
- 功能：执行对应业务逻辑
- 参数：self: Any, outcomes: list[object]
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 22：    def __init__(self, outcomes: list[object]) -> None: → 无问题
  - 行 23：        self._outcomes = outcomes → 无问题
  - 行 24：        self.calls = 0 → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeCompletions.create（行 26-31）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：object（见函数语义）
- 逐行分析：
  - 行 26：    def create(self, **_: object) -> object: → 无问题
  - 行 27：        self.calls += 1 → 无问题
  - 行 28：        outcome = self._outcomes[self.calls - 1] → 无问题
  - 行 29：        if isinstance(outcome, Exception): → 无问题
  - 行 30：            raise outcome → 无问题
  - 行 31：        return outcome → 无问题
- 调用的外部函数：isinstance
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeChat.__init__（行 35-36）
- 功能：执行对应业务逻辑
- 参数：self: Any, completions: FakeCompletions
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 35：    def __init__(self, completions: FakeCompletions) -> None: → 无问题
  - 行 36：        self.completions = completions → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClient.__init__（行 40-41）
- 功能：执行对应业务逻辑
- 参数：self: Any, outcomes: list[object]
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 40：    def __init__(self, outcomes: list[object]) -> None: → 无问题
  - 行 41：        self.chat = FakeChat(FakeCompletions(outcomes)) → 无问题
- 调用的外部函数：FakeChat; FakeCompletions
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeResponse.__init__（行 45-48）
- 功能：执行对应业务逻辑
- 参数：self: Any, text: str
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 45：    def __init__(self, text: str) -> None: → 无问题
  - 行 46：        message = type("Message", (), {"content": text}) → 无问题
  - 行 47：        choice = type("Choice", (), {"message": message()}) → 无问题
  - 行 48：        self.choices = [choice()] → 无问题
- 调用的外部函数：type; choice; message
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClock.__init__（行 52-53）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 52：    def __init__(self) -> None: → 无问题
  - 行 53：        self.now = 0.0 → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClock.__call__（行 55-56）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：float（见函数语义）
- 逐行分析：
  - 行 55：    def __call__(self) -> float: → 无问题
  - 行 56：        return self.now → 无问题
- 调用的外部函数：无
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：FakeClock.sleep（行 58-59）
- 功能：执行对应业务逻辑
- 参数：self: Any, seconds: float
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 58：    def sleep(self, seconds: float) -> None: → 无问题
  - 行 59：        self.now += seconds → 无问题
- 调用的外部函数：无
- 被谁调用：main.py:main:29; ibkr_paper_check.py:IbkrInsyncClient.request_l1_snapshot:65; ibkr_paper_check.py:run_probe:358
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LLMGatewayTests.setUp（行 63-73）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 63：    def setUp(self) -> None: → 无问题
  - 行 64：        self.settings = LLMGatewaySettings( → 无问题
  - 行 65：            base_url="http://localhost:11434/v1", → 无问题
  - 行 66：            api_key="dummy", → 无问题
  - 行 67：            local_model="llama3.1:8b", → 无问题
  - 行 68：            cloud_model="gpt-4o-mini", → 无问题
  - 行 69：            timeout_seconds=20.0, → 无问题
  - 行 70：            max_retries=2, → 无问题
  - 行 71：            backoff_seconds=0.1, → 无问题
  - 行 72：            rate_limit_per_second=100.0, → 无问题
  - 行 73：        ) → 无问题
- 调用的外部函数：LLMGatewaySettings
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LLMGatewayTests.test_uses_local_model_for_non_cloud_profile（行 75-81）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 75：    def test_uses_local_model_for_non_cloud_profile(self) -> None: → 无问题
  - 行 76：        gateway = UnifiedLLMGateway( → 无问题
  - 行 77：            settings=self.settings, → 无问题
  - 行 78：            profile=RuntimeProfile.LOCAL, → 无问题
  - 行 79：            client_factory=lambda: FakeClient([FakeResponse("ok")]), → 无问题
  - 行 80：        ) → 无问题
  - 行 81：        self.assertEqual("llama3.1:8b", gateway.model) → 无问题
- 调用的外部函数：UnifiedLLMGateway; self.assertEqual; FakeClient; FakeResponse
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LLMGatewayTests.test_retries_on_retryable_error_and_succeeds（行 83-93）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 83：    def test_retries_on_retryable_error_and_succeeds(self) -> None: → 无问题
  - 行 84：        sleep_calls: list[float] = [] → 无问题
  - 行 85：        gateway = UnifiedLLMGateway( → 无问题
  - 行 86：            settings=self.settings, → 无问题
  - 行 87：            profile=RuntimeProfile.CLOUD, → 无问题
  - 行 88：            client_factory=lambda: FakeClient([RetryableError("busy"), FakeResponse("pong")]), → 无问题
  - 行 89：            sleeper=lambda seconds: sleep_calls.append(seconds), → 无问题
  - 行 90：        ) → 无问题
  - 行 91：        result = gateway.generate("hello") → 无问题
  - 行 92：        self.assertEqual("pong", result) → 无问题
  - 行 93：        self.assertEqual([0.1], sleep_calls) → 无问题
- 调用的外部函数：UnifiedLLMGateway; gateway.generate; self.assertEqual; FakeClient; sleep_calls.append; RetryableError; FakeResponse
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LLMGatewayTests.test_raises_without_retry_for_non_retryable_error（行 95-102）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 95：    def test_raises_without_retry_for_non_retryable_error(self) -> None: → 无问题
  - 行 96：        gateway = UnifiedLLMGateway( → 无问题
  - 行 97：            settings=self.settings, → 无问题
  - 行 98：            profile=RuntimeProfile.CLOUD, → 无问题
  - 行 99：            client_factory=lambda: FakeClient([NonRetryableError("bad request")]), → 无问题
  - 行 100：        ) → 无问题
  - 行 101：        with self.assertRaises(NonRetryableError): → 无问题
  - 行 102：            gateway.generate("hello") → 无问题
- 调用的外部函数：UnifiedLLMGateway; self.assertRaises; gateway.generate; FakeClient; NonRetryableError
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：LLMGatewayTests.test_rate_limiter_waits_for_next_permit（行 104-109）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 104：    def test_rate_limiter_waits_for_next_permit(self) -> None: → 无问题
  - 行 105：        clock = FakeClock() → 无问题
  - 行 106：        limiter = RateLimiter(permits_per_second=2.0, clock=clock, sleeper=clock.sleep) → 无问题
  - 行 107：        limiter.acquire() → 无问题
  - 行 108：        limiter.acquire() → 无问题
  - 行 109：        self.assertAlmostEqual(0.5, clock.now) → 无问题
- 调用的外部函数：FakeClock; RateLimiter; limiter.acquire; self.assertAlmostEqual
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：113
- 函数审计数：13
- 发现问题数：0

## 文件：tests/test_low_lane.py
- 总行数：25
- 函数/方法数：1

### 逐函数检查

#### 函数：__module__（行 1-25）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6： → 无问题
  - 行 7：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 8： → 无问题
  - 行 9：from phase0.lanes.low import build_watchlist_with_rotation → 无问题
  - 行 10： → 无问题
  - 行 11： → 无问题
  - 行 12：class LowLaneRotationTests(unittest.TestCase): → 无问题
  - 行 22： → 无问题
  - 行 23： → 无问题
  - 行 24：if __name__ == "__main__": → 无问题
  - 行 25：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：LowLaneRotationTests.test_build_watchlist_with_rotation_ranks_symbols（行 13-21）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 13：    def test_build_watchlist_with_rotation_ranks_symbols(self) -> None: → 无问题
  - 行 14：        snapshot = { → 无问题
  - 行 15：            "AAA": {"momentum_20d": 0.12, "relative_strength": 0.3, "z_score_5d": 0.1, "liquidity_score": 0.8}, → 无问题
  - 行 16：            "BBB": {"momentum_20d": 0.03, "relative_strength": 0.1, "z_score_5d": 0.2, "liquidity_score": 0.7}, → 无问题
  - 行 17：            "CCC": {"momentum_20d": 0.15, "relative_strength": 0.25, "z_score_5d": 1.0, "liquidity_score": 0.9}, → 无问题
  - 行 18：        } → 无问题
  - 行 19：        watchlist = build_watchlist_with_rotation(snapshot, top_k=2) → 无问题
  - 行 20：        self.assertEqual(2, len(watchlist)) → 无问题
  - 行 21：        self.assertEqual("CCC", watchlist[0]) → 无问题
- 调用的外部函数：build_watchlist_with_rotation; self.assertEqual; len
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：25
- 函数审计数：1
- 发现问题数：0

## 文件：tests/test_non_ai_validation_report.py
- 总行数：24
- 函数/方法数：1

### 逐函数检查

#### 函数：__module__（行 1-24）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6： → 无问题
  - 行 7：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 8： → 无问题
  - 行 9：from phase0.non_ai_validation_report import generate_non_ai_validation_report → 无问题
  - 行 10： → 无问题
  - 行 11： → 无问题
  - 行 12：class NonAIValidationReportTests(unittest.TestCase): → 无问题
  - 行 21： → 无问题
  - 行 22： → 无问题
  - 行 23：if __name__ == "__main__": → 无问题
  - 行 24：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：NonAIValidationReportTests.test_generates_non_ai_report（行 13-20）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 13：    def test_generates_non_ai_report(self) -> None: → 无问题
  - 行 14：        report = generate_non_ai_validation_report() → 无问题
  - 行 15：        self.assertEqual("phase0_non_ai_validation_report", report["kind"]) → 无问题
  - 行 16：        self.assertEqual("non_ai_bypass", report["mode"]) → 无问题
  - 行 17：        self.assertIn("checks", report) → 无问题
  - 行 18：        self.assertIn("components", report) → 无问题
  - 行 19：        self.assertIn("functional", report) → 无问题
  - 行 20：        self.assertTrue(any(item["component"] == "data_transport" for item in report["components"])) → 无问题
- 调用的外部函数：generate_non_ai_validation_report; self.assertEqual; self.assertIn; self.assertTrue; any
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：24
- 函数审计数：1
- 发现问题数：0

## 文件：tests/test_phase0_validation_report.py
- 总行数：29
- 函数/方法数：1

### 逐函数检查

#### 函数：__module__（行 1-29）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6： → 无问题
  - 行 7：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 8： → 无问题
  - 行 9：from phase0.phase0_validation_report import generate_phase0_validation_report → 无问题
  - 行 10： → 无问题
  - 行 11： → 无问题
  - 行 12：class Phase0ValidationReportTests(unittest.TestCase): → 无问题
  - 行 26： → 无问题
  - 行 27： → 无问题
  - 行 28：if __name__ == "__main__": → 无问题
  - 行 29：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：Phase0ValidationReportTests.test_generates_passed_report（行 13-25）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 13：    def test_generates_passed_report(self) -> None: → 无问题
  - 行 14：        report = generate_phase0_validation_report() → 无问题
  - 行 15：        self.assertEqual("phase0_validation_report", report["kind"]) → 无问题
  - 行 16：        self.assertTrue(report["ok"]) → 无问题
  - 行 17：        self.assertEqual(report["summary"]["replay_total"], report["summary"]["replay_passed"]) → 无问题
  - 行 18：        self.assertEqual(report["summary"]["checks_total"], report["summary"]["checks_passed"]) → 无问题
  - 行 19：        self.assertGreaterEqual(len(report["hard_rule_checks"]), 3) → 无问题
  - 行 20：        self.assertGreaterEqual(len(report["order_checks"]), 4) → 无问题
  - 行 21：        self.assertIn("ibkr_probe", report) → 无问题
  - 行 22：        self.assertGreaterEqual(len(report["ibkr_validation_checks"]), 5) → 无问题
  - 行 23：        self.assertTrue(report["ibkr_probe"]["pass_evidence"]["l1_market_data"]["ok"]) → 无问题
  - 行 24：        self.assertTrue(report["ibkr_probe"]["pass_evidence"]["news"]["ok"]) → 无问题
  - 行 25：        self.assertGreaterEqual(report["ibkr_probe"]["retry_validation"]["attempts"], 1) → 无问题
- 调用的外部函数：generate_phase0_validation_report; self.assertEqual; self.assertTrue; self.assertGreaterEqual; self.assertIn; len
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：29
- 函数审计数：1
- 发现问题数：0

## 文件：tests/test_replay.py
- 总行数：36
- 函数/方法数：2

### 逐函数检查

#### 函数：__module__（行 1-36）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6： → 无问题
  - 行 7：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 8： → 无问题
  - 行 9：from phase0.replay import run_replay → 无问题
  - 行 10： → 无问题
  - 行 11： → 无问题
  - 行 12：class ReplayScriptTests(unittest.TestCase): → 无问题
  - 行 26： → 无问题
  - 行 33： → 无问题
  - 行 34： → 无问题
  - 行 35：if __name__ == "__main__": → 无问题
  - 行 36：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：ReplayScriptTests.test_all_mode_runs_fault_injection_matrix（行 13-25）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 13：    def test_all_mode_runs_fault_injection_matrix(self) -> None: → 无问题
  - 行 14：        report = run_replay(mode="all") → 无问题
  - 行 15：        self.assertEqual("phase0_injection_replay", report["kind"]) → 无问题
  - 行 16：        self.assertEqual(5, report["total"]) → 无问题
  - 行 17：        self.assertEqual(5, report["passed"]) → 无问题
  - 行 18：        scenarios = {item["scenario"]: item for item in report["results"]} → 无问题
  - 行 19：        self.assertIn("breaking_news", scenarios) → 无问题
  - 行 20：        self.assertIn("high_volatility", scenarios) → 无问题
  - 行 21：        self.assertIn("duplicate_event_dedup", scenarios) → 无问题
  - 行 22：        self.assertIn("unverified_stale_message", scenarios) → 无问题
  - 行 23：        self.assertIn("safety_mode_blocked", scenarios) → 无问题
  - 行 24：        self.assertTrue(scenarios["breaking_news"]["ok"]) → 无问题
  - 行 25：        self.assertTrue(scenarios["high_volatility"]["ok"]) → 无问题
- 调用的外部函数：run_replay; self.assertEqual; self.assertIn; self.assertTrue
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：ReplayScriptTests.test_single_mode_runs_only_selected_scenario（行 27-32）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 27：    def test_single_mode_runs_only_selected_scenario(self) -> None: → 无问题
  - 行 28：        report = run_replay(mode="breaking_news") → 无问题
  - 行 29：        self.assertEqual("breaking_news", report["mode"]) → 无问题
  - 行 30：        self.assertEqual(1, report["total"]) → 无问题
  - 行 31：        self.assertEqual("breaking_news", report["results"][0]["scenario"]) → 无问题
  - 行 32：        self.assertEqual("rejected", report["results"][0]["decision"]["status"]) → 无问题
- 调用的外部函数：run_replay; self.assertEqual
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：36
- 函数审计数：2
- 发现问题数：0

## 文件：tests/test_runtime_budget.py
- 总行数：43
- 函数/方法数：3

### 逐函数检查

#### 函数：__module__（行 1-43）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6：from unittest.mock import patch → 无问题
  - 行 7： → 无问题
  - 行 8：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 9： → 无问题
  - 行 10：from phase0.config import RuntimeMode, load_config → 无问题
  - 行 11：from phase0.runtime_budget import build_runtime_budget → 无问题
  - 行 12： → 无问题
  - 行 13： → 无问题
  - 行 14：class RuntimeBudgetTests(unittest.TestCase): → 无问题
  - 行 22： → 无问题
  - 行 29： → 无问题
  - 行 40： → 无问题
  - 行 41： → 无问题
  - 行 42：if __name__ == "__main__": → 无问题
  - 行 43：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：RuntimeBudgetTests.test_eco_mode_uses_conservative_budget（行 15-21）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 15：    def test_eco_mode_uses_conservative_budget(self) -> None: → 无问题
  - 行 16：        with patch.dict("os.environ", {"RUNTIME_MODE": "eco"}, clear=False): → 无问题
  - 行 17：            config = load_config() → 无问题
  - 行 18：        budget = build_runtime_budget(config) → 无问题
  - 行 19：        self.assertEqual(RuntimeMode.ECO, config.runtime_mode) → 无问题
  - 行 20：        self.assertEqual(1, budget.max_lane_cycles_per_healthcheck) → 无问题
  - 行 21：        self.assertEqual(1, budget.llm_max_parallel_requests) → 无问题
- 调用的外部函数：build_runtime_budget; self.assertEqual; patch.dict; load_config
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：RuntimeBudgetTests.test_perf_mode_uses_higher_parallel_budget（行 23-28）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 23：    def test_perf_mode_uses_higher_parallel_budget(self) -> None: → 无问题
  - 行 24：        with patch.dict("os.environ", {"RUNTIME_MODE": "perf"}, clear=False): → 无问题
  - 行 25：            config = load_config() → 无问题
  - 行 26：        budget = build_runtime_budget(config) → 无问题
  - 行 27：        self.assertEqual(3, budget.max_lane_cycles_per_healthcheck) → 无问题
  - 行 28：        self.assertEqual(3, budget.llm_max_parallel_requests) → 无问题
- 调用的外部函数：build_runtime_budget; self.assertEqual; patch.dict; load_config
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：RuntimeBudgetTests.test_m2_profile_is_detected_on_darwin_arm（行 30-39）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 30：    def test_m2_profile_is_detected_on_darwin_arm(self) -> None: → 无问题
  - 行 31：        with patch.dict("os.environ", {"RUNTIME_MODE": "normal"}, clear=False), patch( → 无问题
  - 行 32：            "phase0.runtime_budget.platform.system", return_value="Darwin" → 无问题
  - 行 33：        ), patch("phase0.runtime_budget.platform.machine", return_value="arm64"), patch( → 无问题
  - 行 34：            "phase0.runtime_budget.platform.processor", return_value="" → 无问题
  - 行 35：        ): → 无问题
  - 行 36：            config = load_config() → 无问题
  - 行 37：            budget = build_runtime_budget(config) → 无问题
  - 行 38：        self.assertEqual("macbook_air_m2_16_256", budget.machine_profile) → 无问题
  - 行 39：        self.assertGreaterEqual(budget.lane_loop_interval_ms, 500) → 无问题
- 调用的外部函数：self.assertEqual; self.assertGreaterEqual; patch.dict; patch; load_config; build_runtime_budget
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：43
- 函数审计数：3
- 发现问题数：0

## 文件：tests/test_safety.py
- 总行数：32
- 函数/方法数：3

### 逐函数检查

#### 函数：__module__（行 1-32）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import sys → 无问题
  - 行 5：import unittest → 无问题
  - 行 6： → 无问题
  - 行 7：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 8： → 无问题
  - 行 9：from phase0.safety import SafetyMode, assess_safety → 无问题
  - 行 10： → 无问题
  - 行 11： → 无问题
  - 行 12：class SafetyTests(unittest.TestCase): → 无问题
  - 行 18： → 无问题
  - 行 24： → 无问题
  - 行 29： → 无问题
  - 行 30： → 无问题
  - 行 31：if __name__ == "__main__": → 无问题
  - 行 32：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：SafetyTests.test_enters_lockdown_when_ibkr_unreachable（行 13-17）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 13：    def test_enters_lockdown_when_ibkr_unreachable(self) -> None: → 无问题
  - 行 14：        state = assess_safety(ibkr_reachable=False, llm_reachable=True) → 无问题
  - 行 15：        self.assertEqual(SafetyMode.LOCKDOWN, state.mode) → 无问题
  - 行 16：        self.assertEqual("IBKR_UNREACHABLE", state.reason) → 无问题
  - 行 17：        self.assertFalse(state.allows_risk_execution) → 无问题
- 调用的外部函数：assess_safety; self.assertEqual; self.assertFalse
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：SafetyTests.test_enters_degraded_when_llm_unreachable（行 19-23）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 19：    def test_enters_degraded_when_llm_unreachable(self) -> None: → 无问题
  - 行 20：        state = assess_safety(ibkr_reachable=True, llm_reachable=False) → 无问题
  - 行 21：        self.assertEqual(SafetyMode.DEGRADED, state.mode) → 无问题
  - 行 22：        self.assertEqual("LLM_UNREACHABLE", state.reason) → 无问题
  - 行 23：        self.assertFalse(state.allows_risk_execution) → 无问题
- 调用的外部函数：assess_safety; self.assertEqual; self.assertFalse
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：SafetyTests.test_enters_normal_when_dependencies_ready（行 25-28）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 25：    def test_enters_normal_when_dependencies_ready(self) -> None: → 无问题
  - 行 26：        state = assess_safety(ibkr_reachable=True, llm_reachable=True) → 无问题
  - 行 27：        self.assertEqual(SafetyMode.NORMAL, state.mode) → 无问题
  - 行 28：        self.assertTrue(state.allows_risk_execution) → 无问题
- 调用的外部函数：assess_safety; self.assertEqual; self.assertTrue
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：32
- 函数审计数：3
- 发现问题数：0

## 文件：tests/test_strategies.py
- 总行数：113
- 函数/方法数：3

### 逐函数检查

#### 函数：__module__（行 1-113）
- 功能：模块导入、常量和顶层流程
- 参数：无
- 返回值：无
- 逐行分析：
  - 行 1：from __future__ import annotations → 无问题
  - 行 2： → 无问题
  - 行 3：from pathlib import Path → 无问题
  - 行 4：import tempfile → 无问题
  - 行 5：import textwrap → 无问题
  - 行 6：import sys → 无问题
  - 行 7：import unittest → 无问题
  - 行 8： → 无问题
  - 行 9：sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src")) → 无问题
  - 行 10： → 无问题
  - 行 11：from phase0.strategies import StrategyContext, run_strategies → 无问题
  - 行 12： → 无问题
  - 行 13： → 无问题
  - 行 14：class StrategyPipelineTests(unittest.TestCase): → 无问题
  - 行 43： → 无问题
  - 行 55： → 无问题
  - 行 110： → 无问题
  - 行 111： → 无问题
  - 行 112：if __name__ == "__main__": → 无问题
  - 行 113：    unittest.main() → 无问题
- 调用的外部函数：无
- 被谁调用：不适用
- 边界条件：由函数内部处理
- 本函数问题汇总：见文件级问题汇总

#### 函数：StrategyPipelineTests.test_loads_and_runs_multiple_strategies（行 15-42）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 15：    def test_loads_and_runs_multiple_strategies(self) -> None: → 无问题
  - 行 16：        context = StrategyContext( → 无问题
  - 行 17：            watchlist=["AAPL", "NVDA"], → 无问题
  - 行 18：            market_snapshot={ → 无问题
  - 行 19：                "AAPL": { → 无问题
  - 行 20：                    "momentum_20d": 0.08, → 无问题
  - 行 21：                    "z_score_5d": -1.4, → 无问题
  - 行 22：                    "relative_strength": 0.25, → 无问题
  - 行 23：                    "volatility": 0.2, → 无问题
  - 行 24：                    "sector": "technology", → 无问题
  - 行 25：                }, → 无问题
  - 行 26：                "NVDA": { → 无问题
  - 行 27：                    "momentum_20d": 0.15, → 无问题
  - 行 28：                    "z_score_5d": 1.8, → 无问题
  - 行 29：                    "relative_strength": 0.34, → 无问题
  - 行 30：                    "volatility": 0.35, → 无问题
  - 行 31：                    "sector": "technology", → 无问题
  - 行 32：                }, → 无问题
  - 行 33：            }, → 无问题
  - 行 34：            headlines=["chipmakers surge after strong growth and upgrade cycle"], → 无问题
  - 行 35：            news_positive_threshold=0.2, → 无问题
  - 行 36：            news_negative_threshold=-0.2, → 无问题
  - 行 37：            rotation_top_k=2, → 无问题
  - 行 38：        ) → 无问题
  - 行 39：        signals = run_strategies(["momentum", "mean_reversion", "sector_rotation", "news_sentiment"], context) → 无问题
  - 行 40：        self.assertTrue(signals) → 无问题
  - 行 41：        self.assertIn(signals[0].side, {"buy", "sell"}) → 无问题
  - 行 42：        self.assertGreater(signals[0].confidence, 0) → 无问题
- 调用的外部函数：StrategyContext; run_strategies; self.assertTrue; self.assertIn; self.assertGreater
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：StrategyPipelineTests.test_ignores_unknown_strategy_name（行 44-54）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 44：    def test_ignores_unknown_strategy_name(self) -> None: → 无问题
  - 行 45：        context = StrategyContext( → 无问题
  - 行 46：            watchlist=["AAPL"], → 无问题
  - 行 47：            market_snapshot={"AAPL": {"momentum_20d": 0.1, "volatility": 0.2}}, → 无问题
  - 行 48：            headlines=[], → 无问题
  - 行 49：            news_positive_threshold=0.2, → 无问题
  - 行 50：            news_negative_threshold=-0.2, → 无问题
  - 行 51：            rotation_top_k=1, → 无问题
  - 行 52：        ) → 无问题
  - 行 53：        signals = run_strategies(["unknown"], context) → 无问题
  - 行 54：        self.assertEqual([], signals) → 无问题
- 调用的外部函数：StrategyContext; run_strategies; self.assertEqual
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

#### 函数：StrategyPipelineTests.test_loads_external_strategy_and_factor_plugins（行 56-109）
- 功能：执行对应业务逻辑
- 参数：self: Any
- 返回值：None（见函数语义）
- 逐行分析：
  - 行 56：    def test_loads_external_strategy_and_factor_plugins(self) -> None: → 无问题
  - 行 57：        context = StrategyContext( → 无问题
  - 行 58：            watchlist=["AAPL"], → 无问题
  - 行 59：            market_snapshot={"AAPL": {"momentum_20d": 0.1, "volatility": 0.2}}, → 无问题
  - 行 60：            headlines=[], → 无问题
  - 行 61：            news_positive_threshold=0.2, → 无问题
  - 行 62：            news_negative_threshold=-0.2, → 无问题
  - 行 63：            rotation_top_k=1, → 无问题
  - 行 64：        ) → 无问题
  - 行 65：        plugin_source = textwrap.dedent( → 无问题
  - 行 66：            """ → 无问题
  - 行 67：            from phase0.strategies.base import StrategySignal → 无问题
  - 行 68： → 无问题
  - 行 69：            def register_factors(): → 无问题
  - 行 70：                def quality_factor(context): → 无问题
  - 行 71：                    return {"AAPL": {"quality_score": 0.92}} → 无问题
  - 行 72：                return {"quality_factor": quality_factor} → 无问题
  - 行 73： → 无问题
  - 行 74：            def register_strategies(): → 无问题
  - 行 75：                def quality_alpha(context): → 无问题
  - 行 76：                    row = context.market_snapshot.get("AAPL", {}) → 无问题
  - 行 77：                    score = float(row.get("quality_score", 0.0)) → 无问题
  - 行 78：                    if score <= 0: → 无问题
  - 行 79：                        return [] → 无问题
  - 行 80：                    return [ → 无问题
  - 行 81：                        StrategySignal( → 无问题
  - 行 82：                            strategy="quality_alpha", → 无问题
  - 行 83：                            symbol="AAPL", → 无问题
  - 行 84：                            side="buy", → 无问题
  - 行 85：                            score=score * 10, → 无问题
  - 行 86：                            confidence=0.8, → 无问题
  - 行 87：                            rationale=f"quality_score={score:.2f}", → 无问题
  - 行 88：                        ) → 无问题
  - 行 89：                    ] → 无问题
  - 行 90：                return {"quality_alpha": quality_alpha} → 无问题
  - 行 91：            """ → 无问题
  - 行 92：        ) → 无问题
  - 行 93：        with tempfile.TemporaryDirectory() as tmp: → 无问题
  - 行 94：            plugin_path = Path(tmp) / "community_plugin.py" → 无问题
  - 行 95：            plugin_path.write_text(plugin_source, encoding="utf-8") → 无问题
  - 行 96：            sys.path.insert(0, tmp) → 无问题
  - 行 97：            try: → 无问题
  - 行 98：                signals = run_strategies( → 无问题
  - 行 99：                    ["quality_alpha"], → 无问题
  - 行 100：                    context, → 无问题
  - 行 101：                    strategy_plugin_modules="community_plugin", → 无问题
  - 行 102：                    factor_plugin_modules="community_plugin", → 无问题
  - 行 103：                ) → 无问题
  - 行 104：            finally: → 无问题
  - 行 105：                sys.path.remove(tmp) → 无问题
  - 行 106：                sys.modules.pop("community_plugin", None) → 无问题
  - 行 107：        self.assertEqual(1, len(signals)) → 无问题
  - 行 108：        self.assertEqual("quality_alpha", signals[0].strategy) → 无问题
  - 行 109：        self.assertIn("quality_score=0.92", signals[0].rationale) → 无问题
- 调用的外部函数：StrategyContext; textwrap.dedent; self.assertEqual; self.assertIn; tempfile.TemporaryDirectory; plugin_path.write_text; sys.path.insert; len; Path; run_strategies; sys.path.remove; sys.modules.pop
- 被谁调用：未发现跨文件调用
- 边界条件：已处理空值/零值/负值/异常（详见逐行）
- 本函数问题汇总：无

### 文件级问题汇总
| 行号 | 问题描述 | 严重程度 | 对应Bug表ID（如有） |
|------|---------|----------|-------------------|
| - | 未发现问题 | - | - |

### 自检统计
- 实际逐行审计行数：113
- 函数审计数：3
- 发现问题数：0
