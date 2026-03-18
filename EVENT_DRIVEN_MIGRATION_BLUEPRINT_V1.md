# EVENT_DRIVEN_MIGRATION_BLUEPRINT_V1

更新时间：2026-03-18  
范围：`/src/phase0`、`/scripts`、`/tests`、`pyproject.toml`  
目标：以“事件驱动新线”为唯一目标主线，规划旧实现的保留、迁移、兼容和删除路径，避免误删仍被新线依赖的核心能力。

## 1. 执行摘要

- 目标主线选型：事件驱动主线。
- 迁移原则：删旧壳层，不删旧核心。
- 当前判断：旧的 cycle/scheduler 线不是最终目标，但其中的 market_data、hard risk、execution、state_store 等能力仍是新主线的迁移底座。
- 当前禁止动作：禁止直接删除 `run_lane_cycle`、`run_lane_cycle_with_guard`、`execute_cycle`、`ibkr_execution.py`、`lanes/high.py`。
- 当前优先动作：先完成执行收口、总线统一、Ultra 真实事件化，再退役兼容壳层。

## 2. 两条线路的准确定义

## 2.1 当前可运行线（Legacy Cycle Line）

```text
phase0-health
  -> phase0.main:main
  -> app.health_check
  -> run_lane_cycle_with_guard
  -> run_lane_cycle
  -> strategies + ai + high + discipline
  -> ibkr_order_adapter

phase0-ibkr-execute
  -> execute_cycle
  -> run_lane_cycle
  -> risk_engine.evaluate_order_intents
  -> IbkrExecutionClient.submit_bracket_signal
```

特点：
- 可测试、可回放、可生成报告。
- 编排集中在 `lanes/__init__.py`。
- 兼容链路多，职责混合重。

## 2.2 目标主线（Event-Driven To-Be Line）

```text
market_data/feed workers
  -> ultra worker
  -> signal events
  -> low/high context + risk decision
  -> order intents
  -> execution worker
  -> state_store + observability
```

特点：
- 契约先行，分层单向依赖。
- 执行统一收口，不允许在 Subscriber 内自行补价格和重跑风控。
- Ultra 使用真实事件输入，不再依赖合成 tick。

## 3. 架构决策

## 3.1 保留什么

- 保留所有可复用的核心能力模块。
- 保留现有旧线作为兼容层，直到新线闭环。
- 保留 `execute_cycle` 背后的执行与状态能力，但要拆出“纯执行服务”。

## 3.2 删除什么

- 删除重复壳层、合成事件工具、反向依赖链路、旧调度入口。
- 删除的前提是：调用点已经切到新契约，测试和验证入口已替换。

## 3.3 不做什么

- 不在当前阶段引入新 alpha。
- 不在当前阶段重写整个系统。
- 不把“文档上的 To-Be”误当成“已经实现完毕”。

## 4. 文件级动作总表

