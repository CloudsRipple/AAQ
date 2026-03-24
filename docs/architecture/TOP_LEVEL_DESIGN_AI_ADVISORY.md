# Top-Level Design: Quant Core + AI Advisory Plane

更新时间：2026-03-18

## 1. 目标

本设计将当前系统重构为：

- 一个运行宿主（Runtime Host）
- 一个统一决策内核（Quant Decision Kernel）
- 三个通道守护进程（Low / Ultra / High）
- 一个受治理的 AI/Agent 建议平面（AI Advisory Plane）
- 一组清晰的 Stores 和 Adapters

核心判断：

- 系统不是 AI-native trading system
- 系统是 traditional quant core with bounded AI advisory
- AI 只能建议，不拥有交易主权

## 2. 设计原则

1. 单一主路径
   市场数据、信号、决策、风控、执行必须只有一条权威路径。

2. 三通道不是三套系统
   Low、Ultra、High 是不同时间尺度的 worker，不是独立交易引擎。

3. High 是唯一决策收口点
   只有 High 可以形成 `TradeDecision`。

4. AI 是能力，不是骨架
   LLM/agent 只做解释、参数建议、风险覆盖，不负责最终交易动作。

5. 风控与执行必须可脱离 AI 独立工作
   任意时刻关闭 AI，系统仍必须保持可运行、可回放、可审计。

6. 硬边界必须在 LLM 外部
   kill switch、market access control、exposure limit、drawdown limit、session guard 必须由规则核强制执行。

## 3. 非目标

- 不在本阶段做微服务拆分
- 不让 LLM 直接生成下单动作
- 不让 agent 获得 broker 直接控制权
- 不让 AI 修改硬风控参数

## 4. 顶层架构

```text
Runtime Host
  ├─ Supervisor
  ├─ Scheduler
  ├─ Health / Replay / Validation Jobs
  └─ Observability bootstrap

Quant Decision Kernel
  ├─ Internal Event Bus
  ├─ Coordinator
  ├─ Contract Registry
  └─ Policy Snapshot

Lane Daemons
  ├─ Low Lane Daemon   -> produce LowContext
  ├─ Ultra Lane Daemon -> produce UltraSignal
  └─ High Lane Daemon  -> consume LowContext + UltraSignal -> produce TradeDecision

Core Services
  ├─ MarketDataService
  ├─ RiskService
  ├─ ExecutionService
  ├─ PortfolioService
  └─ ObservabilityService

AI Advisory Plane
  ├─ ContextAnnotator
  ├─ EventInterpreter
  ├─ RiskAdjuster
  ├─ OfflineResearchAgent
  └─ OnlineAdvisoryAgent

Governance Plane
  ├─ ParameterRegistry
  ├─ AdjustmentValidator
  ├─ EnvelopeEnforcer
  ├─ ApprovalPolicy
  └─ AdjustmentAudit

Infra
  ├─ Stores
  └─ Adapters
```

## 5. 三通道职责

### 5.1 Low Lane

职责：

- 生成慢变量上下文
- 维护 regime、sector bias、macro context、slow committee summary

输出：

- `LowContext`

禁止：

- 直接下单
- 直接修改 broker 状态
- 直接调用 ExecutionService

### 5.2 Ultra Lane

职责：

- 处理快变量事件
- 识别价格异动、成交量异常、新闻事件、异常信号

输出：

- `UltraSignal`

禁止：

- 直接给出最终交易批准
- 直接调用 RiskService / ExecutionService

### 5.3 High Lane

职责：

- 汇聚 `LowContext`、`UltraSignal`、`MarketSnapshot`、`PortfolioState`
- 形成唯一的 `TradeDecision`

输出：

- `TradeDecision`

禁止：

- 直接操作 broker adapter
- 跳过 RiskService

## 6. AI Advisory Plane

### 6.1 AI 的定位

AI 只做三类事情：

1. Interpret
   将文本、新闻、叙事、上下文转为结构化特征或标签。

2. Propose
   在既定 envelope 内提出参数调整建议。

3. Overlay
   生成临时风险覆盖，如观察名单、短时冻结、新闻告警升级。

### 6.2 AI 不允许做的事

- 直接输出最终买卖动作
- 直接决定下单数量
- 直接调用 broker
- 直接写核心状态表
- 直接修改硬风控参数

### 6.3 AI 输出契约

只保留两类一级 AI 输出：

- `AdjustmentProposal`
- `RiskOverlay`

#### AdjustmentProposal

字段：

