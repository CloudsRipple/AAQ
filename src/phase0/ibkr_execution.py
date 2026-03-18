from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from time import perf_counter
from typing import Any, Callable, Protocol

from .config import AppConfig, load_config
from .execution_lifecycle import (
    build_reject_recovery_runtime,
    process_execution_report,
    submit_with_retry,
)
from .lanes import run_lane_cycle
from .observability import build_metrics_snapshot, evaluate_alerts, log_event
from .risk_engine import evaluate_order_intents
from .state_store import (
    ORDER_STATUS_ACK,
    ORDER_STATUS_NEW,
    ORDER_STATUS_SENT,
    SYSTEM_STATUS_BOOTSTRAP,
    SYSTEM_STATUS_DEGRADED,
    SYSTEM_STATUS_HALTED,
    SYSTEM_STATUS_RECONCILE,
    SYSTEM_STATUS_RUNNING,
    apply_order_report,
    apply_reconcile_snapshot,
    ensure_trade_state_db,
    get_runtime_state,
    get_system_status,
    is_idempotency_key_seen,
    list_execution_quality,
    list_order_lifecycle_events,
    list_open_orders,
    list_positions,
    register_idempotency_key,
    save_execution_report,
    set_runtime_state,
    set_system_status,
    update_idempotency_status,
    list_risk_decision_audit,
)


class ExecutionClient(Protocol):
    def submit_bracket_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        ...

    def close(self) -> None:
        ...

    def reconcile_snapshot(self) -> dict[str, Any]:
        ...

    def activate_kill_switch(self) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class ExecutionConfig:
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 91
    timeout_seconds: float = 3.0
    exchange: str = "SMART"
    currency: str = "USD"
    account: str = ""
    session_guard_enabled: bool = False
    session_start_utc: str = "13:30"
    session_end_utc: str = "20:00"
    good_after_seconds: int = 5
    slippage_bps: float = 2.0
    commission_per_share: float = 0.005


