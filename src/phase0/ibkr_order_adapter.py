from __future__ import annotations

from typing import Any


def map_decision_to_ibkr_bracket(
    decision: dict[str, Any],
    *,
    exchange: str = "SMART",
    currency: str = "USD",
) -> dict[str, Any] | None:
    if decision.get("status") != "accepted":
        return None
    bracket = decision.get("bracket_order", {})
    parent = bracket.get("parent", {})
    take_profit = bracket.get("take_profit", {})
    stop_loss = bracket.get("stop_loss", {})
    symbol = str(parent.get("symbol", decision.get("symbol", ""))).upper()
    if not symbol:
        return None
    parent_ref = str(parent.get("client_order_id", "PARENT"))
    tp_ref = str(take_profit.get("client_order_id", "TAKE_PROFIT"))
    sl_ref = str(stop_loss.get("client_order_id", "STOP_LOSS"))
    qty = int(parent.get("quantity", decision.get("quantity", 0)) or 0)
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
        "strategy_id": str(decision.get("strategy_id", decision.get("strategy", "unknown"))),
        "signal_ts": str(decision.get("signal_ts", "")),
        "side": parent_action,
        "snapshot_id": str(decision.get("snapshot_id", "")),
        "snapshot_ts": str(decision.get("snapshot_ts", "")),
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
