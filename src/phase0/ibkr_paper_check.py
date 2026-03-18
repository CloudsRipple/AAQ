from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import socket
import time
from typing import Any, Callable, Protocol


class MarketDataClient(Protocol):
    def request_l1_snapshot(self, symbol: str) -> dict[str, Any]:
        ...

    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, Any]]:
        ...

    def close(self) -> None:
        ...


@dataclass(frozen=True)
class ProbeConfig:
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 77
    timeout_seconds: float = 1.0
    symbol: str = "AAPL"
    news_limit: int = 5
    max_retries: int = 2


@dataclass(frozen=True)
class PortStatus:
    ok: bool
    host: str
    port: int
    latency_ms: float | None
    error: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "host": self.host,
            "port": self.port,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }


class IbkrInsyncClient:
    def __init__(self, host: str, port: int, client_id: int, timeout_seconds: float) -> None:
        from ib_insync import IB

        self._ib = IB()
        self._ib.connect(host, port, clientId=client_id, timeout=timeout_seconds, readonly=True)

    def request_l1_snapshot(self, symbol: str) -> dict[str, Any]:
        from ib_insync import Stock, util

        contract = Stock(symbol.upper(), "SMART", "USD")
        self._ib.qualifyContracts(contract)
        ticker = self._ib.reqMktData(contract, genericTickList="", snapshot=True, regulatorySnapshot=False)
        self._ib.sleep(1.2)
        payload = {
            "symbol": symbol.upper(),
            "bid": ticker.bid,
            "ask": ticker.ask,
            "last": ticker.last,
            "close": ticker.close,
            "timestamp": util.formatIBDatetime(datetime.now(tz=timezone.utc)),
        }
        self._ib.cancelMktData(contract)
        return payload

    def request_news(self, symbol: str, limit: int = 5) -> list[dict[str, Any]]:
        from ib_insync import Stock

        contract = Stock(symbol.upper(), "SMART", "USD")
        self._ib.qualifyContracts(contract)
        con_id = contract.conId
        providers = self._ib.reqNewsProviders()
        if not providers:
            return []
        provider_codes = "+".join(provider.code for provider in providers)
        items = self._ib.reqHistoricalNews(con_id, provider_codes, "", "", limit)
        return [
            {
                "time": item.time,
                "provider_code": item.providerCode,
                "article_id": item.articleId,
                "headline": item.headline,
            }
            for item in items
        ]

    def close(self) -> None:
        if self._ib.isConnected():
            self._ib.disconnect()


def check_port(host: str, port: int, timeout_seconds: float) -> PortStatus:
    started = datetime.now(tz=timezone.utc)
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            elapsed = datetime.now(tz=timezone.utc) - started
            latency_ms = round(elapsed.total_seconds() * 1000, 3)
            return PortStatus(ok=True, host=host, port=port, latency_ms=latency_ms, error=None)
    except OSError as exc:
        return PortStatus(ok=False, host=host, port=port, latency_ms=None, error=str(exc))


def fetch_yfinance_snapshot(symbol: str) -> dict[str, Any]:
    try:
        import yfinance as yf
    except Exception as exc:
        return {"ok": False, "source": "yfinance", "symbol": symbol.upper(), "error": str(exc)}
    try:
        history = yf.Ticker(symbol.upper()).history(period="1d", interval="1m")
        if history.empty:
            return {
                "ok": False,
                "source": "yfinance",
                "symbol": symbol.upper(),
                "error": "empty history",
            }
        last_row = history.tail(1).iloc[0]
        timestamp = history.tail(1).index[0].isoformat()
        return {
            "ok": True,
            "source": "yfinance",
            "symbol": symbol.upper(),
            "last": float(last_row["Close"]),
            "timestamp": timestamp,
        }
    except Exception as exc:
        return {"ok": False, "source": "yfinance", "symbol": symbol.upper(), "error": str(exc)}


