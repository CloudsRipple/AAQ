# Refactor Blueprint: File-Level Migration Plan

更新时间：2026-03-18

## 1. 目标

本蓝图给出从当前仓库迁移到 `Quant Core + AI Advisory Plane` 架构的文件级改造路径。

目标不是一次性重写，而是：

- 保留已有可运行能力
- 消灭双路径和重复评估
- 收敛 AI 为受治理的参数建议层
- 为后续渐进重构提供稳定落点

## 2. 当前主要问题

### 2.1 总装厂文件

- `src/phase0/lanes/__init__.py`

问题：

- 同时做市场数据、策略、AI、记忆、纪律、风控前调整、事件发布、订单映射
- 已经不是 lane 包的 init 文件，而是 coordinator

结论：

- 必拆

### 2.2 双重 high 语义

- `src/phase0/lanes/high.py`
- `src/phase0/ai/high.py`

问题：

- 两个 high 语义冲突
- 一个是硬风控/仓位决策
- 一个是 AI 风险调整建议

结论：

- 必重命名

### 2.3 双 runtime / 双主路径

- `src/phase0/main.py`
- `src/phase0/app.py`
- `src/phase0/execution_subscriber.py`
- `src/phase0/ai/low.py`
- `src/phase0/ai/high.py`
- `src/phase0/ai/ultra.py`

问题：

- health-check loop 和 event-driven daemon 双轨并行
- execution 阶段还会反向重算 high

结论：

- 必收敛成单一路径

### 2.4 巨型状态存储

- `src/phase0/state_store.py`

问题：

- runtime、execution、risk、alerts、low analysis 全部混在一个模块

结论：

- 必逻辑拆分

## 3. 目标结构与映射

### 3.1 runtime

新文件：

- `src/phase0/runtime/bootstrap.py`
- `src/phase0/runtime/host.py`
- `src/phase0/runtime/supervisor.py`

来源：

- `src/phase0/main.py`
- `src/phase0/app.py`

处理：

- `main.py` 降为薄 CLI
- 运行装配迁移到 `runtime/bootstrap.py`
- daemon 生命周期管理迁移到 `runtime/host.py`

### 3.2 kernel

新文件：

- `src/phase0/kernel/coordinator.py`
- `src/phase0/kernel/contracts.py`
- `src/phase0/kernel/bus.py`
- `src/phase0/kernel/policy.py`

来源：

- `src/phase0/lanes/__init__.py`
- `src/phase0/lanes/bus.py`
- `src/phase0/models/signals.py`

处理：

- `lanes/__init__.py` 中的编排逻辑迁移到 `kernel/coordinator.py`
- `models/signals.py` 的稳定契约迁移到 `kernel/contracts.py`
- bus 二选一，只保留统一实现

### 3.3 lanes/low

新文件：

- `src/phase0/lanes/low/service.py`
- `src/phase0/lanes/low/models.py`

来源：

- `src/phase0/lanes/low.py`
- `src/phase0/lanes/low_engine.py`
- `src/phase0/lanes/low_subscriber.py`
- `src/phase0/ai/low.py`

处理：

- 只保留一套 low daemon 实现
- `ai/low.py` 中与 LLM 相关的部分下沉到 advisory
- `low/service.py` 负责 low lane 的主逻辑

### 3.4 lanes/ultra

新文件：

- `src/phase0/lanes/ultra/service.py`
- `src/phase0/lanes/ultra/models.py`

来源：

- `src/phase0/lanes/ultra.py`
- `src/phase0/ai/ultra.py`

处理：

- 保留 Ultra 的规则哨兵与事件契约
- 将 LLM/vector/news interpretation 拆到 advisory

### 3.5 lanes/high

新文件：

- `src/phase0/lanes/high/service.py`
- `src/phase0/lanes/high/models.py`

来源：

- `src/phase0/lanes/high.py`

处理：

- High 只负责统一交易决策
- 不包含 AI 建议逻辑
- 不包含 broker 逻辑

