from __future__ import annotations

from datetime import datetime, timedelta, timezone


def emit_event(
    symbol: str,
    overrides: dict[str, str] | None = None,
    market_row: dict[str, float | str] | None = None,
) -> dict[str, str]:
    last_exit_at = (datetime.now(tz=timezone.utc) - timedelta(days=2)).isoformat()
    row = market_row or {}
    reference_price = max(1.0, float(row.get("reference_price", 100.0)))
    stop_ratio = max(0.01, min(0.2, float(row.get("stop_ratio", 0.05))))
    take_profit_ratio = max(0.02, min(0.3, float(row.get("take_profit_ratio", 0.08))))
    event = {
        "lane": "ultra",
        "symbol": symbol.upper(),
        "kind": "signal",
        "side": "buy",
        "entry_price": f"{reference_price:.4f}",
        "stop_loss_price": f"{(reference_price * (1 - stop_ratio)):.4f}",
        "take_profit_price": f"{(reference_price * (1 + take_profit_ratio)):.4f}",
        "equity": "100000",
        "current_exposure": "10000",
        "current_exposure_unit": "notional",
        "last_exit_at": last_exit_at,
    }
    if overrides:
        event.update(overrides)
    return event