| 文件 | 角色判断 | 动作 | 结论 |
|---|---|---|---|
| `src/phase0/market_data.py` | 新主线底座 | 保留 | 作为 `market_data` 层核心 |
| `src/phase0/strategies/loader.py` | 新主线底座 | 保留 | 作为 `signal_engine` 的策略装配器 |
| `src/phase0/lanes/high.py` | 新主线底座 | 保留 | 作为硬风控/仓位 sizing 内核 |
| `src/phase0/risk_engine.py` | 新主线底座 | 保留并扩展 | 作为统一 `risk_engine` 收口 |
| `src/phase0/ibkr_order_adapter.py` | 新主线底座 | 保留 | 作为 `OrderIntent -> BrokerPayload` 适配层 |
| `src/phase0/state_store.py` | 新主线底座 | 保留并增强 | 作为执行与风险状态事实存储 |
| `src/phase0/execution_lifecycle.py` | 新主线底座 | 保留 | 作为执行生命周期治理层 |
| `src/phase0/observability.py` | 新主线底座 | 保留 | 作为可观测性层 |
| `src/phase0/ai/ultra.py` | 新主线逻辑未完工 | 保留并重构 | 真实事件输入替换占位循环 |
| `src/phase0/ai/low.py` | 新主线逻辑可复用 | 保留并迁位 | 保留分析能力，弱化 daemon 身份 |
| `src/phase0/ai/high.py` | 新主线逻辑可复用 | 保留并迁位 | 保留评估能力，弱化 daemon 身份 |
| `src/phase0/ibkr_execution.py` | 核心+旧编排混合 | 拆分 | 提取纯执行服务，保留执行与对账 |
| `src/phase0/main.py` | 过渡入口 | 重写 | 改成事件驱动唯一入口，健康检查独立 |
| `src/phase0/app.py` | 旧健康壳层 | 兼容保留后退役 | 不再承担交易编排 |
| `src/phase0/lanes/__init__.py` | God module | 拆分 | 最终只保留 compat runner 或删除 |
| `src/phase0/lanes/ultra.py` | 合成事件工具 | 删除前迁移 | 测试/回放专用 fixture 替代 |
| `src/phase0/lanes/low_subscriber.py` | 反向依赖链路 | 删除 | Low 不应依赖 High 决策触发 |
| `src/phase0/lanes/low_engine.py` | 缓存与 daemon 混合 | 拆分或迁移 | 缓存入 store，daemon 并入 worker |
| `src/phase0/execution_subscriber.py` | 旧执行旁路 | 重写后保留名字或删除 | 改成仅消费 `OrderIntent` |
| `src/phase0/lanes/bus.py` | 两套总线并存 | 拆分语义 | 生产保留 `AsyncEventBus`，`InMemoryLaneBus` 仅测试 |
| `src/phase0/replay.py` | 验证入口 | 兼容保留后迁移 | 迁到新事件契约 |
| `src/phase0/non_ai_validation_report.py` | 验证入口 | 兼容保留后迁移 | 切到新入口 |
| `tests/test_lane_bus.py` 等旧线测试 | 旧契约测试 | 分阶段迁移 | 先保留，再补新线测试 |
| `pyproject.toml` | CLI 注册 | 更新 | 新增事件驱动主入口脚本 |

## 5. 哪些旧模块必须保留作为新线依赖

## 5.1 必须保留

### `src/phase0/market_data.py`
- 原因：已经具备 snapshot quality gate、calendar gate、snapshot registry 能力。
- 目标位置：`market_data` 层核心。

### `src/phase0/strategies/*`
- 原因：策略与因子注册已经相对清晰。
- 目标位置：`signal_engine` 层核心。

### `src/phase0/lanes/high.py`
- 原因：已经承担价格结构校验、冷却期、持仓期、风险预算、仓位 sizing、bracket 构造。
- 目标位置：`risk_engine` 的高频硬规则内核。

### `src/phase0/risk_engine.py`
- 原因：已经开始具备 `OrderIntent` 审批、position/open order 审批、fail-closed 风险处理能力。
- 目标位置：新主线的统一风险收口层。

### `src/phase0/ibkr_order_adapter.py`
- 原因：新线仍需要 broker payload 适配器。

### `src/phase0/ibkr_execution.py`
- 原因：对账、幂等、提交、执行回报处理能力已经在这里收敛。
- 但禁止继续把它当“信号编排入口”使用。

### `src/phase0/state_store.py`
- 原因：新线必须依赖事实状态存储，不能退回纯内存去重。

## 5.2 只保留逻辑，不保留现有组织方式

### `src/phase0/ai/ultra.py`
- 保留 `UltraSignal`、sentinel、规则/向量能力。
- 不保留当前 `start_ultra_engine` 的占位运行方式。

### `src/phase0/ai/low.py`
- 保留 Low 分析能力。
- 不保留“周期性发 `low.analysis`”作为最终编排方式。

### `src/phase0/ai/high.py`
- 保留 High 评估能力。
- 不保留“订阅 `ultra.signal` 后直接发布 `high.decision`”作为最终唯一权威路径。

## 6. 哪些旧模块可以删

## 6.1 确认可删除，但必须先完成前置迁移