- `proposal_id`
- `scope`
- `target_param`
- `current_value`
- `suggested_value`
- `min_allowed`
- `max_allowed`
- `confidence`
- `reason`
- `evidence_refs`
- `ttl_seconds`
- `mode`

#### RiskOverlay

字段：

- `overlay_id`
- `scope`
- `overlay_type`
- `effect`
- `severity`
- `expires_at`
- `reason`
- `evidence_refs`

## 7. 参数治理

### 7.1 参数分级

#### Hard Params

永远不允许 AI 在线改动。

示例：

- max drawdown
- max total exposure
- kill switch
- session guard
- broker routing rules

#### Soft Params

允许 AI 在 envelope 内调整。

示例：

- risk multiplier
- stop loss band
- take profit boost
- cooldown extension
- signal weight bias
- news threshold

#### Research Params

只能由离线 agent 研究建议，再经人工评审进入版本化配置。

示例：

- strategy enable list
- factor definitions
- sizing formula
- portfolio construction logic

### 7.2 AI 模式

- `OFF`
- `SHADOW`
- `BOUNDED_AUTO`
- `HUMAN_APPROVAL`

默认要求：

- 线上默认 `SHADOW`
- 研究或回放环境才允许 `BOUNDED_AUTO`

### 7.3 从 SHADOW 升级到 BOUNDED_AUTO 的条件

升级只允许发生在 `paper` 环境。

`real money / production` 环境在当前阶段不允许进入 `BOUNDED_AUTO`。

最少运行门槛：

- 连续 `20` 个交易日 paper 运行
- 最近 `10` 个交易日无中断
- 至少 `100` 笔非 dry-run 执行尝试
- 至少 `30` 笔已闭环的 paper 交易可用于统计胜率

最低指标门槛：

- 最近 `30` 笔闭环 paper 交易胜率 `>= 55%`
- paper 期间滚动最大回撤 `<= 硬回撤阈值的 50%`
- 执行失败率 `<= 1.0%`
- 最近 `10` 个交易日 `critical` 告警数量必须为 `0`
- 最近 `10` 个交易日不得出现重复单风险
- 最近 `10` 个交易日不得因执行链问题进入 `HALTED` 或 `DEGRADED`

硬约束：

- 未完成闭环胜率统计时，不允许升级
- 未消除 execution 阶段的重复 high/risk 评估时，不允许升级
- 未建立 proposal 审计和 TTL 回放机制时，不允许升级

审批规则：

- 当前阶段不允许自动升级
- 系统只能生成“升级建议”
- `SHADOW -> BOUNDED_AUTO` 必须经过人工确认
- 人工审批只允许把 paper 环境切换到 `BOUNDED_AUTO`

## 8. Governance Plane

Governance Plane 负责把 AI 输出转化为可控行为。

### 8.1 组件

#### ParameterRegistry

定义每个可调参数的：

- 所属域
- 默认值
- 最小值
- 最大值
- 允许模式
- 是否需要人工审批

#### AdjustmentValidator

检查：

- schema 合法性
- 建议值是否越界
- 证据是否完整
- mode 是否允许
- ttl 是否合法

#### EnvelopeEnforcer

强制截断到批准边界内。

#### ApprovalPolicy

决定当前 proposal 是：

- reject
- shadow only
- bounded auto
- human approval required

#### AdjustmentAudit

记录：

- 原值
- 建议值
- 最终生效值
- 触发原因
- 时间戳
- trace_id
- operator / model identity

### 8.2 AdjustmentProposal 生效流程

固定状态机：

`GENERATED -> INTAKE_VALIDATED -> REGISTRY_BOUND -> POLICY_VALIDATED -> {REJECTED | SHADOWED | PENDING_HUMAN | APPROVED_AUTO} -> AUDITED -> APPLIED -> {EXPIRED | REVOKED}`

处理步骤：

1. `ContextAnnotator / EventInterpreter / RiskAdjuster` 只能产出 `AdjustmentProposal`
2. `advisory/contracts.py` 做 schema 校验和字段完整性校验
3. `ParameterRegistry` 校验 `target_param` 是否存在，并确认参数属于 `SOFT`
4. `AdjustmentValidator` 校验证据完整性、TTL、mode、系统状态、proposal 去重状态
5. `EnvelopeEnforcer` 将建议值截断到允许边界内；被截断的 proposal 不允许自动生效
6. `ApprovalPolicy` 根据当前 mode 决定 `reject / shadow only / bounded auto / human approval required`
7. 需要人工审批的 proposal 进入人工审批队列，并记录 `operator_id / approved_at / approved_value`
8. `AdjustmentAudit` 必须先于参数生效落库；审计失败时一律降级为 `SHADOW_ONLY`
9. `PolicySnapshotApplicator` 只把已批准 proposal 写入 runtime policy snapshot，不直接写策略代码或 broker 状态
10. `Expiry/Revoke Job` 在 TTL 到期后自动撤销 overlay，并回退到前一有效值或 baseline

