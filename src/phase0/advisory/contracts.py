from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AdjustmentProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    target_param: str = Field(min_length=1)
    current_value: Any
    suggested_value: Any
    min_allowed: Any
    max_allowed: Any
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    ttl_seconds: int = Field(gt=0)
    mode: Literal["OFF", "SHADOW", "BOUNDED_AUTO", "HUMAN_APPROVAL"]


class RiskOverlay(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overlay_id: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    overlay_type: str = Field(min_length=1)
    effect: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    expires_at: datetime
    reason: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)


__all__ = [
    "AdjustmentProposal",
    "RiskOverlay",
]
