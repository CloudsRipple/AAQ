from __future__ import annotations

import ast
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src" / "phase0"
ARTIFACTS = ROOT / "artifacts"
OUTPUT = ARTIFACTS / "project_assembly_sheet.md"


@dataclass(frozen=True)
class FuncInfo:
    qname: str
    module: str
    file: str
    line: int
    kind: str


def iter_py_files() -> Iterable[Path]:
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def module_name_from_path(path: Path) -> str:
    rel = path.relative_to(SRC_ROOT).with_suffix("")
    return "phase0." + ".".join(rel.parts)


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
    cur = target
    while "." in cur:
        cur = cur.rsplit(".", 1)[0]
        if cur in modules:
            return cur
    return None


def collect_defs(modules: dict[str, Path]) -> tuple[list[FuncInfo], dict[str, set[str]], dict[str, set[str]], dict[str, int]]:
    defs: list[FuncInfo] = []
    module_level: dict[str, set[str]] = defaultdict(set)
    class_methods: dict[str, set[str]] = defaultdict(set)
    class_counts: dict[str, int] = defaultdict(int)

    class Visitor(ast.NodeVisitor):
        def __init__(self, module: str, path: Path) -> None:
            self.module = module
            self.path = path
            self.class_stack: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            class_counts[self.module] += 1
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._add(node.name, node.lineno, "function")
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._add(node.name, node.lineno, "async_function")
            self.generic_visit(node)

        def _add(self, name: str, line: int, kind: str) -> None:
            rel_file = str(self.path.relative_to(ROOT))
            if self.class_stack:
                class_name = self.class_stack[-1]
                qname = f"{self.module}.{class_name}.{name}"
                class_methods[self.module].add(f"{class_name}.{name}")
                kind = "method" if kind == "function" else "async_method"
            else:
                qname = f"{self.module}.{name}"
                module_level[self.module].add(name)
            defs.append(FuncInfo(qname=qname, module=self.module, file=rel_file, line=line, kind=kind))

    for mod, path in modules.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        Visitor(mod, path).visit(tree)
    return defs, module_level, class_methods, class_counts


def analyze_edges(
    modules: dict[str, Path],
    module_level: dict[str, set[str]],
    class_methods: dict[str, set[str]],
) -> tuple[list[tuple[str, str, int]], list[tuple[str, str, int, int]], list[tuple[str, str, str, int]]]:
    module_names = set(modules.keys())
    import_edges: list[tuple[str, str, int]] = []
    call_edges: list[tuple[str, str, int, int]] = []  # caller_mod, callee_mod, line, n
    topic_edges: list[tuple[str, str, str, int]] = []  # module, op, topic, line

    class Visitor(ast.NodeVisitor):
        def __init__(self, module: str, path: Path) -> None:
            self.module = module
            self.path = path
            self.alias_to_module: dict[str, str] = {}
            self.alias_to_symbol: dict[str, str] = {}
            self.class_stack: list[str] = []
            self.func_stack: list[str] = []

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                full = alias.name
                nearest = nearest_project_module(module_names, full)
                if nearest and nearest.startswith("phase0"):
                    import_edges.append((self.module, nearest, node.lineno))
                    self.alias_to_module[alias.asname or full.split(".")[-1]] = nearest
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            resolved = resolve_import_from(self.module, node.level, node.module)
            if resolved:
                nearest = nearest_project_module(module_names, resolved)
                if nearest and nearest.startswith("phase0"):
                    import_edges.append((self.module, nearest, node.lineno))
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    bind = alias.asname or alias.name
                    nearest_symbol_module = nearest_project_module(module_names, resolved)
                    if nearest_symbol_module and nearest_symbol_module.startswith("phase0"):
                        self.alias_to_symbol[bind] = nearest_symbol_module
            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.func_stack.append(node.name)
            self.generic_visit(node)
            self.func_stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.func_stack.append(node.name)
            self.generic_visit(node)
            self.func_stack.pop()

        def visit_Call(self, node: ast.Call) -> None:
            callee = self._resolve_callee(node.func)
            if callee:
                call_edges.append((self.module, callee, node.lineno, 1))

            op_topic = self._resolve_bus_topic(node)
            if op_topic:
                op, topic = op_topic
                topic_edges.append((self.module, op, topic, node.lineno))
            self.generic_visit(node)

        def _resolve_callee(self, expr: ast.expr) -> str | None:
            if isinstance(expr, ast.Name):
                name = expr.id
                if name in self.alias_to_symbol:
                    tgt_mod = self.alias_to_symbol[name]
                    if tgt_mod.startswith("phase0"):
                        return tgt_mod
                if name in module_level[self.module]:
                    return self.module
                return None

            if isinstance(expr, ast.Attribute) and isinstance(expr.value, ast.Name):
                base = expr.value.id
                attr = expr.attr
                if base in self.alias_to_module:
                    return self.alias_to_module[base]
                if base in self.alias_to_symbol:
                    tgt_mod = self.alias_to_symbol[base]
                    if tgt_mod.startswith("phase0"):
                        return tgt_mod
                if base == "self" and self.class_stack:
                    method_key = f"{self.class_stack[-1]}.{attr}"
                    if method_key in class_methods[self.module]:
                        return self.module
            return None

        @staticmethod
        def _resolve_bus_topic(node: ast.Call) -> tuple[str, str] | None:
            if not isinstance(node.func, ast.Attribute):
                return None
            op = node.func.attr
            if op not in {"publish", "apublish", "subscribe", "consume", "consume_for", "aconsume", "aconsume_for"}:
                return None
            if not node.args:
                return None
            topic_node = node.args[0]
            if isinstance(topic_node, ast.Constant) and isinstance(topic_node.value, str):
                return op, topic_node.value
            return None

    for mod, path in modules.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        Visitor(mod, path).visit(tree)
    return import_edges, call_edges, topic_edges


