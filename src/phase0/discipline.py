from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HoldWorthiness:
    score: float
    should_wait: bool
    recommended_holding_days: int
    reasons: list[str]


def evaluate_hold_worthiness(
    *,
    market_row: dict[str, float | str],
    strategy_confidence: float,
    ultra_authenticity_score: float,
    low_committee_approved: bool,
    hold_score_threshold: float,
    max_holding_days: int,
) -> HoldWorthiness:
    momentum = max(0.0, float(market_row.get("momentum_20d", 0.0)))
    relative_strength = max(0.0, float(market_row.get("relative_strength", 0.0)))
    volatility = max(0.01, float(market_row.get("volatility", 0.2)))
    momentum_score = min(1.0, momentum / 0.12)
    rel_score = min(1.0, relative_strength / 0.3)
    vol_penalty = min(0.4, volatility / 1.2)
    committee_bonus = 0.1 if low_committee_approved else -0.08
    raw_score = (
        momentum_score * 0.3
        + rel_score * 0.25
        + max(0.0, strategy_confidence) * 0.2
        + max(0.0, ultra_authenticity_score) * 0.25
        + committee_bonus
        - vol_penalty
    )
    score = max(0.0, min(1.0, round(raw_score, 6)))
    should_wait = score >= hold_score_threshold
    recommended_holding_days = min(max(1, max_holding_days), 3 if should_wait else 1)
    reasons: list[str] = []
    if momentum_score > 0.65:
        reasons.append("MOMENTUM_STRONG")
    if rel_score > 0.6:
        reasons.append("SECTOR_RELATIVE_STRENGTH")
    if ultra_authenticity_score >= 0.7:
        reasons.append("NEWS_AUTHENTIC")
    if low_committee_approved:
        reasons.append("LOW_COMMITTEE_APPROVED")
    if volatility > 0.28:
        reasons.append("VOLATILITY_ELEVATED")
    if not reasons:
        reasons.append("NO_CLEAR_EDGE")
    return HoldWorthiness(
        score=score,
        should_wait=should_wait,
        recommended_holding_days=recommended_holding_days,
        reasons=reasons,
    )


def build_daily_discipline_plan(
    *,
    actions_today: int,
    has_open_position: bool,
    min_actions_per_day: int,
    discipline_enabled: bool,
    hold: HoldWorthiness,
) -> dict[str, object]:
    if not discipline_enabled:
        return {
            "enabled": False,
            "required_action": "none",
            "action_reason": "DISCIPLINE_DISABLED",
            "actions_today": actions_today,
            "min_actions_per_day": min_actions_per_day,
            "hold_score": hold.score,
            "recommended_holding_days": hold.recommended_holding_days,
            "should_wait": hold.should_wait,
            "reasons": hold.reasons,
        }
    required_action = "none"
    action_reason = "TARGET_REACHED"
    if actions_today < min_actions_per_day:
        if has_open_position and not hold.should_wait:
            required_action = "sell"
            action_reason = "DAILY_QUOTA_AND_LOW_HOLD_SCORE"
        elif has_open_position and hold.should_wait:
            required_action = "hold"
            action_reason = "DAILY_QUOTA_BUT_HOLD_SCORE_HIGH"
        else:
            required_action = "buy"
            action_reason = "DAILY_QUOTA_NO_POSITION_BUY"
    return {
        "enabled": True,
        "required_action": required_action,
        "action_reason": action_reason,
        "actions_today": actions_today,
        "min_actions_per_day": min_actions_per_day,
        "hold_score": hold.score,
        "recommended_holding_days": hold.recommended_holding_days,
        "should_wait": hold.should_wait,
        "reasons": hold.reasons,
    }
