# AAQ Review 修复与进化方案报告

更新日期：2026-03-18

## 1. 背景

本报告基于当前 review 的 5 个确认问题编写，覆盖以下风险点：

- `src/phase0/main.py`：默认主链路绕过统一执行风控栈
- `src/phase0/ai/ultra.py`：Ultra 引擎未向总线发布信号
- `src/phase0/ai/high.py`：High 读取的 Low 缓存与当前启动链路不一致
- `src/phase0/execution_subscriber.py`：执行层重建风控上下文时发生弱化
- `src/phase0/market_data.py`：数据门控返回值存在状态不一致

这 5 个问题并不是彼此独立的点状缺陷，而是同一个架构问题在不同层的表现：

- 系统当前同时存在两套控制面：
  - `run_lane_cycle` / `execute_cycle` 这一套同步、集中式控制面
  - `main -> Ultra/High/Low/ExecutionSubscriber` 这一套事件驱动控制面
- 两套控制面对执行、状态、风控、幂等、对账的边界定义不一致。
- 结果是默认启动路径已经切到事件驱动链路，但真正的生产级风控能力仍主要集中在 `execute_cycle`。

## 2. 总体结论

建议采用以下总原则作为修复和进化基线：

1. `execute_cycle` 对应的执行控制面继续作为唯一的真实下单入口。
2. 事件驱动链路在完成收口前，只能产出信号或意图，不能直接形成独立的实盘提交流程。
3. `Low/High/Ultra` 之间的共享状态不得依赖进程内全局缓存作为唯一真源。
4. 所有状态不一致、依赖缺失、数据锁冲突场景统一 `fail-closed`，即默认阻断开仓与提单。

如果只修单点而不做控制面收口，问题会持续以新的形式反复出现。

## 3. 修复优先级

| 优先级 | 主题 | 目标 |
|---|---|---|
| P0 | 执行安全收口 | 阻止默认链路绕过风险引擎与对账控制面 |
| P0 | 事件链路打通 | 让 `Ultra -> High -> Execution` 的契约真实可用，或默认禁用 |
| P1 | 状态真源统一 | 消除 `Low` 缓存与消费方读取路径不一致 |
| P1 | 执行上下文补全 | 避免执行层凭猜测重建风控输入 |
| P2 | 门控一致性 | 修正 `allow_trading` 与 `allow_opening` 的不变量 |

## 4. 分项修复方案

### 4.1 Finding A：数据门控返回值存在不一致

对应问题：

- `src/phase0/market_data.py`
- 当 DB 锁冲突时，仅将 `allow_trading` 置为 `false`，但没有同步重算 `allow_opening`
- 这会导致返回值可能出现 `allow_trading=false` 且 `allow_opening=true`

立即修复：

- 在 `load_market_snapshot_with_gate` 返回前增加统一收口逻辑：
  - `if not allow_trading: allow_opening = False`
- 在 DB 锁冲突、主源失效、质量校验失败三类分支都走同一套最终归一化逻辑，避免各分支各改一半状态。
- 将 `allow_opening` 视为 `allow_trading` 的严格子集，形成显式不变量。

进化方案：

- 将市场门控结果从裸 `dict` 收敛为一个明确的数据结构，例如 `MarketDataGateResult`
- 在结构构造函数或工厂方法里直接保证：
  - `allow_opening => allow_trading`
  - `degraded => not allow_trading`

验收标准：

- 任意场景下都不存在 `allow_opening=true` 且 `allow_trading=false`
- 新增单测覆盖 DB 锁冲突分支和数据降级分支

### 4.2 Finding B：默认主链路绕过风控执行栈

对应问题：

- `src/phase0/main.py`
- 当前默认 `LANE_SCHEDULER_ENABLED=false`
- `main` 启动后直接走事件驱动链路
- 事件驱动链路没有复用 `execute_cycle` 中的幂等、风险引擎、对账、系统状态机与 kill-switch

立即修复：

- 在真正完成执行收口前，默认生产路径必须回到统一执行控制面。
- 可选落地方式二选一，推荐方案 1：

方案 1：

- 保持事件驱动链路可开发、可实验，但默认不允许其直接接入真实提交流程。
- 在 `main` 中增加显式实验开关，例如 `EVENT_DRIVEN_RUNTIME_ENABLED=false`
- 未开启该开关时，仅运行当前稳定控制面

方案 2：

- 将现有 `LANE_SCHEDULER_ENABLED` 默认值切回安全路径
- 但该方案语义不够清晰，因为它把“旧调度器”和“生产执行入口”混在同一个开关里

推荐最终决策：

- 引入一个新的显式开关区分“运行模式”和“是否允许事件驱动执行”
- 即使事件驱动 Runtime 打开，也不能绕开统一执行入口

进化方案：

- 抽象一个统一的 `ExecutionOrchestrator`
- 所有链路只允许向它提交 `ExecutionIntent`
- `ExecutionOrchestrator` 内部串联：
  - 风险引擎
  - 幂等注册
  - 对账
  - 状态持久化
  - 提交与回报处理

