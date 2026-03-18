from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from statistics import quantiles
from typing import Any

from .config import AppConfig
from .state_store import (
    append_alert_event,
    get_runtime_state,
    list_alert_events,
    list_execution_quality,
    list_execution_reports,
    summarize_risk_decision_outcome,
)


logger = logging.getLogger(__name__)


def log_event(event_name: str, **fields: Any) -> None:
    payload = {"event": event_name, **fields}
    logger.info(event_name, extra={"event_payload": payload})


def build_metrics_snapshot(config: AppConfig) -> dict[str, Any]:
    reports = list_execution_reports(config.ai_state_db_path, limit=2000)
    quality = list_execution_quality(config.ai_state_db_path, limit=2000)
    risk_summary = summarize_risk_decision_outcome(config.ai_state_db_path)
    runtime = get_runtime_state(config.ai_state_db_path)
    attempts = [item for item in reports if not item.get("dry_run", False)]
    total_attempts = len(attempts)
    success_count = sum(1 for item in attempts if bool(item.get("ok", False)))
    reject_count = _count_rejected(attempts)
    latency_samples = _extract_latency_samples(attempts)
    p95_latency_ms = _p95(latency_samples)
    slippage_samples = [float(item.get("slippage_bps", 0.0) or 0.0) for item in quality if item.get("slippage_bps") is not None]
    avg_slippage_bps = _mean(slippage_samples)
    metrics = {
        "orders_attempted": total_attempts,
        "order_success_rate": _safe_ratio(success_count, total_attempts),
        "order_reject_rate": _safe_ratio(reject_count, total_attempts),
        "p95_latency_ms": p95_latency_ms,
        "avg_slippage_bps": avg_slippage_bps,
        "drawdown_pct": float(runtime.drawdown),
        "risk_reject_rate": _safe_ratio(int(risk_summary.get("REJECTED", 0)), int(risk_summary.get("TOTAL", 0))),
        "risk_decisions_total": int(risk_summary.get("TOTAL", 0)),
    }
    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "metrics": metrics,
        "raw": {
            "latency_samples_count": len(latency_samples),
            "slippage_samples_count": len(slippage_samples),
        },
    }