### 3.6 advisory

新文件：

- `src/phase0/advisory/context_annotator.py`
- `src/phase0/advisory/event_interpreter.py`
- `src/phase0/advisory/risk_adjuster.py`
- `src/phase0/advisory/governance.py`
- `src/phase0/advisory/contracts.py`

来源：

- `src/phase0/ai/low.py`
- `src/phase0/ai/ultra.py`
- `src/phase0/ai/high.py`
- `src/phase0/audit.py`

处理：

- AI 从骨架中降级为 advisory 层
- `ai/high.py` 重构为 `risk_adjuster.py`
- `ai/low.py` 重构为 `context_annotator.py`
- `ai/ultra.py` 中 AI 解释部分重构为 `event_interpreter.py`
- `audit.py` 中 AI 参数审计能力迁移到 advisory audit/store

### 3.7 services

新文件：

- `src/phase0/services/market_data.py`
- `src/phase0/services/risk.py`
- `src/phase0/services/execution.py`
- `src/phase0/services/portfolio.py`
- `src/phase0/services/observability.py`

来源：

- `src/phase0/market_data.py`
- `src/phase0/risk_engine.py`
- `src/phase0/ibkr_execution.py`
- `src/phase0/observability.py`
- `src/phase0/execution_lifecycle.py`

处理：

- 这些文件原则上保留逻辑，调整边界与命名

### 3.8 infra/stores

新文件：

- `src/phase0/infra/stores/runtime_store.py`
- `src/phase0/infra/stores/lane_context_store.py`
- `src/phase0/infra/stores/execution_store.py`
- `src/phase0/infra/stores/risk_store.py`
- `src/phase0/infra/stores/adjustment_audit_store.py`
- `src/phase0/infra/stores/alert_store.py`

来源：

- `src/phase0/state_store.py`
- `src/phase0/audit.py`

处理：

- 先逻辑拆文件，底层可短期共用 SQLite

### 3.9 infra/adapters

新文件：

- `src/phase0/infra/adapters/broker_ibkr.py`
- `src/phase0/infra/adapters/llm_gateway.py`
- `src/phase0/infra/adapters/market_provider.py`

来源：

- `src/phase0/ibkr_order_adapter.py`
- `src/phase0/ibkr_execution.py`
- `src/phase0/llm_gateway.py`
- `src/phase0/market_data.py`

## 4. 文件去留表

### 4.1 保留并迁移逻辑

- `src/phase0/market_data.py`
- `src/phase0/risk_engine.py`
- `src/phase0/observability.py`
- `src/phase0/execution_lifecycle.py`
- `src/phase0/models/signals.py`

### 4.2 拆分后保留部分逻辑

- `src/phase0/lanes/__init__.py`
- `src/phase0/state_store.py`
- `src/phase0/ibkr_execution.py`
- `src/phase0/audit.py`
- `src/phase0/config.py`

### 4.3 重命名

- `src/phase0/ai/high.py` -> `src/phase0/advisory/risk_adjuster.py`
- `src/phase0/ai/low.py` -> `src/phase0/advisory/context_annotator.py`
- `src/phase0/ai/ultra.py` -> `src/phase0/advisory/event_interpreter.py`

### 4.4 最终删除候选

- `src/phase0/lanes/low_engine.py`
- `src/phase0/lanes/low_subscriber.py`
- 旧版 `src/phase0/lanes/__init__.py`
- 旧版重复 bus 实现中的一套

## 5. 关键重构动作

### 5.1 收敛为唯一主路径

必须实现：

- health mode、replay mode、event-driven mode 复用同一个 coordinator
- execution 阶段不再反向构造 high event

针对文件：

- `src/phase0/execution_subscriber.py`
- `src/phase0/main.py`
- `src/phase0/app.py`

### 5.2 AI 从骨架中剥离

必须实现：

- AI 输出只保留 `AdjustmentProposal` / `RiskOverlay`
- LLM 不再直接参与 runtime 启动结构

针对文件：