强制规则：

- AI 失败、超时、非法 JSON、解析失败时，默认行为是 `NO_PROPOSAL`
- `AdjustmentProposal` 不得直接生成 `TradeDecision`
- `AdjustmentProposal` 不得跳过 `RiskService`
- `SHADOWED` proposal 必须完整审计，但不得改变运行参数
- 系统处于 `RECOVERING`、`HALTED` 或关键 store damaged 时，proposal 最多只能 `SHADOWED`
- 重启恢复时，只允许从审计 store 回放 `APPLIED` 且未过期的 proposal

## 9. 统一主路径

```text
MarketData -> LowContext
MarketData + EventStream -> UltraSignal
LowContext + UltraSignal + PortfolioState + MarketSnapshot -> High
High -> TradeDecision
TradeDecision -> RiskService
RiskService -> OrderIntent
OrderIntent -> ExecutionService
ExecutionService -> BrokerAdapter
Broker reports -> Stores -> Observability
```

要求：

- 这条路径必须是唯一权威路径
- 任何 event-driven runtime、replay、health mode 都只能复用这条路径
- 禁止在 execution 阶段反向拼装 high event 再次评估

## 10. Runtime Host

Runtime Host 负责：

- daemon 生命周期
- scheduler
- health checks
- replay jobs
- validation jobs
- observability bootstrap

Runtime Host 不负责：

- 交易逻辑
- 风控计算
- 参数调整决策

### 10.1 Lane Daemon 的触发频率和数据新鲜度要求

#### Low Lane

- 默认每 `60` 分钟运行一次
- 开盘前执行一次强制刷新
- 收到明确宏观事件时允许即时补跑
- `LowContext` 目标年龄 `<= 2` 小时
- `LowContext` 硬 TTL 为 `6` 小时
- 单次运行 `p95 <= 90` 秒，硬上限 `5` 分钟

降级规则：

- 超过 `90` 秒只告警，保留本轮执行
- 超过 `5` 分钟中止本轮，继续使用 last-good context
- 超过 `6` 小时无有效 context 时，High 改用 neutral context，不等待 Low 恢复

#### Ultra Lane

- 默认 `1` 秒心跳
- tick / news 到达时立即触发，不等待下一轮
- 输入事件进入 worker 到 `UltraSignal` 发布的 `p95 <= 1.2` 秒
- 硬上限 `3` 秒
- 可用于交易的事件年龄必须 `<= 10` 秒
- `10-60` 秒的事件只允许观察和告警，不得触发开仓
- `> 60` 秒的事件直接丢弃

降级规则：

- 超过 `1.2` 秒记录 `ULTRA_LAGGING`
- 超过 `3` 秒或事件过旧时，Ultra 失去开仓触发权
- 上游市场数据同时退化时，强制 `allow_opening=false`

#### High Lane

- 纯事件驱动
- 每收到一条有效 `UltraSignal` 立即处理
- 额外保留 `2` 秒健康心跳，仅用于 backlog 检查，不参与决策
- `UltraSignal` 年龄必须 `<= 10` 秒
- `Portfolio/OpenOrders` 状态必须 `<= 10` 秒
- `MarketSnapshot` 必须 `<= 180` 秒
- `LowContext` 目标年龄 `<= 2` 小时，硬 TTL `6` 小时
- 从 `UltraSignal` 到 `TradeDecision` 的 `p95 <= 800` 毫秒
- 硬上限 `2` 秒

降级规则：

- High 不允许为了等待 AI/advisory 而阻塞主决策
- advisory 超时后直接旁路，切到 rule-only
- 超过 `2` 秒或关键输入超鲜度上限时，High 对开仓 `fail-closed`
- 降级时只允许平仓、减仓、撤单、kill-switch

## 11. Stores 和 Adapters

### 11.1 Stores

拆分为逻辑上独立的 store：

- `runtime_store`
- `lane_context_store`
- `execution_store`
- `risk_store`
- `adjustment_audit_store`
- `alert_store`

短期可以继续共享一个 SQLite 文件，但代码边界必须分开。

### 11.2 Adapters

外部 IO 只允许出现在 adapters：

- broker adapter
- llm adapter
- market data adapter

