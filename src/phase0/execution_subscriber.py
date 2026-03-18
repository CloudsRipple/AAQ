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
from .lanes.high import HighLaneSettings, evaluate_event
from .models.signals import ExecutionIntentEvent, HighDecisionEvent
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
    lane_settings = HighLaneSettings.from_app_config(config)

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
            lane_settings=lane_settings,
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
    lane_settings: HighLaneSettings,
) -> None:
    while True:
        event = await queue.get()
        try:
            await _handle_execution_intent_event(
                event=event,
                config=config,
                lane_settings=lane_settings,
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
        decision = HighDecisionEvent.model_validate(getattr(event, "payload", event))
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
    decision: HighDecisionEvent,
    config: AppConfig,
    market_snapshot: dict[str, dict[str, float | str]],
) -> ExecutionIntentEvent | None:
    symbol = decision.symbol.upper()
    ultra = decision.ultra_signal
    raw_data = dict(ultra.raw_data or {})
    side = str(raw_data.get("side", "buy")).strip().lower()
    if side not in {"buy", "sell"}:
        logger.error("ExecutionSubscriber: missing/invalid side for %s, fail-closed", symbol)
        return None

    row = dict(market_snapshot.get(symbol, {}) or {})
    entry_price = float(raw_data.get("price_current", row.get("reference_price", 0.0)) or 0.0)
    if entry_price <= 0:
        logger.error("ExecutionSubscriber: missing entry_price for %s, fail-closed", symbol)
        return None

    stop_pct = float(decision.stop_loss_pct)
    if stop_pct <= 0:
        logger.error("ExecutionSubscriber: invalid stop_loss_pct for %s, fail-closed", symbol)
        return None

    if side == "buy":
        stop_loss = entry_price * (1.0 - stop_pct)
        take_profit = entry_price * (1.0 + stop_pct * 2.0)
    else:
        stop_loss = entry_price * (1.0 + stop_pct)
        take_profit = entry_price * (1.0 - stop_pct * 2.0)
    if stop_loss <= 0 or take_profit <= 0:
        logger.error("ExecutionSubscriber: generated invalid bracket prices for %s, fail-closed", symbol)
        return None

    runtime = get_runtime_state(config.ai_state_db_path)
    equity = float(runtime.equity or 0.0)
    if equity <= 0:
        logger.error("ExecutionSubscriber: missing runtime equity for %s, fail-closed", symbol)
        return None

    positions = list_positions(config.ai_state_db_path)
    open_orders = list_open_orders(config.ai_state_db_path)
    current_symbol_exposure = _symbol_exposure_notional(
        symbol=symbol,
        positions=positions,
        open_orders=open_orders,
    )

    snapshot_id = str(raw_data.get("snapshot_id", "")).strip()
    snapshot_ts_raw = raw_data.get("snapshot_ts")
    if not snapshot_id or not snapshot_ts_raw:
        logger.error("ExecutionSubscriber: missing snapshot metadata for %s, fail-closed", symbol)
        return None

    last_exit_at_raw = raw_data.get("last_exit_at")
    last_exit_at: datetime | None = None
    if isinstance(last_exit_at_raw, str) and last_exit_at_raw.strip():
        try:
            last_exit_at = datetime.fromisoformat(last_exit_at_raw.replace("Z", "+00:00"))
        except ValueError:
            last_exit_at = None
    last_exit_reason = str(raw_data.get("last_exit_reason", "NOT_AVAILABLE_IN_STATE_STORE"))

    try:
        return ExecutionIntentEvent(
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
            strategy_id=str(raw_data.get("strategy", f"ultra_{ultra.event_type}")),
            risk_multiplier=float(decision.risk_multiplier),
            stop_loss_pct=stop_pct,
            high_reason=decision.reason,
            ultra_signal=ultra,
            allow_opening=bool(raw_data.get("allow_opening", True)),
            data_degraded=bool(raw_data.get("data_degraded", False)),
            data_quality_errors=list(raw_data.get("data_quality_errors", []) or []),
        )
    except ValidationError as exc:
        logger.error("ExecutionSubscriber: invalid execution.intent payload, fail-closed: %s", str(exc))
        return None


async def _handle_execution_intent_event(
    *,
    event: Any,
    config: AppConfig,
    lane_settings: HighLaneSettings,
) -> None:
    try:
        intent = ExecutionIntentEvent.model_validate(getattr(event, "payload", event))
    except ValidationError as exc:
        logger.error("ExecutionSubscriber: invalid execution.intent payload, fail-closed: %s", str(exc))
        return

    high_event = {
        "lane": "ultra",
        "kind": "signal",
        "symbol": intent.symbol,
        "side": intent.side,
        "entry_price": str(intent.entry_price),
        "stop_loss_price": str(intent.stop_loss),
        "take_profit_price": str(intent.take_profit),
        "equity": str(intent.equity),
        "current_exposure": str(intent.current_symbol_exposure),
        "current_symbol_exposure": str(intent.current_symbol_exposure),
        "current_exposure_unit": "notional",
        "last_exit_at": intent.last_exit_at.isoformat() if intent.last_exit_at else "",
        "snapshot_id": intent.snapshot_id,
        "snapshot_ts": intent.snapshot_ts.isoformat(),
    }
    decision = evaluate_event(
        event=high_event,
        settings=lane_settings,
        strategy_adjustments={"risk_multiplier": intent.risk_multiplier, "take_profit_boost_pct": 0.0},
    )
    if decision.get("status") != "accepted":
        logger.warning(
            "ExecutionSubscriber: high lane rejected execution.intent for %s: %s",
            intent.symbol,
            decision.get("reject_reasons", []),
        )
        return

    ibkr_signal = map_decision_to_ibkr_bracket(decision)
    if ibkr_signal is None:
        logger.error("ExecutionSubscriber: failed to map execution.intent for %s", intent.symbol)
        return
    ibkr_signal["strategy_id"] = intent.strategy_id
    ibkr_signal["signal_ts"] = intent.snapshot_ts.isoformat()
    ibkr_signal["side"] = intent.side.upper()
    ibkr_signal["snapshot_id"] = intent.snapshot_id
    ibkr_signal["snapshot_ts"] = intent.snapshot_ts.isoformat()

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
