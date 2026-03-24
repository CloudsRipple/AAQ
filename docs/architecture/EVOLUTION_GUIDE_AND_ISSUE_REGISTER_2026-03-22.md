# AAQ 未来演变导向与问题统计清单（设计者视角）

更新时间：2026-03-22

## 1) 结论先行

当前项目不是“坏代码堆”，而是**原型能力完整但结构边界尚未收敛**的系统。  
核心风险不是单点 bug，而是：

1. 运行主路径与语义存在并行/重叠（双路径、双语义）。
2. 编排中心化（`lanes/__init__.py`）与共享状态中心化（`state_store.py`）。
3. 基础设施层自实现比例偏高，替换和维护成本持续上升。

这意味着：后续应当以“**先收敛边界，再替换实现**”为主线，而不是直接大规模重写。

---

## 2) 当前结构统计（基于代码扫描产物）

数据来源：
- `artifacts/project_assembly_sheet.md`
- `artifacts/oss_replacement_audit.md`
- `issues_master.json`

### 2.1 代码结构规模

- 模块数：53
- 函数/方法数：404
- 模块导入边：109
- 模块调用边：615
- Topic 通信边：20

### 2.2 历史问题（已修复）

- 总计：15
- 致命：1
- 高：7
- 中：7
- 低：0

### 2.3 当前架构性问题（未收敛）

来自架构文档与代码观察，共 9 项：
- ARCH-01 双主路径
- ARCH-02 总装厂
- ARCH-03 收口冲突
- ARCH-04 AI 越权
- ARCH-05 状态 ownership 模糊
- ARCH-06 IO 边界泄漏
- ARCH-07 High 语义重叠
- ARCH-08 缓存耦合
- ARCH-09 中心化依赖

### 2.4 耦合热点模块（按结构耦合分数）

耦合分数口径：`import_in + import_out + call_in + call_out`

1. `phase0.state_store` = 151  
2. `phase0.config` = 130  
3. `phase0.ibkr_execution` = 109  
4. `phase0.ai.high` = 98  
5. `phase0.lanes.__init__` = 89  
6. `phase0.market_data` = 84  
7. `phase0.lanes.high` = 70  

说明：耦合集中在“状态、配置、执行、中心编排”，而非单个算法函数。

### 2.5 事件通信热点

Topic 总量：
- `high.decision`：7
- `ultra.signal`：6
- `low.analysis`：4
- `execution.intent`：2
- `low.analysis.updated`：1

说明：通信模型已初步事件化，但语义仍有重复通道与回流复杂度。

---

## 3) 问题全景（按耦合类型）

## 3.1 控制耦合（Control Coupling）

- 症状：`lanes/__init__.py` 同时承载数据、策略、AI、纪律、映射、总线编排。
- 风险：任何变更都扩大回归范围，影响不可局部化。
- 证据：ARCH-02、`src/phase0/lanes/__init__.py`

## 3.2 状态耦合（State Coupling）

- 症状：`state_store.py` 单体承载多域状态；Low 缓存全局共享。
- 风险：恢复顺序复杂，状态一致性问题难定界。
- 证据：ARCH-05、ARCH-08、`src/phase0/state_store.py`、`src/phase0/lanes/low_engine.py`

## 3.3 语义耦合（Semantic Coupling）

- 症状：High 在 `lanes/high.py` 与 `ai/high.py` 语义重叠。
- 风险：命名一致但职责冲突，导致“看起来对，实际上不一致”。
- 证据：ARCH-07

## 3.4 路径耦合（Path Coupling）

- 症状：health/lane cycle 与 event-driven 并存；execution 可能破坏唯一收口。
- 风险：审计链分叉、回放一致性下降。
- 证据：ARCH-01、ARCH-03

## 3.5 边界耦合（Boundary Coupling）

- 症状：service/domain 与 adapter 的 IO 边界存在穿透。
- 风险：基础设施替换牵一发动全身。
- 证据：ARCH-06、ARCH-09

## 3.6 平台耦合（Platform Coupling）

- 症状：基础设施自实现较多（LLM、Bus、Store、重试、报告流水线）。
- 风险：长期维护成本高，质量稳定性依赖个体实现。
- 证据：`artifacts/oss_replacement_audit.md`

---

## 4) 北极星架构（未来演变导向）

目标定位：`single-host modular monolith`（单宿主模块化单体）

### 4.1 架构原则

1. 单一主路径：`MarketData -> Low/Ultra Context -> High Decision -> Risk -> Execution`
2. High 唯一收口：`TradeDecision` 只能由 High 产出
3. AI 受治理：AI 仅提供 proposal/overlay，不直接越权改 live 决策
4. 风险 fail-closed：关键依赖异常默认拒绝高风险动作
5. 外部 IO 仅经 Adapter：域层不直接持有外部 SDK/网络细节
6. 状态按域 ownership：runtime/execution/risk/context 拆仓管理