### 11.3 系统重启后的状态恢复顺序

重启开始时，系统必须先进入：

- `system_status=RECOVERING`
- `send_enabled=false`
- `opening_allowed=false`
- `ai_adjustment_mode=SHADOW`

固定恢复顺序：

1. 加载静态配置和 contracts，构建 baseline policy snapshot
2. 对所有 store 执行健康检查
3. 先恢复 `runtime_store`
4. 再恢复 `execution_store`
5. 只有 `runtime_store + execution_store` 健康时，才允许执行 broker reconcile
6. reconcile 成功后，回写 `execution_store` 和 `runtime_store`
7. 只有在 reconcile 成功后，才允许回放 `adjustment_audit_store` 中未过期的 `APPLIED` proposal
8. 然后恢复 `risk_store`
9. 然后恢复 `lane_context_store`
10. 最后恢复 `alert_store`
11. 所有前置条件满足后，才允许打开 `execution send gate`

store 健康检查至少包括：

- 可打开
- schema / version 正确
- 必需表存在
- 关键 bootstrap 记录可读
- SQLite `quick_check` 通过
- 关键 JSON 行可解析

ready 条件：

- `runtime_store healthy`
- `execution_store healthy`
- `reconcile_ok=true`
- `kill_switch_active=false`
- `system_status != HALTED`
- `equity > 0`
- `opening gate ready`

Store 损坏时的降级规则：

- `runtime_store` 损坏：进入 `HALTED_NO_SEND`
- `execution_store` 损坏：进入 `DEGRADED_NO_SEND`；broker reconcile 成功前不得发送任何订单
- `adjustment_audit_store` 损坏：进入 `AI_SHADOW_ONLY`，所有 active AI adjustments 回退到 baseline
- `risk_store` 损坏：进入 `REDUCE_ONLY`
- `lane_context_store` 损坏：允许 market data 和 observability 继续，但禁止依赖历史 context 的新开仓
- `alert_store` 损坏：只影响 observability，核心链路可继续

补充规则：

- `runtime_store` 或 `execution_store` 任一 damaged，系统都不得进入 `send_enabled=true`
- `execution send gate` 永远最后打开
- `AI auto-apply` 永远晚于 `execution reconcile` 打开
- `execution_store` damaged 且 reconcile 未成功前，不得自动重放任何旧 intent
- 任意恢复阶段如果再次触发 kill switch，恢复立即中止并回到 `HALTED_NO_SEND`

## 12. 推荐目录

```text
src/phase0/
  runtime/
    bootstrap.py
    host.py
    supervisor.py

  kernel/
    coordinator.py
    contracts.py
    bus.py
    policy.py

  lanes/
    low/
      service.py
      models.py
    ultra/
      service.py
      models.py
    high/
      service.py
      models.py

  services/
    market_data.py
    risk.py
    execution.py
    portfolio.py
    observability.py

  advisory/
    context_annotator.py
    event_interpreter.py
    risk_adjuster.py
    governance.py
    contracts.py

  infra/
    adapters/
      broker_ibkr.py
      llm_gateway.py
      market_provider.py
    stores/
      runtime_store.py
      lane_context_store.py
      execution_store.py
      risk_store.py
      adjustment_audit_store.py
      alert_store.py

  jobs/
    replay.py
    validate.py
    health.py
```

## 13. 迁移原则

1. 先稳定契约，再迁移实现
2. 先消灭双路径，再谈优化
3. 先把 AI 从骨架中降级为建议层，再保留其价值
4. 任何 AI 输出都必须支持 audit、ttl、fallback、off switch

## 14. 外部参考

- QuantConnect LEAN Algorithm Engine
  https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/algorithm-engine
- NautilusTrader Architecture
  https://nautilustrader.io/docs/latest/concepts/architecture/
- NautilusTrader Adapters
  https://nautilustrader.io/docs/latest/concepts/adapters/
- vn.py MainEngine
  https://github.com/vnpy/vnpy/blob/master/vnpy/trader/engine.py
- vn.py EventEngine
  https://github.com/vnpy/vnpy/blob/master/vnpy/event/engine.py
- Freqtrade Bot Basics
  https://www.freqtrade.io/en/stable/bot-basics/
- AlphaForgeBench
  https://arxiv.org/abs/2602.18481
- Standard Benchmarks Fail for Financial LLM Agents
  https://arxiv.org/abs/2502.15865
- SEC Rule 15c3-5
  https://www.sec.gov/rules/final/2010/34-63241.pdf
- Fed SR 11-7
  https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm
- NIST AI RMF 1.0
  https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf
