from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "LayeredMemoryStore",
    "PersistentLayeredMemoryStore",
    "MemoryRecord",
    "MemoryMatch",
    "BaseUltraSentinel",
    "AsyncUltraSentinel",
    "UltraSignal",
    "build_ultra_sentinel",
    "evaluate_ultra_guard",
    "CommitteeVote",
    "LowAnalysis",
    "analyze_low_lane",
    "analyze_low_lane_async",
    "HighAdjustmentDecision",
    "evaluate_high_adjustment",
    "HighAssessment",
    "HighCommitteeVote",
    "assess_high_lane",
    "assess_high_lane_async",
    "build_high_prompt",
    "start_high_engine",
    "start_low_engine",
    "start_ultra_engine",
]


_EXPORT_MODULE_MAP: dict[str, str] = {
    "LayeredMemoryStore": ".memory",
    "PersistentLayeredMemoryStore": ".memory",
    "MemoryRecord": ".memory",
    "MemoryMatch": ".memory",
    "BaseUltraSentinel": ".ultra",
    "AsyncUltraSentinel": ".ultra",
    "UltraSignal": ".ultra",
    "build_ultra_sentinel": ".ultra",
    "evaluate_ultra_guard": ".ultra",
    "CommitteeVote": ".low",
    "LowAnalysis": ".low",
    "analyze_low_lane": ".low",
    "analyze_low_lane_async": ".low",
    "HighAdjustmentDecision": ".high",
    "evaluate_high_adjustment": ".high",
    "HighAssessment": ".high",
    "HighCommitteeVote": ".high",
    "assess_high_lane": ".high",
    "assess_high_lane_async": ".high",
    "build_high_prompt": ".high",
    "start_high_engine": ".high",
    "start_low_engine": ".low",
    "start_ultra_engine": ".ultra",
}


def __getattr__(name: str) -> Any:
    module_name = _EXPORT_MODULE_MAP.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_name, __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(list(globals().keys()) + __all__))