验收标准：

- 默认启动路径不再存在任何直接绕过 `execute_cycle` 核心控制能力的链路
- 任何真实下单行为都能在单一入口被追踪

### 4.3 Finding C：Ultra 引擎未向总线发布信号

对应问题：

- `src/phase0/ai/ultra.py`
- `start_ultra_engine` 完成初始化后仅进入 `sleep` 循环
- 下游 `High` 订阅 `ultra.signal`，但上游没有真实发布
- 当前事件驱动主链路在行为上属于“空转”

立即修复：

- 如果短期内没有真实行情/新闻输入源，不应把这条链路作为默认主执行路径。
- 对于事件驱动链路，至少补齐以下最小能力：
  - 接收 tick/news 输入
  - 调用 sentinel 生成 `UltraSignalEvent`
  - 将事件转换为 `LaneEvent`
  - 发布到 `ultra.signal`

推荐实现拆分：

- `UltraInputAdapter`：负责接行情与新闻输入
- `UltraPublisher`：负责把 `UltraSignalEvent` 转为总线消息
- `start_ultra_engine`：只做编排，不再承担“占位循环”的职责

进化方案：

- 明确 Ultra 的输入契约，不再允许“先启动、后等待未来实现”的占位模式进入主链路
- 为 `Ultra -> High` 加入集成测试，验证一次完整发布和消费

验收标准：

- 启动事件驱动链路后，至少能稳定产生一条可被 High 消费的 `ultra.signal`
- 若输入源不可用，则系统明确进入 `fail-closed`，而不是静默空转

### 4.4 Finding D：High 读取的 Low 缓存在当前架构下为空

对应问题：

- `src/phase0/ai/high.py`
- `High` 从 `lanes.low_engine` 的全局缓存读取 Low 分析结果
- 但当前 `main` 实际启动的是 `ai.low.start_low_engine`
- 该实现不会更新 `lanes.low_engine` 中的缓存
- 导致 `low_committee_approved` 长期缺失或退化为错误值

立即修复：

- 停止让 `High` 依赖进程内缓存作为唯一数据源。
- 短期推荐两步：
  - 由 `Low` 明确发布 `low.analysis` 事件
  - `High` 明确订阅或读取持久化后的最近一次 Low 结论

临时兜底策略：

- 若 `High` 未获取到有效 Low 结论，不要静默降级为“默认拒绝但无上下文”
- 应返回明确原因，例如 `LOW_ANALYSIS_UNAVAILABLE`
- 并通过日志/监控暴露成可观测问题

推荐最终决策：

- 引入 `LowAnalysisStore`
- 以 SQLite / `state_store` 为真源，缓存仅作为加速层，不再承担正确性职责

进化方案：

- 收敛 Low 输出契约：
  - `analysis_id`
  - `generated_at`
  - `committee_approved`
  - `committee_votes`
  - `preferred_sector`
  - `ttl`
- `High` 只接受带版本和时间戳的 Low 结论

验收标准：

- `Low` 与 `High` 不再依赖进程级全局变量协作
- 重启后仍能读取最近一次可用 Low 结论
- 缺失 Low 结论时系统可观测且默认阻断开仓

### 4.5 Finding E：ExecutionSubscriber 风控上下文被弱化

对应问题：

- `src/phase0/execution_subscriber.py`
- `current_exposure` 被固定写为 `0`
- `last_exit_at` 留空
- `side` 被写死为 `buy`
- 导致 cooldown、方向、敞口、持仓状态等关键风控输入与真实账户状态脱节

立即修复：

- 执行层不应靠“猜测”重建 High 事件。
- 短期修复原则：
  - 上游传什么，执行层就消费什么
  - 执行层不再自行推断方向、敞口和冷却状态
  - 任一关键字段缺失则 `fail-closed`

推荐短期实现：

- 将 `ExecutionSubscriber` 的输入从“半结构化的 high decision”提升为“完整的执行意图”
- 至少显式携带：
  - `side`
  - `equity`
  - `current_symbol_exposure`
  - `current_exposure_unit`
  - `last_exit_at`
  - `position_opened_at`
  - `entry/stop/take_profit`

推荐最终决策：

- `ExecutionSubscriber` 不再重新调用 `evaluate_event`
- 风控评估前移到统一控制面
- Subscriber 只承担“接收已批准意图 -> 调用统一执行入口”的职责

进化方案：

- 引入 `ExecutionIntent` / `ApprovedOrderIntent`
- 形成严格类型边界，消除执行层临时拼接和字段漂移

验收标准：

- 执行层不再硬编码 `side=buy`
- 执行层不再把 `current_exposure=0` 当作默认值继续执行
- 缺少真实状态时默认拒绝，不允许静默补零

## 5. 推荐技术决策

