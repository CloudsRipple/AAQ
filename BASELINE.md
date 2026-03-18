# BASELINE（审计基线冻结）

更新时间：2026-03-15  
范围：`/src/phase0`、`/scripts`、`/tests`、`README.md`、`pyproject.toml`、`artifacts/*.db`

## 1. 当前行为基线（As-Is）

### 1.1 启动与调度
- 主入口 `phase0-health` 为 `phase0.main:main`，加载配置后执行 `health_check`，可按 `lane_scheduler_cycles` 循环执行。  
  证据：`src/phase0/main.py:17-30`，`pyproject.toml:17-24`
- `health_check` 会执行安全状态判断后，固定调用 `run_lane_cycle_with_guard("AAPL", ...)`。  
  证据：`src/phase0/app.py:25-33`

### 1.2 交易决策主链
- 交易链路：`run_lane_cycle` 内部依次执行  
  `市场快照加载 -> watchlist -> strategies -> Ultra/Low/High -> discipline -> IBKR映射`。  
  证据：`src/phase0/lanes/__init__.py:47-68`、`73-160`、`163-235`、`288-289`
- 高速风控 `evaluate_event` 做了来源校验、价格结构校验、冷却期、持仓期、回撤、风险预算、暴露上限。  
  证据：`src/phase0/lanes/high.py:47-147`

### 1.3 下单执行链
- 执行入口 `phase0-ibkr-execute` 调 `execute_cycle`，当 `--send` 打开时调用 `IbkrExecutionClient.submit_bracket_signal`。  
  证据：`src/phase0/ibkr_execution.py:119-178`、`294-307`
- IBKR bracket 通过三腿顺序发送（parent/take_profit/stop_loss），第三腿 `transmit=true`。  
  证据：`src/phase0/ibkr_order_adapter.py:41-71`，`src/phase0/ibkr_execution.py:97-101`

### 1.4 状态与持久化
- SQLite 持久化仅用于参数审计与 AI memory。  
  证据：`src/phase0/audit.py:26-67`，`src/phase0/ai/memory.py:87-103`
- 未发现订单账本、持仓账本、执行幂等键持久化表。  
  证据：`src/phase0` 下 `sqlite3.connect` 仅出现在 `audit.py` 与 `ai/memory.py`（检索结果）

### 1.5 验证与回放
- 存在故障注入回放 (`phase0-replay`) 与验证报告 (`phase0-validation-report`)。  
  证据：`src/phase0/replay.py:150-181`，`src/phase0/phase0_validation_report.py:164-188`
- 验证报告在动态探测失败时可进入 `fallback_sample` 模式。  
  证据：`src/phase0/phase0_validation_report.py:112-123`

## 2. 已知缺陷基线（按优先级）

## P0

### P0-1：交易入口存在硬编码标的
- 现象：`health_check` 固定传入 `"AAPL"`，与多标的配置不一致。  
  证据：`src/phase0/app.py:29-33`
- 风险：资产配置偏离、策略覆盖范围失真、风控预算与真实持仓不一致。

### P0-2：数据源失败会静默回退到硬编码默认行情
- 现象：live/JSON 失败后直接返回 `_default_market_snapshot()`。  
  证据：`src/phase0/lanes/__init__.py:580-591`，`359-393`
- 风险：在真实市场中基于伪数据做交易决策。

### P0-3：事件去重仅内存态，重启后失效
- 现象：`InMemoryLaneBus` 去重依赖 `_seen_trace_ids` 与 `_seen_order`，无持久化。  
  证据：`src/phase0/lanes/bus.py:30-46`
- 风险：进程重启或容量淘汰后，重复事件可能再次发送。

### P0-4：执行层缺少订单幂等账本与重启对账闭环
- 现象：执行时直接 `placeOrder`，未见“已提交 orderRef 去重 + 启动 reconcile”流程。  
  证据：`src/phase0/ibkr_execution.py:97-101`，`218-227`
- 风险：重复下单、状态错位（本地与券商状态不一致）。

## P1

### P1-1：执行客户端按周期创建/关闭连接
- 现象：`execute_cycle` 内部创建客户端并在 finally 关闭。  
  证据：`src/phase0/ibkr_execution.py:141-156`
- 风险：高频 connect/disconnect 触发网关不稳定或限流。

### P1-2：会话窗口仅按 HH:MM 比较，缺少交易日历
- 现象：`_is_within_session_window` 只做分钟比较，不校验交易日。  
  证据：`src/phase0/ibkr_execution.py:235-245`
- 风险：周末/节假日/特殊时段行为不可控。

### P1-3：naive 时间被直接当 UTC
- 现象：时间解析里若无 tzinfo，直接 `replace(tzinfo=UTC)`。  
  证据：`src/phase0/lanes/high.py:200-211`
- 风险：上游传本地时区字符串时，冷却/持仓判断偏移。

### P1-4：LLM 可用性未进入运行时 safety 判定
- 现象：`assess_safety` 支持 `llm_reachable`，但 `health_check` 调用未传该参数。  
  证据：`src/phase0/safety.py:23-35`，`src/phase0/app.py:25-28`
- 风险：AI依赖异常时系统可能仍在 normal 模式运行。

## P2

### P2-1：执行失败处理以“记录并继续”为主，缺少统一重试策略
- 现象：单笔失败捕获异常后写入结果，未统一重试/熔断。  
  证据：`src/phase0/ibkr_execution.py:143-154`

### P2-2：使用 yfinance 作为市场回退源，稳定性与一致性不足
- 现象：`_load_market_snapshot_from_yfinance` 与 `fetch_yfinance_snapshot` 作为 fallback。  
  证据：`src/phase0/lanes/__init__.py:611-648`，`src/phase0/ibkr_paper_check.py:114-139`

### P2-3：宽泛异常捕获降低故障可观测性
- 现象：多个入口/探针使用 `except Exception` 输出 error 字段。  
  证据：`src/phase0/llm_connectivity_check.py:36-46`，`src/phase0/main.py:34-36`

## 3. 假设基线（当前系统默认假设）
- 假设 `MARKET_SNAPSHOT_JSON` 或 yfinance 能提供可交易级别数据。  
  证据：`src/phase0/lanes/__init__.py:580-648`
- 假设 `orderRef` 足以支撑执行链一致性，但未建立本地幂等账本。  
  证据：`src/phase0/ibkr_order_adapter.py:21-24`，`src/phase0/ibkr_execution.py:93`
- 假设配置驱动能够约束风险，但关键交易状态并未完整持久化。  
  证据：`src/phase0/config.py:115-170`，`src/phase0/audit.py:26-55`

## 4. 无法验证事项（需补充材料）
- 无法验证是否有外部进程管理/守护（systemd/launchd/supervisor）与自动重启策略（仓库未包含部署清单）。
- 无法验证券商真实账户端的 reject code 分布与重连行为（缺少生产运行日志样本）。
- 无法验证真实盘中数据延迟分布（缺少端到端延迟指标历史）。

## 5. 基线冻结结论
- 本基线描述当前“可运行原型”的真实行为，不代表可直接实盘。
- 任何后续改造应以本文件作为回归对照，优先修复 P0/P1，再扩展功能。