def _append_critical_path_log(
    report: dict[str, Any],
    *,
    step: str,
    level: str,
    status: str,
    message: str,
    attempt: int | None = None,
    retryable: bool | None = None,
) -> None:
    entry: dict[str, Any] = {
        "time": datetime.now(tz=timezone.utc).isoformat(),
        "step": step,
        "level": level,
        "status": status,
        "message": message,
    }
    if attempt is not None:
        entry["attempt"] = attempt
    if retryable is not None:
        entry["retryable"] = retryable
    report["critical_path_logs"].append(entry)


def _append_alert(report: dict[str, Any], *, level: str, code: str, message: str) -> None:
    report["alerts"].append(
        {
            "time": datetime.now(tz=timezone.utc).isoformat(),
            "level": level,
            "code": code,
            "message": message,
        }
    )


def _is_retryable_probe_exception(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    lower_message = str(exc).lower()
    return any(token in lower_message for token in {"timeout", "temporar", "try again", "timed out", "busy"})


def _build_pass_evidence(symbol: str, l1_payload: dict[str, Any], news_items: list[dict[str, Any]]) -> dict[str, Any]:
    normalized_symbol = symbol.upper()
    l1_required_fields = {"bid", "ask", "last"}
    l1_present = sorted(key for key in l1_required_fields if l1_payload.get(key) is not None)
    l1_missing = sorted(l1_required_fields - set(l1_present))
    l1_ok = l1_payload.get("symbol", normalized_symbol).upper() == normalized_symbol and not l1_missing
    first_news = news_items[0] if news_items else {}
    news_required_fields = {"headline", "provider_code", "article_id"}
    news_present = sorted(key for key in news_required_fields if first_news.get(key))
    news_missing = sorted(news_required_fields - set(news_present))
    news_ok = bool(news_items) and not news_missing
    return {
        "l1_market_data": {
            "ok": l1_ok,
            "symbol_match": l1_payload.get("symbol", normalized_symbol).upper() == normalized_symbol,
            "required_fields_present": l1_present,
            "missing_fields": l1_missing,
            "snapshot": l1_payload,
        },
        "news": {
            "ok": news_ok,
            "items_count": len(news_items),
            "required_fields_present": news_present,
            "missing_fields": news_missing,
            "sample": first_news,
        },
    }


def run_probe(
    config: ProbeConfig,
    client_factory: Callable[[ProbeConfig], MarketDataClient] | None = None,
    port_checker: Callable[[str, int, float], PortStatus] | None = None,
    fallback_fetcher: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    factory = client_factory or (lambda conf: IbkrInsyncClient(conf.host, conf.port, conf.client_id, conf.timeout_seconds))
    active_port_checker = port_checker or check_port
    active_fallback_fetcher = fallback_fetcher or fetch_yfinance_snapshot
    report: dict[str, Any] = {
        "kind": "ibkr_paper_probe",
        "symbol": config.symbol.upper(),
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "critical_path_logs": [],
        "alerts": [],
    }

    port_status = active_port_checker(config.host, config.port, config.timeout_seconds)
    report["port_7497"] = port_status.to_dict()
    report["l1_market_data"] = {
        "ok": False,
        "source": "ibkr",
        "symbol": config.symbol.upper(),
        "error": "not attempted",
    }
    report["news"] = []
    report["fallback_market_data"] = None
    report["pass_evidence"] = {
        "l1_market_data": {
            "ok": False,
            "symbol_match": False,
            "required_fields_present": [],
            "missing_fields": ["bid", "ask", "last"],
            "snapshot": {},
        },
        "news": {
            "ok": False,
            "items_count": 0,
            "required_fields_present": [],
            "missing_fields": ["headline", "provider_code", "article_id"],
            "sample": {},
        },
    }
    report["retry_validation"] = {
        "max_retries": config.max_retries,
        "attempts": 0,
        "retried": False,
        "retryable_errors": [],
        "exhausted": False,
    }
    _append_critical_path_log(
        report,
        step="port_probe",
        level="INFO",
        status="start",
        message=f"start checking {config.host}:{config.port}",
    )

    if not port_status.ok:
        _append_critical_path_log(
            report,
            step="port_probe",
            level="WARN",
            status="failed",
            message=port_status.error or "port probe failed",
        )
        _append_alert(
            report,
            level="WARN",
            code="PORT_UNREACHABLE",
            message=f"{config.host}:{config.port} unreachable",
        )
        report["l1_market_data"]["error"] = "7497 unreachable"
        report["fallback_market_data"] = active_fallback_fetcher(config.symbol)
        report["ok"] = False
        return report

    _append_critical_path_log(
        report,
        step="port_probe",
        level="INFO",
        status="passed",
        message=f"{config.host}:{config.port} reachable",
    )
    client: MarketDataClient | None = None
    try:
        for attempt in range(1, config.max_retries + 2):
            report["retry_validation"]["attempts"] = attempt
            _append_critical_path_log(
                report,
                step="ibkr_probe",
                level="INFO",
                status="start",
                message="start requesting l1 and news",
                attempt=attempt,
            )
            try:
                client = factory(config)
                l1_payload = client.request_l1_snapshot(config.symbol)
                report["l1_market_data"] = {"ok": True, "source": "ibkr", **l1_payload}
                report["news"] = client.request_news(config.symbol, limit=config.news_limit)
                report["fallback_market_data"] = None
                report["pass_evidence"] = _build_pass_evidence(config.symbol, l1_payload, report["news"])
                if not report["pass_evidence"]["news"]["ok"]:
                    _append_alert(
                        report,
                        level="WARN",
                        code="NEWS_EVIDENCE_WEAK",
                        message="news evidence missing required fields or empty",
                    )
                _append_critical_path_log(
                    report,
                    step="ibkr_probe",
                    level="INFO",
                    status="passed",
                    message="l1 and news probe succeeded",
                    attempt=attempt,
                )
                break
            except Exception as exc:
                retryable = _is_retryable_probe_exception(exc)
                report["l1_market_data"] = {
                    "ok": False,
                    "source": "ibkr",
                    "symbol": config.symbol.upper(),
                    "error": str(exc),
                }
                _append_critical_path_log(
                    report,
                    step="ibkr_probe",
                    level="WARN" if retryable else "ERROR",
                    status="failed",
                    message=str(exc),
                    attempt=attempt,
                    retryable=retryable,
                )
                _append_alert(
                    report,
                    level="WARN" if retryable else "ERROR",
                    code="IBKR_PROBE_FAILED",
                    message=str(exc),
                )
                if retryable:
                    report["retry_validation"]["retryable_errors"].append(str(exc))
                if retryable and attempt <= config.max_retries:
                    report["retry_validation"]["retried"] = True
                    time.sleep(0.05 * attempt)
                    continue
                report["fallback_market_data"] = active_fallback_fetcher(config.symbol)
                report["retry_validation"]["exhausted"] = retryable and attempt > config.max_retries
                break
            finally:
                if client is not None:
                    client.close()
                    client = None
    finally:
        report["ok"] = (
            bool(report["l1_market_data"].get("ok"))
            and bool(report["pass_evidence"]["l1_market_data"]["ok"])
            and bool(report["pass_evidence"]["news"]["ok"])
        )
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="phase0-ibkr-paper-check")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7497)
    parser.add_argument("--client-id", type=int, default=77)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--symbol", default="AAPL")
    parser.add_argument("--news-limit", type=int, default=5)
    parser.add_argument("--max-retries", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config = ProbeConfig(
        host=args.host,
        port=args.port,
        client_id=args.client_id,
        timeout_seconds=args.timeout,
        symbol=args.symbol.upper(),
        news_limit=args.news_limit,
        max_retries=max(0, args.max_retries),
    )
    report = run_probe(config)
    print(json.dumps(report, ensure_ascii=False))
    if report.get("ok"):
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
