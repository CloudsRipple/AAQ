# 混合量化系统演进规划（evolution_plan）

## 1. 原始愿景清单（标准化）
- 愿景 A：构建超高速/高速/低速三层协同架构，信号处理与执行解耦。
- 愿景 B：传统量化与 AI 协同，强本地信号可快速通过，弱信号交由 AI 深度审查。
- 愿景 C：执行路径必须统一经过风控与审计，禁止旁路下单。
- 愿景 D：支持本地 AI 与云端 AI 统一接口，具备可降级能力。
- 愿景 E：策略轮换、选股、板块轮动可持续运行并可验证。
- 愿景 F：采用渐进式改造，不推翻现有 Phase 0 骨架，可回滚、可复验。

## 2. 现状能力与证据索引
- 三层车道主循环已可运行：`run_lane_cycle` 输出 Ultra/Low/High 结果、执行信号、纪律计划。
  - 证据：`src/phase0/lanes/__init__.py`
- Ultra 已具备本地快筛与时效/可信度门禁：
  - 证据：`src/phase0/ai/ultra.py`
- Low 已具备委员会投票与板块偏好分析：
  - 证据：`src/phase0/ai/low.py`
- High 已具备本地/云端统一委员会接口与结构化评估输出：
  - 证据：`src/phase0/ai/high.py`
- 执行层已对接 IBKR 语义（bracket 三腿、STP、transmit）：
  - 证据：`src/phase0/ibkr_order_adapter.py`、`src/phase0/ibkr_execution.py`
- 统一硬风控与审计已存在：
  - 证据：`src/phase0/lanes/high.py`、`src/phase0/audit.py`
- 策略轮换与板块轮动已实现：
  - 证据：`src/phase0/strategies/library.py`、`src/phase0/strategies/loader.py`

## 3. 偏差项与优先级
- P0：真实 High 云端委员会回包尚未接入网关，只输出结构化 prompt 与本地评分。
- P0：执行层尚缺回执落盘、幂等防重下单、故障重试闭环。
- P1：超高速层缺“盘中微结构指标”可配置门限模板（目前仅基础快筛）。
- P1：阶段验收报告尚未统一沉淀为单一里程碑工件。
- P2：多账户/多交易所路由策略未纳入执行配置层。

## 4. 目标架构蓝图

### 4.1 超高速层（Ultra）
- 输入：行情快照、新闻标题、时间戳、本地快筛因子。
- 输出：`UltraSignal`（可信度、时效、快筛分、拒绝原因、唤醒标志）。
- 触发：信号进入主循环时优先执行。
- 禁止行为：
  - 禁止直接下单。
  - 禁止跳过 High 风控。
  - 禁止写入审计结论。

### 4.2 高速层（High）
- 输入：策略置信度、Low 委员会结论、Ultra 门禁结果、当前风控状态。
- 输出：风险调整决策（risk multiplier、stoploss 调整）与结构化评估结果。
- 触发：Ultra 唤醒后执行。
- 禁止行为：
  - 禁止绕过 `lanes/high.py` 硬风控直接产生命令。
  - 禁止跳过审计写入。

### 4.3 低速层（Low）
- 输入：市场快照、策略上下文、委员会模型列表。
- 输出：板块偏好、策略拟合、委员会投票。
- 触发：High 决策后异步补充分析。
- 禁止行为：
  - 禁止直接影响订单发送。
  - 禁止单模型直接覆盖委员会阈值。

## 5. 本地 AI / 云端 AI 仲裁链路与越权边界

### 5.1 仲裁流程
1. Ultra 先给出门禁。
2. 若通过，Low 委员会给出板块与策略支持。
3. High 按 `AI_HIGH_MODE` 选择 local/cloud 模式，并按 `AI_HIGH_COMMITTEE_MODELS` 投票。
4. 仅当 High 委员会达到支持阈值时，才允许风险参数调整。
5. 最终仍必须通过 `lanes/high.py` 硬风控判定。

### 5.2 越权边界
- 云端模型不能直接下单。
- 本地模型不能绕开审计写入。
- 任一模型结论都不能覆盖硬风控拒绝。
- 任何策略/AI 分支都不得绕过执行总线与风险总线。

## 6. 统一风控、审计、执行总线不可绕过约束
- 风控门：`evaluate_event` 是唯一下单前硬门。
- 审计门：参数覆盖必须写入 `audit`。
- 执行门：仅消费 `ibkr_order_signals` 并映射为 IBKR bracket 语义。
- 纪律门：`daily_discipline` 在日级目标未达时给出强约束动作建议。

