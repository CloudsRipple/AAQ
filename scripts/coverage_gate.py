from __future__ import annotations

from dataclasses import dataclass
import ast
import io
import json
from pathlib import Path
import sys
import traceback
from trace import Trace
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

CORE_MODULES = [
    "phase0/ibkr_execution.py",
    "phase0/risk_engine.py",
    "phase0/market_data.py",
    "phase0/execution_lifecycle.py",
    "phase0/state_store.py",
]
CORE_FUNCTIONS = {
    "phase0/ibkr_execution.py": {
        "execute_cycle",
        "_build_idempotency_key",
    },
    "phase0/risk_engine.py": {
        "evaluate_order_intents",
        "_evaluate_single_intent",
        "_fail_closed_decision",
    },
    "phase0/market_data.py": {
        "load_market_snapshot_with_gate",
        "evaluate_snapshot_quality",
        "get_market_calendar_status",
        "compute_snapshot_id",
    },
    "phase0/execution_lifecycle.py": {
        "process_execution_report",
    },
    "phase0/state_store.py": {
        "ensure_trade_state_db",
        "set_runtime_state",
        "get_runtime_state",
        "register_idempotency_key",
        "apply_order_report",
    },
}
THRESHOLD = 85.0


@dataclass
class ModuleCoverage:
    module: str
    executable_lines: int
    covered_lines: int

    @property
    def percent(self) -> float:
        if self.executable_lines <= 0:
            return 100.0
        return (self.covered_lines / self.executable_lines) * 100


def _count_executable_lines(path: Path, *, module_key: str) -> set[int]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    target_funcs = CORE_FUNCTIONS.get(module_key, set())
    selected_ranges: list[tuple[int, int]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in target_funcs:
            end_line = int(getattr(node, "end_lineno", node.lineno))
            selected_ranges.append((int(node.lineno), end_line))
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name in target_funcs:
                    end_line = int(getattr(child, "end_lineno", child.lineno))
                    selected_ranges.append((int(child.lineno), end_line))
    executable: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt) and hasattr(node, "lineno"):
            line_no = int(node.lineno)
            if selected_ranges:
                if any(start <= line_no <= end for start, end in selected_ranges):
                    executable.add(line_no)
            else:
                executable.add(line_no)
    return executable


def main() -> int:
    tracer = Trace(count=1, trace=0, ignoredirs=[sys.prefix, str(PROJECT_ROOT / ".venv"), str(PROJECT_ROOT / ".git")])
    loader = unittest.TestLoader()
    suite = loader.discover(str(PROJECT_ROOT / "tests"), pattern="test_*.py")
    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=1)
    result = tracer.runfunc(runner.run, suite)
    traces = tracer.results().counts
    module_reports: list[ModuleCoverage] = []
    for rel in CORE_MODULES:
        file_path = SRC_ROOT / rel
        executable = _count_executable_lines(file_path, module_key=rel)
        covered = {
            lineno
            for (fname, lineno), count in traces.items()
            if Path(fname).resolve() == file_path.resolve() and count > 0 and lineno in executable
        }
        module_reports.append(
            ModuleCoverage(
                module=rel,
                executable_lines=len(executable),
                covered_lines=len(covered),
            )
        )
    total_exec = sum(item.executable_lines for item in module_reports)
    total_cov = sum(item.covered_lines for item in module_reports)
    total_percent = 100.0 if total_exec <= 0 else (total_cov / total_exec) * 100
    passed = bool(result.wasSuccessful()) and total_percent >= THRESHOLD
    artifacts = PROJECT_ROOT / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    coverage_json = artifacts / "coverage_report.json"
    payload = {
        "tests_ok": bool(result.wasSuccessful()),
        "tests_run": int(result.testsRun),
        "threshold": THRESHOLD,
        "core_total_executable_lines": total_exec,
        "core_total_covered_lines": total_cov,
        "core_total_percent": round(total_percent, 2),
        "core_modules": [
            {
                "module": item.module,
                "executable_lines": item.executable_lines,
                "covered_lines": item.covered_lines,
                "percent": round(item.percent, 2),
            }
            for item in module_reports
        ],
        "passed": passed,
    }
    coverage_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    coverage_md = artifacts / "coverage_report.md"
    lines = [
        "# Coverage Report",
        "",
        f"- tests_ok: {payload['tests_ok']}",
        f"- tests_run: {payload['tests_run']}",
        f"- threshold: {THRESHOLD:.2f}%",
        f"- core_total_percent: {payload['core_total_percent']:.2f}%",
        "",
        "| module | executable | covered | percent |",
        "|---|---:|---:|---:|",
    ]
    for item in payload["core_modules"]:
        lines.append(
            f"| {item['module']} | {item['executable_lines']} | {item['covered_lines']} | {item['percent']:.2f}% |"
        )
    coverage_md.write_text("\n".join(lines), encoding="utf-8")
    print(stream.getvalue())
    print(json.dumps(payload, ensure_ascii=False))
    if not passed:
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(3)