class IbkrExecutionClient:
    def __init__(
        self,
        config: ExecutionConfig,
        *,
        ib_factory: Callable[[], Any] | None = None,
        stock_factory: Callable[[str, str, str], Any] | None = None,
    ) -> None:
        self._config = config
        if ib_factory is None or stock_factory is None:
            ib_cls, stock_cls = _import_ib_insync()
            self._ib = (ib_factory or ib_cls)()
            self._stock_factory = stock_factory or stock_cls
        else:
            self._ib = ib_factory()
            self._stock_factory = stock_factory
        self._ib.connect(
            config.host,
            config.port,
            clientId=config.client_id,
            timeout=config.timeout_seconds,
            readonly=False,
        )

    def submit_bracket_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        contract_payload = signal.get("contract", {})
        orders_payload = signal.get("orders", [])
        if len(orders_payload) != 3:
            return {"ok": False, "error": "INVALID_BRACKET_SIGNAL", "signal": signal}
        if not _is_valid_transmit_chain(orders_payload):
            return {"ok": False, "error": "INVALID_TRANSMIT_CHAIN", "signal": signal}
        if self._config.session_guard_enabled and not _is_within_session_window(
            self._config.session_start_utc,
            self._config.session_end_utc,
        ):
            return {"ok": False, "error": "SESSION_CLOSED", "signal": signal}
        symbol = str(contract_payload.get("symbol", "")).upper()
        exchange = str(contract_payload.get("exchange", self._config.exchange))
        currency = str(contract_payload.get("currency", self._config.currency))
        contract = self._stock_factory(symbol, exchange, currency)
        self._ib.qualifyContracts(contract)
        parent_info, take_profit_info, stop_loss_info = orders_payload
        quantity = float(parent_info.get("totalQuantity", 0.0))
        bracket = self._ib.bracketOrder(
            str(parent_info.get("action", "BUY")),
            quantity,
            float(parent_info.get("lmtPrice", 0.0)),
            float(take_profit_info.get("lmtPrice", 0.0)),
            float(stop_loss_info.get("auxPrice", 0.0)),
        )
        parent, take_profit, stop_loss = bracket
        good_after = _build_good_after_time(self._config.good_after_seconds)
        for order, payload in zip((parent, take_profit, stop_loss), orders_payload):
            order.tif = str(payload.get("tif", "DAY"))
            order.transmit = bool(payload.get("transmit", False))
            order.orderRef = str(payload.get("orderRef", ""))
            order.goodAfterTime = good_after
            if self._config.account:
                order.account = self._config.account
        trades = [
            self._ib.placeOrder(contract, parent),
            self._ib.placeOrder(contract, take_profit),
            self._ib.placeOrder(contract, stop_loss),
        ]
        return {
            "ok": True,
            "symbol": symbol,
            "executed_at": datetime.now(tz=timezone.utc).isoformat(),
            "orders": [_trade_to_dict(item) for item in trades],
            "estimated_transaction_cost": _estimate_signal_cost(
                signal,
                slippage_bps=self._config.slippage_bps,
                commission_per_share=self._config.commission_per_share,
            ),
        }

    def close(self) -> None:
        if self._ib.isConnected():
            self._ib.disconnect()

    def reconcile_snapshot(self) -> dict[str, Any]:
        open_orders: list[dict[str, Any]] = []
        positions: list[dict[str, Any]] = []
        trades: list[dict[str, Any]] = []
        open_trades = list(getattr(self._ib, "openTrades", lambda: [])() or [])
        for trade in open_trades:
            order = getattr(trade, "order", None)
            contract = getattr(trade, "contract", None)
            status = str(getattr(getattr(trade, "orderStatus", None), "status", "Submitted"))
            order_ref = str(getattr(order, "orderRef", ""))
            qty = float(getattr(order, "totalQuantity", 0.0) or 0.0)
            symbol = str(getattr(contract, "symbol", ""))
            side = str(getattr(order, "action", ""))
            open_orders.append(
                {
                    "order_ref": order_ref,
                    "symbol": symbol.upper(),
                    "side": side.upper(),
                    "quantity": qty,
                    "reference_price": float(
                        getattr(order, "lmtPrice", 0.0)
                        or getattr(order, "auxPrice", 0.0)
                        or 0.0
                    ),
                    "broker_order_id": str(getattr(order, "orderId", "")),
                    "broker_status": status.upper(),
                    "local_status": ORDER_STATUS_ACK if status else ORDER_STATUS_SENT,
                }
            )
        ib_positions = list(getattr(self._ib, "positions", lambda: [])() or [])
        for item in ib_positions:
            contract = getattr(item, "contract", None)
            symbol = str(getattr(contract, "symbol", ""))
            positions.append(
                {
                    "symbol": symbol.upper(),
                    "quantity": float(getattr(item, "position", 0.0) or 0.0),
                    "avg_price": float(getattr(item, "avgCost", 0.0) or 0.0),
                }
            )
        exec_entries = list(getattr(self._ib, "reqExecutions", lambda: [])() or [])
        for item in exec_entries:
            execution = getattr(item, "execution", item)
            trades.append(
                {
                    "exec_id": str(getattr(execution, "execId", "")),
                    "symbol": str(getattr(getattr(item, "contract", None), "symbol", "")).upper(),
                    "shares": float(getattr(execution, "shares", 0.0) or 0.0),
                    "price": float(getattr(execution, "price", 0.0) or 0.0),
                    "time": str(getattr(execution, "time", "")),
                }
            )
        equity = 0.0
        try:
            summary = self._ib.accountSummary()
            for tag in summary:
                if tag.tag == "NetLiquidation":
                    equity = float(tag.value)
                    break
        except Exception:
            pass
        return {
            "ok": True,
            "open_orders": open_orders,
            "positions": positions,
            "trades": trades,
            "equity": equity,
        }

    def activate_kill_switch(self) -> dict[str, Any]:
        cancelled = 0
        flattened = 0
        cancel_errors: list[str] = []
        flatten_errors: list[str] = []
        open_trades = list(getattr(self._ib, "openTrades", lambda: [])() or [])
        for trade in open_trades:
            order = getattr(trade, "order", None)
            try:
                cancel_order = getattr(self._ib, "cancelOrder", None)
                if callable(cancel_order) and order is not None:
                    cancel_order(order)
                cancelled += 1
            except Exception as exc:
                cancel_errors.append(str(exc))
        ib_positions = list(getattr(self._ib, "positions", lambda: [])() or [])
        for item in ib_positions:
            position = float(getattr(item, "position", 0.0) or 0.0)
            if position == 0:
                continue
            contract = getattr(item, "contract", None)
            action = "SELL" if position > 0 else "BUY"
            quantity = abs(position)
            try:
                order_cls = getattr(self._ib, "MarketOrder", None)
                if callable(order_cls):
                    close_order = order_cls(action, quantity)
                else:
                    close_order = type("_Order", (), {"action": action, "totalQuantity": quantity})()
                place_order = getattr(self._ib, "placeOrder", None)
                if callable(place_order) and contract is not None:
                    place_order(contract, close_order)
                flattened += 1
            except Exception as exc:
                flatten_errors.append(str(exc))
        return {
            "ok": not cancel_errors and not flatten_errors,
            "cancelled_orders": cancelled,
            "flattened_positions": flattened,
            "cancel_errors": cancel_errors,
            "flatten_errors": flatten_errors,
        }