def load_issues_master() -> list[dict[str, str]]:
    p = ROOT / "issues_master.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return list(data.get("issues", []))


def build_open_arch_issues() -> list[dict[str, str]]:
    return [
        {
            "id": "ARCH-01",
            "category": "双主路径",
            "problem": "health-check/lane cycle 与 event-driven daemon 双轨并存，业务语义重复。",
            "evidence": "docs/architecture/MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN.md:76",
            "impact": "维护成本高、变更需双轨同步、审计口径可能分叉。",
            "source": "MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN",
        },
        {
            "id": "ARCH-02",
            "category": "总装厂",
            "problem": "lanes/__init__.py 承担过多职责（市场、策略、AI、风控前调整、审计、映射、总线）。",
            "evidence": "docs/architecture/MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN.md:97",
            "impact": "高耦合、难测试、回归范围大。",
            "source": "MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN",
        },
        {
            "id": "ARCH-03",
            "category": "收口冲突",
            "problem": "Execution 阶段存在反向重算 High 的语义，冲击 High 唯一收口原则。",
            "evidence": "docs/architecture/MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN.md:118",
            "impact": "决策重复、审计链不确定。",
            "source": "MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN",
        },
        {
            "id": "ARCH-04",
            "category": "AI 越权",
            "problem": "AI 在主链上直接影响 live decision 参数，未完整通过治理平面。",
            "evidence": "docs/architecture/MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN.md:134",
            "impact": "边界模糊、回放一致性变弱。",
            "source": "MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN",
        },
        {
            "id": "ARCH-05",
            "category": "状态 ownership",
            "problem": "state_store 聚合过多业务状态，ownership 不清晰。",
            "evidence": "docs/architecture/MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN.md:148",
            "impact": "恢复顺序复杂、演进风险高。",
            "source": "MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN",
        },
        {
            "id": "ARCH-06",
            "category": "边界泄漏",
            "problem": "service/domain 与 adapter 边界存在直接 IO 调用穿透。",
            "evidence": "docs/architecture/MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN.md:172",
            "impact": "替换成本高、可测试性降低。",
            "source": "MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN",
        },
        {
            "id": "ARCH-07",
            "category": "语义重叠",
            "problem": "lanes/high.py 与 ai/high.py 的 High 语义重叠。",
            "evidence": "docs/architecture/REFACTOR_BLUEPRINT_AI_ADVISORY.md:29",
            "impact": "命名与职责冲突，理解成本高。",
            "source": "REFACTOR_BLUEPRINT_AI_ADVISORY",
        },
        {
            "id": "ARCH-08",
            "category": "缓存耦合",
            "problem": "Low 全局缓存由多模块共享读写（隐式耦合）。",
            "evidence": "src/phase0/lanes/low_engine.py:15; src/phase0/lanes/low_subscriber.py:8",
            "impact": "状态一致性与并发语义难验证。",
            "source": "code-observation",
        },
        {
            "id": "ARCH-09",
            "category": "中心化依赖",
            "problem": "AI 层直接依赖 lanes 实现与共享状态（非纯 contract 依赖）。",
            "evidence": "src/phase0/ai/high.py:18; src/phase0/ai/high.py:21",
            "impact": "层间解耦不足，迁移成本高。",
            "source": "code-observation",
        },
    ]


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return out