### `src/phase0/lanes/ultra.py`
- 当前职责：合成 event，主要服务旧链路和兼容入口。
- 删除前提：
  - `run_lane_cycle_with_guard` 不再依赖 `emit_event`
  - replay 有独立 fixture builder
  - 旧健康检查入口不再伪造交易事件

### `src/phase0/lanes/low_subscriber.py`
- 当前职责：消费 `high.decision` 再生成 `low.analysis`
- 删除理由：依赖方向错误，Low 不应由 High 反向触发。

### `src/phase0/app.py`
- 当前职责：旧的健康检查壳层
- 删除前提：
  - `phase0-health` 指向新诊断入口
  - 测试与报告不再通过 `health_check -> run_lane_cycle_with_guard`

## 6.2 不建议整文件删除，只建议拆分

### `src/phase0/ibkr_execution.py`
- 禁止直接删。
- 应拆为：
  - `execution_service.py`
  - `execution_client_ibkr.py`
  - `execution_entry_compat.py`

### `src/phase0/lanes/__init__.py`
- 禁止直接删。
- 应拆为：
  - `compat_cycle_runner.py`
  - `signal_pipeline_service.py`
  - `risk_pipeline_service.py`

## 7. 当前删线冲突清单

## 7.1 如果现在删除旧 cycle runner，会坏掉的地方

### 入口冲突
- `phase0-health = "phase0.main:main"` 仍依赖旧切换逻辑。
- `scripts/healthcheck.py` 仍依赖 `phase0.main:main`。
- `phase0-ibkr-execute` 的 `execute_cycle` 仍内部调用 `run_lane_cycle`。

### 验证冲突
- `replay.py` 仍依赖 `run_lane_cycle_with_guard`。
- `non_ai_validation_report.py` 仍依赖 `run_lane_cycle_with_guard` 和 `phase0.main`。

### 测试冲突
- `tests/test_lane_bus.py`
- `tests/test_app_health.py`
- `tests/test_market_data_gate.py`
- `tests/test_ultra_queue_wiring.py`
- `tests/test_audit_and_memory_persistence.py`

这些测试的断言语义都建立在旧 cycle runner 之上。

## 7.2 如果现在删除旧执行收口，会坏掉的地方

- `execution_subscriber.py` 当前还没有新的统一执行接口可以调用。
- `tests/test_ibkr_execution.py`
- `tests/test_execution_lifecycle.py`
- `tests/test_fund_safety_core.py`
- `tests/test_integration_e2e.py`
- `tests/test_observability.py`

这些都依赖 `execute_cycle` 或其背后的执行状态机。

## 8. 修复 List（按迁移优先级）

## P0：先把新主线补成闭环

### P0-1 提取统一执行服务
- 目标：从 `ibkr_execution.py` 提取纯执行接口。
- 新接口建议：
  - `reconcile_execution_runtime(config, client_factory)`
  - `execute_order_intents(intents, config, client_factory)`
- 删除风险消除：让事件驱动执行器不再依赖 `run_lane_cycle()`。

### P0-2 重写 `execution_subscriber.py`
- 当前问题：自己拼价格、自己查状态、自己再跑一遍 `evaluate_event()`。
- 目标行为：只消费 `OrderIntent`，调用统一执行服务，写回 `ExecutionReport`。

### P0-3 补齐 Ultra 真实事件输入
- 当前问题：`start_ultra_engine` 为占位循环。
- 目标行为：对接真实 ticker/news feed，产出标准化 `SignalEvent`。
- 同时停用 `_build_ultra_signal_snapshot()` 作为生产信号来源。

### P0-4 收敛事件总线
- 目标：生产只保留异步总线。
- 处理方式：
  - `AsyncEventBus` 用于 runtime
  - `InMemoryLaneBus` 限定为 replay/test adapter

## P1：把旧壳层降为兼容层

### P1-1 拆分 `main.py`
- 新增：
  - `phase0-daemon`
  - `phase0-healthcheck`
- 旧的 `phase0-health` 暂时兼容，内部转发到新诊断入口。

