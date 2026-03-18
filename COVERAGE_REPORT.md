# 覆盖率报告

数据来源：`artifacts/coverage_report.json`（由 `scripts/coverage_gate.py` 生成）  
执行时间：2026-03-15

- tests_ok: `true`
- tests_run: `92`
- threshold: `85.00%`
- core_total_percent: `87.74%`
- gate_passed: `true`

| 模块 | 可执行行 | 已覆盖行 | 覆盖率 |
|---|---:|---:|---:|
| phase0/ibkr_execution.py | 83 | 74 | 89.16% |
| phase0/risk_engine.py | 79 | 70 | 88.61% |
| phase0/market_data.py | 134 | 117 | 87.31% |
| phase0/execution_lifecycle.py | 22 | 19 | 86.36% |
| phase0/state_store.py | 49 | 42 | 85.71% |

结论：
- 核心关键路径总覆盖率满足 `>=85%` 门禁。
- 核心模块关键路径覆盖率均达到 85% 及以上。
