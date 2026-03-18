from __future__ import annotations

from datetime import datetime, timedelta, timezone
import time
from typing import Any, Callable

from .state_store import (
    ORDER_STATUS_ACK,
    ORDER_STATUS_CANCELED,
    ORDER_STATUS_FILLED,
    ORDER_STATUS_NEW,
    ORDER_STATUS_PARTIAL,
    ORDER_STATUS_REJECTED,
    ORDER_STATUS_SENT,
    append_order_lifecycle_event,
    derive_local_order_status,
    has_open_order_ref,
    get_open_order_state,
    record_execution_quality,
)


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    ORDER_STATUS_NEW: {ORDER_STATUS_SENT, ORDER_STATUS_ACK, ORDER_STATUS_PARTIAL, ORDER_STATUS_FILLED, ORDER_STATUS_REJECTED, ORDER_STATUS_CANCELED},
    ORDER_STATUS_SENT: {ORDER_STATUS_ACK, ORDER_STATUS_PARTIAL, ORDER_STATUS_FILLED, ORDER_STATUS_REJECTED, ORDER_STATUS_CANCELED, ORDER_STATUS_SENT},
    ORDER_STATUS_ACK: {ORDER_STATUS_PARTIAL, ORDER_STATUS_FILLED, ORDER_STATUS_REJECTED, ORDER_STATUS_CANCELED, ORDER_STATUS_ACK},
    ORDER_STATUS_PARTIAL: {ORDER_STATUS_PARTIAL, ORDER_STATUS_FILLED, ORDER_STATUS_CANCELED, ORDER_STATUS_REJECTED},
    ORDER_STATUS_FILLED: {ORDER_STATUS_FILLED},
    ORDER_STATUS_CANCELED: {ORDER_STATUS_CANCELED},
    ORDER_STATUS_REJECTED: {ORDER_STATUS_REJECTED},
}


def submit_with_retry(
    *,
    submit_fn: Callable[[dict[str, Any]], dict[str, Any]],
    signal: dict[str, Any],
    max_attempts: int = 3,
    base_backoff_seconds: float = 0.2,
) -> dict[str, Any]:
    attempts = max(1, int(max_attempts))
    last_exc: Exception | None = None
    for idx in range(attempts):
        try:
            result = submit_fn(signal)
            if isinstance(result, dict):
                result["retry_attempt"] = idx + 1
            return result
        except (TimeoutError, ConnectionError) as exc:
            last_exc = exc
            if idx >= attempts - 1:
                break
            wait = max(0.0, base_backoff_seconds) * (2**idx)
            time.sleep(wait)
        except Exception:
            raise
    if last_exc is None:
        raise RuntimeError("submit_with_retry exhausted without exception context")
    raise last_exc


def process_execution_report(
    *,
    db_path: str,
    signal: dict[str, Any],
    execution_result: dict[str, Any],
) -> dict[str, Any]:
    orders = list(execution_result.get("orders", []) or [])
    transitions: list[dict[str, Any]] = []
    state_by_ref: dict[str, str] = {}
    for item in orders:
        order_ref = str(item.get("order_ref", "")).strip()
        if not order_ref:
            continue
        prev_state = get_open_order_state(db_path, order_ref=order_ref)
        broker_status = str(item.get("status", "UNKNOWN")).upper()
        filled = float(item.get("filled_quantity", 0.0) or 0.0)
        remaining = float(item.get("remaining_quantity", 0.0) or 0.0)
        next_state = derive_local_order_status(broker_status=broker_status, filled=filled, remaining=remaining)
        if next_state not in _ALLOWED_TRANSITIONS.get(prev_state, {next_state}):
            next_state = _coerce_transition(prev_state=prev_state, next_state=next_state)
        append_order_lifecycle_event(
            db_path,
            order_ref=order_ref,
            prev_state=prev_state,
            next_state=next_state,
            broker_status=broker_status,
            filled_quantity=filled,
            remaining_quantity=remaining,
        )
        transitions.append(
            {
                "order_ref": order_ref,
                "prev_state": prev_state,
                "next_state": next_state,
                "broker_status": broker_status,
                "filled_quantity": filled,
                "remaining_quantity": remaining,
            }
        )
        state_by_ref[order_ref] = next_state
    quality = _record_quality(db_path=db_path, signal=signal, execution_result=execution_result)
    atomicity = _check_bracket_atomicity(
        db_path=db_path,
        signal=signal,
        transitions=transitions,
        state_by_ref=state_by_ref,
    )
    rejected = any(item["next_state"] == ORDER_STATUS_REJECTED for item in transitions)
    return {
        "transitions": transitions,
        "rejected": rejected,
        "quality": quality,
        "atomicity": atomicity,
    }