def execute_cycle(
    *,
    symbol: str,
    config: AppConfig,
    send: bool,
    daily_state: dict[str, object] | None = None,
    client_factory: Callable[[ExecutionConfig], ExecutionClient] | None = None,
) -> dict[str, Any]:
    state_db_path = config.ai_state_db_path
    ensure_trade_state_db(state_db_path)
    runtime = get_runtime_state(state_db_path)
    if runtime.kill_switch_active and send:
        status = get_system_status(state_db_path)
        return {
            "kind": "phase0_ibkr_execution",
            "symbol": symbol.upper(),
            "send_enabled": send,
            "signals_count": 0,
            "lane": {},
            "executions": [],
            "system_state": status,
            "blocked_reason": "KILL_SWITCH_ACTIVE",
        }
    lane_output = run_lane_cycle(symbol=symbol, config=config, daily_state=daily_state)
    set_runtime_state(
        state_db_path,
        drawdown=_read_current_drawdown_pct(),
        day_trade_count=int((daily_state or {}).get("actions_today", runtime.day_trade_count)),
        cooldown_until=str((daily_state or {}).get("cooldown_until", runtime.cooldown_until)),
        kill_switch_active=runtime.kill_switch_active,
        equity=runtime.equity,
    )
    return execute_intents_with_control_plane(
        symbol=symbol,
        intents=list(lane_output.get("ibkr_order_signals", []) or []),
        lane_output=lane_output,
        config=config,
        send=send,
        client_factory=client_factory,
    )


