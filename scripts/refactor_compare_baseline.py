from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


def _timestamp_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_summary(base_dir: Path) -> dict[str, Any]:
    summary_path = base_dir / "baseline_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing summary file: {summary_path}")
    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {summary_path}: {exc}") from exc


def _compare_exit_codes(
    baseline_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
) -> list[str]:
    diffs: list[str] = []
    baseline_commands = baseline_summary.get("commands", {})
    candidate_commands = candidate_summary.get("commands", {})
    for command_name in ("replay", "validation"):
        baseline_exit = baseline_commands.get(command_name, {}).get("exit_code")
        candidate_exit = candidate_commands.get(command_name, {}).get("exit_code")
        if baseline_exit != candidate_exit:
            diffs.append(
                f"- `{command_name}` exit code changed: baseline `{baseline_exit}` vs candidate `{candidate_exit}`"
            )
    return diffs


def _compare_replay(
    baseline_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
) -> list[str]:
    diffs: list[str] = []
    baseline_replay = baseline_summary.get("replay_summary", {})
    candidate_replay = candidate_summary.get("replay_summary", {})
    scalar_keys = ("present", "kind", "mode", "passed", "total")
    for key in scalar_keys:
        if baseline_replay.get(key) != candidate_replay.get(key):
            diffs.append(
                f"- replay `{key}` changed: baseline `{baseline_replay.get(key)}` vs candidate `{candidate_replay.get(key)}`"
            )
    baseline_scenarios = baseline_replay.get("scenario_status", {})
    candidate_scenarios = candidate_replay.get("scenario_status", {})
    all_scenarios = sorted(set(baseline_scenarios) | set(candidate_scenarios))
    for scenario in all_scenarios:
        if baseline_scenarios.get(scenario) != candidate_scenarios.get(scenario):
            diffs.append(
                f"- replay scenario `{scenario}` changed: baseline `{baseline_scenarios.get(scenario)}` vs candidate `{candidate_scenarios.get(scenario)}`"
            )
    return diffs


def _compare_validation(
    baseline_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
) -> list[str]:
    diffs: list[str] = []
    baseline_validation = baseline_summary.get("validation_summary", {})
    candidate_validation = candidate_summary.get("validation_summary", {})
    keys = (
        "command_output_present",
        "report_present",
        "command_ok",
        "kind",
        "ok",
        "replay_passed",
        "replay_total",
        "checks_passed",
        "checks_total",
        "dynamic_probe_ok",
        "validation_mode",
    )
    for key in keys:
        if baseline_validation.get(key) != candidate_validation.get(key):
            diffs.append(
                f"- validation `{key}` changed: baseline `{baseline_validation.get(key)}` vs candidate `{candidate_validation.get(key)}`"
            )
    return diffs


def _render_markdown(
    baseline_dir: Path,
    candidate_dir: Path,
    diffs: list[str],
) -> str:
    status = "PASS" if not diffs else "FAIL"
    lines = [
        "# Refactor Baseline Diff Report",
        "",
        f"- Generated at (UTC): {datetime.now(tz=timezone.utc).isoformat()}",
        f"- Baseline dir: `{baseline_dir}`",
        f"- Candidate dir: `{candidate_dir}`",
        f"- Status: **{status}**",
        "",
        "## Diff Summary",
    ]
    if not diffs:
        lines.append("- No differences found in captured summaries.")
    else:
        lines.extend(diffs)
    return "\n".join(lines) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="refactor-compare-baseline",
        description="Compare two refactor baseline snapshots and emit a markdown diff report.",
    )
    parser.add_argument(
        "--baseline-dir",
        required=True,
        help="Frozen baseline snapshot directory (contains baseline_summary.json).",
    )
    parser.add_argument(
        "--candidate-dir",
        required=True,
        help="Candidate snapshot directory (contains baseline_summary.json).",
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help="Optional report path (default: artifacts/refactor_baseline_diff_<ts>.md).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    baseline_dir = Path(args.baseline_dir).resolve()
    candidate_dir = Path(args.candidate_dir).resolve()
    if not baseline_dir.exists():
        print(f"[ERROR] Baseline directory not found: {baseline_dir}", file=sys.stderr)
        return 2
    if not candidate_dir.exists():
        print(f"[ERROR] Candidate directory not found: {candidate_dir}", file=sys.stderr)
        return 2

    try:
        baseline_summary = _load_summary(baseline_dir)
        candidate_summary = _load_summary(candidate_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    diffs = []
    diffs.extend(_compare_exit_codes(baseline_summary, candidate_summary))
    diffs.extend(_compare_replay(baseline_summary, candidate_summary))
    diffs.extend(_compare_validation(baseline_summary, candidate_summary))

    report_path = (
        Path(args.report_path)
        if args.report_path
        else Path("artifacts") / f"refactor_baseline_diff_{_timestamp_now()}.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_markdown(baseline_dir, candidate_dir, diffs), encoding="utf-8")

    print(
        json.dumps(
            {
                "report_path": str(report_path),
                "diff_count": len(diffs),
                "ok": len(diffs) == 0,
            },
            ensure_ascii=False,
        )
    )
    return 0 if not diffs else 3


if __name__ == "__main__":
    raise SystemExit(main())
