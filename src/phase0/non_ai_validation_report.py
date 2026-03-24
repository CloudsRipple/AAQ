from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

from .config import load_config
from .kernel.coordinator import run_guarded_coordinator_cycle


NON_AI_TEST_MODULES = [
    "test_config",
    "test_runtime_budget",
    "test_safety",
    "test_high_lane",
    "test_low_lane",
    "test_strategies",
    "test_lane_bus",
    "test_app_health",
    "test_ibkr_paper_check",
    "test_replay",
    "test_phase0_validation_report",
]


def generate_non_ai_validation_report() -> dict[str, Any]:
    env = os.environ.copy()
    env["AI_ENABLED"] = "false"
    env["LANE_SCHEDULER_ENABLED"] = "true"
    env["LANE_SCHEDULER_CYCLES"] = "1"
    py = sys.executable
    now = datetime.now(tz=timezone.utc)
    checks = [
        _run_command_check(
            name="unit_non_ai_suite",
            command=[py, "-m", "unittest", "-q", *NON_AI_TEST_MODULES],
            env=_with_pythonpath(env),
        ),
        _run_command_check(
            name="health_cli_non_ai",
            command=[py, "-m", "phase0.main"],
            env=_with_pythonpath(env),
        ),
        _run_command_check(
            name="replay_non_ai",
            command=[py, "-m", "phase0.replay", "--mode", "all"],
            env=_with_pythonpath(env),
        ),
        _run_command_check(
            name="validation_report_non_ai",
            command=[
                py,
                "-m",
                "phase0.phase0_validation_report",
                "--output",
                "artifacts/phase0_validation_report.non_ai.latest.json",
            ],
            env=_with_pythonpath(env),
        ),
    ]
    functional = _functional_non_ai_checks()
    components = _build_component_status(checks, functional)
    potential_issues = [item for item in _build_potential_issues(checks, functional)]
    ok = all(item["ok"] for item in checks) and functional["ok"]
    return {
        "kind": "phase0_non_ai_validation_report",
        "generated_at": now.isoformat(),
        "mode": "non_ai_bypass",
        "checks": checks,
        "functional": functional,
        "components": components,
        "potential_issues": potential_issues,
        "summary": {
            "checks_passed": sum(1 for item in checks if item["ok"]),
            "checks_total": len(checks),
            "functional_ok": functional["ok"],
        },
        "ok": ok,
    }


def _with_pythonpath(env: dict[str, str]) -> dict[str, str]:
    enriched = dict(env)
    existing = enriched.get("PYTHONPATH", "")
    base_paths = "src:tests"
    enriched["PYTHONPATH"] = f"{base_paths}:{existing}" if existing else base_paths
    return enriched


def _run_command_check(name: str, command: list[str], env: dict[str, str]) -> dict[str, Any]:
    result = subprocess.run(
        command,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return {
        "name": name,
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout_tail": _tail(result.stdout),
        "stderr_tail": _tail(result.stderr),
        "command": command,
    }


def _functional_non_ai_checks() -> dict[str, Any]:
    previous = os.environ.get("AI_ENABLED")
    os.environ["AI_ENABLED"] = "false"
    try:
        config = load_config()
        lane = run_guarded_coordinator_cycle("AAPL", config=config, allow_risk_execution=True)
    finally:
        if previous is None:
            os.environ.pop("AI_ENABLED", None)
        else:
            os.environ["AI_ENABLED"] = previous
    decision = lane["decisions"][0] if lane["decisions"] else {}
    checks = [
        {"name": "ai_bypassed_flag", "ok": lane.get("ai_bypassed") is True},
        {"name": "lane_decision_generated", "ok": bool(decision)},
        {"name": "data_pipeline_kept", "ok": len(lane.get("watchlist", [])) > 0},
        {"name": "error_handling_surface", "ok": isinstance(decision.get("reject_reasons", []), list)},
    ]
    return {
        "ok": all(item["ok"] for item in checks),
        "checks": checks,
        "lane_snapshot": {
            "execution_status": decision.get("status"),
            "watchlist_size": len(lane.get("watchlist", [])),
            "published_events": lane.get("published_events", 0),
        },
    }


def _build_component_status(command_checks: list[dict[str, Any]], functional: dict[str, Any]) -> list[dict[str, Any]]:
    status_map = {item["name"]: item["ok"] for item in command_checks}
    fchecks = {item["name"]: item["ok"] for item in functional["checks"]}
    return [
        {
            "component": "data_input",
            "ok": status_map.get("unit_non_ai_suite", False) and fchecks.get("data_pipeline_kept", False),
        },
        {
            "component": "data_preprocessing",
            "ok": status_map.get("unit_non_ai_suite", False),
        },
        {
            "component": "data_transport",
            "ok": status_map.get("replay_non_ai", False) and fchecks.get("lane_decision_generated", False),
        },
        {
            "component": "storage",
            "ok": status_map.get("validation_report_non_ai", False),
        },
        {
            "component": "user_interface",
            "ok": status_map.get("health_cli_non_ai", False),
        },
        {
            "component": "error_handling",
            "ok": fchecks.get("error_handling_surface", False),
        },
    ]


def _build_potential_issues(command_checks: list[dict[str, Any]], functional: dict[str, Any]) -> list[dict[str, str]]:
    for item in command_checks:
        if not item["ok"]:
            yield {
                "source": item["name"],
                "problem": "command_failed",
                "hint": (item.get("stderr_tail") or item.get("stdout_tail") or "unknown_error")[:200],
            }
    for item in functional["checks"]:
        if not item["ok"]:
            yield {
                "source": "functional_non_ai",
                "problem": item["name"],
                "hint": "需要检查非AI模式旁路链路是否保持完整",
            }


def _tail(text: str, limit: int = 1200) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="phase0-non-ai-validation-report")
    parser.add_argument("--output", default="artifacts/phase0_non_ai_validation_report.json")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    report = generate_non_ai_validation_report()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json_atomic(output_path, report)
    print(json.dumps({"ok": report["ok"], "output": str(output_path)}, ensure_ascii=False))
    if report["ok"]:
        return 0
    return 2


def _write_json_atomic(output_path: Path, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(output_path.parent),
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp_path = Path(tmp.name)
    temp_path.replace(output_path)


if __name__ == "__main__":
    raise SystemExit(main())