def execute_intents_with_control_plane(
    *,
    symbol: str,
    intents: list[dict[str, Any]],
    lane_output: dict[str, Any],
    config: AppConfig,
    send: bool,
    client_factory: Callable[[ExecutionConfig], ExecutionClient] | None = None,
) -> dict[str, Any]:
    state_db_path = config.ai_state_db_path
    ensure_trade_state_db(state_db_path)
    runtime = get_runtime_state(state_db_path)
    if runtime.kill_switch_active and send:
        status = get_system_status(state_db_path)
        return {
            "kind": "phase0_ibkr_execution",
            "symbol": symbol.upper(),
            "send_enabled": send,
            "signals_count": 0,
            "lane": lane_output,
            "executions": [],
            "system_state": status,
            "blocked_reason": "KILL_SWITCH_ACTIVE",
        }
    risk_report = evaluate_order_intents(
        intents=list(intents),
        config=config,
        lane_output=lane_output,
    )
    signals = list(risk_report.get("approved_intents", []) or [])
    executions: list[dict[str, Any]] = []
    current_system_state = get_system_status(state_db_path)
    if current_system_state["status"] != SYSTEM_STATUS_HALTED:
        set_system_status(state_db_path, SYSTEM_STATUS_BOOTSTRAP, "EXECUTE_CYCLE_START")
    reconcile: dict[str, Any] = {"ok": not send, "skipped": not send}
    if get_system_status(state_db_path)["status"] == SYSTEM_STATUS_HALTED:
        return {
            "kind": "phase0_ibkr_execution",
            "symbol": symbol.upper(),
            "send_enabled": send,
            "signals_count": len(signals),
            "lane": lane_output,
            "executions": [],
            "risk_engine": risk_report,
            "system_state": get_system_status(state_db_path),
            "blocked_reason": "SYSTEM_HALTED_BY_RISK",
            "reconcile": reconcile,
        }
    if send and signals:
        execution_config = ExecutionConfig(
            host=config.ibkr_host,
            port=config.ibkr_port,
            session_guard_enabled=config.execution_session_guard_enabled,
            session_start_utc=config.execution_session_start_utc,
            session_end_utc=config.execution_session_end_utc,
            good_after_seconds=config.execution_good_after_seconds,
            slippage_bps=config.risk_slippage_bps,
            commission_per_share=config.risk_commission_per_share,
        )
        client = (client_factory or IbkrExecutionClient)(execution_config)
        try:
            set_system_status(state_db_path, SYSTEM_STATUS_RECONCILE, "RECONCILE_START")
            reconcile = _reconcile_before_running(client=client, db_path=state_db_path)
            if not reconcile.get("ok", False):
                set_system_status(state_db_path, SYSTEM_STATUS_HALTED, "RECONCILE_FAILED")
                return {
                    "kind": "phase0_ibkr_execution",
                    "symbol": symbol.upper(),
                    "send_enabled": send,
                    "signals_count": len(signals),
                    "lane": lane_output,
                    "executions": [],
                    "risk_engine": risk_report,
                    "system_state": get_system_status(state_db_path),
                    "reconcile": reconcile,
                }
            set_system_status(state_db_path, SYSTEM_STATUS_RUNNING, "RECONCILE_PASSED")
            executions = _execute_approved_intents(
                signals=signals,
                state_db_path=state_db_path,
                client=client,
            )
            if any(not item.get("ok", False) for item in executions):
                set_system_status(state_db_path, SYSTEM_STATUS_DEGRADED, "PARTIAL_EXECUTION_FAILURE")
        finally:
            client.close()
    else:
        executions = [
            {
                "ok": True,
                "dry_run": True,
                "signal": signal,
                "estimated_transaction_cost": _estimate_signal_cost(
                    signal,
                    slippage_bps=config.risk_slippage_bps,
                    commission_per_share=config.risk_commission_per_share,
                ),
            }
            for signal in signals
        ]
    cycle_report = {
        "kind": "phase0_ibkr_execution",
        "symbol": symbol.upper(),
        "send_enabled": send,
        "signals_count": len(signals),
        "lane": lane_output,
        "risk_engine": risk_report,
        "executions": executions,
        "system_state": get_system_status(state_db_path),
        "runtime_state": {
            "drawdown": get_runtime_state(state_db_path).drawdown,
            "day_trade_count": get_runtime_state(state_db_path).day_trade_count,
            "cooldown_until": get_runtime_state(state_db_path).cooldown_until,
            "kill_switch_active": get_runtime_state(state_db_path).kill_switch_active,
        },
        "reconcile": reconcile,
        "open_orders": list_open_orders(state_db_path),
        "positions": list_positions(state_db_path),
        "risk_audit_log": list_risk_decision_audit(state_db_path, limit=20),
        "order_lifecycle_events": list_order_lifecycle_events(state_db_path, limit=50),
        "execution_quality": list_execution_quality(state_db_path, limit=50),
    }
    metrics_snapshot = build_metrics_snapshot(config)
    alerts = evaluate_alerts(config=config, cycle_report=cycle_report, metrics_snapshot=metrics_snapshot)
    cycle_report["metrics"] = metrics_snapshot.get("metrics", {})
    cycle_report["alerts"] = alerts
    log_event(
        "execution_cycle_completed",
        symbol=symbol.upper(),
        send_enabled=send,
        signals_count=len(signals),
        executions_count=len(executions),
        system_state=cycle_report["system_state"],
        metrics=cycle_report["metrics"],
        alerts_count=len(alerts),
    )
    return cycle_report