def _coerce_transition(*, prev_state: str, next_state: str) -> str:
    if prev_state == ORDER_STATUS_SENT and next_state in {ORDER_STATUS_PARTIAL, ORDER_STATUS_FILLED}:
        return next_state
    if prev_state == ORDER_STATUS_NEW and next_state in {ORDER_STATUS_PARTIAL, ORDER_STATUS_FILLED}:
        return next_state
    if prev_state in {ORDER_STATUS_FILLED, ORDER_STATUS_CANCELED, ORDER_STATUS_REJECTED}:
        return prev_state
    return next_state


def _record_quality(
    *,
    db_path: str,
    signal: dict[str, Any],
    execution_result: dict[str, Any],
) -> dict[str, float]:
    orders = list(signal.get("orders", []) or [])
    parent = dict(orders[0] if orders and isinstance(orders[0], dict) else {})
    expected_price = float(parent.get("lmtPrice", 0.0) or 0.0)
    expected_qty = float(parent.get("totalQuantity", 0.0) or 0.0)
    side = str(parent.get("action", signal.get("side", "BUY"))).upper()
    symbol = str(signal.get("symbol") or signal.get("contract", {}).get("symbol", "")).upper()
    intent_ref = str(parent.get("orderRef", ""))
    total_filled = 0.0
    weighted_price = 0.0
    for item in list(execution_result.get("orders", []) or []):
        filled = float(item.get("filled_quantity", 0.0) or 0.0)
        avg_fill = float(item.get("avg_fill_price", 0.0) or 0.0)
        if filled <= 0:
            continue
        total_filled += filled
        weighted_price += filled * avg_fill
    avg_fill_price = weighted_price / total_filled if total_filled > 0 else 0.0
    slippage_bps = 0.0
    if expected_price > 0 and avg_fill_price > 0:
        direction = 1.0 if side == "BUY" else -1.0
        slippage_bps = ((avg_fill_price - expected_price) / expected_price) * 10000 * direction
    filled_qty_for_record = total_filled if total_filled > 0 else expected_qty
    record_execution_quality(
        db_path,
        intent_ref=intent_ref,
        symbol=symbol,
        side=side,
        expected_price=expected_price,
        avg_fill_price=avg_fill_price,
        slippage_bps=slippage_bps,
        filled_quantity=filled_qty_for_record,
    )
    return {
        "expected_price": expected_price,
        "avg_fill_price": avg_fill_price,
        "slippage_bps": slippage_bps,
        "filled_quantity": filled_qty_for_record,
    }


def _check_bracket_atomicity(
    *,
    db_path: str,
    signal: dict[str, Any],
    transitions: list[dict[str, Any]],
    state_by_ref: dict[str, str],
) -> dict[str, Any]:
    orders = list(signal.get("orders", []) or [])
    parent_ref = str(dict(orders[0] if orders and isinstance(orders[0], dict) else {}).get("orderRef", ""))
    tp_ref = str(dict(orders[1] if len(orders) > 1 and isinstance(orders[1], dict) else {}).get("orderRef", ""))
    sl_ref = str(dict(orders[2] if len(orders) > 2 and isinstance(orders[2], dict) else {}).get("orderRef", ""))
    parent_transition = next((item for item in transitions if item["order_ref"] == parent_ref), None)
    parent_filled = False
    if parent_transition is not None:
        parent_filled = parent_transition["next_state"] in {ORDER_STATUS_PARTIAL, ORDER_STATUS_FILLED} and parent_transition["filled_quantity"] > 0
    protections = [tp_ref, sl_ref]
    missing: list[str] = []
    for ref in protections:
        if not ref:
            continue
        if ref in state_by_ref:
            continue
        if not has_open_order_ref(db_path, order_ref=ref):
            missing.append(ref)
    bad = [
        ref
        for ref in protections
        if (
            (ref in state_by_ref and state_by_ref[ref] in {ORDER_STATUS_REJECTED, ORDER_STATUS_CANCELED})
            or (
                ref not in state_by_ref
                and has_open_order_ref(db_path, order_ref=ref)
                and get_open_order_state(db_path, order_ref=ref) in {ORDER_STATUS_REJECTED, ORDER_STATUS_CANCELED}
            )
        )
    ]
    needs_emergency = bool(parent_filled and (missing or bad))
    return {
        "ok": not needs_emergency,
        "needs_emergency": needs_emergency,
        "missing_protection_refs": missing,
        "invalid_protection_refs": bad,
    }


def build_reject_recovery_runtime(*, cooldown_minutes: int = 10) -> dict[str, str]:
    until = datetime.now(tz=timezone.utc) + timedelta(minutes=max(1, cooldown_minutes))
    return {"cooldown_until": until.isoformat()}
