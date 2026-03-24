from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timestamp_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _extract_last_json_line(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        candidate = line.strip()
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _extract_replay_summary(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {"present": False}
    scenario_status: dict[str, bool] = {}
    for item in payload.get("results", []):
        if isinstance(item, dict) and "scenario" in item:
            scenario_status[str(item["scenario"])] = bool(item.get("ok"))
    return {
        "present": True,
        "kind": payload.get("kind"),
        "mode": payload.get("mode"),
        "passed": payload.get("passed"),
        "total": payload.get("total"),
        "scenario_status": scenario_status,
    }


def _extract_validation_summary(
    command_payload: dict[str, Any] | None,
    report_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = {
        "command_output_present": bool(command_payload),
        "report_present": bool(report_payload),
    }
    if command_payload:
        summary["command_ok"] = command_payload.get("ok")
        summary["command_output_path"] = command_payload.get("output")
    if report_payload:
        report_summary = report_payload.get("summary", {})
        ibkr_probe = report_payload.get("ibkr_probe", {})
        summary.update(
            {
                "kind": report_payload.get("kind"),
                "ok": report_payload.get("ok"),
                "replay_passed": report_summary.get("replay_passed"),
                "replay_total": report_summary.get("replay_total"),
                "checks_passed": report_summary.get("checks_passed"),
                "checks_total": report_summary.get("checks_total"),
                "dynamic_probe_ok": ibkr_probe.get("dynamic_probe_ok"),
                "validation_mode": ibkr_probe.get("validation_mode"),
            }
        )
    return summary


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run_command(
    name: str,
    command: list[str],
    output_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    process = subprocess.run(command, capture_output=True, text=True)
    stdout_path = output_dir / "stdout.log"
    stderr_path = output_dir / "stderr.log"
    result_path = output_dir / "result.json"

    stdout_path.write_text(process.stdout, encoding="utf-8")
    stderr_path.write_text(process.stderr, encoding="utf-8")

    parsed_stdout = _extract_last_json_line(process.stdout)
    result_payload = {
        "name": name,
        "command": command,
        "exit_code": process.returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
    }
    _write_json(result_path, result_payload)
    return result_payload, parsed_stdout


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="refactor-capture-baseline",
        description="Capture baseline artifacts for zero-incident refactor verification.",
    )
    parser.add_argument(
        "--out-root",
        default="artifacts/refactor_baseline",
        help="Base directory used to create a timestamped baseline snapshot.",
    )
    parser.add_argument(
        "--timestamp",
        default=None,
        help="Optional fixed timestamp folder name (default: UTC now in YYYYMMDDTHHMMSSZ).",
    )
    parser.add_argument(
        "--python-bin",
        default="python3",
        help="Python executable used to run phase0 commands (default: python3).",
    )
    parser.add_argument(
        "--replay-mode",
        default="all",
        choices=[
            "all",
            "breaking_news",
            "high_volatility",
            "duplicate_event_dedup",
            "unverified_stale_message",
            "safety_mode_blocked",
        ],
        help="Replay mode passed to phase0.replay.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    timestamp = args.timestamp or _timestamp_now()
    baseline_dir = Path(args.out_root) / timestamp
    if baseline_dir.exists():
        print(f"[ERROR] Baseline directory already exists: {baseline_dir}", file=sys.stderr)
        return 2

    replay_dir = baseline_dir / "replay"
    validation_dir = baseline_dir / "validation"
    replay_dir.mkdir(parents=True, exist_ok=False)
    validation_dir.mkdir(parents=True, exist_ok=False)

    validation_output_path = validation_dir / "phase0_validation_report.json"
    commands = [
        ("replay", [args.python_bin, "-m", "phase0.replay", "--mode", args.replay_mode], replay_dir),
        (
            "validation",
            [
                args.python_bin,
                "-m",
                "phase0.phase0_validation_report",
                "--output",
                str(validation_output_path),
            ],
            validation_dir,
        ),
    ]

    command_results: dict[str, Any] = {}
    replay_stdout_json: dict[str, Any] | None = None
    validation_stdout_json: dict[str, Any] | None = None

    for name, command, command_dir in commands:
        try:
            result, stdout_json = _run_command(name=name, command=command, output_dir=command_dir)
        except OSError as exc:
            print(f"[ERROR] Failed to run command {' '.join(command)!r}: {exc}", file=sys.stderr)
            return 2
        command_results[name] = result
        if name == "replay":
            replay_stdout_json = stdout_json
        if name == "validation":
            validation_stdout_json = stdout_json

    validation_report_json: dict[str, Any] | None = None
    if validation_output_path.exists():
        try:
            validation_report_json = json.loads(validation_output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[ERROR] Invalid validation report JSON at {validation_output_path}: {exc}", file=sys.stderr)
            return 2

    summary = {
        "captured_at": datetime.now(tz=timezone.utc).isoformat(),
        "baseline_dir": str(baseline_dir),
        "commands": command_results,
        "replay_summary": _extract_replay_summary(replay_stdout_json),
        "validation_summary": _extract_validation_summary(validation_stdout_json, validation_report_json),
    }
    summary_path = baseline_dir / "baseline_summary.json"
    _write_json(summary_path, summary)

    checksums = {
        "replay_stdout_log_sha256": _sha256_file(replay_dir / "stdout.log"),
        "replay_stderr_log_sha256": _sha256_file(replay_dir / "stderr.log"),
        "validation_stdout_log_sha256": _sha256_file(validation_dir / "stdout.log"),
        "validation_stderr_log_sha256": _sha256_file(validation_dir / "stderr.log"),
        "baseline_summary_sha256": _sha256_file(summary_path),
        "replay_stdout_sha256": _sha256_text((replay_dir / "stdout.log").read_text(encoding="utf-8")),
        "validation_stdout_sha256": _sha256_text((validation_dir / "stdout.log").read_text(encoding="utf-8")),
    }
    if validation_output_path.exists():
        checksums["validation_report_sha256"] = _sha256_file(validation_output_path)
    checksums_path = baseline_dir / "checksums_sha256.json"
    _write_json(checksums_path, checksums)

    exit_codes = [item["exit_code"] for item in command_results.values()]
    has_failure = any(code != 0 for code in exit_codes)
    print(
        json.dumps(
            {
                "baseline_dir": str(baseline_dir),
                "summary": str(summary_path),
                "checksums": str(checksums_path),
                "exit_codes": exit_codes,
                "ok": not has_failure,
            },
            ensure_ascii=False,
        )
    )
    return 0 if not has_failure else 2


if __name__ == "__main__":
    raise SystemExit(main())