基于以上 5 个 finding，建议立即确认以下三项架构决策：

### 决策 1：统一执行控制面

结论：

- 保留 `execute_cycle` 所代表的执行控制面，作为唯一真实提单入口。
- 事件驱动 Runtime 必须向这个入口收口，而不是并行再造一套执行逻辑。

原因：

- 当前风险引擎、幂等、对账、状态机、kill-switch 已经主要聚集在这条链路
- 平行维护两套控制面，只会持续制造状态分叉和风控遗漏

### 决策 2：统一状态真源

结论：

- `LowAnalysis`、运行时敞口、冷却信息、最近退出时间等关键状态统一入库
- 进程内缓存只作为性能优化，不再作为唯一正确性来源

原因：

- 当前问题本质上是“生产路径变了，但状态读取路径没变”
- 只要状态真源不是统一的，这类 bug 会反复出现

### 决策 3：统一事件契约

结论：

- 为 `ultra.signal`、`high.decision`、`low.analysis`、`execution.intent` 建立显式 schema
- 推荐使用 `Pydantic` 模型或 dataclass + 校验函数

原因：

- 当前大量字段是 `dict[str, Any]` 临时拼装
- 只要字段名、来源、默认值稍有变化，就会在下游形成静默语义漂移

## 6. 分阶段落地计划

### Phase 0：安全收口（建议 1-2 天）

目标：

- 先封堵默认路径上的高风险问题，不追求一次性完成完整重构

任务：

- 修复 `market_data` 中的 `allow_opening` / `allow_trading` 不一致
- 默认关闭事件驱动直连执行能力
- 在 `main` 中明确区分实验运行模式与稳定执行模式
- 为上述行为加日志和告警

交付结果：

- 默认启动路径重新回到安全可控状态
- 数据门控不变量成立

### Phase 1：执行入口收口（建议 3-5 天）

目标：

- 把事件驱动链路接到统一执行控制面，而不是继续双轨运行

任务：

- 引入 `ExecutionIntent`
- 将 `ExecutionSubscriber` 改成薄编排层
- 禁止 Subscriber 自行重算风控
- 把事件驱动链路的下单动作收口到统一执行入口

交付结果：

- 任何真实提交都有统一幂等、对账和状态记录

### Phase 2：状态与总线契约收口（建议 5-7 天）

目标：

- 消除当前 `Low`/`High` 之间的全局缓存耦合

任务：

- 引入 `LowAnalysisStore`
- `Low` 发布事件并写入真源
- `High` 从真源或规范事件消费
- 为总线消息加 schema 校验

交付结果：

- 重启后状态不丢
- 缺状态时可观测、可阻断

### Phase 3：事件驱动链路真实化（建议 5-10 天）

目标：

- 让 `Ultra` 真正基于输入源而不是占位循环运行

任务：

- 接入真实 tick/news 输入适配器
- 完成 `Ultra -> High -> ExecutionIntent` 集成验证
- 增加链路监控、回放与压力测试

交付结果：

- 事件驱动链路从“实验骨架”升级为“可灰度运行”的真实通路

## 7. 测试与验收计划

建议补充以下测试：

### 单元测试

- `market_data`：
  - DB 锁冲突时 `allow_opening` 必须为 `false`
- `main`：
  - 默认启动路径不会直接进入未经收口的事件驱动执行链
- `execution_subscriber`：
  - 缺少 `side/current_exposure/last_exit_at` 时必须拒绝
- `high`：
  - `Low` 状态缺失时产生明确拒绝原因，而不是静默误判
- `ultra`：
  - 生成信号后确实发布到 `ultra.signal`

### 集成测试

- `Ultra -> High -> ExecutionIntent` 全链路
- `Low` 更新后 `High` 能读到同一版本结论
- 默认主路径不能绕过统一执行入口
- 事件驱动开启但输入源不可用时，系统进入阻断状态而不是空转

### 发布门禁

- 所有现有回归测试通过
- 新增单元与集成测试通过
- Paper 环境 dry-run 验证：
  - 无重复订单
  - 无绕过风险引擎的提交
  - 无状态丢失导致的误开仓

## 8. 风险与边界

需要明确以下工程边界：

- 在 Phase 1 完成前，不建议把当前事件驱动链路作为默认实盘入口
- 在状态真源统一前，不建议继续扩展更多进程内缓存协作
- 在事件契约显式化前，不建议继续新增基于裸 `dict` 的跨模块字段传递

## 9. 结论

本次修复不应理解为“修 5 个 bug”，而应理解为“把系统从双控制面收口为单控制面”的一次结构整改。

推荐执行顺序如下：

1. 先做安全收口，阻断默认路径的 P0 风险
2. 再做执行入口统一，禁止事件驱动链路独立提单
3. 最后完成状态真源与事件契约治理，推动事件驱动链路可灰度上线

如果需要一个最终的一句话架构目标，可以表述为：

`Event-driven for signal generation, single control-plane for execution.`
