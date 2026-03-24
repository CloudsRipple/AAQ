from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from pydantic import ValidationError

from .config import AppConfig
from .ibkr_execution import execute_intents_with_control_plane
from .ibkr_order_adapter import map_decision_to_ibkr_bracket
from .lanes.bus import AsyncEventBus, LaneEvent
from .models.signals import OrderIntent, TradeDecision
from .state_store import get_runtime_state, list_open_orders, list_positions

logger = logging.getLogger(__name__)


async def start_execution_subscriber(
    bus: AsyncEventBus,
    config: AppConfig,
    market_snapshot: dict[str, dict[str, float | str]],
) -> None:
    logger.info("Starting ExecutionSubscriber Daemon...")
    decision_queue = bus.subscribe("high.decision")
    intent_queue = bus.subscribe("execution.intent")

    decision_worker = asyncio.create_task(
        _consume_high_decisions(
            queue=decision_queue,
            bus=bus,
            config=config,
            market_snapshot=market_snapshot,
        )
    )
    intent_worker = asyncio.create_task(
        _consume_execution_intents(
            queue=intent_queue,
            config=config,
        )
    )

    try:
        await asyncio.gather(decision_worker, intent_worker)
    except asyncio.CancelledError:
        logger.info("ExecutionSubscriber: Shutting down")
        decision_worker.cancel()
        intent_worker.cancel()
        await asyncio.gather(decision_worker, intent_worker, return_exceptions=True)
        raise
    finally:
        bus.unsubscribe("high.decision", decision_queue)
        bus.unsubscribe("execution.intent", intent_queue)


async def _consume_high_decisions(
    *,
    queue: asyncio.Queue[Any],
    bus: AsyncEventBus,
    config: AppConfig,
    market_snapshot: dict[str, dict[str, float | str]],
) -> None:
    while True:
        event = await queue.get()
        try:
            await _handle_high_decision_event(
                event=event,
                bus=bus,
                config=config,
                market_snapshot=market_snapshot,
            )
        except Exception as exc:
            logger.error("ExecutionSubscriber: failed to process high.decision: %s", str(exc))
        finally:
            queue.task_done()


async def _consume_execution_intents(
    *,
    queue: asyncio.Queue[Any],
    config: AppConfig,
) -> None:
    while True:
        event = await queue.get()
        try:
            await _handle_execution_intent_event(
                event=event,
                config=config,
            )
        except Exception as exc:
            logger.error("ExecutionSubscriber: failed to process execution.intent: %s", str(exc))
        finally:
            queue.task_done()


async def _handle_high_decision_event(
    *,
    event: Any,
    bus: AsyncEventBus,
    config: AppConfig,
    market_snapshot: dict[str, dict[str, float | str]],
) -> None:
    try:
        decision = TradeDecision.model_validate(getattr(event, "payload", event))
    except ValidationError as exc:
        logger.error("ExecutionSubscriber: invalid high.decision payload, fail-closed: %s", str(exc))
        return

    symbol = decision.symbol.upper()
    if not decision.approved:
        logger.info("ExecutionSubscriber: High rejected %s, reason=%s", symbol, decision.reason)
        return

    intent = _build_execution_intent_from_decision(
        decision=decision,
        config=config,
        market_snapshot=market_snapshot,
    )
    if intent is None:
        return

    intent_event = LaneEvent.from_payload(
        event_type="intent",
        source_lane="execution",
        payload=intent.model_dump(mode="json"),
    )
    bus.publish("execution.intent", intent_event)


def _build_execution_intent_from_decision(
    *,
    decision: TradeDecision,
    config: AppConfig,
    market_snapshot: dict[str, dict[str, float | str]],
) -> OrderIntent | None:
    symbol = decision.symbol.upper()
    ultra = decision.ultra_signal
    raw_data = dict(ultra.raw_data or {})
    side = str(decision.side or raw_data.get("side", "")).strip().lower()
    if side not in {"buy", "sell"}:
        logger.error("ExecutionSubscriber: missing/invalid side for %s, fail-closed", symbol)
        return None

    quantity = int(decision.quantity or 0)
    bracket_order = dict(decision.bracket_order or {})
    estimated_transaction_cost = dict(decision.estimated_transaction_cost or {})
    if quantity <= 0 or not bracket_order or not estimated_transaction_cost:
        logger.error("ExecutionSubscriber: high decision for %s is not execution-ready, fail-closed", symbol)
        return None

    prices = _extract_bracket_prices(bracket_order)
    if prices is None:
        logger.error("ExecutionSubscriber: invalid bracket order for %s, fail-closed", symbol)
        return None
    entry_price, stop_loss, take_profit = prices

    runtime = get_runtime_state(config.ai_state_db_path)
    equity = float(runtime.equity or 0.0)
    if equity <= 0:
        logger.error("ExecutionSubscriber: missing runtime equity for %s, fail-closed", symbol)
        return None

    current_symbol_exposure = _symbol_exposure_notional(
        symbol=symbol,
        positions=list_positions(config.ai_state_db_path),
        open_orders=list_open_orders(config.ai_state_db_path),
    )
    snapshot_id = str(decision.snapshot_id or raw_data.get("snapshot_id", "")).strip()
    snapshot_ts_raw = decision.snapshot_ts or _parse_optional_datetime(raw_data.get("snapshot_ts"))
    if not snapshot_id or snapshot_ts_raw is None:
        logger.error("ExecutionSubscriber: missing snapshot metadata for %s, fail-closed", symbol)
        return None

    last_exit_at = _parse_optional_datetime(raw_data.get("last_exit_at"))
    last_exit_reason = str(raw_data.get("last_exit_reason", "NOT_AVAILABLE_IN_STATE_STORE"))
    strategy_id = str(decision.strategy_id or raw_data.get("strategy", f"ultra_{ultra.event_type}")).strip()
    if not strategy_id:
        logger.error("ExecutionSubscriber: missing strategy_id for %s, fail-closed", symbol)
        return None

    try:
        return OrderIntent(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            equity=equity,
            current_symbol_exposure=current_symbol_exposure,
            last_exit_at=last_exit_at,
            last_exit_reason=last_exit_reason,
            snapshot_id=snapshot_id,
            snapshot_ts=snapshot_ts_raw,
            strategy_id=strategy_id,
            risk_multiplier=float(decision.risk_multiplier),
            stop_loss_pct=float(decision.stop_loss_pct),
            high_reason=decision.reason,
            ultra_signal=ultra,
            quantity=quantity,
            bracket_order=bracket_order,
            estimated_transaction_cost=estimated_transaction_cost,
            allow_opening=bool(decision.allow_opening),
            data_degraded=bool(decision.data_degraded),
            data_quality_errors=list(decision.data_quality_errors or []),
        )
    except ValidationError as exc:
        logger.error("ExecutionSubscriber: invalid execution.intent payload, fail-closed: %s", str(exc))
        return None


async def _handle_execution_intent_event(
    *,
    event: Any,
    config: AppConfig,
) -> None:
    try:
        intent = OrderIntent.model_validate(getattr(event, "payload", event))
    except ValidationError as exc:
        logger.error("ExecutionSubscriber: invalid execution.intent payload, fail-closed: %s", str(exc))
        return

    ibkr_signal = map_decision_to_ibkr_bracket(
        {
            "status": "accepted",
            "symbol": intent.symbol,
            "quantity": intent.quantity,
            "bracket_order": intent.bracket_order,
            "strategy_id": intent.strategy_id,
            "signal_ts": intent.snapshot_ts.isoformat(),
            "side": intent.side.upper(),
            "snapshot_id": intent.snapshot_id,
            "snapshot_ts": intent.snapshot_ts.isoformat(),
        }
    )
    if ibkr_signal is None:
        logger.error("ExecutionSubscriber: failed to map execution.intent for %s", intent.symbol)
        return

    lane_output = {
        "source": "event_driven_runtime",
        "data_quality_gate": {
            "allow_opening": intent.allow_opening,
            "degraded": intent.data_degraded,
            "quality": {"errors": list(intent.data_quality_errors)},
            "snapshot_id": intent.snapshot_id,
            "snapshot_ts": intent.snapshot_ts.isoformat(),
        },
        "execution_intent": intent.model_dump(mode="json"),
    }
    report = await asyncio.to_thread(
        execute_intents_with_control_plane,
        symbol=intent.symbol,
        intents=[ibkr_signal],
        lane_output=lane_output,
        config=config,
        send=True,
    )
    executions = list(report.get("executions", []) or [])
    if not executions:
        logger.warning("ExecutionSubscriber: no execution results for %s", intent.symbol)
        return
    if all(item.get("ok", False) for item in executions):
        logger.info("ExecutionSubscriber: order submitted for %s", intent.symbol)
    else:
        logger.error("ExecutionSubscriber: order submission failed for %s: %s", intent.symbol, executions)


def _extract_bracket_prices(bracket_order: dict[str, Any]) -> tuple[float, float, float] | None:
    parent = dict(bracket_order.get("parent", {}) or {})
    take_profit = dict(bracket_order.get("take_profit", {}) or {})
    stop_loss = dict(bracket_order.get("stop_loss", {}) or {})
    try:
        entry_price = float(parent.get("limit_price", 0.0) or 0.0)
        take_profit_price = float(take_profit.get("limit_price", 0.0) or 0.0)
        stop_loss_price = float(stop_loss.get("stop_price", 0.0) or 0.0)
    except (TypeError, ValueError):
        return None
    if entry_price <= 0 or take_profit_price <= 0 or stop_loss_price <= 0:
        return None
    return entry_price, stop_loss_price, take_profit_price


def _parse_optional_datetime(raw_value: object) -> datetime | None:
    if isinstance(raw_value, datetime):
        return raw_value
    text = str(raw_value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _symbol_exposure_notional(
    *,
    symbol: str,
    positions: list[dict[str, Any]],
    open_orders: list[dict[str, Any]],
) -> float:
    symbol_key = symbol.upper()
    exposure = 0.0
    avg_price = 0.0
    for item in positions:
        if str(item.get("symbol", "")).upper() != symbol_key:
            continue
        qty = abs(float(item.get("quantity", 0.0) or 0.0))
        price = abs(float(item.get("avg_price", 0.0) or 0.0))
        if price > 0:
            avg_price = price
        exposure += qty * price
    for item in open_orders:
        if str(item.get("symbol", "")).upper() != symbol_key:
            continue
        qty = abs(float(item.get("quantity", 0.0) or 0.0))
        price = abs(float(item.get("reference_price", 0.0) or 0.0))
        if price <= 0:
            price = avg_price if avg_price > 0 else 1.0
        exposure += qty * price
    return max(0.0, exposure)
