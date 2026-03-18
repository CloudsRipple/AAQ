# TEST_PLAN

更新时间：2026-03-15

## 1. 测试金字塔设计

## 1.1 单元测试层
- 目标：核心逻辑快速回归，覆盖风险、执行、数据质量、状态持久化。
- 范围：
  - 风控：`tests/test_risk_engine.py`
  - 执行生命周期：`tests/test_execution_lifecycle.py`
  - 数据门禁：`tests/test_market_data_gate.py`
  - 状态存储：`tests/test_audit_and_memory_persistence.py` + `tests/test_fund_safety_core.py`
- 门槛：核心关键路径覆盖率总计 >= 85%（由 `scripts/coverage_gate.py` 强制）。

## 1.2 集成测试层
- 目标：验证“数据 -> 信号 -> 风控 -> 执行”全链路无断层。
- 场景：
  - `tests/test_integration_e2e.py` 覆盖完整路径。
  - `tests/test_ibkr_execution.py` 覆盖执行入口与策略输出衔接。

## 1.3 故障注入层（Chaos）
- 目标：在异常环境下验证系统降级行为与稳定性。
- 场景：
  - 断网与重试：`test_network_disconnect_retry_then_success`
  - 延迟与脏数据：`test_latency_and_dirty_data_block_trading`
  - 重启与去重：`test_restart_dedup_prevents_duplicate_submit`
  - DB 锁冲突：`test_db_lock_conflict_degrades_data_gate`
- 入口：`tests/test_chaos_resilience.py`

## 1.4 回放测试层（Replay）
- 目标：用历史注入事件重放行为稳定性。
- 场景矩阵：breaking_news / high_volatility / duplicate_event_dedup / unverified_stale_message / safety_mode_blocked。
- 入口：
  - 单测：`tests/test_replay.py`
  - 脚本：`python -m phase0.replay --mode all`

## 2. 质量门禁

## 2.1 本地门禁
- 全量测试：
  - `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`
- 覆盖率门禁：
  - `.venv/bin/python scripts/coverage_gate.py`
  - 失败条件：
    - 任一测试失败
    - 核心关键路径总覆盖率 < 85%

## 2.2 CI 门禁
- 工作流：`.github/workflows/ci.yml`
- 阻断策略：
  - 单元/集成/Chaos/Replay 任一步失败即失败
  - 覆盖率门禁失败则禁止合并

## 3. 产物与报告
- 覆盖率：`artifacts/coverage_report.json`、`artifacts/coverage_report.md`
- Chaos：`CHAOS_REPORT.md`
- 失败用例与修复建议：`FAILURE_CASES.md`
