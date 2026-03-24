from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from .contracts import AdjustmentProposal, RiskOverlay

if TYPE_CHECKING:
    from ..config import AppConfig


class GovernanceMode(str, Enum):
    OFF = "OFF"
    SHADOW = "SHADOW"
    BOUNDED_AUTO = "BOUNDED_AUTO"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class GovernanceOutcome(str, Enum):
    REJECTED = "REJECTED"
    SHADOWED = "SHADOWED"
    PENDING_HUMAN = "PENDING_HUMAN"
    APPROVED_AUTO = "APPROVED_AUTO"


@dataclass(frozen=True)
class HighPolicySnapshot:
    risk_multiplier: float
    stop_loss_pct: float
    source: str
    proposal_id: str
    updated_at: datetime


@dataclass(frozen=True)
class GovernanceDecision:
    proposal_id: str
    target_param: str
    outcome: GovernanceOutcome
    reason: str
    applied_value: float | None
    audited_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class GovernanceAuditRecord:
    proposal_id: str
    target_param: str
    mode: GovernanceMode
    runtime_profile: str
    outcome: GovernanceOutcome
    reason: str
    state_path: tuple[str, ...]
    applied_value: float | None
    audited_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class ParameterEnvelope:
    min_value: float
    max_value: float
    hard_param: bool = False


