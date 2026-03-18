from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StopLossOverrideState:
    _used_symbols: set[str]

    def was_used(self, symbol: str) -> bool:
        return symbol.upper() in self._used_symbols

    def mark_used(self, symbol: str) -> None:
        self._used_symbols.add(symbol.upper())


STATE = StopLossOverrideState(_used_symbols=set())
