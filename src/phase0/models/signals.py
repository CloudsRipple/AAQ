from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UltraSignalEvent(BaseModel):
    # 严格禁止额外字段，确保 Ultra->High 契约稳定且可跨进程序列化
    model_config = ConfigDict(extra="forbid")

    # 触发标的，例如 AAPL、MSFT
    symbol: str = Field(min_length=1)
    # 事件发生时间，统一使用 datetime 以便后续切换 ZeroMQ/JSON 时标准化处理
    timestamp: datetime
    # 事件类型：价格异动、成交量激增、新闻预警、复合事件
    event_type: Literal["price_spike", "volume_surge", "news_alert", "composite"]
    # 置信度分数，范围固定在 [0.0, 1.0]
    confidence_score: float = Field(ge=0.0, le=1.0)
    # 事件来源：规则引擎、向量匹配、复合判定
    source: Literal["rule_engine", "vector_match", "composite"]
    # 命中的原型事件描述；规则层触发时可为空
    matched_prototype: Optional[str] = None
    # 原始触发数据，供 High 层审计与回放
    raw_data: dict[str, Any]


class HighDecisionEvent(BaseModel):
    # 严格契约：High 只输出可被执行层消费的必要字段
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1)
    approved: bool
    risk_multiplier: float = Field(ge=0.1, le=3.0)
    stop_loss_pct: float = Field(gt=0.0, le=1.0)
    reason: str = Field(min_length=1)
    ultra_signal: UltraSignalEvent
    decision_ts: datetime


class ExecutionIntentEvent(BaseModel):
    # 严格契约：执行意图必须完整，缺字段 fail-closed
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
    allow_opening: bool = True
    data_degraded: bool = False
    data_quality_errors: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_temporal_and_price_invariants(self) -> "ExecutionIntentEvent":
        if self.last_exit_at is None and not (self.last_exit_reason or "").strip():
            raise ValueError("last_exit_reason required when last_exit_at is null")
        if self.side == "buy":
            if not (self.stop_loss < self.entry_price < self.take_profit):
                raise ValueError("buy intent must satisfy stop_loss < entry_price < take_profit")
        else:
            if not (self.take_profit < self.entry_price < self.stop_loss):
                raise ValueError("sell intent must satisfy take_profit < entry_price < stop_loss")
        return self