def _execute_approved_intents(
    *,
    signals: list[dict[str, Any]],
    state_db_path: str,
    client: ExecutionClient,
) -> list[dict[str, Any]]:
    executions: list[dict[str, Any]] = []
    for signal in signals:
        idempotency = _build_idempotency_key(signal)
        if is_idempotency_key_seen(state_db_path, idempotency["idempotency_key"]):
            executions.append(
                {
                    "ok": True,
                    "deduplicated": True,
                    "idempotency_key": idempotency["idempotency_key"],
                    "signal": signal,
                }
            )
            continue
        inserted = register_idempotency_key(
            state_db_path,
            idempotency_key=idempotency["idempotency_key"],
            strategy_id=idempotency["strategy_id"],
            symbol=idempotency["symbol"],
            signal_ts=idempotency["signal_ts"],
            side=idempotency["side"],
            status=ORDER_STATUS_NEW,
        )
        if not inserted:
            executions.append(
                {
                    "ok": True,
                    "deduplicated": True,
                    "idempotency_key": idempotency["idempotency_key"],
                    "signal": signal,
                }
            )
            continue
        try:
            execution_result: dict[str, Any] | None = None
            update_idempotency_status(
                state_db_path,
                idempotency_key=idempotency["idempotency_key"],
                status=ORDER_STATUS_SENT,
            )
            started = perf_counter()
            execution_result = submit_with_retry(
                submit_fn=client.submit_bracket_signal,
                signal=signal,
                max_attempts=max(1, int(os.getenv("EXEC_MAX_RETRY_ATTEMPTS", "3"))),
                base_backoff_seconds=max(0.0, float(os.getenv("EXEC_RETRY_BASE_BACKOFF_SECONDS", "0.2"))),
            )
            execution_result["latency_ms"] = round((perf_counter() - started) * 1000.0, 3)
            execution_result["idempotency_key"] = idempotency["idempotency_key"]
            executions.append(execution_result)
            if execution_result.get("ok"):
                lifecycle = process_execution_report(
                    db_path=state_db_path,
                    signal=signal,
                    execution_result=execution_result,
                )
                apply_order_report(
                    state_db_path,
                    symbol=idempotency["symbol"],
                    side=idempotency["side"],
                    report_orders=list(execution_result.get("orders", []) or []),
                )
                execution_result["lifecycle"] = lifecycle
                final_status = ORDER_STATUS_ACK
                if lifecycle.get("rejected", False):
                    final_status = "REJECTED"
                    _apply_reject_recovery(state_db_path=state_db_path, runtime=get_runtime_state(state_db_path))
                if lifecycle.get("atomicity", {}).get("needs_emergency", False):
                    emergency = client.activate_kill_switch()
                    execution_result["emergency"] = emergency
                    final_status = "EMERGENCY_KILL_SWITCH"
                    set_system_status(state_db_path, SYSTEM_STATUS_DEGRADED, "PROTECTION_LEG_MISSING")
                update_idempotency_status(
                    state_db_path,
                    idempotency_key=idempotency["idempotency_key"],
                    status=final_status,
                )
                save_execution_report(
                    state_db_path,
                    idempotency_key=idempotency["idempotency_key"],
                    report=execution_result,
                )
            else:
                update_idempotency_status(
                    state_db_path,
                    idempotency_key=idempotency["idempotency_key"],
                    status="FAILED",
                )
                save_execution_report(
                    state_db_path,
                    idempotency_key=idempotency["idempotency_key"],
                    report=execution_result,
                )
        except Exception as exc:
            if execution_result is not None and bool(execution_result.get("ok", False)):
                update_idempotency_status(
                    state_db_path,
                    idempotency_key=idempotency["idempotency_key"],
                    status=ORDER_STATUS_ACK,
                )
                execution_result["post_submit_error"] = {
                    "error": exc.__class__.__name__,
                    "message": str(exc),
                    "category": _classify_execution_error(exc),
                }
                save_execution_report(
                    state_db_path,
                    idempotency_key=idempotency["idempotency_key"],
                    report=execution_result,
                )
                continue
            update_idempotency_status(
                state_db_path,
                idempotency_key=idempotency["idempotency_key"],
                status="FAILED",
            )
            executions.append(
                {
                    "ok": False,
                    "error": exc.__class__.__name__,
                    "message": str(exc),
                    "error_category": _classify_execution_error(exc),
                    "latency_ms": 0.0,
                    "idempotency_key": idempotency["idempotency_key"],
                    "signal": signal,
                }
            )
    return executions