## 7. 渐进式迁移路径（扩展优先、替换其次）

### 阶段 1：接口标准化（已完成）
- 目标：统一 Ultra/Low/High 输出结构与配置入口。
- 保留策略：不改动既有硬风控主实现，仅加适配与扩展字段。
- 验证命令：
  - `python3 -m unittest discover -s tests -q`
  - `PYTHONPATH=src python3 -m phase0.replay --mode all`
- 通过标准：
  - 单测全绿。
  - 回放场景通过。
- 回滚策略：
  - 回退新增字段读取，恢复 legacy 输出键。
- 兼容策略：
  - 保留 legacy 函数 `evaluate_high_adjustment`。
- 数据迁移策略：
  - 不变更历史审计表结构，仅追加字段消费方。

### 阶段 2：High 云端委员会接入（进行中）
- 目标：接入 `UnifiedLLMGateway` 执行 High 云端投票。
- 保留策略：云端不可用时自动回落本地评分。
- 验证命令：
  - `phase0-llm-check --profile local`
  - `phase0-llm-check --profile cloud`
  - `python3 -m unittest discover -s tests -q`
- 通过标准：
  - local/cloud 探针成功。
  - 云端失败时 fallback 正常且不影响硬风控。
- 回滚策略：
  - 切换 `AI_HIGH_MODE=local`。
- 兼容策略：
  - 委员会投票结果统一映射到 `HighAssessment`。
- 数据迁移策略：
  - 新增评估日志文件，不影响既有 audit 表。

### 阶段 3：执行闭环增强（待开始）
- 目标：增加回执落盘、幂等键、防重复下单、失败重试。
- 保留策略：IBKR 发送仍通过现有 `phase0-ibkr-execute` 入口。
- 验证命令：
  - `phase0-ibkr-execute --symbol AAPL`
  - `phase0-ibkr-execute --symbol AAPL --send`
  - `python3 -m unittest discover -s tests -q`
- 通过标准：
  - dry-run 与 send 模式均输出可追踪回执。
  - 同一幂等键不会重复提交。
- 回滚策略：
  - 关闭 send，仅保留 dry-run。
- 兼容策略：
  - 维持 `ibkr_order_signals` 输入契约稳定。
- 数据迁移策略：
  - 新建执行回执表或 JSONL，不改旧数据。

### 阶段 4：里程碑验收与治理固化（待开始）
- 目标：固化矩阵评估、门禁阻断、升级流程模板。
- 验证命令：
  - `phase0-validation-report --output artifacts/phase0_validation_report.latest.json`
  - `phase0-non-ai-validation-report --output artifacts/phase0_non_ai_validation_report.latest.json`
- 通过标准：
  - 报告 `ok=true`。
  - 矩阵状态可追溯。
- 回滚策略：
  - 阶段门禁失败则禁止进入下一阶段开发。
- 兼容策略：
  - 保留现有测试入口与脚本命令不变。
- 数据迁移策略：
  - 验收报告按日期归档。

## 8. 愿景符合性矩阵

| 愿景条目 | 能力点 | 验证项 | 状态 |
|---|---|---|---|
| 三层协同 | Ultra/High/Low 输出齐全 | replay 全场景通过 | 已实现 |
| 传统+AI协同 | Ultra 快筛 + Low/High 评估 | unit + replay | 已实现 |
| 风控审计不可绕过 | 统一风控与审计写入 | high_lane + audit 测试 | 已实现 |
| 本地/云端统一接口 | High mode + committee models | 配置与评估输出检查 | 部分实现 |
| 策略轮换与板块轮动 | momentum/reversion/rotation | strategies/lane_bus 测试 | 已实现 |
| 渐进式改造 | 分阶段目标与回滚策略 | 本文档阶段条目 | 已实现 |

## 9. 阶段检查清单与阻断规则
- 阻断规则 1：任一单测失败，禁止合并。
- 阻断规则 2：回放 `passed != total`，禁止进入下一阶段。
- 阻断规则 3：风控拒绝路径被绕过，必须回滚。
- 阻断规则 4：执行层无审计/回执追踪，禁止开启生产发送。

## 10. 下一阶段执行建议与优先级队列
- P0：接入 High 云端委员会真实网关调用 + fallback 机制。
- P0：执行回执落盘 + 幂等防重复提交。
- P1：Ultra 快筛因子配置化（阈值按标的/时段可调）。
- P1：统一里程碑报告聚合器（AI/非AI/执行）一键产物。
- P2：多账户与路由策略扩展。
