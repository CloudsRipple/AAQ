from __future__ import annotations

import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src" / "phase0"
OUTPUT_MD = ROOT / "artifacts" / "relationship_map.md"
OUTPUT_MODULE_CSV = ROOT / "artifacts" / "module_edges.csv"
OUTPUT_FUNCTION_CSV = ROOT / "artifacts" / "function_edges.csv"


@dataclass(frozen=True)
class FunctionDefInfo:
    qname: str
    module: str
    line: int


@dataclass(frozen=True)
class FunctionCallEdge:
    caller: str
    callee: str
    caller_module: str
    callee_module: str
    line: int


@dataclass(frozen=True)
class ModuleImportEdge:
    source: str
    target: str
    line: int


def module_name_from_path(path: Path) -> str:
    rel = path.relative_to(SRC_ROOT).with_suffix("")
    return "phase0." + ".".join(rel.parts)


def iter_py_files() -> Iterable[Path]:
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def resolve_import_from(current_module: str, level: int, module: str | None) -> str | None:
    if level <= 0:
        return module
    parts = current_module.split(".")[:-1]
    if level > len(parts) + 1:
        return None
    base = parts[: len(parts) - (level - 1)]
    if module:
        return ".".join(base + module.split("."))
    return ".".join(base)


def nearest_project_module(modules: set[str], target: str) -> str | None:
    if target in modules:
        return target
    current = target
    while "." in current:
        current = current.rsplit(".", 1)[0]
        if current in modules:
            return current
    return None


def build_index(modules: dict[str, Path]) -> tuple[dict[str, FunctionDefInfo], dict[str, set[str]], dict[str, set[str]]]:
    all_functions: dict[str, FunctionDefInfo] = {}
    module_level_functions: dict[str, set[str]] = defaultdict(set)
    module_class_methods: dict[str, set[str]] = defaultdict(set)

    class Collector(ast.NodeVisitor):
        def __init__(self, module: str) -> None:
            self.module = module
            self.class_stack: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._record(node.name, node.lineno)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._record(node.name, node.lineno)
            self.generic_visit(node)

        def _record(self, name: str, lineno: int) -> None:
            if self.class_stack:
                class_name = self.class_stack[-1]
                qname = f"{self.module}.{class_name}.{name}"
                module_class_methods[self.module].add(f"{class_name}.{name}")
            else:
                qname = f"{self.module}.{name}"
                module_level_functions[self.module].add(name)
            all_functions[qname] = FunctionDefInfo(qname=qname, module=self.module, line=lineno)

    for module, path in modules.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        Collector(module).visit(tree)

    return all_functions, module_level_functions, module_class_methods


