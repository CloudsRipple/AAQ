from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import sqlite3
from typing import Any
from zoneinfo import ZoneInfo

from .config import AppConfig


def load_market_snapshot_with_gate(
    *,
    config: AppConfig,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now = now_utc or datetime.now(tz=timezone.utc)
    calendar = get_market_calendar_status(now_utc=now)
    if config.market_data_mode == "live":
        primary_source = "live"
        backup_source = "json"
    elif config.market_snapshot_json:
        primary_source = "json"
        backup_source = "none"
    else:
        primary_source = "static"
        backup_source = "none"
    primary = _load_primary_snapshot(config=config, source=primary_source)
    degraded = False
    blocked_reasons: list[str] = []
    snapshot: dict[str, dict[str, float | str]] = {}
    source_used = ""
    if primary["ok"]:
        snapshot = dict(primary["snapshot"])
        source_used = primary_source
    else:
        degraded = True
        blocked_reasons.append("PRIMARY_SOURCE_UNAVAILABLE")
        if backup_source != "none":
            backup = _load_primary_snapshot(config=config, source=backup_source)
            if backup["ok"]:
                snapshot = dict(backup["snapshot"])
                source_used = backup_source
            else:
                source_used = "none"
                blocked_reasons.append("BACKUP_SOURCE_UNAVAILABLE")
        else:
            source_used = "none"
    try:
        quality = evaluate_snapshot_quality(
            snapshot=snapshot,
            source=source_used,
            state_db_path=config.ai_state_db_path,
            now_utc=now,
        )
    except sqlite3.OperationalError:
        degraded = True
        blocked_reasons.append("DB_LOCK_CONFLICT")
        quality = {
            "ok": False,
            "errors": ["DB_LOCK_CONFLICT"],
            "snapshot_ts": now.isoformat(),
            "lag_seconds": 0,
            "dirty_symbols": [],
            "jump_symbols": [],
        }
    if not quality["ok"]:
        degraded = True
        blocked_reasons.extend(list(quality["errors"]))
    if primary_source == "live" and source_used != "live":
        degraded = True
        blocked_reasons.append("PRIMARY_NOT_IN_USE")
    allow_trading = not degraded and quality["ok"] and bool(snapshot)
    allow_opening = bool(
        allow_trading
        and calendar.get("is_trading_day", False)
        and str(calendar.get("session_state", "")).upper() == "RTH"
    )
    snapshot_ts = str(quality.get("snapshot_ts", now.isoformat()))
    snapshot_id = compute_snapshot_id(snapshot=snapshot, source=source_used, snapshot_ts=snapshot_ts)
    try:
        record_market_snapshot_state(
            db_path=config.ai_state_db_path,
            snapshot_id=snapshot_id,
            snapshot=snapshot,
            snapshot_ts=snapshot_ts,
        )
    except sqlite3.OperationalError:
        degraded = True
        allow_trading = False
        blocked_reasons.append("DB_LOCK_CONFLICT")
    if not allow_trading:
        allow_opening = False
    return {
        "ok": bool(snapshot),
        "allow_trading": allow_trading,
        "allow_opening": allow_opening,
        "degraded": degraded,
        "source_primary": primary_source,
        "source_used": source_used,
        "blocked_reasons": sorted(set(blocked_reasons)),
        "snapshot": snapshot,
        "snapshot_id": snapshot_id,
        "snapshot_ts": snapshot_ts,
        "quality": quality,
        "calendar": calendar,
    }


def evaluate_snapshot_quality(
    *,
    snapshot: dict[str, dict[str, float | str]],
    source: str,
    state_db_path: str,
    now_utc: datetime,
) -> dict[str, Any]:
    errors: list[str] = []
    latency_threshold_seconds = _read_int_env("MARKET_DATA_LATENCY_THRESHOLD_SECONDS", 180)
    jump_threshold_pct = _read_float_env("MARKET_DATA_JUMP_THRESHOLD_PCT", 0.2)
    required_positive_fields = ("reference_price", "volatility")
    snapshot_ts = _extract_snapshot_ts(snapshot=snapshot) or now_utc.isoformat()
    parsed_snapshot_ts = _parse_any_datetime(snapshot_ts)
    if parsed_snapshot_ts is None:
        errors.append("SNAPSHOT_TS_INVALID")
        parsed_snapshot_ts = now_utc
    if parsed_snapshot_ts.tzinfo is None:
        parsed_snapshot_ts = parsed_snapshot_ts.replace(tzinfo=timezone.utc)
    parsed_snapshot_ts = parsed_snapshot_ts.astimezone(timezone.utc)
    lag_seconds = max(0, int((now_utc - parsed_snapshot_ts).total_seconds()))
    if lag_seconds > latency_threshold_seconds:
        errors.append("SNAPSHOT_LATENCY_EXCEEDED")
    _ensure_market_data_gate_db(state_db_path)
    previous_ts = _read_gate_meta(state_db_path, "last_snapshot_ts")
    if previous_ts:
        prev_dt = _parse_any_datetime(previous_ts)
        if prev_dt is not None:
            prev_utc = prev_dt if prev_dt.tzinfo is not None else prev_dt.replace(tzinfo=timezone.utc)
            prev_utc = prev_utc.astimezone(timezone.utc)
            if parsed_snapshot_ts < prev_utc:
                errors.append("TIMESTAMP_REVERSED")
    if not snapshot:
        errors.append("SNAPSHOT_EMPTY")
    dirty_symbols: list[str] = []
    jump_symbols: list[str] = []
    for symbol, row in snapshot.items():
        if not isinstance(row, dict):
            dirty_symbols.append(str(symbol).upper())
            continue
        symbol_key = str(symbol).upper()
        for field in required_positive_fields:
            value = row.get(field)
            if value is None:
                dirty_symbols.append(symbol_key)
                break
            numeric = _to_float(value)
            if numeric is None or not math.isfinite(numeric) or numeric <= 0:
                dirty_symbols.append(symbol_key)
                break
        current_price = _to_float(row.get("reference_price"))
        if current_price is None or current_price <= 0:
            continue
        previous_price = _read_last_price(state_db_path, symbol_key)
        if previous_price is not None and previous_price > 0:
            jump = abs(current_price - previous_price) / previous_price
            if jump > jump_threshold_pct:
                jump_symbols.append(symbol_key)
    if dirty_symbols:
        errors.append("MISSING_OR_INVALID_VALUES")
    if jump_symbols:
        errors.append("ABNORMAL_PRICE_JUMP")
    if source in {"none", ""}:
        errors.append("DATA_SOURCE_EMPTY")
    ok = not errors
    if ok:
        _write_gate_meta(state_db_path, "last_snapshot_ts", parsed_snapshot_ts.isoformat())
    return {
        "ok": ok,
        "errors": sorted(set(errors)),
        "snapshot_ts": parsed_snapshot_ts.isoformat(),
        "lag_seconds": lag_seconds,
        "dirty_symbols": sorted(set(dirty_symbols)),
        "jump_symbols": sorted(set(jump_symbols)),
    }


def get_market_calendar_status(*, now_utc: datetime) -> dict[str, Any]:
    tz = ZoneInfo("America/New_York")
    now_et = now_utc.astimezone(tz)
    trading_day = now_et.date()
    if trading_day.weekday() >= 5:
        return {
            "is_trading_day": False,
            "is_holiday": False,
            "is_half_day": False,
            "session_start_utc": None,
            "session_end_utc": None,
            "timezone": "America/New_York",
            "session_state": "CLOSED_WEEKEND",
        }
    holidays = us_market_holidays(trading_day.year)
    if trading_day in holidays:
        return {
            "is_trading_day": False,
            "is_holiday": True,
            "is_half_day": False,
            "session_start_utc": None,
            "session_end_utc": None,
            "timezone": "America/New_York",
            "session_state": "CLOSED_HOLIDAY",
        }
    half_days = us_market_half_days(trading_day.year)
    is_half_day = trading_day in half_days
    start_local = datetime.combine(trading_day, time(hour=9, minute=30), tzinfo=tz)
    end_hour = 13 if is_half_day else 16
    end_local = datetime.combine(trading_day, time(hour=end_hour, minute=0), tzinfo=tz)
    if now_et < start_local:
        session_state = "PRE_MARKET"
    elif now_et > end_local:
        session_state = "POST_MARKET"
    else:
        session_state = "RTH"
    return {
        "is_trading_day": True,
        "is_holiday": False,
        "is_half_day": is_half_day,
        "session_start_utc": start_local.astimezone(timezone.utc).isoformat(),
        "session_end_utc": end_local.astimezone(timezone.utc).isoformat(),
        "timezone": "America/New_York",
        "session_state": session_state,
    }


def compute_snapshot_id(*, snapshot: dict[str, dict[str, float | str]], source: str, snapshot_ts: str) -> str:
    normalized = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = sha256(f"{source}|{snapshot_ts}|{normalized}".encode("utf-8")).hexdigest()
    return digest[:24]


def record_market_snapshot_state(
    *,
    db_path: str,
    snapshot_id: str,
    snapshot: dict[str, dict[str, float | str]],
    snapshot_ts: str,
) -> None:
    _ensure_market_data_gate_db(db_path)
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO market_snapshot_registry(snapshot_id, snapshot_json, snapshot_ts, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(snapshot_id) DO UPDATE SET
                snapshot_json=excluded.snapshot_json,
                snapshot_ts=excluded.snapshot_ts,
                created_at=excluded.created_at
            """,
            (snapshot_id, json.dumps(snapshot, ensure_ascii=False), snapshot_ts, now),
        )
        for symbol, row in snapshot.items():
            symbol_key = str(symbol).upper()
            price = _to_float(row.get("reference_price"))
            if price is None or price <= 0:
                continue
            conn.execute(
                """
                INSERT INTO market_last_price(symbol, reference_price, snapshot_ts, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    reference_price=excluded.reference_price,
                    snapshot_ts=excluded.snapshot_ts,
                    updated_at=excluded.updated_at
                """,
                (symbol_key, float(price), snapshot_ts, now),
            )
        conn.commit()


def us_market_holidays(year: int) -> set[date]:
    holidays: set[date] = set()
    holidays.add(_observed(date(year, 1, 1)))
    holidays.add(_nth_weekday_of_month(year, 1, 0, 3))
    holidays.add(_nth_weekday_of_month(year, 2, 0, 3))
    holidays.add(_good_friday(year))
    holidays.add(_last_weekday_of_month(year, 5, 0))
    holidays.add(_observed(date(year, 6, 19)))
    holidays.add(_observed(date(year, 7, 4)))
    holidays.add(_nth_weekday_of_month(year, 9, 0, 1))
    holidays.add(_nth_weekday_of_month(year, 11, 3, 4))
    holidays.add(_observed(date(year, 12, 25)))
    return holidays


def us_market_half_days(year: int) -> set[date]:
    half_days: set[date] = set()
    thanksgiving = _nth_weekday_of_month(year, 11, 3, 4)
    next_day = thanksgiving + timedelta(days=1)
    if next_day.weekday() < 5:
        half_days.add(next_day)
    christmas_eve = date(year, 12, 24)
    if christmas_eve.weekday() < 5 and christmas_eve not in us_market_holidays(year):
        half_days.add(christmas_eve)
    independence_eve = date(year, 7, 3)
    if independence_eve.weekday() < 5 and independence_eve not in us_market_holidays(year):
        half_days.add(independence_eve)
    return half_days


def _load_primary_snapshot(*, config: AppConfig, source: str) -> dict[str, Any]:
    if source == "json":
        loaded = _load_market_snapshot_from_json_env(config.market_snapshot_json)
        return {"ok": bool(loaded), "snapshot": loaded}
    if source == "live":
        loaded = _load_market_snapshot_from_yfinance(config.market_symbols)
        return {"ok": bool(loaded), "snapshot": loaded}
    if source == "static":
        loaded = _default_market_snapshot()
        return {"ok": bool(loaded), "snapshot": loaded}
    return {"ok": False, "snapshot": {}}


def _load_market_snapshot_from_json_env(raw_json: str) -> dict[str, dict[str, float | str]]:
    if not raw_json:
        return {}
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    normalized: dict[str, dict[str, float | str]] = {}
    for symbol, row in payload.items():
        if not isinstance(row, dict):
            continue
        normalized[str(symbol).upper()] = dict(row)
    return normalized


def _load_market_snapshot_from_yfinance(raw_symbols: str) -> dict[str, dict[str, float | str]]:
    symbols = [item.strip().upper() for item in raw_symbols.split(",") if item.strip()]
    if not symbols:
        return {}
    try:
        import yfinance as yf
    except Exception:
        return {}
    snapshot: dict[str, dict[str, float | str]] = {}
    now = datetime.now(tz=timezone.utc).isoformat()
    for symbol in symbols:
        try:
            history = yf.Ticker(symbol).history(period="3mo", interval="1d")
            if history.empty or len(history) < 25:
                continue
            closes = history["Close"].dropna()
            if len(closes) < 25:
                continue
            ref_price = float(closes.iloc[-1])
            momentum_20d = (ref_price - float(closes.iloc[-21])) / max(1e-6, float(closes.iloc[-21]))
            returns = closes.pct_change().dropna()
            volatility = float(returns.tail(20).std()) if len(returns) >= 20 else 0.2
            mean_5 = float(closes.tail(5).mean())
            std_20 = float(closes.tail(20).std()) if len(closes) >= 20 else 1.0
            z_score_5d = (ref_price - mean_5) / max(1e-6, std_20)
            snapshot[symbol] = {
                "momentum_20d": round(momentum_20d, 6),
                "z_score_5d": round(z_score_5d, 6),
                "relative_strength": round(max(0.0, momentum_20d), 6),
                "volatility": round(max(0.01, volatility), 6),
                "reference_price": round(ref_price, 6),
                "liquidity_score": 0.8,
                "sector": "unknown",
                "snapshot_ts": now,
            }
        except Exception:
            continue
    return snapshot


def _default_market_snapshot() -> dict[str, dict[str, float | str]]:
    now = datetime.now(tz=timezone.utc).isoformat()
    return {
        "AAPL": {
            "momentum_20d": 0.08,
            "z_score_5d": -0.6,
            "relative_strength": 0.26,
            "volatility": 0.22,
            "reference_price": 180.0,
            "sector": "technology",
            "snapshot_ts": now,
        },
        "MSFT": {
            "momentum_20d": 0.07,
            "z_score_5d": 0.8,
            "relative_strength": 0.21,
            "volatility": 0.19,
            "reference_price": 420.0,
            "sector": "technology",
            "snapshot_ts": now,
        },
        "NVDA": {
            "momentum_20d": 0.14,
            "z_score_5d": 1.4,
            "relative_strength": 0.33,
            "volatility": 0.34,
            "reference_price": 950.0,
            "sector": "technology",
            "snapshot_ts": now,
        },
        "XOM": {
            "momentum_20d": 0.05,
            "z_score_5d": -1.3,
            "relative_strength": 0.18,
            "volatility": 0.18,
            "reference_price": 115.0,
            "sector": "energy",
            "snapshot_ts": now,
        },
    }


def _extract_snapshot_ts(snapshot: dict[str, dict[str, float | str]]) -> str | None:
    for row in snapshot.values():
        if not isinstance(row, dict):
            continue
        for key in ("snapshot_ts", "timestamp", "asof", "ts"):
            value = row.get(key)
            if value:
                return str(value)
    return None


def _parse_any_datetime(raw: str) -> datetime | None:
    text = str(raw).strip()
    if not text:
        return None
    candidate = text
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None


def _ensure_market_data_gate_db(db_path: str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_data_gate_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_last_price (
                symbol TEXT PRIMARY KEY,
                reference_price REAL NOT NULL,
                snapshot_ts TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_snapshot_registry (
                snapshot_id TEXT PRIMARY KEY,
                snapshot_json TEXT NOT NULL,
                snapshot_ts TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _write_gate_meta(db_path: str, key: str, value: str) -> None:
    now = datetime.now(tz=timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO market_data_gate_meta(key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                updated_at=excluded.updated_at
            """,
            (key, value, now),
        )
        conn.commit()


def _read_gate_meta(db_path: str, key: str) -> str:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT value FROM market_data_gate_meta WHERE key = ?", (key,)).fetchone()
    if row is None:
        return ""
    return str(row[0])


def _read_last_price(db_path: str, symbol: str) -> float | None:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT reference_price FROM market_last_price WHERE symbol = ?",
            (symbol.upper(),),
        ).fetchone()
    if row is None:
        return None
    value = _to_float(row[0])
    if value is None:
        return None
    return value


def _to_float(value: object) -> float | None:
    try:
        parsed = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed):
        return None
    return parsed


def _observed(day: date) -> date:
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def _nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    if month == 12:
        day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        day = date(year, month + 1, 1) - timedelta(days=1)
    while day.weekday() != weekday:
        day -= timedelta(days=1)
    return day


def _good_friday(year: int) -> date:
    easter = _western_easter(year)
    return easter - timedelta(days=2)


def _western_easter(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return date(year, month, day)


def _read_int_env(name: str, default_value: int) -> int:
    raw = os.getenv(name, str(default_value))
    try:
        return int(raw)
    except ValueError:
        return default_value


def _read_float_env(name: str, default_value: float) -> float:
    raw = os.getenv(name, str(default_value))
    try:
        return float(raw)
    except ValueError:
        return default_value