def execute_kill_switch(
    *,
    config: AppConfig,
    client_factory: Callable[[ExecutionConfig], ExecutionClient] | None = None,
) -> dict[str, Any]:
    state_db_path = config.ai_state_db_path
    ensure_trade_state_db(state_db_path)
    execution_config = ExecutionConfig(
        host=config.ibkr_host,
        port=config.ibkr_port,
        session_guard_enabled=False,
        good_after_seconds=config.execution_good_after_seconds,
        slippage_bps=config.risk_slippage_bps,
        commission_per_share=config.risk_commission_per_share,
    )
    set_system_status(state_db_path, SYSTEM_STATUS_HALTED, "KILL_SWITCH_ACTIVATED")
    current_runtime = get_runtime_state(state_db_path)
    set_runtime_state(
        state_db_path,
        drawdown=current_runtime.drawdown,
        day_trade_count=current_runtime.day_trade_count,
        cooldown_until=current_runtime.cooldown_until,
        kill_switch_active=True,
        equity=current_runtime.equity,
    )
    client = (client_factory or IbkrExecutionClient)(execution_config)
    try:
        handler = getattr(client, "activate_kill_switch", None)
        if callable(handler):
            result = handler()
        else:
            result = {"ok": False, "error": "KILL_SWITCH_NOT_SUPPORTED"}
        return {
            "kind": "phase0_kill_switch",
            "ok": bool(result.get("ok", False)),
            "result": result,
            "system_state": get_system_status(state_db_path),
        }
    finally:
        client.close()


def _import_ib_insync() -> tuple[type[Any], Callable[[str, str, str], Any]]:
    from ib_insync import IB, Stock

    return IB, Stock


def _trade_to_dict(trade: Any) -> dict[str, Any]:
    order = getattr(trade, "order", None)
    order_status = getattr(trade, "orderStatus", None)
    status = getattr(order_status, "status", "UNKNOWN")
    filled = float(getattr(order_status, "filled", 0.0) or 0.0)
    remaining = float(getattr(order_status, "remaining", 0.0) or 0.0)
    avg_fill_price = float(getattr(order_status, "avgFillPrice", 0.0) or 0.0)
    fills_payload = []
    for fill in list(getattr(trade, "fills", []) or []):
        execution = getattr(fill, "execution", None)
        fills_payload.append(
            {
                "exec_id": getattr(execution, "execId", ""),
                "shares": float(getattr(execution, "shares", 0.0) or 0.0),
                "price": float(getattr(execution, "price", 0.0) or 0.0),
                "time": str(getattr(execution, "time", "")),
            }
        )
    return {
        "status": status,
        "order_id": getattr(order, "orderId", None),
        "perm_id": getattr(order, "permId", None),
        "order_ref": getattr(order, "orderRef", ""),
        "lmt_price": float(getattr(order, "lmtPrice", 0.0) or 0.0),
        "aux_price": float(getattr(order, "auxPrice", 0.0) or 0.0),
        "filled_quantity": filled,
        "remaining_quantity": remaining,
        "avg_fill_price": avg_fill_price,
        "fills_count": len(fills_payload),
        "fills": fills_payload,
    }