def parse_relationships(
    modules: dict[str, Path],
    all_functions: dict[str, FunctionDefInfo],
    module_level_functions: dict[str, set[str]],
    module_class_methods: dict[str, set[str]],
) -> tuple[list[ModuleImportEdge], list[FunctionCallEdge]]:
    module_names = set(modules.keys())
    import_edges: list[ModuleImportEdge] = []
    call_edges: list[FunctionCallEdge] = []

    class Analyzer(ast.NodeVisitor):
        def __init__(self, module: str, path: Path) -> None:
            self.module = module
            self.path = path
            self.alias_to_module: dict[str, str] = {}
            self.alias_to_symbol: dict[str, str] = {}
            self.function_stack: list[str] = []
            self.class_stack: list[str] = []

        def current_caller(self) -> str | None:
            if not self.function_stack:
                return None
            if self.class_stack:
                return f"{self.module}.{self.class_stack[-1]}.{self.function_stack[-1]}"
            return f"{self.module}.{self.function_stack[-1]}"

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                full_name = alias.name
                nearest = nearest_project_module(module_names, full_name)
                if nearest and nearest.startswith("phase0"):
                    bind = alias.asname or full_name.split(".")[-1]
                    self.alias_to_module[bind] = nearest
                    import_edges.append(ModuleImportEdge(source=self.module, target=nearest, line=node.lineno))

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            resolved = resolve_import_from(self.module, node.level, node.module)
            if not resolved:
                return
            nearest = nearest_project_module(module_names, resolved)
            if nearest and nearest.startswith("phase0"):
                import_edges.append(ModuleImportEdge(source=self.module, target=nearest, line=node.lineno))
            for alias in node.names:
                if alias.name == "*":
                    continue
                bind = alias.asname or alias.name
                if resolved.startswith("phase0"):
                    symbol_qname = f"{resolved}.{alias.name}"
                    self.alias_to_symbol[bind] = symbol_qname

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.function_stack.append(node.name)
            self.generic_visit(node)
            self.function_stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.function_stack.append(node.name)
            self.generic_visit(node)
            self.function_stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            caller = self.current_caller()
            if caller is None:
                self.generic_visit(node)
                return
            callee = self._resolve_callee(node.func)
            if callee and callee.startswith("phase0"):
                callee_module = callee.rsplit(".", 1)[0]
                call_edges.append(
                    FunctionCallEdge(
                        caller=caller,
                        callee=callee,
                        caller_module=self.module,
                        callee_module=callee_module,
                        line=node.lineno,
                    )
                )
            self.generic_visit(node)

        def _resolve_callee(self, expr: ast.expr) -> str | None:
            if isinstance(expr, ast.Name):
                name = expr.id
                if name in self.alias_to_symbol:
                    return self.alias_to_symbol[name]
                if name in module_level_functions[self.module]:
                    return f"{self.module}.{name}"
                return None

            if isinstance(expr, ast.Attribute):
                if isinstance(expr.value, ast.Name):
                    base = expr.value.id
                    attr = expr.attr
                    if base in self.alias_to_module:
                        return f"{self.alias_to_module[base]}.{attr}"
                    if base in self.alias_to_symbol:
                        return f"{self.alias_to_symbol[base]}.{attr}"
                    if base == "self" and self.class_stack:
                        method_key = f"{self.class_stack[-1]}.{attr}"
                        if method_key in module_class_methods[self.module]:
                            return f"{self.module}.{method_key}"
                return None
            return None

    for module, path in modules.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        Analyzer(module, path).visit(tree)

    return import_edges, call_edges


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    lines = [",".join(header)]
    for row in rows:
        escaped = []
        for col in row:
            col = str(col).replace('"', '""')
            if any(ch in col for ch in [",", '"', "\n"]):
                col = f'"{col}"'
            escaped.append(col)
        lines.append(",".join(escaped))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    modules = {module_name_from_path(path): path for path in iter_py_files()}
    all_functions, module_level_functions, module_class_methods = build_index(modules)
    import_edges, call_edges = parse_relationships(
        modules=modules,
        all_functions=all_functions,
        module_level_functions=module_level_functions,
        module_class_methods=module_class_methods,
    )

    import_counter = Counter((edge.source, edge.target) for edge in import_edges)
    module_call_counter = Counter((edge.caller_module, edge.callee_module) for edge in call_edges)
    top_module_imports = sorted(import_counter.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))
    top_module_calls = sorted(module_call_counter.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))
    top_function_calls = sorted(call_edges, key=lambda x: (x.caller, x.line, x.callee))

    md_lines: list[str] = []
    md_lines.append("# 项目函数/模块关系总览")
    md_lines.append("")
    md_lines.append(f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}")
    md_lines.append(f"- 扫描范围：`{SRC_ROOT}`")
    md_lines.append(f"- 模块数量：{len(modules)}")
    md_lines.append(f"- 函数/方法数量：{len(all_functions)}")
    md_lines.append(f"- 模块导入边数量：{len(import_edges)}")
    md_lines.append(f"- 函数调用边数量（可静态解析）：{len(call_edges)}")
    md_lines.append("")

    md_lines.append("## 模块依赖关系（按导入频次）")
    md_lines.append("")
    md_lines.append("| 源模块 | 目标模块 | 导入次数 |")
    md_lines.append("|---|---|---:|")
    for (source, target), count in top_module_imports:
        md_lines.append(f"| `{source}` | `{target}` | {count} |")
    md_lines.append("")

    md_lines.append("## 模块调用关系（按函数调用聚合）")
    md_lines.append("")
    md_lines.append("| 调用方模块 | 被调模块 | 调用次数 |")
    md_lines.append("|---|---|---:|")
    for (caller_module, callee_module), count in top_module_calls:
        md_lines.append(f"| `{caller_module}` | `{callee_module}` | {count} |")
    md_lines.append("")

    md_lines.append("## 函数级调用关系（明细）")
    md_lines.append("")
    md_lines.append("| 调用函数 | 被调函数 | 调用行号 |")
    md_lines.append("|---|---|---:|")
    for edge in top_function_calls:
        md_lines.append(f"| `{edge.caller}` | `{edge.callee}` | {edge.line} |")
    md_lines.append("")

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(md_lines), encoding="utf-8")

    write_csv(
        OUTPUT_MODULE_CSV,
        ["source_module", "target_module", "edge_count"],
        [[s, t, str(c)] for (s, t), c in top_module_calls],
    )
    write_csv(
        OUTPUT_FUNCTION_CSV,
        ["caller", "callee", "caller_module", "callee_module", "line"],
        [[e.caller, e.callee, e.caller_module, e.callee_module, str(e.line)] for e in top_function_calls],
    )

    print(f"written: {OUTPUT_MD}")
    print(f"written: {OUTPUT_MODULE_CSV}")
    print(f"written: {OUTPUT_FUNCTION_CSV}")


if __name__ == "__main__":
    main()
