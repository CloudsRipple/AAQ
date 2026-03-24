from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def map_decision_to_ibkr_bracket(
    decision: dict[str, Any] | Mapping[str, Any] | Any,
    *,
    exchange: str = "SMART",
    currency: str = "USD",
) -> dict[str, Any] | None:
    payload = _coerce_payload_dict(decision)
    status = str(payload.get("status", "")).strip().lower()
    if not status and "approved" in payload:
        status = "accepted" if bool(payload.get("approved")) else "rejected"
    if status != "accepted":
        return None
    if isinstance(payload.get("orders"), list) and payload.get("contract"):
        return _normalize_prebuilt_signal(payload, exchange=exchange, currency=currency)
    bracket = payload.get("bracket_order", {})
    parent = bracket.get("parent", {})
    take_profit = bracket.get("take_profit", {})
    stop_loss = bracket.get("stop_loss", {})
    symbol = str(parent.get("symbol", payload.get("symbol", ""))).upper()
    if not symbol:
        return None
    parent_ref = str(parent.get("client_order_id", "PARENT"))
    tp_ref = str(take_profit.get("client_order_id", "TAKE_PROFIT"))
    sl_ref = str(stop_loss.get("client_order_id", "STOP_LOSS"))
    qty = int(parent.get("quantity", payload.get("quantity", 0)) or 0)
    if qty <= 0:
        return None
    parent_limit_price = float(parent.get("limit_price", 0.0))
    tp_limit_price = float(take_profit.get("limit_price", 0.0))
    sl_stop_price = float(stop_loss.get("stop_price", 0.0))
    if parent_limit_price <= 0 or tp_limit_price <= 0 or sl_stop_price <= 0:
        return None
    parent_action = str(parent.get("action", "BUY")).upper()
    exit_action = "SELL" if parent_action == "BUY" else "BUY"
    return {
        "contract": {
            "symbol": symbol,
            "secType": "STK",
            "exchange": exchange,
            "currency": currency,
        },
        "strategy_id": str(payload.get("strategy_id", payload.get("strategy", "unknown"))),
        "signal_ts": str(payload.get("signal_ts", "")),
        "side": parent_action,
        "snapshot_id": str(payload.get("snapshot_id", "")),
        "snapshot_ts": str(payload.get("snapshot_ts", "")),
        "orders": [
            {
                "orderRef": parent_ref,
                "action": parent_action,
                "orderType": "LMT",
                "totalQuantity": qty,
                "lmtPrice": parent_limit_price,
                "tif": str(parent.get("time_in_force", "DAY")),
                "transmit": False,
            },
            {
                "orderRef": tp_ref,
                "parentRef": parent_ref,
                "action": exit_action,
                "orderType": "LMT",
                "totalQuantity": qty,
                "lmtPrice": tp_limit_price,
                "tif": str(take_profit.get("time_in_force", "GTC")),
                "transmit": False,
            },
            {
                "orderRef": sl_ref,
                "parentRef": parent_ref,
                "action": exit_action,
                "orderType": "STP",
                "totalQuantity": qty,
                "auxPrice": sl_stop_price,
                "tif": str(stop_loss.get("time_in_force", "GTC")),
                "transmit": True,
            },
        ],
        "sequence": ["parent", "take_profit", "stop_loss"],
        "note": "parent/tp/sl should be sent sequentially with IBKR parentId/orderId mapping",
    }


def _coerce_payload_dict(payload: dict[str, Any] | Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, Mapping):
        return dict(payload)
    model_dump = getattr(payload, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
        if isinstance(dumped, dict):
            return dict(dumped)
    return dict(getattr(payload, "__dict__", {}) or {})


def _normalize_prebuilt_signal(
    payload: dict[str, Any],
    *,
    exchange: str,
    currency: str,
) -> dict[str, Any] | None:
    contract = dict(payload.get("contract", {}) or {})
    orders = list(payload.get("orders", []) or [])
    if len(orders) != 3:
        return None
    symbol = str(contract.get("symbol", payload.get("symbol", ""))).upper()
    if not symbol:
        return None
    parent, take_profit, stop_loss = (dict(orders[0]), dict(orders[1]), dict(orders[2]))
    if not parent.get("orderType") or not take_profit.get("orderType") or not stop_loss.get("orderType"):
        return None
    qty = int(parent.get("totalQuantity", 0) or 0)
    if qty <= 0:
        return None
    contract.setdefault("symbol", symbol)
    contract.setdefault("secType", "STK")
    contract.setdefault("exchange", exchange)
    contract.setdefault("currency", currency)
    return {
        "contract": contract,
        "strategy_id": str(payload.get("strategy_id", payload.get("strategy", "unknown"))),
        "signal_ts": str(payload.get("signal_ts", "")),
        "side": str(payload.get("side", parent.get("action", "BUY"))).upper(),
        "snapshot_id": str(payload.get("snapshot_id", "")),
        "snapshot_ts": str(payload.get("snapshot_ts", "")),
        "orders": [parent, take_profit, stop_loss],
        "sequence": list(payload.get("sequence", ["parent", "take_profit", "stop_loss"])),
        "note": str(payload.get("note", "parent/tp/sl should be sent sequentially with IBKR parentId/orderId mapping")),
    }