def _is_valid_transmit_chain(orders_payload: list[dict[str, Any]]) -> bool:
    if len(orders_payload) != 3:
        return False
    flags = [bool(item.get("transmit", False)) for item in orders_payload]
    if flags != [False, False, True]:
        return False
    parent_ref = str(orders_payload[0].get("orderRef", ""))
    if not parent_ref:
        return False
    return all(str(item.get("parentRef", "")) == parent_ref for item in orders_payload[1:])


def _build_good_after_time(good_after_seconds: int) -> str:
    ts = datetime.now(tz=timezone.utc) + timedelta(seconds=max(0, good_after_seconds))
    return ts.strftime("%Y%m%d %H:%M:%S UTC")


def _is_within_session_window(start_utc: str, end_utc: str) -> bool:
    now = datetime.now(tz=timezone.utc)
    start = _parse_hhmm(start_utc)
    end = _parse_hhmm(end_utc)
    if start is None or end is None:
        return False
    current_minutes = now.hour * 60 + now.minute
    if start <= end:
        return start <= current_minutes <= end
    return current_minutes >= start or current_minutes <= end


def _parse_hhmm(raw: str) -> int | None:
    text = raw.strip()
    parts = text.split(":")
    if len(parts) not in {2, 3}:
        return None
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except Exception:
        return None
    if len(parts) == 3:
        try:
            second = int(parts[2])
        except Exception:
            return None
        if second < 0 or second > 59:
            return None
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return None
    return hour * 60 + minute


