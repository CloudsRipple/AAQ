from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any


SYSTEM_STATUS_BOOTSTRAP = "BOOTSTRAP"
SYSTEM_STATUS_RECONCILE = "RECONCILE"
SYSTEM_STATUS_RUNNING = "RUNNING"
SYSTEM_STATUS_DEGRADED = "DEGRADED"
SYSTEM_STATUS_HALTED = "HALTED"

ORDER_STATUS_NEW = "NEW"
ORDER_STATUS_SENT = "SENT"
ORDER_STATUS_ACK = "ACK"
ORDER_STATUS_PARTIAL = "PARTIAL"
ORDER_STATUS_FILLED = "FILLED"
ORDER_STATUS_CANCELED = "CANCELED"
ORDER_STATUS_REJECTED = "REJECTED"


@dataclass(frozen=True)
class RuntimeState:
    drawdown: float
    day_trade_count: int
    cooldown_until: str
    kill_switch_active: bool
    equity: float = 0.0


def ensure_trade_state_db(db_path: str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS system_runtime_state (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS order_idempotency (
                idempotency_key TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                signal_ts TEXT NOT NULL,
                side TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_status TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                idempotency_key TEXT NOT NULL,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS open_orders (
                order_ref TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                reference_price REAL NOT NULL DEFAULT 0.0,
                broker_order_id TEXT,
                broker_status TEXT NOT NULL,
                local_status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        _ensure_open_orders_columns(conn)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                quantity REAL NOT NULL,
                avg_price REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_decision_audit (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id TEXT NOT NULL,
                intent_ref TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                outcome TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                trigger_value REAL NOT NULL,
                threshold_value REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS order_lifecycle_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_ref TEXT NOT NULL,
                prev_state TEXT NOT NULL,
                next_state TEXT NOT NULL,
                broker_status TEXT NOT NULL,
                filled_quantity REAL NOT NULL,
                remaining_quantity REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_quality (
                quality_id INTEGER PRIMARY KEY AUTOINCREMENT,
                intent_ref TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                expected_price REAL NOT NULL,
                avg_fill_price REAL NOT NULL,
                slippage_bps REAL NOT NULL,
                filled_quantity REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_decision_outcome (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id TEXT NOT NULL,
                intent_ref TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                outcome TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS observability_alerts (
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                detail_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def set_system_status(db_path: str, status: str, reason: str = "") -> None:
    ensure_trade_state_db(db_path)
    _set_runtime_value(
        db_path,
        key="system_status",
        payload={"status": status, "reason": reason},
    )


def get_system_status(db_path: str) -> dict[str, str]:
    ensure_trade_state_db(db_path)
    payload = _get_runtime_value(db_path, "system_status")
    if not payload:
        return {"status": SYSTEM_STATUS_BOOTSTRAP, "reason": "UNSET"}
    return {
        "status": str(payload.get("status", SYSTEM_STATUS_BOOTSTRAP)),
        "reason": str(payload.get("reason", "")),
    }


def set_runtime_state(
    db_path: str,
    *,
    drawdown: float,
    day_trade_count: int,
    cooldown_until: str,
    kill_switch_active: bool,
    equity: float = 0.0,
) -> None:
    ensure_trade_state_db(db_path)
    _set_runtime_value(
        db_path,
        key="trading_runtime",
        payload={
            "drawdown": max(0.0, drawdown),
            "day_trade_count": max(0, day_trade_count),
            "cooldown_until": cooldown_until,
            "kill_switch_active": bool(kill_switch_active),
            "equity": max(0.0, equity),
        },
    )


def get_runtime_state(db_path: str) -> RuntimeState:
    ensure_trade_state_db(db_path)
    payload = _get_runtime_value(db_path, "trading_runtime")
    if not payload:
        return RuntimeState(
            drawdown=0.0,
            day_trade_count=0,
            cooldown_until="",
            kill_switch_active=False,
            equity=0.0,
        )
    return RuntimeState(
        drawdown=max(0.0, float(payload.get("drawdown", 0.0) or 0.0)),
        day_trade_count=max(0, int(payload.get("day_trade_count", 0) or 0)),
        cooldown_until=str(payload.get("cooldown_until", "")),
        kill_switch_active=bool(payload.get("kill_switch_active", False)),
        equity=max(0.0, float(payload.get("equity", 0.0) or 0.0)),
    )


def is_idempotency_key_seen(db_path: str, idempotency_key: str) -> bool:
    ensure_trade_state_db(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM order_idempotency WHERE idempotency_key = ? LIMIT 1",
            (idempotency_key,),
        ).fetchone()
    return row is not None


def register_idempotency_key(
    db_path: str,
    *,
    idempotency_key: str,
    strategy_id: str,
    symbol: str,
    signal_ts: str,
    side: str,
    status: str = ORDER_STATUS_NEW,
) -> bool:
    ensure_trade_state_db(db_path)
    now = datetime.now(tz=timezone.utc).isoformat()
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO order_idempotency(
                    idempotency_key, strategy_id, symbol, signal_ts, side, created_at, last_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    idempotency_key,
                    strategy_id,
                    symbol.upper(),
                    signal_ts,
                    side.upper(),
                    now,
                    status,
                ),
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def update_idempotency_status(db_path: str, *, idempotency_key: str, status: str) -> None:
    ensure_trade_state_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            UPDATE order_idempotency
            SET last_status = ?
            WHERE idempotency_key = ?
            """,
            (status, idempotency_key),
        )
        conn.commit()


def save_execution_report(db_path: str, *, idempotency_key: str, report: dict[str, Any]) -> None:
    ensure_trade_state_db(db_path)
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO execution_reports(idempotency_key, report_json, created_at)
            VALUES (?, ?, ?)
            """,
            (idempotency_key, json.dumps(report, ensure_ascii=False), now),
        )
        conn.commit()


def list_execution_reports(db_path: str, *, limit: int = 500) -> list[dict[str, Any]]:
    ensure_trade_state_db(db_path)
    safe_limit = max(1, int(limit))
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT idempotency_key, report_json, created_at
            FROM execution_reports
            ORDER BY report_id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        try:
            payload = json.loads(str(row[1]))
            if not isinstance(payload, dict):
                payload = {}
        except json.JSONDecodeError:
            payload = {}
        payload["idempotency_key"] = str(row[0])
        payload["created_at"] = str(row[2])
        result.append(payload)
    return result


def apply_order_report(
    db_path: str,
    *,
    symbol: str,
    side: str,
    report_orders: list[dict[str, Any]],
) -> None:
    ensure_trade_state_db(db_path)
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        for item in report_orders:
            order_ref = str(item.get("order_ref", "")).strip()
            if not order_ref:
                continue
            broker_status = str(item.get("status", "UNKNOWN")).upper()
            local_status = derive_local_order_status(
                broker_status=broker_status,
                filled=float(item.get("filled_quantity", 0.0) or 0.0),
                remaining=float(item.get("remaining_quantity", 0.0) or 0.0),
            )
            qty = float(item.get("filled_quantity", 0.0) or 0.0) + float(item.get("remaining_quantity", 0.0) or 0.0)
            reference_price = max(
                0.0,
                float(
                    item.get("lmt_price", 0.0)
                    or item.get("avg_fill_price", 0.0)
                    or item.get("aux_price", 0.0)
                    or 0.0
                ),
            )
            if local_status in {ORDER_STATUS_FILLED, ORDER_STATUS_CANCELED, ORDER_STATUS_REJECTED}:
                conn.execute("DELETE FROM open_orders WHERE order_ref = ?", (order_ref,))
                continue
            conn.execute(
                """
                INSERT INTO open_orders(order_ref, symbol, side, quantity, reference_price, broker_order_id, broker_status, local_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(order_ref) DO UPDATE SET
                    symbol=excluded.symbol,
                    side=excluded.side,
                    quantity=excluded.quantity,
                    reference_price=excluded.reference_price,
                    broker_order_id=excluded.broker_order_id,
                    broker_status=excluded.broker_status,
                    local_status=excluded.local_status,
                    updated_at=excluded.updated_at
                """,
                (
                    order_ref,
                    symbol.upper(),
                    side.upper(),
                    max(0.0, qty),
                    reference_price,
                    str(item.get("order_id", "")),
                    broker_status,
                    local_status,
                    now,
                ),
            )
        conn.commit()


def apply_reconcile_snapshot(
    db_path: str,
    *,
    positions: list[dict[str, Any]],
    open_orders: list[dict[str, Any]],
) -> None:
    ensure_trade_state_db(db_path)
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM positions")
        for item in positions:
            symbol = str(item.get("symbol", "")).upper().strip()
            if not symbol:
                continue
            conn.execute(
                """
                INSERT INTO positions(symbol, quantity, avg_price, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    symbol,
                    float(item.get("quantity", 0.0) or 0.0),
                    float(item.get("avg_price", 0.0) or 0.0),
                    now,
                ),
            )
        conn.execute("DELETE FROM open_orders")
        for item in open_orders:
            order_ref = str(item.get("order_ref", "")).strip()
            if not order_ref:
                continue
            reference_price = max(
                0.0,
                float(
                    item.get("reference_price", 0.0)
                    or item.get("lmt_price", 0.0)
                    or item.get("avg_price", 0.0)
                    or item.get("price", 0.0)
                    or 0.0
                ),
            )
            conn.execute(
                """
                INSERT INTO open_orders(order_ref, symbol, side, quantity, reference_price, broker_order_id, broker_status, local_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_ref,
                    str(item.get("symbol", "")).upper(),
                    str(item.get("side", "")).upper(),
                    float(item.get("quantity", 0.0) or 0.0),
                    reference_price,
                    str(item.get("broker_order_id", "")),
                    str(item.get("broker_status", "UNKNOWN")).upper(),
                    str(item.get("local_status", ORDER_STATUS_ACK)).upper(),
                    now,
                ),
            )
        conn.commit()


def list_open_orders(db_path: str) -> list[dict[str, Any]]:
    ensure_trade_state_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT order_ref, symbol, side, quantity, reference_price, broker_order_id, broker_status, local_status, updated_at
            FROM open_orders
            ORDER BY updated_at DESC
            """
        ).fetchall()
    return [
        {
            "order_ref": str(row[0]),
            "symbol": str(row[1]),
            "side": str(row[2]),
            "quantity": float(row[3]),
            "reference_price": float(row[4]),
            "broker_order_id": str(row[5]),
            "broker_status": str(row[6]),
            "local_status": str(row[7]),
            "updated_at": str(row[8]),
        }
        for row in rows
    ]


def list_positions(db_path: str) -> list[dict[str, Any]]:
    ensure_trade_state_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT symbol, quantity, avg_price, updated_at
            FROM positions
            ORDER BY symbol ASC
            """
        ).fetchall()
    return [
        {
            "symbol": str(row[0]),
            "quantity": float(row[1]),
            "avg_price": float(row[2]),
            "updated_at": str(row[3]),
        }
        for row in rows
    ]


def derive_local_order_status(*, broker_status: str, filled: float, remaining: float) -> str:
    status = broker_status.strip().upper()
    if status in {"API_PENDING", "PENDING_SUBMIT", "PRE_SUBMITTED"}:
        return ORDER_STATUS_SENT
    if status in {"SUBMITTED", "ACK"} and filled <= 0:
        return ORDER_STATUS_ACK
    if status in {"PARTIAL", "PARTIALLYFILLED"} or (filled > 0 and remaining > 0):
        return ORDER_STATUS_PARTIAL
    if status in {"FILLED"} or (filled > 0 and remaining <= 0):
        return ORDER_STATUS_FILLED
    if status in {"CANCELLED", "CANCELED", "PENDING_CANCEL", "API_CANCELLED"}:
        return ORDER_STATUS_CANCELED
    if status in {"INACTIVE", "REJECTED"}:
        return ORDER_STATUS_REJECTED
    return ORDER_STATUS_NEW


def append_risk_decision_audit(
    db_path: str,
    *,
    decision_id: str,
    intent_ref: str,
    symbol: str,
    side: str,
    outcome: str,
    rule_id: str,
    trigger_value: float,
    threshold_value: float,
) -> None:
    ensure_trade_state_db(db_path)
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO risk_decision_audit(
                decision_id, intent_ref, symbol, side, outcome, rule_id, trigger_value, threshold_value, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                intent_ref,
                symbol.upper(),
                side.upper(),
                outcome.upper(),
                rule_id,
                float(trigger_value),
                float(threshold_value),
                now,
            ),
        )
        conn.commit()


def list_risk_decision_audit(db_path: str, *, limit: int = 50) -> list[dict[str, Any]]:
    ensure_trade_state_db(db_path)
    safe_limit = max(1, int(limit))
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT decision_id, intent_ref, symbol, side, outcome, rule_id, trigger_value, threshold_value, created_at
            FROM risk_decision_audit
            ORDER BY audit_id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
    return [
        {
            "decision_id": str(row[0]),
            "intent_ref": str(row[1]),
            "symbol": str(row[2]),
            "side": str(row[3]),
            "outcome": str(row[4]),
            "rule_id": str(row[5]),
            "trigger_value": float(row[6]),
            "threshold_value": float(row[7]),
            "created_at": str(row[8]),
        }
        for row in rows
    ]


def get_open_order_state(db_path: str, *, order_ref: str) -> str:
    ensure_trade_state_db(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT local_status FROM open_orders WHERE order_ref = ? LIMIT 1",
            (order_ref,),
        ).fetchone()
    if row is None:
        return ORDER_STATUS_NEW
    return str(row[0] or ORDER_STATUS_NEW).upper()


def has_open_order_ref(db_path: str, *, order_ref: str) -> bool:
    ensure_trade_state_db(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM open_orders WHERE order_ref = ? LIMIT 1",
            (order_ref,),
        ).fetchone()
    return row is not None


def append_order_lifecycle_event(
    db_path: str,
    *,
    order_ref: str,
    prev_state: str,
    next_state: str,
    broker_status: str,
    filled_quantity: float,
    remaining_quantity: float,
) -> None:
    ensure_trade_state_db(db_path)
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO order_lifecycle_events(
                order_ref, prev_state, next_state, broker_status, filled_quantity, remaining_quantity, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_ref,
                prev_state.upper(),
                next_state.upper(),
                broker_status.upper(),
                float(filled_quantity),
                float(remaining_quantity),
                now,
            ),
        )
        conn.commit()


def list_order_lifecycle_events(db_path: str, *, order_ref: str = "", limit: int = 100) -> list[dict[str, Any]]:
    ensure_trade_state_db(db_path)
    safe_limit = max(1, int(limit))
    with sqlite3.connect(db_path) as conn:
        if order_ref:
            rows = conn.execute(
                """
                SELECT order_ref, prev_state, next_state, broker_status, filled_quantity, remaining_quantity, created_at
                FROM order_lifecycle_events
                WHERE order_ref = ?
                ORDER BY event_id ASC
                LIMIT ?
                """,
                (order_ref, safe_limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT order_ref, prev_state, next_state, broker_status, filled_quantity, remaining_quantity, created_at
                FROM order_lifecycle_events
                ORDER BY event_id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
    return [
        {
            "order_ref": str(row[0]),
            "prev_state": str(row[1]),
            "next_state": str(row[2]),
            "broker_status": str(row[3]),
            "filled_quantity": float(row[4]),
            "remaining_quantity": float(row[5]),
            "created_at": str(row[6]),
        }
        for row in rows
    ]


def record_execution_quality(
    db_path: str,
    *,
    intent_ref: str,
    symbol: str,
    side: str,
    expected_price: float,
    avg_fill_price: float,
    slippage_bps: float,
    filled_quantity: float,
) -> None:
    ensure_trade_state_db(db_path)
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO execution_quality(
                intent_ref, symbol, side, expected_price, avg_fill_price, slippage_bps, filled_quantity, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                intent_ref,
                symbol.upper(),
                side.upper(),
                float(expected_price),
                float(avg_fill_price),
                float(slippage_bps),
                float(filled_quantity),
                now,
            ),
        )
        conn.commit()


def list_execution_quality(db_path: str, *, limit: int = 100) -> list[dict[str, Any]]:
    ensure_trade_state_db(db_path)
    safe_limit = max(1, int(limit))
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT intent_ref, symbol, side, expected_price, avg_fill_price, slippage_bps, filled_quantity, created_at
            FROM execution_quality
            ORDER BY quality_id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
    return [
        {
            "intent_ref": str(row[0]),
            "symbol": str(row[1]),
            "side": str(row[2]),
            "expected_price": float(row[3]),
            "avg_fill_price": float(row[4]),
            "slippage_bps": float(row[5]),
            "filled_quantity": float(row[6]),
            "created_at": str(row[7]),
        }
        for row in rows
    ]


def append_risk_decision_outcome(
    db_path: str,
    *,
    decision_id: str,
    intent_ref: str,
    symbol: str,
    side: str,
    outcome: str,
    rule_id: str,
) -> None:
    ensure_trade_state_db(db_path)
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO risk_decision_outcome(
                decision_id, intent_ref, symbol, side, outcome, rule_id, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                intent_ref,
                symbol.upper(),
                side.upper(),
                outcome.upper(),
                rule_id,
                now,
            ),
        )
        conn.commit()


def summarize_risk_decision_outcome(db_path: str) -> dict[str, int]:
    ensure_trade_state_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT outcome, COUNT(1)
            FROM risk_decision_outcome
            GROUP BY outcome
            """
        ).fetchall()
    summary = {"APPROVED": 0, "REJECTED": 0, "TOTAL": 0}
    for outcome, count in rows:
        key = str(outcome).upper()
        summary[key] = int(count)
        summary["TOTAL"] += int(count)
    return summary


def append_alert_event(
    db_path: str,
    *,
    rule_id: str,
    severity: str,
    title: str,
    detail: dict[str, Any],
) -> None:
    ensure_trade_state_db(db_path)
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO observability_alerts(rule_id, severity, title, detail_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                rule_id,
                severity.upper(),
                title,
                json.dumps(detail, ensure_ascii=False),
                now,
            ),
        )
        conn.commit()


def list_alert_events(db_path: str, *, limit: int = 100) -> list[dict[str, Any]]:
    ensure_trade_state_db(db_path)
    safe_limit = max(1, int(limit))
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT rule_id, severity, title, detail_json, created_at
            FROM observability_alerts
            ORDER BY alert_id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        try:
            detail = json.loads(str(row[3]))
            if not isinstance(detail, dict):
                detail = {}
        except json.JSONDecodeError:
            detail = {}
        result.append(
            {
                "rule_id": str(row[0]),
                "severity": str(row[1]),
                "title": str(row[2]),
                "detail": detail,
                "created_at": str(row[4]),
            }
        )
    return result


def _set_runtime_value(db_path: str, *, key: str, payload: dict[str, Any]) -> None:
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO system_runtime_state(key, value_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value_json=excluded.value_json,
                updated_at=excluded.updated_at
            """,
            (key, json.dumps(payload, ensure_ascii=False), now),
        )
        conn.commit()


def _ensure_open_orders_columns(conn: sqlite3.Connection) -> None:
    columns = conn.execute("PRAGMA table_info(open_orders)").fetchall()
    names = {str(item[1]).lower() for item in columns}
    if "reference_price" not in names:
        conn.execute("ALTER TABLE open_orders ADD COLUMN reference_price REAL NOT NULL DEFAULT 0.0")


def _get_runtime_value(db_path: str, key: str) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT value_json FROM system_runtime_state WHERE key = ?", (key,)).fetchone()
    if row is None:
        return {}
    try:
        loaded = json.loads(str(row[0]))
    except json.JSONDecodeError:
        return {}
    if not isinstance(loaded, dict):
        return {}
    return loaded