def main() -> None:
    modules = {module_name_from_path(p): p for p in iter_py_files()}
    defs, module_level, class_methods, class_counts = collect_defs(modules)
    import_edges, call_edges, topic_edges = analyze_edges(modules, module_level, class_methods)

    func_count_by_module = Counter(d.module for d in defs)
    import_out = Counter(src for src, _, _ in import_edges)
    import_in = Counter(dst for _, dst, _ in import_edges)
    call_out = Counter(src for src, _, _, _ in call_edges)
    call_in = Counter(dst for _, dst, _, _ in call_edges)

    module_rows = []
    for module in sorted(modules):
        module_rows.append(
            [
                f"`{module}`",
                f"`{modules[module].relative_to(ROOT)}`",
                str(class_counts.get(module, 0)),
                str(func_count_by_module.get(module, 0)),
                str(import_out.get(module, 0)),
                str(import_in.get(module, 0)),
                str(call_out.get(module, 0)),
                str(call_in.get(module, 0)),
            ]
        )

    import_pair_counts = Counter((s, t) for s, t, _ in import_edges)
    call_pair_counts = Counter((s, t) for s, t, _, _ in call_edges)
    comm_rows = []
    all_pairs = sorted(set(import_pair_counts) | set(call_pair_counts))
    for s, t in all_pairs:
        comm_rows.append(
            [
                f"`{s}`",
                f"`{t}`",
                str(import_pair_counts.get((s, t), 0)),
                str(call_pair_counts.get((s, t), 0)),
            ]
        )

    topic_counts = Counter((m, op, topic) for m, op, topic, _ in topic_edges)
    topic_rows = []
    for (m, op, topic), n in sorted(topic_counts.items(), key=lambda x: (x[0][2], x[0][0], x[0][1])):
        topic_rows.append([f"`{m}`", f"`{op}`", f"`{topic}`", str(n)])

    func_rows = [
        [f"`{d.qname}`", f"`{d.module}`", f"`{d.file}`", str(d.line), f"`{d.kind}`"]
        for d in sorted(defs, key=lambda x: (x.module, x.line, x.qname))
    ]

    arch_issues = build_open_arch_issues()
    arch_issue_rows = [
        [f"`{i['id']}`", i["category"], i["problem"], f"`{i['evidence']}`", i["impact"], i["source"]]
        for i in arch_issues
    ]

    fixed_issues = load_issues_master()
    fixed_issue_rows = [
        [
            str(i.get("id", "")),
            str(i.get("类别", "")),
            str(i.get("描述", "")),
            f"`{i.get('文件', '')}:{i.get('行号', '')}`",
            str(i.get("严重程度", "")),
            str(i.get("状态", "")),
        ]
        for i in fixed_issues
    ]

    lines: list[str] = []
    lines.append("# 项目总装分析表（函数 / 模块 / 通信 / 问题）")
    lines.append("")
    lines.append(f"- 生成时间：`{datetime.now().isoformat(timespec='seconds')}`")
    lines.append(f"- 扫描目录：`{SRC_ROOT}`")
    lines.append(f"- 模块数：`{len(modules)}`；函数/方法数：`{len(defs)}`")
    lines.append(f"- 模块导入边：`{len(import_edges)}`；模块调用边：`{len(call_edges)}`；Topic 通信边：`{len(topic_edges)}`")
    lines.append("")
    lines.append("## A. 模块总表")
    lines.extend(
        markdown_table(
            ["模块", "文件", "类数", "函数/方法数", "导入出度", "导入入度", "调用出度", "调用入度"],
            module_rows,
        )
    )
    lines.append("")
    lines.append("## B. 模块间通信总表（Import + Call）")
    lines.extend(markdown_table(["源模块", "目标模块", "Import 边数", "Call 边数"], comm_rows))
    lines.append("")
    lines.append("## C. 事件 Topic 通信总表（publish/subscribe/consume）")
    lines.extend(markdown_table(["模块", "操作", "Topic", "出现次数"], topic_rows))
    lines.append("")
    lines.append("## D. 函数/方法总表（全量）")
    lines.extend(markdown_table(["函数/方法", "模块", "文件", "行号", "类型"], func_rows))
    lines.append("")
    lines.append("## E. 当前结构问题总表（未收敛）")
    lines.extend(markdown_table(["ID", "类别", "问题", "证据", "影响", "来源"], arch_issue_rows))
    lines.append("")
    lines.append("## F. 历史问题与修复状态（issues_master）")
    lines.extend(markdown_table(["ID", "类别", "描述", "文件:行号", "严重程度", "状态"], fixed_issue_rows))
    lines.append("")
    lines.append("## G. 参考文档")
    lines.append("- `docs/architecture/MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN.md`")
    lines.append("- `docs/architecture/REFACTOR_BLUEPRINT_AI_ADVISORY.md`")
    lines.append("- `docs/architecture/TOP_LEVEL_DESIGN_AI_ADVISORY.md`")
    lines.append("- `issues_master.json`")
    lines.append("")

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"written: {OUTPUT}")


if __name__ == "__main__":
    main()
