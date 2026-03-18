from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from ..config import AppConfig


@dataclass(frozen=True)
class HighLaneSettings:
    single_trade_risk_pct: float = 0.01
    total_exposure_limit_pct: float = 0.30
    stop_loss_min_pct: float = 0.05
    stop_loss_max_pct: float = 0.08
    max_drawdown_pct: float = 0.12
    min_trade_units: int = 1
    slippage_bps: float = 2.0
    commission_per_share: float = 0.005
    cooldown_hours: int = 24
    holding_days: int = 2
    risk_multiplier_min: float = 0.5
    risk_multiplier_max: float = 1.5
    take_profit_boost_max_pct: float = 0.2

    @classmethod
    def from_app_config(cls, config: AppConfig) -> "HighLaneSettings":
        return cls(
            single_trade_risk_pct=config.risk_single_trade_pct,
            total_exposure_limit_pct=config.risk_total_exposure_pct,
            stop_loss_min_pct=config.risk_stop_loss_min_pct,
            stop_loss_max_pct=config.risk_stop_loss_max_pct,
            max_drawdown_pct=config.risk_max_drawdown_pct,
            min_trade_units=max(1, config.risk_min_trade_units),
            slippage_bps=max(0.0, config.risk_slippage_bps),
            commission_per_share=max(0.0, config.risk_commission_per_share),
            cooldown_hours=config.cooldown_hours,
            holding_days=config.holding_days,
            risk_multiplier_min=config.high_risk_multiplier_min,
            risk_multiplier_max=config.high_risk_multiplier_max,
            take_profit_boost_max_pct=config.high_take_profit_boost_max_pct,
        )