### 4.2 模块目标分层

- `kernel`: contracts、coordinator、policy、bus abstraction
- `lanes`: low/ultra/high 纯业务服务
- `advisory`: AI 解释与建议（非执行权）
- `services`: market/risk/execution/portfolio/observability
- `infra`: stores/adapters/providers
- `runtime`: host/bootstrap/supervisor

---

## 5) 6 个月演进路线（分阶段）

## 阶段 0（第 0-2 周）：风险冻结与可观测基线

- 产出：Runbook、baseline capture/compare、硬不变量门禁
- 完成标准：
  - 能采集基线并自动差异报告
  - High 唯一收口/fail-closed/bracket transmit 有显式检查

## 阶段 1（第 3-6 周）：边界收敛（不换实现）

- 动作：
  - 抽象 `LLMPort / EventBusPort / StateStorePort`
  - `app.py` 降为兼容层，runtime 单入口
  - 从 `lanes/__init__.py` 持续迁移编排到 `kernel/coordinator`
- 完成标准：
  - 业务层不再直接依赖具体基础设施实现
  - 总装厂职责下降（可量化：行数/直接依赖数下降）

## 阶段 2（第 7-12 周）：基础设施替换（逐项）

- 替换序列建议：
  1) LLM 重试/限流
  2) Bus 统一实现
  3) Store repository 拆分
  4) 报告流水线统一
- 完成标准：
  - 每次替换都可 shadow 对账
  - 对外接口不变，行为差异在阈值内

## 阶段 3（第 13-24 周）：语义统一与收口清理

- 动作：
  - High 语义统一命名与职责
  - 删除双路径遗留与临时兼容
  - 完成文档、报警、值班、恢复流程一体化
- 完成标准：
  - 架构问题清单 ARCH-01..09 至少关闭 7 项
  - 核心链路可回放、可审计、可恢复

---

## 6) 风险登记（Top 8）

| 风险ID | 风险描述 | 概率 | 影响 | 优先级 | 控制策略 |
|---|---|---|---|---|---|
| R1 | 重构导致决策语义漂移 | 中 | 高 | P0 | 基线回放 + 不变量门禁 |
| R2 | 双路径并存期出现审计分叉 | 高 | 高 | P0 | 单主路径优先收敛，影子链仅观测 |
| R3 | 状态拆分导致恢复失败 | 中 | 高 | P0 | 先 repository 抽象，再物理拆分 |
| R4 | AI 越权回归 | 中 | 高 | P1 | governance 强制、无审批不生效 |
| R5 | 事件总线替换引发时序问题 | 中 | 中 | P1 | 双写双读 + 时序对账 |
| R6 | 外部 IO 边界回退穿透 | 中 | 中 | P1 | adapter lint/静态规则检查 |
| R7 | 团队并行改动冲突 | 高 | 中 | P1 | owner 切片 + feature flag + 小步合并 |
| R8 | 清理阶段误删隐式依赖 | 中 | 中 | P2 | 观察窗 + 分批下线 + 回滚剧本 |

---

## 7) 执行看板（每周必须更新）

## 7.1 结构指标

- 总装厂依赖数（`lanes/__init__.py` import/call 边）
- `state_store` 入边数与跨域调用数
- 双路径调用占比（health path vs event-driven path）

## 7.2 质量指标

- baseline diff 通过率
- 回放场景一致性（pass/total）
- validation checks 通过率

## 7.3 运行指标

- High 收口一致性（是否唯一）
- fail-closed 触发与误放行数
- bracket 完整性异常数

---

## 8) 决策建议（现在就做）

1. 把本文件作为“架构总账”，每周更新一次。  
2. 用 `ZERO_INCIDENT_REFACTOR_RUNBOOK` 作为执行纪律，不跳阶段。  
3. 先完成“接口收敛”再做“实现替换”；先证据化，再重构。  
4. 每次仅推进一个核心主题（LLM/Bus/Store 三选一），避免并发大手术。  

---

## 9) 关联文档

- `docs/architecture/ZERO_INCIDENT_REFACTOR_RUNBOOK.md`
- `docs/architecture/MASTER_REMEDIATION_AND_ARCH_REFACTOR_PLAN.md`
- `docs/architecture/REFACTOR_BLUEPRINT_AI_ADVISORY.md`
- `artifacts/project_assembly_sheet.md`
- `artifacts/oss_replacement_audit.md`
- `issues_master.json`
