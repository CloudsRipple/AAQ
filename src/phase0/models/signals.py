from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    matched_prototype: str | None = None
    # 原始触发数据，供 High 层审计与回放
    raw_data: dict
