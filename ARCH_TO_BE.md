# ARCH_TO_BE（目标架构设计）

更新时间：2026-03-15  
范围：仅架构设计，不含实现代码改动。  
目标：构建“可维护、可审计、可恢复”的交易系统目标架构（To-Be）。

## 1. 设计目标与边界

## 1.1 目标
- 可维护：模块职责单一、依赖方向单向、变更影响面可控。
- 可审计：全链路事件可追踪，订单与风控决策可复盘。
- 可恢复：崩溃/断网/重启后可先对账再交易，避免重复下单与状态错位。

## 1.2 非目标
- 不在本阶段引入新策略 alpha 逻辑。
- 不在本阶段追求超低延迟 HFT 优化。
- 不在本阶段改动业务参数语义（风险阈值、策略阈值保持配置兼容）。

## 1.3 设计依据（现状痛点）
- 内存去重导致重启后可能重复事件：[bus.py:L30-L46](file:///Users/cloudsripple/Documents/trae_projects/AAQ/src/phase0/lanes/bus.py#L30-L46)
- 执行链缺幂等账本与重启对账闭环：[ibkr_execution.py:L97-L101](file:///Users/cloudsripple/Documents/trae_projects/AAQ/src/phase0/ibkr_execution.py#L97-L101)
- 行情失败回退默认快照存在伪数据风险：[__init__.py:L580-L591](file:///Users/cloudsripple/Documents/trae_projects/AAQ/src/phase0/lanes/__init__.py#L580-L591)

## 2. 领域分层（六层）

## 2.1 分层定义

### market_data
- 职责：行情、新闻、交易日历、时钟统一接入与质量校验。
- 输入：外部数据源（IBKR/yfinance/本地快照）。
- 输出：标准化 `MarketSnapshot`、`NewsBatch`、`DataHealth`。
- 禁止：直接触发下单、直接写订单状态。

### signal_engine
- 职责：策略计算与信号生成（仅表达交易意图，不表达可执行性）。
- 输入：`MarketSnapshot`、`NewsBatch`、策略配置。
- 输出：`SignalEvent`（可多策略并行产出）。
- 禁止：直接调用券商 API、直接落订单状态。

### risk_engine
- 职责：风险校验、仓位计算、纪律门控、风险降级策略执行。
- 输入：`SignalEvent`、账户状态、仓位状态、风险配置、系统状态。
- 输出：`RiskDecision` + `OrderIntent`（仅在 approved 时产出）。
- 禁止：直接发单。

### execution_engine
- 职责：下单编排、回报处理、对账、幂等提交、重试与重连。
- 输入：`OrderIntent`、系统状态、会话状态。
- 输出：`ExecutionReport`、`OrderStateTransition`、`ReconcileResult`。
- 禁止：修改策略信号与风险规则。

### state_store
- 职责：状态持久化与读取抽象（订单账本、持仓账本、幂等索引、审计日志）。
- 输入：各层产生的“事实事件”。
- 输出：一致性读模型（订单、持仓、风控计数器、系统状态）。
- 禁止：调用业务层逻辑。

### observability
- 职责：日志、指标、告警、审计查询、追踪关联。
- 输入：各层事件与状态转移。
- 输出：结构化日志、指标流、告警事件、审计报表。
- 禁止：反向控制业务决策（只读+告警）。

## 2.2 依赖方向（强约束）
- 允许依赖：`market_data -> signal_engine -> risk_engine -> execution_engine -> state_store -> observability`
- 横切依赖：各层可写入 `observability`，但不可反向调用业务层。
- 禁止跨层：`signal_engine` 禁止直接调用 `execution_engine`；`execution_engine` 禁止直接调用 `signal_engine`。

## 2.3 模块边界示意

```text
[market_data] --> [signal_engine] --> [risk_engine] --> [execution_engine]
       |                  |                 |                    |
       +------------------+-----------------+--------------------+
                                  |
                              [state_store]
                                  |
                            [observability]
```

## 3. 契约定义（事件模型）

## 3.1 SignalEvent
- 语义：策略层“可交易想法”，不代表可执行。
- 必填字段：
  - `event_id`（全局唯一）
  - `trace_id`（链路追踪）
  - `strategy_id`、`symbol`、`side`
  - `signal_strength`、`confidence`
  - `market_ts`（数据时间戳，UTC）
  - `generated_at`（事件生成时间，UTC）
  - `feature_digest`（特征哈希，用于审计复现）
- 错误语义：
  - `SIGNAL_INVALID_SCHEMA`
  - `SIGNAL_STALE_DATA`
  - `SIGNAL_DUPLICATED`

## 3.2 RiskDecision
- 语义：风控层对 `SignalEvent` 的可执行性判定。
- 必填字段：
  - `decision_id`
  - `trace_id`、`signal_event_id`
  - `approved`（bool）
  - `reasons`（拒绝或调整原因列表）
  - `risk_snapshot`（权益、回撤、暴露、冷却状态）
  - `computed_limits`（单笔风险预算、总暴露上限）
- 错误语义：
  - `RISK_INPUT_MISSING`
  - `RISK_POLICY_VIOLATION`
  - `RISK_ENGINE_UNAVAILABLE`

## 3.3 OrderIntent
- 语义：执行层可消费的“意图订单”，由风控批准生成。
- 必填字段：
  - `intent_id`（幂等键，稳定生成）
  - `trace_id`、`decision_id`
  - `symbol`、`side`、`quantity`
  - `order_type`、`limit_price`、`stop_price`（按类型必填）
  - `time_in_force`
  - `protection`（止盈/止损保护单要求）
  - `intent_version`（版本化契约）
- 错误语义：
  - `INTENT_INVALID_SCHEMA`
  - `INTENT_NOT_APPROVED`
  - `INTENT_IDEMPOTENCY_CONFLICT`

## 3.4 ExecutionReport
- 语义：执行层对提交/回报/状态转移的事实记录。
- 必填字段：
  - `report_id`
  - `trace_id`、`intent_id`
  - `broker`、`broker_order_id`、`broker_status`
  - `local_status`（本地状态机状态）
  - `filled_qty`、`avg_fill_price`
  - `occurred_at`、`received_at`
  - `error_code`、`error_message`（失败时必填）
- 错误语义：
  - `EXEC_SUBMIT_TIMEOUT`
  - `EXEC_BROKER_REJECTED`
  - `EXEC_STATE_MISMATCH`
  - `EXEC_RECONCILE_REQUIRED`

## 4. 每层输入/输出与错误语义

| 层 | 输入 | 输出 | 可恢复错误 | 不可恢复错误 |
|---|---|---|---|---|
| market_data | 源数据连接、symbol列表、时钟 | snapshot/news/health | `MD_TIMEOUT` `MD_PARTIAL` | `MD_SCHEMA_BROKEN` |
| signal_engine | snapshot/news/策略配置 | SignalEvent[] | `SE_PLUGIN_FAIL` | `SE_CONTRACT_BREAK` |
| risk_engine | SignalEvent+状态 | RiskDecision/OrderIntent | `RE_TEMP_UNAVAILABLE` | `RE_POLICY_CORRUPTED` |
| execution_engine | OrderIntent | ExecutionReport/状态转移 | `EE_RETRYABLE_IO` | `EE_IDEMPOTENCY_BROKEN` |
| state_store | 事实事件 | 一致性读模型 | `SS_LOCK_RETRY` | `SS_DATA_CORRUPTION` |
| observability | 全层事件 | 日志/指标/告警 | `OBS_BACKPRESSURE` | `OBS_PIPELINE_BROKEN` |

统一错误处理原则：
- 可恢复错误：进入重试/退避/降级路径，并打 `WARN` 告警。
- 不可恢复错误：触发系统状态转 `HALTED`，阻断新单，保留减仓能力。

## 5. 状态机设计

## 5.1 订单状态机

状态集合：`NEW -> SENT -> ACK -> PARTIAL -> FILLED`  
终止分支：`CANCELED`、`REJECTED`

```text
NEW -> SENT -> ACK -> PARTIAL -> FILLED
                 |         |
                 v         v
              REJECTED   CANCELED
ACK ---------> FILLED
SENT --------> REJECTED
PARTIAL -----> CANCELED
```

关键不变量：
- `intent_id` 全局幂等，同一 `intent_id` 仅允许一次“首次提交”。
- 状态单调前进，禁止回退（除重建时通过 reconcile 修正并记录修正事件）。
- 任一 `FILLED` 必须有对应 `ExecutionReport` 和成交明细。

## 5.2 系统运行状态机

状态集合：`BOOTSTRAP / RECONCILE / RUNNING / DEGRADED / HALTED`

```text
BOOTSTRAP -> RECONCILE -> RUNNING
                    |         |
                    v         v
                 HALTED    DEGRADED
                               |
                               v
                            RUNNING
DEGRADED -> HALTED
RECONCILE -> HALTED
```

转移规则：
- `BOOTSTRAP -> RECONCILE`：配置加载完成、依赖探活通过最低门槛。
- `RECONCILE -> RUNNING`：订单/持仓/成交对账一致且无未决冲突。
- `RUNNING -> DEGRADED`：数据断流、网关波动、风险服务降级可控。
- `* -> HALTED`：幂等冲突、状态不一致不可修复、风控不可用且无安全降级。

## 6. 故障降级策略（必须可执行）

## 6.1 数据断流（market_data）
- 当前行为风险：回退默认快照可能产生伪信号（见现状证据）。
- To-Be 行为：
  - 连续 N 次拉取失败 -> 系统转 `DEGRADED`
  - 禁止开新仓，仅允许平仓/减仓
  - 超过阈值仍失败 -> 转 `HALTED`
- 需要能力：数据健康分级、快照版本标记、信号冻结开关。

## 6.2 网关断连（execution_engine）
- To-Be 行为：
  - 即刻停止新意图提交
  - 启动退避重连（指数退避+上限）
  - 重连成功后先 `RECONCILE` 再恢复 `RUNNING`
- 需要能力：连接状态机、断线期间待处理意图队列、重放防重。

## 6.3 DB 锁冲突（state_store）
- To-Be 行为：
  - 读写冲突进入短重试（抖动退避）
  - 超过重试预算 -> `DEGRADED` 并阻断新单
  - 长时间不可用 -> `HALTED`
- 需要能力：事务边界统一、写入幂等、死锁告警。

## 6.4 风控不可用（risk_engine）
- To-Be 行为：
  - 禁止新开仓（fail-closed）
  - 允许已有持仓执行保护性减仓/止损
  - 风控恢复后必须先重放未决 `SignalEvent` 并重新判定
- 需要能力：风控旁路开关（仅减仓模式）、风险服务心跳。

## 7. 可维护性规则（强制）

## 7.1 模块边界
- 每层只暴露 `service interface + event contract`，禁止暴露内部数据结构。
- 业务逻辑不得直接访问他层私有存储。

## 7.2 依赖方向
- 仅允许“上层依赖下层接口，不依赖实现”。
- state_store 由接口注入，不允许业务层直接 `sqlite3.connect`。

## 7.3 禁止跨层调用
- `signal_engine` 禁止导入 `execution_engine`。
- `execution_engine` 禁止导入策略模块。
- `observability` 禁止回调业务层。

## 7.4 配置管理原则
- 配置分层：`static config`（版本化）+ `runtime switches`（可热更新）+ `secret`（外置托管）。
- 所有默认值必须区分“开发默认”与“生产默认”；生产模式禁止危险回退（如默认快照交易）。
- 配置变更必须输出 `ConfigChangeAudit` 事件。

## 7.5 审计与可追踪原则
- 每个 `trace_id` 必须可串联：SignalEvent -> RiskDecision -> OrderIntent -> ExecutionReport。
- 每个状态转移必须持久化并可重放。
- 告警必须可回链到具体 `trace_id` 与 `intent_id`。

## 8. 最小可行改造目标（架构级）
- 先建立契约与状态机，再迁移实现。
- 先保证“不会重复下单/不会伪数据交易/重启可恢复”，再做性能优化。
- 全量切换前必须保留兼容桥接层（Legacy Adapter），以支持分阶段灰度。

## 9. 与现有仓库的映射建议（非实现）
- `market_data`：从 [lanes.__init__.py](file:///Users/cloudsripple/Documents/trae_projects/AAQ/src/phase0/lanes/__init__.py) 中行情加载相关逻辑拆分为独立服务。
- `risk_engine`：以 [high.py](file:///Users/cloudsripple/Documents/trae_projects/AAQ/src/phase0/lanes/high.py) 为核心，增加状态输入与错误分级。
- `execution_engine`：以 [ibkr_execution.py](file:///Users/cloudsripple/Documents/trae_projects/AAQ/src/phase0/ibkr_execution.py) 为核心，补幂等与 reconcile。
- `state_store`：在 [audit.py](file:///Users/cloudsripple/Documents/trae_projects/AAQ/src/phase0/audit.py) 基础上扩展订单/持仓账本。
- `observability`：统一现有日志与报告输出，接入统一指标与告警通道。
