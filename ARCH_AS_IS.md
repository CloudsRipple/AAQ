# ARCH_AS_IS（现状架构）

更新时间：2026-03-15  
目标：描述当前仓库“真实运行架构”，用于后续分阶段改造对照。

## 1. 模块拓扑（As-Is）

```text
Entrypoints
  ├─ phase0-health / scripts/healthcheck.py
  ├─ phase0-ibkr-execute / scripts/ibkr_execute.py
  ├─ phase0-ibkr-paper-check / scripts/ibkr_paper_check.py
  ├─ phase0-llm-check / scripts/llm_connectivity_check.py
  ├─ phase0-replay / scripts/replay.py
  └─ phase0-validation-report / scripts/phase0_validation_report.py

Core Runtime
  main.py -> app.py -> lanes.__init__.py(run_lane_cycle/run_lane_cycle_with_guard)
      ├─ lanes/ultra.py (事件生成)
      ├─ strategies/* (策略与因子)
      ├─ ai/ultra.py + ai/low.py + ai/high.py (AI评估)
      ├─ lanes/high.py (硬风控与仓位)
      ├─ discipline.py (纪律门控)
      ├─ ibkr_order_adapter.py (IBKR bracket 语义映射)
      └─ ibkr_execution.py (真实发送/回报整形)

State & Persistence
  ├─ audit.py (parameter_audit + stoploss_override_state, SQLite)
  ├─ ai/memory.py (memory_records, SQLite)
  └─ lanes/bus.py (内存事件总线+去重+消费位点)
```

证据：
- CLI 注册：`pyproject.toml:17-24`，`src/aaq_phase0.egg-info/entry_points.txt:1-8`
- 主链编排：`src/phase0/main.py:17-30`，`src/phase0/app.py:17-57`，`src/phase0/lanes/__init__.py:34-301`
- 执行链：`src/phase0/ibkr_order_adapter.py:6-74`，`src/phase0/ibkr_execution.py:62-178`

## 2. 关键入口与调用链

## 2.1 健康检查链（不下单）
`phase0-health -> main.main -> app.health_check -> safety.assess_safety -> run_lane_cycle_with_guard`

证据：
- `src/phase0/main.py:17-30`
- `src/phase0/app.py:17-33`
- `src/phase0/safety.py:23-35`
- `src/phase0/lanes/__init__.py:292-301`

## 2.2 交易执行链（可下单）
`phase0-ibkr-execute -> execute_cycle -> run_lane_cycle -> map_decision_to_ibkr_bracket -> submit_bracket_signal -> IBKR placeOrder`

证据：
- `src/phase0/ibkr_execution.py:119-178`
- `src/phase0/lanes/__init__.py:232-235`
- `src/phase0/ibkr_order_adapter.py:34-74`
- `src/phase0/ibkr_execution.py:97-101`

## 2.3 验证链（回放+探针）
`phase0-validation-report -> run_replay + run_probe -> 汇总检查项`

证据：
- `src/phase0/phase0_validation_report.py:164-188`
- `src/phase0/replay.py:150-181`
- `src/phase0/ibkr_paper_check.py:212-373`

## 3. 四条核心流

## 3.1 数据流（Data Flow）
1) 配置流：环境变量 -> `load_config` -> 各模块  
2) 市场数据流：`MARKET_SNAPSHOT_JSON` -> yfinance -> 默认快照  
3) 信号输入流：watchlist/snapshot/headlines -> strategies -> high lane

证据：
- `src/phase0/config.py:86-234`
- `src/phase0/lanes/__init__.py:580-648`
- `src/phase0/strategies/loader.py:27-46`

## 3.2 信号流（Signal Flow）
1) `LaneEvent.from_payload` 生成 trace_id  
2) 发布 `ultra.signal` -> 消费 -> 生成 `high.decision`  
3) low subscriber 消费 `high.decision` -> 发布 `low.analysis`

证据：
- `src/phase0/lanes/bus.py:20-27`，`69-81`
- `src/phase0/lanes/__init__.py:163-208`
- `src/phase0/lanes/low_subscriber.py:25-56`

## 3.3 执行流（Execution Flow）
1) High lane 形成 bracket_order  
2) adapter 转为 IBKR contract + 3 legs  
3) execution client 下发并返回 trade 摘要

证据：
- `src/phase0/lanes/high.py:334-385`
- `src/phase0/ibkr_order_adapter.py:34-73`
- `src/phase0/ibkr_execution.py:81-112`

## 3.4 状态流（State Flow）
1) 安全状态：`NORMAL/DEGRADED/LOCKDOWN`  
2) 纪律状态：`required_action` 门控 accepted 决策  
3) 审计状态：stoploss override TTL + parameter audit  
4) 总线状态：去重窗口与消费位点（内存）

证据：
- `src/phase0/safety.py:7-35`
- `src/phase0/discipline.py:62-104`，`src/phase0/lanes/__init__.py:538-557`
- `src/phase0/audit.py:47-55`，`134-176`
- `src/phase0/lanes/bus.py:31-37`，`58-66`

## 4. 关键架构约束与偏差

### 4.1 架构约束（当前实现）
- 事件总线与去重为单进程内存实现，不支持跨进程一致性。  
  证据：`src/phase0/lanes/bus.py:30-37`
- 执行链是“单次 cycle 驱动”，非常驻连接池。  
  证据：`src/phase0/ibkr_execution.py:141-156`
- 持久化仅覆盖参数审计与记忆，不覆盖订单/持仓账本。  
  证据：`src/phase0/audit.py:26-55`，`src/phase0/ai/memory.py:87-103`

### 4.2 设计偏差（文档 vs 代码）
- 文档描述多标的能力，但健康检查链硬编码 `AAPL`。  
  证据：`README.md:169-170`，`src/phase0/app.py:29-33`
- 风控状态机包含 LLM 可用性维度，但调用点未注入该维度。  
  证据：`src/phase0/safety.py:26-35`，`src/phase0/app.py:25-28`

## 5. 高风险改动区（必须设保护带）

## 5.1 下单执行高风险区
- `src/phase0/ibkr_execution.py`
- `src/phase0/ibkr_order_adapter.py`
- `src/phase0/lanes/high.py`（`_build_bracket_order`、`evaluate_event`）

## 5.2 风控高风险区
- `src/phase0/lanes/high.py`
- `src/phase0/safety.py`
- `src/phase0/discipline.py`
- `src/phase0/lanes/__init__.py`（`_apply_discipline_gate`、`run_lane_cycle_with_guard`）

## 5.3 状态持久化高风险区
- `src/phase0/audit.py`
- `src/phase0/ai/memory.py`
- `src/phase0/lanes/bus.py`
- `src/phase0/app.py`（当前 drawdown 来源）

## 6. 现状架构结论
- 该系统当前是“可运行、可验证、可演示”的原型架构，不是“可直接实盘”的生产架构。
- 生产化瓶颈集中在：执行幂等、状态持久化、数据质量回退策略、连接与会话治理。