- `src/phase0/ai/high.py`
- `src/phase0/ai/low.py`
- `src/phase0/ai/ultra.py`
- `src/phase0/lanes/__init__.py`

### 5.3 引入 Governance

新增：

- parameter registry
- bounded envelope
- approval mode
- ttl
- audit trail

针对文件：

- `src/phase0/advisory/governance.py`
- `src/phase0/advisory/contracts.py`
- `src/phase0/infra/stores/adjustment_audit_store.py`

### 5.4 拆分 state store

优先级高：

- 把 `state_store.py` 中的表访问按域拆到多个 store 文件
- 禁止 lane/service 直接依赖整个大 store

## 6. 分阶段实施

### Phase 1: 契约冻结

新增：

- `kernel/contracts.py`
- `advisory/contracts.py`

结果：

- 所有匿名 payload dict 开始收敛为稳定契约

### Phase 2: 运行时收敛

新增：

- `runtime/bootstrap.py`
- `kernel/coordinator.py`

结果：

- 单一装配入口

### Phase 3: advisory 层落地

新增：

- `advisory/*`

结果：

- AI 从架构骨架中退出

### Phase 4: store 拆分

新增：

- `infra/stores/*`

结果：

- 状态 ownership 清晰化

### Phase 5: execution 去回流

修改：

- `execution_subscriber.py`

结果：

- 消灭重复 high 评估

### Phase 6: 目录和文档收口

新增或调整：

- `docs/architecture/*`
- `jobs/*`

结果：

- 仓库根目录不再堆叠架构文档和临时报告

## 7. 目标文件映射表

| 当前文件 | 目标文件 | 动作 |
|---|---|---|
| `src/phase0/main.py` | `src/phase0/runtime/bootstrap.py` | 迁移 |
| `src/phase0/app.py` | `src/phase0/runtime/host.py` | 迁移/拆分 |
| `src/phase0/lanes/__init__.py` | `src/phase0/kernel/coordinator.py` | 拆分 |
| `src/phase0/lanes/bus.py` | `src/phase0/kernel/bus.py` | 收敛 |
| `src/phase0/models/signals.py` | `src/phase0/kernel/contracts.py` | 迁移 |
| `src/phase0/ai/high.py` | `src/phase0/advisory/risk_adjuster.py` | 重命名/重构 |
| `src/phase0/ai/low.py` | `src/phase0/advisory/context_annotator.py` | 重命名/重构 |
| `src/phase0/ai/ultra.py` | `src/phase0/advisory/event_interpreter.py` | 重命名/重构 |
| `src/phase0/state_store.py` | `src/phase0/infra/stores/*` | 拆分 |
| `src/phase0/audit.py` | `src/phase0/infra/stores/adjustment_audit_store.py` | 迁移 |
| `src/phase0/market_data.py` | `src/phase0/services/market_data.py` | 调整边界 |
| `src/phase0/risk_engine.py` | `src/phase0/services/risk.py` | 调整边界 |
| `src/phase0/ibkr_execution.py` | `src/phase0/services/execution.py` + `infra/adapters/broker_ibkr.py` | 拆分 |
| `src/phase0/llm_gateway.py` | `src/phase0/infra/adapters/llm_gateway.py` | 迁移 |
| `src/phase0/observability.py` | `src/phase0/services/observability.py` | 调整边界 |

## 8. 完成标准

重构完成时，必须满足：

1. 关闭 AI 后系统仍可完整运行
2. AI 输出不能绕过 RiskService
3. execution 阶段不再回流到 high 重评估
4. 三通道 daemon 可以独立运行，但共享同一 coordinator 契约
5. 所有 AI 参数变更都有 audit、ttl、mode、source

## 9. 建议下一步

推荐按以下顺序执行：

1. 先建立 `docs/architecture` 下的设计与 ADR
2. 再落地 `kernel/contracts.py` 与 `advisory/contracts.py`
3. 再拆 `lanes/__init__.py`
4. 再处理 `execution_subscriber.py`