### P1-2 退役 `app.health_check -> run_lane_cycle_with_guard`
- 健康检查改为：
  - 依赖探活
  - worker 状态
  - bus lag
  - reconcile 状态
  - 风险模式
- 不再伪造交易事件做“健康检查”。

### P1-3 退役 `lanes/ultra.py:emit_event`
- replay 使用 fixture builder
- 测试使用 deterministic event factory

### P1-4 退役 `low_subscriber.py`
- Low 分析结果改为：
  - 定时更新到 state store
  - 或由 signal/risk 阶段只读拉取

## P2：兼容与清理

### P2-1 抽离 `compat_cycle_runner`
- 让 `run_lane_cycle` 和 `run_lane_cycle_with_guard` 成为单独兼容模块。

### P2-2 迁移 replay 和 validation
- replay 改为基于新事件契约回放。
- validation report 改为同时校验：
  - worker 存活
  - reconcile 成功
  - event flow 通
  - execution dry-run 通

### P2-3 清理测试分层
- 旧线测试标记为 compat
- 新线测试建立：
  - `test_ultra_worker.py`
  - `test_execution_worker.py`
  - `test_event_contracts.py`
  - `test_daemon_bootstrap.py`

## 9. 推荐迁移顺序

## 阶段 1：执行收口
- 先提取执行服务。
- 再让 `execution_subscriber` 调新服务。
- 保持旧 `execute_cycle` 可用，但内部改为复用新服务。

## 阶段 2：Ultra 真实事件化
- 接 ticker/news feed。
- 让 Ultra 产出标准化信号。
- 保留旧 snapshot Ultra 仅用于测试兼容。

## 阶段 3：Risk 收口
- 让 High/Low 的结果进入统一风险契约。
- 不再通过 `low_subscriber` 做反向补算。

## 阶段 4：入口收口
- 新建 daemon 主入口。
- 旧 health 入口降级为只读诊断。
- 移除 `LANE_SCHEDULER_ENABLED` 双模切换。

## 阶段 5：兼容层退役
- replay/validation/tests 全部迁完。
- 删除 `app.py` 交易编排职责。
- 删除 `lanes/ultra.py` 与 `low_subscriber.py`。

## 10. 目标调用图（V1）

```text
phase0-daemon
  -> bootstrap runtime
  -> reconcile_execution_runtime
  -> start_market_data_worker
  -> start_ultra_worker
  -> start_signal_engine_worker
  -> start_risk_worker
  -> start_execution_worker
  -> observability/reporting

start_ultra_worker
  -> publish SignalEvent

start_signal_engine_worker
  -> enrich with strategy + low context
  -> publish CandidateSignal / IntentProposal

start_risk_worker
  -> lanes/high.py hard rules
  -> risk_engine.evaluate_order_intents
  -> publish OrderIntent

start_execution_worker
  -> execute_order_intents
  -> save execution reports
  -> update system state
```

## 11. 验收条件

## 11.1 新主线最小验收
- daemon 启动后无旧 scheduler 分支参与主交易逻辑。
- Ultra 有真实事件输入，不依赖合成 tick。
- execution worker 不再自己推导 stop/target/仓位。
- 所有下单统一经过同一执行收口。
- risk decision 与 execution report 可通过 trace/idempotency 串联。

## 11.2 兼容退役验收
- `replay` 不再调用 `run_lane_cycle_with_guard`
- `non_ai_validation_report` 不再依赖 `phase0.main` 双模逻辑
- `phase0-health` 不再触发伪交易事件
- 删除 `low_subscriber.py` 后无反向依赖报错
- 删除 `lanes/ultra.py` 后旧测试已全部迁移

## 12. 本蓝图的落地结论

- 事件驱动新线是对的，应继续推进。
- 旧线不是“全删”，而是“拆出核心、退役壳层”。
- 当前第一优先级不是 UI、不是新策略，而是：
  1. 执行收口
  2. Ultra 真实事件化
  3. 总线与契约统一
  4. 兼容入口退役

- 推荐从 `P0-1 提取统一执行服务` 开始实施，因为这是删除旧线风险最低、收益最大的第一刀。