def _estimate_signal_cost(
    signal: dict[str, Any],
    *,
    slippage_bps: float,
    commission_per_share: float,
) -> dict[str, float]:
    orders = list(signal.get("orders", []) or [])
    if not orders:
        return {"slippage_cost": 0.0, "commission_cost": 0.0, "total": 0.0}
    parent = orders[0]
    quantity = float(parent.get("totalQuantity", 0.0) or 0.0)
    limit_price = float(parent.get("lmtPrice", 0.0) or 0.0)
    notional = max(0.0, quantity * limit_price)
    slippage_cost = notional * max(0.0, slippage_bps) / 10000
    commission_cost = max(0.0, quantity) * max(0.0, commission_per_share)
    total = slippage_cost + commission_cost
    return {
        "slippage_cost": round(slippage_cost, 6),
        "commission_cost": round(commission_cost, 6),
        "total": round(total, 6),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="phase0-ibkr-execute")
    parser.add_argument("--symbol", default="AAPL")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--actions-today", type=int, default=0)
    parser.add_argument("--has-open-position", action="store_true")
    parser.add_argument("--kill-switch", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config = load_config()
    if args.kill_switch:
        report = execute_kill_switch(config=config)
        print(json.dumps(report, ensure_ascii=False))
        return 0 if report.get("ok") else 2
    report = execute_cycle(
        symbol=args.symbol,
        config=config,
        send=args.send,
        daily_state={"actions_today": args.actions_today, "has_open_position": args.has_open_position},
    )
    print(json.dumps(report, ensure_ascii=False))
    all_ok = all(item.get("ok", False) for item in report.get("executions", []))
    if all_ok:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


def _reconcile_before_running(client: ExecutionClient, db_path: str) -> dict[str, Any]:
    try:
        method = getattr(client, "reconcile_snapshot", None)
        if not callable(method):
            return {"ok": False, "error": "RECONCILE_NOT_SUPPORTED"}
        snapshot = method()
        if not snapshot.get("ok", False):
            return {"ok": False, "error": snapshot.get("error", "RECONCILE_FAILED"), "snapshot": snapshot}
        open_orders = list(snapshot.get("open_orders", []) or [])
        positions = list(snapshot.get("positions", []) or [])
        apply_reconcile_snapshot(
            db_path,
            positions=positions,
            open_orders=open_orders,
        )
        equity = float(snapshot.get("equity", 0.0))
        if equity > 0:
            runtime = get_runtime_state(db_path)
            set_runtime_state(
                db_path,
                drawdown=runtime.drawdown,
                day_trade_count=runtime.day_trade_count,
                cooldown_until=runtime.cooldown_until,
                kill_switch_active=runtime.kill_switch_active,
                equity=equity,
            )
        return {
            "ok": True,
            "open_orders": len(open_orders),
            "positions": len(positions),
            "trades": len(list(snapshot.get("trades", []) or [])),
        }
    except Exception as exc:
        return {"ok": False, "error": exc.__class__.__name__, "message": str(exc)}


def _build_idempotency_key(signal: dict[str, Any]) -> dict[str, str]:
    contract = dict(signal.get("contract", {}) or {})
    orders = list(signal.get("orders", []) or [])
    first_order = orders[0] if orders else {}
    parent = dict(first_order) if isinstance(first_order, dict) else {}
    symbol = str(signal.get("symbol") or contract.get("symbol") or "").upper()
    side = str(signal.get("side") or parent.get("action") or "BUY").upper()
    strategy_id = str(signal.get("strategy_id") or signal.get("strategy") or "unknown")
    signal_ts = str(signal.get("signal_ts") or signal.get("generated_at") or "")
    quantity = str(parent.get("totalQuantity", ""))
    entry_price = str(parent.get("lmtPrice", ""))
    order_ref = str(parent.get("orderRef", ""))
    if not signal_ts:
        signal_ts = _signal_payload_fingerprint(signal)
    raw = f"{strategy_id}|{symbol}|{signal_ts}|{side}|{quantity}|{entry_price}|{order_ref}"
    return {
        "idempotency_key": raw,
        "strategy_id": strategy_id,
        "symbol": symbol,
        "signal_ts": signal_ts,
        "side": side,
    }


def _signal_payload_fingerprint(signal: dict[str, Any]) -> str:
    normalized = json.dumps(signal, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(normalized.encode("utf-8")).hexdigest()[:24]


def _read_current_drawdown_pct() -> float:
    raw = os.getenv("CURRENT_DRAWDOWN_PCT", "0")
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.0


def _apply_reject_recovery(*, state_db_path: str, runtime: Any) -> None:
    recovery = build_reject_recovery_runtime(cooldown_minutes=max(1, int(os.getenv("REJECT_RECOVERY_COOLDOWN_MINUTES", "10"))))
    set_runtime_state(
        state_db_path,
        drawdown=float(getattr(runtime, "drawdown", 0.0)),
        day_trade_count=int(getattr(runtime, "day_trade_count", 0)),
        cooldown_until=str(recovery["cooldown_until"]),
        kill_switch_active=bool(getattr(runtime, "kill_switch_active", False)),
        equity=float(getattr(runtime, "equity", 0.0)),
    )
    set_system_status(state_db_path, SYSTEM_STATUS_DEGRADED, "ORDER_REJECTED_RECOVERY")


def _classify_execution_error(exc: Exception) -> str:
    name = exc.__class__.__name__.lower()
    if "timeout" in name:
        return "timeout"
    if "connection" in name or "network" in name:
        return "connectivity"
    if "validation" in name or "valueerror" in name:
        return "validation"
    return "runtime"