def evaluate_event(
    event: dict[str, str],
    settings: HighLaneSettings | None = None,
    strategy_adjustments: dict[str, float] | None = None,
) -> dict[str, Any]:
    active_settings = settings or HighLaneSettings()
    settings_error = _validate_settings_bounds(active_settings)
    if settings_error is not None:
        return _rejected(symbol=event.get("symbol", ""), reasons=[settings_error])
    now = datetime.now(tz=timezone.utc)
    symbol = event.get("symbol", "")
    source_reason = _check_source(event)
    if source_reason:
        return _rejected(symbol=symbol, reasons=[source_reason])
    parse_errors, payload = _parse_event(event)
    if parse_errors:
        return _rejected(symbol=symbol, reasons=parse_errors)

    structure_errors = _check_price_structure(payload, settings=active_settings)
    if structure_errors:
        return _rejected(symbol=symbol, reasons=structure_errors)

    cooldown_reason = _check_cooldown(payload["last_exit_at"], now, active_settings.cooldown_hours)
    if cooldown_reason:
        return _rejected(symbol=symbol, reasons=[cooldown_reason])

    holding_reason = _check_holding(payload["position_opened_at"], now, active_settings.holding_days)
    if holding_reason:
        return _rejected(symbol=symbol, reasons=[holding_reason])
    drawdown_reason = _check_max_drawdown(payload, active_settings.max_drawdown_pct)
    if drawdown_reason:
        return _rejected(symbol=symbol, reasons=[drawdown_reason])

    risk_per_share = abs(payload["entry_price"] - payload["stop_loss_price"])
    if risk_per_share <= 0:
        return _rejected(symbol=symbol, reasons=["STOP_LOSS_INVALID"])

    risk_multiplier = 1.0
    take_profit_boost_pct = 0.0
    if strategy_adjustments:
        raw_risk_multiplier = strategy_adjustments.get("risk_multiplier", 1.0)
        risk_multiplier = max(active_settings.risk_multiplier_min, min(active_settings.risk_multiplier_max, raw_risk_multiplier))
        raw_take_profit_boost = strategy_adjustments.get("take_profit_boost_pct", 0.0)
        take_profit_boost_pct = max(
            0.0,
            min(active_settings.take_profit_boost_max_pct, raw_take_profit_boost),
        )
    risk_budget = payload["equity"] * active_settings.single_trade_risk_pct * risk_multiplier
    shares_by_risk = int(risk_budget // risk_per_share)
    min_trade_units = max(1, active_settings.min_trade_units)
    min_trade_units_applied = False
    if shares_by_risk < min_trade_units:
        shares_by_risk = min_trade_units
        min_trade_units_applied = True
    if shares_by_risk < 1:
        return _rejected(symbol=symbol, reasons=["RISK_BUDGET_EXCEEDED"])

    target_weight = max(0.0, min(1.0, payload.get("target_weight", 1.0)))
    scoped_exposure_limit = payload["equity"] * active_settings.total_exposure_limit_pct * max(1e-6, target_weight)
    available_exposure = scoped_exposure_limit - payload["current_symbol_exposure"]
    if available_exposure <= 0:
        return _rejected(symbol=symbol, reasons=["TOTAL_EXPOSURE_LIMIT"])

    shares_by_exposure = int(available_exposure // payload["entry_price"])
    if shares_by_exposure < 1:
        return _rejected(symbol=symbol, reasons=["TOTAL_EXPOSURE_LIMIT"])

    quantity = min(shares_by_risk, shares_by_exposure)
    if quantity < min_trade_units:
        return _rejected(symbol=symbol, reasons=["INVALID_QUANTITY"])

    estimated_cost = _estimate_transaction_cost(
        entry_price=payload["entry_price"],
        quantity=quantity,
        slippage_bps=active_settings.slippage_bps,
        commission_per_share=active_settings.commission_per_share,
    )
    bracket_order = _build_bracket_order(
        payload=payload,
        quantity=quantity,
        now=now,
        take_profit_boost_pct=take_profit_boost_pct,
        holding_days=max(1, active_settings.holding_days),
    )
    return {
        "lane": "high",
        "status": "accepted",
        "symbol": symbol,
        "quantity": quantity,
        "risk_budget": round(risk_budget, 4),
        "risk_per_share": round(risk_per_share, 4),
        "current_exposure_unit": str(payload.get("current_exposure_unit", "notional")),
        "target_weight": round(target_weight, 6),
        "scoped_exposure_limit": round(scoped_exposure_limit, 4),
        "applied_risk_multiplier": round(risk_multiplier, 4),
        "applied_take_profit_boost_pct": round(take_profit_boost_pct, 4),
        "min_trade_units_applied": min_trade_units_applied,
        "estimated_transaction_cost": estimated_cost,
        "reject_reasons": [],
        "bracket_order": bracket_order,
    }


def _parse_event(event: dict[str, str]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    payload: dict[str, Any] = {}

    symbol = event.get("symbol", "").strip().upper()
    if not symbol:
        errors.append("MISSING_SYMBOL")
    payload["symbol"] = symbol

    side = event.get("side", "buy").strip().lower()
    if side not in {"buy", "sell"}:
        errors.append("INVALID_SIDE")
    payload["side"] = side

    for field in ["entry_price", "stop_loss_price", "take_profit_price", "equity", "current_exposure"]:
        raw = event.get(field)
        if raw is None:
            errors.append(f"MISSING_{field.upper()}")
            continue
        try:
            value = float(raw)
        except ValueError:
            errors.append(f"INVALID_{field.upper()}")
            continue
        if value <= 0 and field != "current_exposure":
            errors.append(f"INVALID_{field.upper()}")
            continue
        if value < 0 and field == "current_exposure":
            errors.append(f"INVALID_{field.upper()}")
            continue
        payload[field] = value
    current_exposure_value = _parse_optional_float(event.get("current_exposure"), default=0.0)
    current_exposure_unit = str(event.get("current_exposure_unit", "notional"))
    payload["current_symbol_exposure"] = _normalize_exposure_to_notional(
        raw_value=event.get("current_symbol_exposure"),
        fallback_value=current_exposure_value,
        unit=current_exposure_unit,
        equity=float(payload.get("equity", 0.0)),
    )
    payload["target_weight"] = _parse_optional_float(event.get("target_weight"), default=1.0)
    payload["current_exposure_unit"] = current_exposure_unit
    payload["equity_peak"] = _parse_optional_float(event.get("equity_peak"), default=float(payload.get("equity", 0.0)))

    payload["last_exit_at"] = _parse_time(event.get("last_exit_at"), "INVALID_LAST_EXIT_AT", errors)
    payload["position_opened_at"] = _parse_time(
        event.get("position_opened_at"), "INVALID_POSITION_OPENED_AT", errors
    )
    return errors, payload


def _parse_time(raw: str | None, error_code: str, errors: list[str]) -> datetime | None:
    if raw is None or not raw.strip():
        return None
    text = raw.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        errors.append(error_code)
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_optional_float(raw: object, default: float) -> float:
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _normalize_exposure_to_notional(
    *,
    raw_value: object,
    fallback_value: float,
    unit: str,
    equity: float,
) -> float:
    value = _parse_optional_float(raw_value, fallback_value)
    normalized_unit = unit.strip().lower()
    if normalized_unit in {"ratio", "weight", "pct", "percent"}:
        if equity <= 0:
            return 0.0
        if normalized_unit in {"pct", "percent"}:
            ratio = max(0.0, value) / 100.0
        else:
            ratio = max(0.0, value)
        ratio = min(1.0, ratio)
        return equity * ratio
    return max(0.0, value)


def _check_source(event: dict[str, str]) -> str | None:
    if event.get("lane", "").strip().lower() != "ultra":
        return "SOURCE_LANE_INVALID"
    if event.get("kind", "").strip().lower() != "signal":
        return "EVENT_KIND_INVALID"
    return None


def _check_price_structure(payload: dict[str, Any], settings: HighLaneSettings) -> list[str]:
    side = payload["side"]
    entry = payload["entry_price"]
    stop = payload["stop_loss_price"]
    take_profit = payload["take_profit_price"]
    errors: list[str] = []
    if side == "buy":
        if stop >= entry:
            errors.append("STOP_LOSS_DIRECTION_INVALID")
        if take_profit <= entry:
            errors.append("TAKE_PROFIT_DIRECTION_INVALID")
        if stop < entry:
            stop_ratio = (entry - stop) / entry
            epsilon = 1e-9
            if stop_ratio + epsilon < settings.stop_loss_min_pct or stop_ratio - epsilon > settings.stop_loss_max_pct:
                errors.append("STOP_LOSS_RANGE_INVALID")
    else:
        if stop <= entry:
            errors.append("STOP_LOSS_DIRECTION_INVALID")
        if take_profit >= entry:
            errors.append("TAKE_PROFIT_DIRECTION_INVALID")
        if stop > entry:
            stop_ratio = (stop - entry) / entry
            epsilon = 1e-9
            if stop_ratio + epsilon < settings.stop_loss_min_pct or stop_ratio - epsilon > settings.stop_loss_max_pct:
                errors.append("STOP_LOSS_RANGE_INVALID")
    return errors


def _check_cooldown(last_exit_at: datetime | None, now: datetime, cooldown_hours: int) -> str | None:
    if last_exit_at is None:
        return None
    if now - last_exit_at < timedelta(hours=cooldown_hours):
        return "COOLDOWN_24H_ACTIVE"
    return None


def _check_holding(position_opened_at: datetime | None, now: datetime, holding_days: int) -> str | None:
    if position_opened_at is None:
        return None
    if now - position_opened_at > timedelta(days=holding_days):
        return "HOLDING_PERIOD_EXCEEDED"
    return None


def _check_max_drawdown(payload: dict[str, Any], max_drawdown_pct: float) -> str | None:
    equity = float(payload.get("equity", 0.0))
    equity_peak = max(equity, float(payload.get("equity_peak", equity)))
    if equity_peak <= 0:
        return None
    drawdown = (equity_peak - equity) / equity_peak
    if drawdown > max_drawdown_pct:
        return "MAX_DRAWDOWN_LIMIT"
    return None


def _validate_settings_bounds(settings: HighLaneSettings) -> str | None:
    if settings.single_trade_risk_pct <= 0 or settings.total_exposure_limit_pct <= 0:
        return "RISK_SETTINGS_INVALID"
    if settings.total_exposure_limit_pct > 1:
        return "RISK_SETTINGS_INVALID"
    if settings.stop_loss_min_pct <= 0 or settings.stop_loss_max_pct <= 0:
        return "STOP_LOSS_SETTINGS_INVALID"
    if settings.stop_loss_min_pct >= settings.stop_loss_max_pct:
        return "STOP_LOSS_SETTINGS_INVALID"
    if settings.risk_multiplier_min <= 0 or settings.risk_multiplier_max <= 0:
        return "RISK_SETTINGS_INVALID"
    if settings.risk_multiplier_min > settings.risk_multiplier_max:
        return "RISK_SETTINGS_INVALID"
    if settings.take_profit_boost_max_pct < 0:
        return "STOP_LOSS_SETTINGS_INVALID"
    if settings.max_drawdown_pct <= 0 or settings.max_drawdown_pct >= 1:
        return "RISK_SETTINGS_INVALID"
    if settings.min_trade_units <= 0:
        return "RISK_SETTINGS_INVALID"
    if settings.slippage_bps < 0 or settings.commission_per_share < 0:
        return "RISK_SETTINGS_INVALID"
    if settings.cooldown_hours < 0 or settings.holding_days < 0:
        return "TEMPORAL_SETTINGS_INVALID"
    return None


def _build_bracket_order(
    payload: dict[str, Any],
    quantity: int,
    now: datetime,
    take_profit_boost_pct: float,
    holding_days: int,
) -> dict[str, Any]:
    side = payload["side"]
    if side == "buy":
        parent_action = "BUY"
        exit_action = "SELL"
    else:
        parent_action = "SELL"
        exit_action = "BUY"
    take_profit_price = payload["take_profit_price"]
    if take_profit_boost_pct > 0:
        if side == "buy":
            take_profit_price = take_profit_price * (1 + take_profit_boost_pct)
        else:
            take_profit_price = take_profit_price * (1 - take_profit_boost_pct)
    hold_until = now + timedelta(days=max(1, holding_days))
    order_id_prefix = f'{payload["symbol"]}-{now.strftime("%Y%m%d%H%M%S%f")}-{uuid4().hex[:8]}'
    return {
        "parent": {
            "client_order_id": f"{order_id_prefix}-P",
            "symbol": payload["symbol"],
            "action": parent_action,
            "order_type": "LIMIT",
            "quantity": quantity,
            "limit_price": payload["entry_price"],
            "time_in_force": "DAY",
        },
        "take_profit": {
            "client_order_id": f"{order_id_prefix}-TP",
            "symbol": payload["symbol"],
            "action": exit_action,
            "order_type": "LIMIT",
            "quantity": quantity,
            "limit_price": round(take_profit_price, 6),
            "time_in_force": "GTC",
        },
        "stop_loss": {
            "client_order_id": f"{order_id_prefix}-SL",
            "symbol": payload["symbol"],
            "action": exit_action,
            "order_type": "STOP",
            "quantity": quantity,
            "stop_price": payload["stop_loss_price"],
            "time_in_force": "GTC",
        },
        "max_hold_until": hold_until.isoformat(),
    }


def _rejected(symbol: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "lane": "high",
        "status": "rejected",
        "symbol": symbol,
        "reject_reasons": reasons,
    }


def _estimate_transaction_cost(
    *,
    entry_price: float,
    quantity: int,
    slippage_bps: float,
    commission_per_share: float,
) -> dict[str, float]:
    notional = entry_price * quantity
    slippage_cost = notional * (slippage_bps / 10000)
    commission_cost = quantity * commission_per_share
    total = slippage_cost + commission_cost
    return {
        "slippage_cost": round(slippage_cost, 6),
        "commission_cost": round(commission_cost, 6),
        "total": round(total, 6),
    }