def evaluate_alerts(*, config: AppConfig, cycle_report: dict[str, Any] | None = None, metrics_snapshot: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    metrics_payload = metrics_snapshot or build_metrics_snapshot(config)
    metrics = dict(metrics_payload.get("metrics", {}) or {})
    report = cycle_report or {}
    alerts: list[dict[str, Any]] = []
    system_state = dict(report.get("system_state", {}) or {})
    state_status = str(system_state.get("status", "")).upper()
    state_reason = str(system_state.get("reason", "")).upper()
    executions = list(report.get("executions", []) or [])
    data_gate = dict(dict(report.get("lane", {}) or {}).get("data_quality_gate", {}) or {})
    if state_status in {"DEGRADED", "HALTED"} and ("RECONCILE" in state_reason or "PARTIAL_EXECUTION_FAILURE" in state_reason):
        alerts.append(
            _alert(
                rule_id="ALERT_GATEWAY_DISCONNECT",
                severity="critical",
                title="网关断连或执行链异常",
                detail={"state_status": state_status, "state_reason": state_reason},
            )
        )
    dedup_count = sum(1 for item in executions if bool(item.get("deduplicated", False)))
    if dedup_count > 0:
        alerts.append(
            _alert(
                rule_id="ALERT_DUPLICATE_ORDER_RISK",
                severity="warning",
                title="检测到重复下单风险",
                detail={"deduplicated_count": dedup_count},
            )
        )
    drawdown = float(metrics.get("drawdown_pct", 0.0) or 0.0)
    if drawdown >= config.risk_max_drawdown_pct * 0.8:
        alerts.append(
            _alert(
                rule_id="ALERT_ABNORMAL_DRAWDOWN",
                severity="critical" if drawdown >= config.risk_max_drawdown_pct else "warning",
                title="异常回撤告警",
                detail={
                    "drawdown_pct": drawdown,
                    "threshold_pct": config.risk_max_drawdown_pct,
                },
            )
        )
    if data_gate.get("degraded", False):
        alerts.append(
            _alert(
                rule_id="ALERT_DATA_OUTAGE",
                severity="critical",
                title="数据断流或数据质量退化",
                detail={"blocked_reasons": list(data_gate.get("blocked_reasons", []) or [])},
            )
        )
    for item in alerts:
        append_alert_event(
            config.ai_state_db_path,
            rule_id=item["rule_id"],
            severity=item["severity"],
            title=item["title"],
            detail=dict(item.get("detail", {}) or {}),
        )
        log_event("alert_triggered", **item)
    return alerts


def generate_daily_health_report(config: AppConfig, *, cycle_report: dict[str, Any] | None = None) -> dict[str, Any]:
    metrics = build_metrics_snapshot(config)
    alerts = evaluate_alerts(config=config, cycle_report=cycle_report, metrics_snapshot=metrics)
    recent_alerts = list_alert_events(config.ai_state_db_path, limit=30)
    summary = {
        "operational_status": _summary_status(alerts),
        "orders_attempted": metrics["metrics"]["orders_attempted"],
        "order_success_rate": metrics["metrics"]["order_success_rate"],
        "order_reject_rate": metrics["metrics"]["order_reject_rate"],
        "p95_latency_ms": metrics["metrics"]["p95_latency_ms"],
        "avg_slippage_bps": metrics["metrics"]["avg_slippage_bps"],
        "drawdown_pct": metrics["metrics"]["drawdown_pct"],
        "risk_reject_rate": metrics["metrics"]["risk_reject_rate"],
        "alerts_today": len(recent_alerts),
    }
    report = {
        "kind": "phase0_daily_health_report",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "metrics": metrics["metrics"],
        "alerts_triggered": alerts,
        "recent_alerts": recent_alerts,
        "summary": summary,
    }
    _write_report(report)
    log_event("daily_health_report_generated", summary=summary)
    return report


def _write_report(payload: dict[str, Any]) -> None:
    artifacts = Path("artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)
    json_path = artifacts / "daily_health_report.latest.json"
    md_path = artifacts / "daily_health_report.latest.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = dict(payload.get("summary", {}) or {})
    lines = [
        "# Daily Health Report",
        "",
        f"- generated_at: {payload.get('generated_at', '')}",
        f"- operational_status: {summary.get('operational_status', '')}",
        f"- orders_attempted: {summary.get('orders_attempted', 0)}",
        f"- order_success_rate: {summary.get('order_success_rate', 0.0):.4f}",
        f"- order_reject_rate: {summary.get('order_reject_rate', 0.0):.4f}",
        f"- p95_latency_ms: {summary.get('p95_latency_ms', 0.0):.2f}",
        f"- avg_slippage_bps: {summary.get('avg_slippage_bps', 0.0):.2f}",
        f"- drawdown_pct: {summary.get('drawdown_pct', 0.0):.4f}",
        f"- risk_reject_rate: {summary.get('risk_reject_rate', 0.0):.4f}",
        f"- alerts_today: {summary.get('alerts_today', 0)}",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    cleaned = sorted(float(item) for item in values)
    q = quantiles(cleaned, n=100, method="inclusive")
    return float(q[94])


def _extract_latency_samples(reports: list[dict[str, Any]]) -> list[float]:
    samples: list[float] = []
    for item in reports:
        value = item.get("latency_ms")
        if value is None:
            continue
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if parsed < 0:
            continue
        samples.append(parsed)
    return samples


def _count_rejected(reports: list[dict[str, Any]]) -> int:
    count = 0
    for item in reports:
        lifecycle = dict(item.get("lifecycle", {}) or {})
        if lifecycle.get("rejected", False):
            count += 1
            continue
        for entry in list(item.get("orders", []) or []):
            if str(entry.get("status", "")).upper() in {"REJECTED", "INACTIVE"}:
                count += 1
                break
    return count


def _alert(*, rule_id: str, severity: str, title: str, detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "title": title,
        "detail": detail,
    }


def _summary_status(alerts: list[dict[str, Any]]) -> str:
    if any(str(item.get("severity", "")).lower() == "critical" for item in alerts):
        return "DEGRADED"
    if alerts:
        return "WARN"
    return "HEALTHY"
