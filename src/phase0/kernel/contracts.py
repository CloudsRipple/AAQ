from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UltraSignalEvent(BaseModel):
    # Transitional contract home for the existing Ultra -> High payload.
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1)
    timestamp: datetime
    event_type: Literal["price_spike", "volume_surge", "news_alert", "composite"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    source: Literal["rule_engine", "vector_match", "composite"]
    matched_prototype: Optional[str] = None
    raw_data: dict[str, Any]


class TradeDecision(BaseModel):
    # Authoritative High output contract.
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1)
    approved: bool
    risk_multiplier: float = Field(ge=0.1, le=3.0)
    stop_loss_pct: float = Field(gt=0.0, le=1.0)
    reason: str = Field(min_length=1)
    reject_reasons: list[str] = Field(default_factory=list)
    ultra_signal: UltraSignalEvent
    decision_ts: datetime
    side: Optional[Literal["buy", "sell"]] = None
    strategy_id: Optional[str] = Field(default=None, min_length=1)
    signal_ts: Optional[datetime] = None
    snapshot_id: Optional[str] = Field(default=None, min_length=1)
    snapshot_ts: Optional[datetime] = None
    quantity: Optional[int] = Field(default=None, ge=1)
    bracket_order: dict[str, Any] = Field(default_factory=dict)
    estimated_transaction_cost: dict[str, float] = Field(default_factory=dict)
    allow_opening: bool = True
    data_degraded: bool = False
    data_quality_errors: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_execution_ready_fields(self) -> "TradeDecision":
        if not self.approved:
            return self
        if self.side is None:
            raise ValueError("approved high decision requires side")
        if self.strategy_id is None:
            raise ValueError("approved high decision requires strategy_id")
        if self.signal_ts is None:
            raise ValueError("approved high decision requires signal_ts")
        if self.snapshot_id is None:
            raise ValueError("approved high decision requires snapshot_id")
        if self.snapshot_ts is None:
            raise ValueError("approved high decision requires snapshot_ts")
        if self.quantity is None:
            raise ValueError("approved high decision requires quantity")
        if not self.bracket_order:
            raise ValueError("approved high decision requires bracket_order")
        if not self.estimated_transaction_cost:
            raise ValueError("approved high decision requires estimated_transaction_cost")
        return self


class OrderIntent(BaseModel):
    # Authoritative Risk -> Execution handoff contract.
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1)
    side: Literal["buy", "sell"]
    entry_price: float = Field(gt=0.0)
    stop_loss: float = Field(gt=0.0)
    take_profit: float = Field(gt=0.0)
    equity: float = Field(gt=0.0)
    current_symbol_exposure: float = Field(ge=0.0)
    last_exit_at: Optional[datetime] = None
    last_exit_reason: Optional[str] = None
    snapshot_id: str = Field(min_length=1)
    snapshot_ts: datetime
    strategy_id: str = Field(min_length=1)
    risk_multiplier: float = Field(gt=0.0, le=3.0)
    stop_loss_pct: float = Field(gt=0.0, le=1.0)
    high_reason: str = Field(min_length=1)
    ultra_signal: UltraSignalEvent
    quantity: int = Field(ge=1)
    bracket_order: dict[str, Any] = Field(default_factory=dict)
    estimated_transaction_cost: dict[str, float] = Field(default_factory=dict)
    allow_opening: bool = True
    data_degraded: bool = False
    data_quality_errors: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_temporal_and_price_invariants(self) -> "OrderIntent":
        if self.last_exit_at is None and not (self.last_exit_reason or "").strip():
            raise ValueError("last_exit_reason required when last_exit_at is null")
        if self.side == "buy":
            if not (self.stop_loss < self.entry_price < self.take_profit):
                raise ValueError("buy intent must satisfy stop_loss < entry_price < take_profit")
        else:
            if not (self.take_profit < self.entry_price < self.stop_loss):
                raise ValueError("sell intent must satisfy take_profit < entry_price < stop_loss")
        if not self.bracket_order:
            raise ValueError("execution-ready intent requires bracket_order")
        if not self.estimated_transaction_cost:
            raise ValueError("execution-ready intent requires estimated_transaction_cost")
        return self


# Compatibility aliases while the repository migrates to formal names.
HighDecisionEvent = TradeDecision
ExecutionIntentEvent = OrderIntent


__all__ = [
    "ExecutionIntentEvent",
    "HighDecisionEvent",
    "OrderIntent",
    "TradeDecision",
    "UltraSignalEvent",
]
