from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import os
from typing import Any

from .config import AppConfig
from .state_store import (
    RuntimeState,
    append_risk_decision_audit,
    append_risk_decision_outcome,
    get_runtime_state,
    list_open_orders,
    list_positions,
    set_system_status,
    SYSTEM_STATUS_HALTED,
)


def evaluate_order_intents(
    *,
    intents: list[dict[str, Any]],
    config: AppConfig,
    lane_output: dict[str, Any],
) -> dict[str, Any]:
    db_path = config.ai_state_db_path
    runtime = get_runtime_state(db_path)
    positions = list_positions(db_path)
    open_orders = list_open_orders(db_path)
    equity = runtime.equity if runtime.equity > 0 else _read_float_env("CURRENT_EQUITY", 100000.0)
    day_loss_pct = _read_float_env("CURRENT_DAY_LOSS_PCT", 0.0)
    daily_loss_limit_pct = _read_float_env("RISK_DAILY_LOSS_LIMIT_PCT", max(0.01, config.risk_max_drawdown_pct * 0.65))
    concentration_limit_pct = _read_float_env(
        "RISK_CONCENTRATION_LIMIT_PCT",
        max(config.risk_single_trade_pct * 2, min(0.35, config.risk_total_exposure_pct)),
    )
    rejected: list[dict[str, Any]] = []
    approved: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    fail_closed = False
    for intent in intents:
        try:
            decision = _evaluate_single_intent(
                intent=intent,
                lane_output=lane_output,
                config=config,
                runtime=runtime,
                positions=positions,
                open_orders=open_orders,
                equity=equity,
                day_loss_pct=day_loss_pct,
                daily_loss_limit_pct=daily_loss_limit_pct,
                concentration_limit_pct=concentration_limit_pct,
            )
        except Exception:
            fail_closed = True
            decision = _fail_closed_decision(intent=intent, positions=positions)
        details.append(decision)
        if decision["approved"]:
            approved.append(intent)
            append_risk_decision_outcome(
                db_path,
                decision_id=decision["decision_id"],
                intent_ref=decision["intent_ref"],
                symbol=decision["symbol"],
                side=decision["side"],
                outcome="APPROVED",
                rule_id=decision["rule_id"],
            )
        else:
            rejected.append(
                {
                    "intent": intent,
                    "reason": decision["reason"],
                    "rule_id": decision["rule_id"],
                    "trigger_value": decision["trigger_value"],
                    "threshold_value": decision["threshold_value"],
                }
            )
            append_risk_decision_audit(
                db_path,
                decision_id=decision["decision_id"],
                intent_ref=decision["intent_ref"],
                symbol=decision["symbol"],
                side=decision["side"],
                outcome="REJECT",
                rule_id=decision["rule_id"],
                trigger_value=float(decision["trigger_value"]),
                threshold_value=float(decision["threshold_value"]),
            )
            append_risk_decision_outcome(
                db_path,
                decision_id=decision["decision_id"],
                intent_ref=decision["intent_ref"],
                symbol=decision["symbol"],
                side=decision["side"],
                outcome="REJECTED",
                rule_id=decision["rule_id"],
            )
    hard_stop = runtime.drawdown >= config.risk_max_drawdown_pct or day_loss_pct >= daily_loss_limit_pct
    if hard_stop:
        set_system_status(db_path, SYSTEM_STATUS_HALTED, "RISK_POST_TRADE_LIMIT_TRIGGERED")
    return {
        "approved_intents": approved,
        "rejected_intents": rejected,
        "decisions": details,
        "fail_closed": fail_closed,
        "hard_stop": hard_stop,
        "risk_unavailable_mode": fail_closed,
    }


