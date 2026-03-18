from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any


@dataclass(frozen=True)
class ParameterAuditEntry:
    ts: str
    symbol: str
    strategy: str
    approved: bool
    reason: str
    before_stop_loss_pct: float
    after_stop_loss_pct: float
    before_risk_multiplier: float
    after_risk_multiplier: float
    low_committee_approved: bool
    ultra_wake_high: bool


def ensure_audit_db(db_path: str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS parameter_audit (
                ts TEXT NOT NULL,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                approved INTEGER NOT NULL,
                reason TEXT NOT NULL,
                before_stop_loss_pct REAL NOT NULL,
                after_stop_loss_pct REAL NOT NULL,
                before_risk_multiplier REAL NOT NULL,
                after_risk_multiplier REAL NOT NULL,
                low_committee_approved INTEGER NOT NULL,
                ultra_wake_high INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stoploss_override_state (
                symbol TEXT PRIMARY KEY,
                used_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        columns = conn.execute("PRAGMA table_info(stoploss_override_state)").fetchall()
        column_names = {str(item[1]) for item in columns}
        if "expires_at" not in column_names:
            conn.execute("ALTER TABLE stoploss_override_state ADD COLUMN expires_at TEXT")
            conn.execute(
                """
                UPDATE stoploss_override_state
                SET expires_at = datetime(used_at, '+72 hours')
                WHERE expires_at IS NULL OR expires_at = ''
                """
            )
        conn.commit()


def write_parameter_audit(db_path: str, entry: ParameterAuditEntry) -> None:
    ensure_audit_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO parameter_audit (
                ts, symbol, strategy, approved, reason,
                before_stop_loss_pct, after_stop_loss_pct,
                before_risk_multiplier, after_risk_multiplier,
                low_committee_approved, ultra_wake_high
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.ts,
                entry.symbol,
                entry.strategy,
                1 if entry.approved else 0,
                entry.reason,
                entry.before_stop_loss_pct,
                entry.after_stop_loss_pct,
                entry.before_risk_multiplier,
                entry.after_risk_multiplier,
                1 if entry.low_committee_approved else 0,
                1 if entry.ultra_wake_high else 0,
            ),
        )
        conn.commit()


def list_recent_audits(db_path: str, limit: int = 50) -> list[dict[str, Any]]:
    ensure_audit_db(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT ts, symbol, strategy, approved, reason,
                   before_stop_loss_pct, after_stop_loss_pct,
                   before_risk_multiplier, after_risk_multiplier,
                   low_committee_approved, ultra_wake_high
            FROM parameter_audit
            ORDER BY ts DESC
            LIMIT ?
            """,
            (max(1, limit),),
        ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        items.append(
            {
                "ts": str(row[0]),
                "symbol": str(row[1]),
                "strategy": str(row[2]),
                "approved": bool(row[3]),
                "reason": str(row[4]),
                "before_stop_loss_pct": float(row[5]),
                "after_stop_loss_pct": float(row[6]),
                "before_risk_multiplier": float(row[7]),
                "after_risk_multiplier": float(row[8]),
                "low_committee_approved": bool(row[9]),
                "ultra_wake_high": bool(row[10]),
            }
        )
    return items


def mark_stoploss_override_used(db_path: str, symbol: str, *, ttl_hours: int = 72) -> None:
    ensure_audit_db(db_path)
    now = datetime.now(tz=timezone.utc)
    expires_at = now + timedelta(hours=max(1, ttl_hours))
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO stoploss_override_state(symbol, used_at, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                used_at=excluded.used_at,
                expires_at=excluded.expires_at
            """,
            (symbol.upper(), now.isoformat(), expires_at.isoformat()),
        )
        conn.commit()


def is_stoploss_override_used(db_path: str, symbol: str) -> bool:
    ensure_audit_db(db_path)
    now = datetime.now(tz=timezone.utc)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT expires_at FROM stoploss_override_state WHERE symbol = ?
            """,
            (symbol.upper(),),
        ).fetchone()
        if row is None:
            return False
        expires_at = str(row[0] or "")
        if expires_at:
            try:
                expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if expires_dt.tzinfo is None:
                    expires_dt = expires_dt.replace(tzinfo=timezone.utc)
                if expires_dt.astimezone(timezone.utc) > now:
                    return True
            except ValueError:
                pass
        conn.execute("DELETE FROM stoploss_override_state WHERE symbol = ?", (symbol.upper(),))
        conn.commit()
    return False


def dump_audit_snapshot(db_path: str, limit: int = 20) -> str:
    return json.dumps({"rows": list_recent_audits(db_path, limit=limit)}, ensure_ascii=False)