@dataclass
class GovernancePlane:
    mode: GovernanceMode
    runtime_profile: str
    _registry: dict[str, ParameterEnvelope]
    _snapshot: HighPolicySnapshot
    _audit_log: list[GovernanceAuditRecord] = field(default_factory=list)

    @classmethod
    def from_app_config(cls, config: AppConfig) -> "GovernancePlane":
        mode = resolve_governance_mode(ai_enabled=config.ai_enabled)
        now = datetime.now(tz=timezone.utc)
        baseline = HighPolicySnapshot(
            risk_multiplier=1.0,
            stop_loss_pct=config.ai_stop_loss_default_pct,
            source="baseline",
            proposal_id="baseline",
            updated_at=now,
        )
        registry = {
            "high.risk_multiplier": ParameterEnvelope(
                min_value=config.high_risk_multiplier_min,
                max_value=config.high_risk_multiplier_max,
            ),
            "high.stop_loss_pct": ParameterEnvelope(
                min_value=config.ai_stop_loss_default_pct,
                max_value=config.ai_stop_loss_break_max_pct,
            ),
        }
        return cls(
            mode=mode,
            runtime_profile=config.runtime_profile.value,
            _registry=registry,
            _snapshot=baseline,
        )

    def current_snapshot(self) -> HighPolicySnapshot:
        return self._snapshot

    def recent_audit(self, limit: int = 100) -> list[GovernanceAuditRecord]:
        if limit <= 0:
            return []
        return self._audit_log[-limit:]

    def submit_adjustment(self, proposal: AdjustmentProposal) -> GovernanceDecision:
        now = datetime.now(tz=timezone.utc)
        state_path: list[str] = [
            "GENERATED",
            "INTAKE_VALIDATED",
            "REGISTRY_BOUND",
            "POLICY_VALIDATED",
        ]
        envelope = self._registry.get(proposal.target_param)
        if envelope is None:
            decision = self._reject(
                proposal=proposal,
                now=now,
                reason="TARGET_PARAM_NOT_REGISTERED",
                state_path=state_path,
            )
            state_path.append("AUDITED")
            self._audit(decision=decision, proposal=proposal, state_path=state_path)
            return decision

        if proposal.mode != self.mode.value:
            decision = self._reject(
                proposal=proposal,
                now=now,
                reason="PROPOSAL_MODE_MISMATCH",
                state_path=state_path,
            )
            state_path.append("AUDITED")
            self._audit(decision=decision, proposal=proposal, state_path=state_path)
            return decision

        suggested_value = _safe_float(proposal.suggested_value)
        if suggested_value is None:
            decision = self._reject(
                proposal=proposal,
                now=now,
                reason="SUGGESTED_VALUE_INVALID",
                state_path=state_path,
            )
            state_path.append("AUDITED")
            self._audit(decision=decision, proposal=proposal, state_path=state_path)
            return decision

        bounded_value = _clamp(suggested_value, envelope.min_value, envelope.max_value)
        state_path.append("ENVELOPE_ENFORCED")
        outcome, reason = self._approval_policy()
        state_path.append(outcome.value)
        expires_at = now + timedelta(seconds=int(proposal.ttl_seconds))
        applied_value: float | None = None
        if outcome == GovernanceOutcome.APPROVED_AUTO:
            state_path.append("APPLIED")
            applied_value = bounded_value
            self._apply(param=proposal.target_param, value=bounded_value, proposal_id=proposal.proposal_id, now=now)
        state_path.append("AUDITED")

        decision = GovernanceDecision(
            proposal_id=proposal.proposal_id,
            target_param=proposal.target_param,
            outcome=outcome,
            reason=reason,
            applied_value=applied_value,
            audited_at=now,
            expires_at=expires_at,
        )
        self._audit(decision=decision, proposal=proposal, state_path=state_path)
        return decision

    def submit_overlay(self, overlay: RiskOverlay) -> GovernanceDecision:
        now = datetime.now(tz=timezone.utc)
        proposal = AdjustmentProposal(
            proposal_id=f"overlay::{overlay.overlay_id}",
            scope=overlay.scope,
            target_param="overlay.effect",
            current_value="N/A",
            suggested_value=overlay.effect,
            min_allowed="N/A",
            max_allowed="N/A",
            confidence=1.0,
            reason=overlay.reason,
            evidence_refs=list(overlay.evidence_refs),
            ttl_seconds=max(1, int((overlay.expires_at - now).total_seconds())),
            mode=self.mode.value,
        )
        decision = GovernanceDecision(
            proposal_id=proposal.proposal_id,
            target_param=proposal.target_param,
            outcome=GovernanceOutcome.SHADOWED,
            reason="OVERLAY_RECORDED_SHADOW_ONLY",
            applied_value=None,
            audited_at=now,
            expires_at=overlay.expires_at,
        )
        self._audit(
            decision=decision,
            proposal=proposal,
            state_path=["GENERATED", "INTAKE_VALIDATED", "AUDITED"],
        )
        return decision

    def _approval_policy(self) -> tuple[GovernanceOutcome, str]:
        if self.mode == GovernanceMode.OFF:
            return GovernanceOutcome.REJECTED, "GOVERNANCE_MODE_OFF"
        if self.mode == GovernanceMode.SHADOW:
            return GovernanceOutcome.SHADOWED, "GOVERNANCE_MODE_SHADOW"
        if self.mode == GovernanceMode.HUMAN_APPROVAL:
            return GovernanceOutcome.PENDING_HUMAN, "HUMAN_APPROVAL_REQUIRED"
        if self.runtime_profile != "paper":
            return GovernanceOutcome.REJECTED, "BOUNDED_AUTO_REQUIRES_PAPER_PROFILE"
        return GovernanceOutcome.APPROVED_AUTO, "APPROVED_WITHIN_ENVELOPE"

    def _apply(self, *, param: str, value: float, proposal_id: str, now: datetime) -> None:
        if param == "high.risk_multiplier":
            self._snapshot = HighPolicySnapshot(
                risk_multiplier=value,
                stop_loss_pct=self._snapshot.stop_loss_pct,
                source="governance",
                proposal_id=proposal_id,
                updated_at=now,
            )
            return
        if param == "high.stop_loss_pct":
            self._snapshot = HighPolicySnapshot(
                risk_multiplier=self._snapshot.risk_multiplier,
                stop_loss_pct=value,
                source="governance",
                proposal_id=proposal_id,
                updated_at=now,
            )

    def _reject(
        self,
        *,
        proposal: AdjustmentProposal,
        now: datetime,
        reason: str,
        state_path: list[str],
    ) -> GovernanceDecision:
        state_path.append("REJECTED")
        return GovernanceDecision(
            proposal_id=proposal.proposal_id,
            target_param=proposal.target_param,
            outcome=GovernanceOutcome.REJECTED,
            reason=reason,
            applied_value=None,
            audited_at=now,
            expires_at=now + timedelta(seconds=max(1, int(proposal.ttl_seconds))),
        )

    def _audit(
        self,
        *,
        decision: GovernanceDecision,
        proposal: AdjustmentProposal,
        state_path: list[str],
    ) -> None:
        self._audit_log.append(
            GovernanceAuditRecord(
                proposal_id=decision.proposal_id,
                target_param=decision.target_param,
                mode=self.mode,
                runtime_profile=self.runtime_profile,
                outcome=decision.outcome,
                reason=decision.reason,
                state_path=tuple(state_path),
                applied_value=decision.applied_value,
                audited_at=decision.audited_at,
                expires_at=decision.expires_at,
            )
        )


def resolve_governance_mode(*, ai_enabled: bool) -> GovernanceMode:
    raw = os.getenv("AI_GOVERNANCE_MODE", "").strip().upper()
    if raw in {item.value for item in GovernanceMode}:
        return GovernanceMode(raw)
    if not ai_enabled:
        return GovernanceMode.OFF
    return GovernanceMode.SHADOW


def _safe_float(raw_value: Any) -> float | None:
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


__all__ = [
    "GovernanceAuditRecord",
    "GovernanceDecision",
    "GovernanceMode",
    "GovernanceOutcome",
    "GovernancePlane",
    "HighPolicySnapshot",
    "resolve_governance_mode",
]