def _evaluate_single_intent(
    *,
    intent: dict[str, Any],
    lane_output: dict[str, Any],
    config: AppConfig,
    runtime: RuntimeState,
    positions: list[dict[str, Any]],
    open_orders: list[dict[str, Any]],
    equity: float,
    day_loss_pct: float,
    daily_loss_limit_pct: float,
    concentration_limit_pct: float,
) -> dict[str, Any]:
    context = _intent_context(intent)
    symbol = context["symbol"]
    side = context["side"]
    quantity = context["quantity"]
    entry_price = context["entry_price"]
    stop_price = context["stop_price"]
    intent_ref = context["intent_ref"]
    is_opening = _is_opening_order(symbol=symbol, side=side, quantity=quantity, positions=positions)
    cooldown_active = _is_cooldown_active(runtime.cooldown_until)
    data_gate = dict(lane_output.get("data_quality_gate", {}) or {})
    allow_opening = bool(data_gate.get("allow_opening", True))
    if is_opening and not allow_opening:
        return _reject(
            intent_ref=intent_ref,
            symbol=symbol,
            side=side,
            rule_id="PRE_MARKET_OPENING_BLOCKED",
            trigger_value=0.0,
            threshold_value=1.0,
            reason="opening blocked by market session gate",
        )
    if is_opening and cooldown_active:
        return _reject(
            intent_ref=intent_ref,
            symbol=symbol,
            side=side,
            rule_id="PRE_COOLDOWN_ACTIVE",
            trigger_value=1.0,
            threshold_value=0.0,
            reason="cooldown active",
        )
    single_trade_risk = max(0.0, abs(entry_price - stop_price) * quantity)
    single_trade_limit = max(1e-6, equity * config.risk_single_trade_pct)
    if is_opening and single_trade_risk > single_trade_limit:
        return _reject(
            intent_ref=intent_ref,
            symbol=symbol,
            side=side,
            rule_id="PRE_SINGLE_TRADE_RISK",
            trigger_value=single_trade_risk,
            threshold_value=single_trade_limit,
            reason="single trade risk exceeded",
        )
    current_exposure = _current_exposure_notional(positions=positions, open_orders=open_orders)
    projected_exposure = current_exposure + (quantity * entry_price if is_opening else 0.0)
    exposure_limit = max(1e-6, equity * config.risk_total_exposure_pct)
    if projected_exposure > exposure_limit:
        return _reject(
            intent_ref=intent_ref,
            symbol=symbol,
            side=side,
            rule_id="PRE_POSITION_LIMIT",
            trigger_value=projected_exposure,
            threshold_value=exposure_limit,
            reason="projected exposure exceeded",
        )
    projected_symbol_exposure = _symbol_exposure_notional(symbol=symbol, positions=positions, open_orders=open_orders)
    if is_opening:
        projected_symbol_exposure += quantity * entry_price
    concentration_limit = max(1e-6, equity * concentration_limit_pct)
    if projected_symbol_exposure > concentration_limit:
        return _reject(
            intent_ref=intent_ref,
            symbol=symbol,
            side=side,
            rule_id="PRE_CONCENTRATION_LIMIT",
            trigger_value=projected_symbol_exposure,
            threshold_value=concentration_limit,
            reason="symbol concentration exceeded",
        )
    gate_quality = dict(data_gate.get("quality", {}) or {})
    errors = set(gate_quality.get("errors", []) or [])
    if data_gate.get("degraded", False) or "ABNORMAL_PRICE_JUMP" in errors:
        return _reject(
            intent_ref=intent_ref,
            symbol=symbol,
            side=side,
            rule_id="INTRA_VOLATILITY_CIRCUIT_BREAKER",
            trigger_value=1.0,
            threshold_value=0.0,
            reason="market data degraded or abnormal jump",
        )
    realtime_exposure_limit = max(1e-6, exposure_limit * 0.95)
    if projected_exposure > realtime_exposure_limit:
        return _reject(
            intent_ref=intent_ref,
            symbol=symbol,
            side=side,
            rule_id="INTRA_REALTIME_EXPOSURE",
            trigger_value=projected_exposure,
            threshold_value=realtime_exposure_limit,
            reason="realtime exposure breaker triggered",
        )
    if runtime.drawdown >= config.risk_max_drawdown_pct:
        return _reject(
            intent_ref=intent_ref,
            symbol=symbol,
            side=side,
            rule_id="POST_DRAWDOWN_HALT",
            trigger_value=runtime.drawdown,
            threshold_value=config.risk_max_drawdown_pct,
            reason="drawdown limit exceeded",
        )
    if day_loss_pct >= daily_loss_limit_pct:
        return _reject(
            intent_ref=intent_ref,
            symbol=symbol,
            side=side,
            rule_id="POST_DAILY_LOSS_LIMIT",
            trigger_value=day_loss_pct,
            threshold_value=daily_loss_limit_pct,
            reason="daily loss limit exceeded",
        )
    return {
        "decision_id": _decision_id(intent_ref, "APPROVE"),
        "intent_ref": intent_ref,
        "symbol": symbol,
        "side": side,
        "approved": True,
        "rule_id": "PASS_ALL",
        "trigger_value": 0.0,
        "threshold_value": 0.0,
        "reason": "approved",
    }


def _fail_closed_decision(*, intent: dict[str, Any], positions: list[dict[str, Any]]) -> dict[str, Any]:
    context = _intent_context(intent)
    symbol = context["symbol"]
    side = context["side"]
    quantity = context["quantity"]
    intent_ref = context["intent_ref"]
    is_opening = _is_opening_order(symbol=symbol, side=side, quantity=quantity, positions=positions)
    if is_opening:
        return _reject(
            intent_ref=intent_ref,
            symbol=symbol,
            side=side,
            rule_id="RISK_UNAVAILABLE_REDUCE_ONLY",
            trigger_value=1.0,
            threshold_value=0.0,
            reason="risk engine unavailable, opening blocked",
        )
    return {
        "decision_id": _decision_id(intent_ref, "APPROVE_REDUCE_ONLY"),
        "intent_ref": intent_ref,
        "symbol": symbol,
        "side": side,
        "approved": True,
        "rule_id": "RISK_UNAVAILABLE_REDUCE_ONLY",
        "trigger_value": 0.0,
        "threshold_value": 0.0,
        "reason": "reduce only fallback approved",
    }


def _intent_context(intent: dict[str, Any]) -> dict[str, Any]:
    contract = dict(intent.get("contract", {}) or {})
    orders = list(intent.get("orders", []) or [])
    parent = dict(orders[0] if orders and isinstance(orders[0], dict) else {})
    stop = dict(orders[2] if len(orders) > 2 and isinstance(orders[2], dict) else {})
    symbol = str(intent.get("symbol") or contract.get("symbol") or "").upper()
    side = str(intent.get("side") or parent.get("action") or "BUY").upper()
    quantity = float(parent.get("totalQuantity", 0.0) or 0.0)
    entry_price = float(parent.get("lmtPrice", 0.0) or 0.0)
    stop_price = float(stop.get("auxPrice", entry_price) or entry_price)
    intent_ref = str(parent.get("orderRef", "")) or f"{symbol}-{side}-{quantity}"
    return {
        "symbol": symbol,
        "side": side,
        "quantity": max(0.0, quantity),
        "entry_price": max(0.0, entry_price),
        "stop_price": max(0.0, stop_price),
        "intent_ref": intent_ref,
    }


def _is_opening_order(*, symbol: str, side: str, quantity: float, positions: list[dict[str, Any]]) -> bool:
    qty = 0.0
    for item in positions:
        if str(item.get("symbol", "")).upper() == symbol:
            qty = float(item.get("quantity", 0.0) or 0.0)
            break
    if qty == 0:
        return True
    if side == "BUY":
        return qty >= 0 or quantity > abs(qty)
    return qty <= 0 or quantity > abs(qty)


def _current_exposure_notional(*, positions: list[dict[str, Any]], open_orders: list[dict[str, Any]]) -> float:
    exposure = 0.0
    avg_price_by_symbol: dict[str, float] = {}
    for item in positions:
        qty = abs(float(item.get("quantity", 0.0) or 0.0))
        avg = abs(float(item.get("avg_price", 0.0) or 0.0))
        symbol = str(item.get("symbol", "")).upper()
        if symbol and avg > 0:
            avg_price_by_symbol[symbol] = avg
        exposure += qty * avg
    for item in open_orders:
        qty = abs(float(item.get("quantity", 0.0) or 0.0))
        symbol = str(item.get("symbol", "")).upper()
        price = abs(float(item.get("reference_price", 0.0) or 0.0))
        if price <= 0:
            price = avg_price_by_symbol.get(symbol, 1.0)
        exposure += qty * price
    return max(0.0, exposure)


def _symbol_exposure_notional(*, symbol: str, positions: list[dict[str, Any]], open_orders: list[dict[str, Any]]) -> float:
    exposure = 0.0
    symbol_avg = 0.0
    for item in positions:
        if str(item.get("symbol", "")).upper() != symbol:
            continue
        qty = abs(float(item.get("quantity", 0.0) or 0.0))
        avg = abs(float(item.get("avg_price", 0.0) or 0.0))
        if avg > 0:
            symbol_avg = avg
        exposure += qty * avg
    for item in open_orders:
        if str(item.get("symbol", "")).upper() != symbol:
            continue
        qty = abs(float(item.get("quantity", 0.0) or 0.0))
        price = abs(float(item.get("reference_price", 0.0) or 0.0))
        if price <= 0:
            price = symbol_avg if symbol_avg > 0 else 1.0
        exposure += qty * price
    return max(0.0, exposure)


def _is_cooldown_active(cooldown_until: str) -> bool:
    text = cooldown_until.strip()
    if not text:
        return False
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return datetime.now(tz=timezone.utc) < parsed.astimezone(timezone.utc)


def _reject(
    *,
    intent_ref: str,
    symbol: str,
    side: str,
    rule_id: str,
    trigger_value: float,
    threshold_value: float,
    reason: str,
) -> dict[str, Any]:
    return {
        "decision_id": _decision_id(intent_ref, rule_id),
        "intent_ref": intent_ref,
        "symbol": symbol,
        "side": side,
        "approved": False,
        "rule_id": rule_id,
        "trigger_value": float(trigger_value),
        "threshold_value": float(threshold_value),
        "reason": reason,
    }


def _decision_id(intent_ref: str, salt: str) -> str:
    now = datetime.now(tz=timezone.utc).isoformat()
    digest = sha256(f"{intent_ref}|{salt}|{now}".encode("utf-8")).hexdigest()
    return digest[:20]


def _read_float_env(name: str, default_value: float) -> float:
    raw = os.getenv(name, str(default_value))
    try:
        return float(raw)
    except ValueError:
        return default_value
