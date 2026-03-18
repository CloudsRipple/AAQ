# AAQ 系统深度审计修复方案与决策记录 (Remediation Plan v2)

本文档针对 `[WORKFLOW-BREAK]`、`[WRONG-TOOL]`、`[TRADING-BUG]` 和 `[MATH-BUG]` 四大维度的 16 个高危问题，提供了详尽的修复方案对比与最终技术决策。

---

## 维度 A：工作流完整性断点 (WORKFLOW-BREAK)

### A1. `ultra.py` 行情数据源缺失 (死循环占位)
* **问题描述**：`start_ultra_engine` 中使用 `while True: await asyncio.sleep(interval_seconds)` 占位，导致整个 Ultra 引擎无法接收真实市场 Tick，工作流从源头断裂。
* **方案 A**：**基于 `ib_insync.Ticker` 的事件驱动**。通过 IBKR 客户端订阅 `reqMktData`，在回调函数 `pendingTickersEvent` 中直接触发 `sentinel.on_market_tick()`。
* **方案 B**：**基于现有 `market_data.py` 的轮询拉取**。在 `while True` 循环中，每秒调用一次拉取接口（如 yfinance 或 REST API），计算增量后喂给 Sentinel。
* **👑 最终决策：方案 A**。
  * **原因**：Ultra 层定位于极速响应（毫秒/秒级），轮询拉取（方案B）存在严重的网络开销和延迟瓶颈，且极易触发第三方 API 限流。直接利用 IBKR 的长连接推送是量化实盘的唯一合理选择。

### A2. `execution_subscriber.py` 订单状态持久化缺失
* **问题描述**：订单通过 `submit_bracket_signal` 提交给 IBKR 后，未将返回的执行结果和 `idempotency_key` 写入 SQLite 数据库，导致重启后系统失忆并可能重复下单。
* **方案 A**：**在 Subscriber 中直接写库**。引入 `state_store.py` 的 `register_idempotency_key`，在下单前后手动记录状态。
* **方案 B**：**复用/重定向到统一执行引擎**。不直接在 Subscriber 中调用 IBKR 客户端，而是将事件推送到专门的 `Execution Lane` 或复用 `ibkr_execution.execute_cycle` 进行收口。
* **👑 最终决策：方案 B**。
  * **原因**：直接写库（方案A）会导致状态管理逻辑散落在系统各处（高内聚低耦合被破坏）。将所有执行请求收口到专门的 `ibkr_execution` 模块，能统一处理幂等性、重试机制和断线重连，确保状态机的绝对一致性。

### A3. `execution_subscriber.py` 吞咽历史订单查询异常
* **问题描述**：第 77 行用 `except Exception: pass` 吞掉了对冷却期查询的报错，数据库锁定时将无条件放行订单。
* **方案 A**：**抛出异常并 NACK 消息**。让事件留在总线队列中，等待下一次循环重试。
* **方案 B**：**捕获异常并执行 Fail-Safe (默认拒绝)**。记录错误日志，将该笔信号标记为 `rejected` 并丢弃。
* **👑 最终决策：方案 B**。
  * **原因**：交易系统的第一原则是**资金安全 (Fail-Safe)**。如果系统状态未知（查不到历史订单），盲目重试可能导致死锁积压，默认拒绝入场是最保守且最安全的做法。

### A4. `ibkr_execution.py` 吞咽账户净值查询异常
* **问题描述**：第 219 行在 `reconcile_snapshot` 中 `accountSummary` 查询失败时直接 `pass`，导致系统以 `equity = 0.0` 继续运行。
* **方案 A**：**使用最近一次的有效缓存值**。从 `state_store` 读取上一次持久化的净值作为兜底。
* **方案 B**：**阻断执行并返回明确错误**。返回 `{"ok": False, "error": "RECONCILE_FAILED"}`，交由上层中止本轮风控评估。
* **👑 最终决策：方案 B**。
  * **原因**：净值 (`equity`) 是计算单笔风控 (1% Risk) 和总敞口限制的核心基数。使用过期缓存（方案A）在剧烈波动市中极易导致仓位超限或保证金不足。宁可错失交易，不可盲目计算。

---

## 维度 B：技术工具选型错误 (WRONG-TOOL)

### B1. `ultra.py` 新闻语义处理使用正则匹配
* **问题描述**：使用 `text.count("fake")` 等硬编码字符串匹配判断新闻真伪，缺乏语义理解。
* **方案 A**：**轻量级本地向量检索**。使用 `SentenceTransformers` 将新闻转为 Embedding，与本地预设的 "事件原型库" 计算余弦相似度。
* **方案 B**：**异步调用 LLM 进行分类**。把新闻发给大模型，要求返回 JSON 格式的真伪置信度。
* **👑 最终决策：方案 A**。
  * **原因**：Ultra 层是高频防线，LLM 调用（方案B）存在 1-3 秒的网络延迟，完全无法满足抢单要求。本地 Embedding 模型（如 `bge-small-en`）推理仅需 10-30 毫秒，兼顾了语义理解与极速响应。

### B2. `bus.py` 事件队列使用 `list.pop(0)`
* **问题描述**：Python 的 `list.pop(0)` 时间复杂度为 O(N)，积压时会导致 CPU 飙升。
* **方案 A**：**替换为 `collections.deque`**。双端队列的 `popleft()` 为 O(1)。
* **方案 B**：**替换为 `asyncio.Queue`**。原生支持协程等待和背压控制。
* **👑 最终决策：方案 B**。
  * **原因**：当前总线系统运行在 `asyncio` 协程环境下，`asyncio.Queue` 不仅解决了性能问题，还能天然提供 `put_nowait` / `get` 的协程挂起机制，避免死循环空转。

### B3. `low_engine.py` 内存字典缓存状态
* **问题描述**：使用全局变量 `LOW_ANALYSIS_CACHE = {}` 存储分析结果，重启即丢失。
* **方案 A**：**存入 SQLite (`state_store.py`)**。将分析结果序列化为 JSON 持久化。
* **方案 B**：**引入 Redis**。使用 Redis 的键值对和过期时间(TTL)管理缓存。
* **👑 最终决策：方案 A**。
  * **原因**：根据项目架构约束（Macbook Air M2 本机常驻），尽量减少额外的基础组件依赖。SQLite 配合 WAL 模式完全能满足当前低频（每小时一次）的读写并发需求，且维护成本极低。

### B4. `llm_gateway.py` 异步并发被锁死
* **问题描述**：在 `async_generate` 中使用了同步客户端并通过 `_async_lock` 强制串行化，废掉了多模型共识的并发能力。
* **方案 A**：**移除 Lock 并保留 `to_thread`**。利用同步客户端内置的连接池在多线程下并发。
* **方案 B**：**重构为 `AsyncOpenAI` 客户端**。彻底移除线程池，使用真正的 asyncio 协程并发。
* **👑 最终决策：方案 B**。
  * **原因**：Python 的线程池受制于 GIL，且创建线程有内存开销。网络 IO 密集型任务使用官方提供的 `AsyncOpenAI` 是最优解，能以极低的开销并发请求多个大模型节点。

### B5. `lanes/__init__.py` 滥用原生线程
* **问题描述**：使用 `threading.Thread` 手动启动新线程并运行 `asyncio.run()`。
* **方案 A**：**使用 `asyncio.to_thread`**。
* **方案 B**：**彻底异步化，直接 `await`**。消除同步包装层。
* **👑 最终决策：方案 B**。
  * **原因**：混合使用同步/异步模型会导致事件循环碎片化。将外层调用链彻底 `async/await` 化，不仅代码更简洁，也能消除上下文切换带来的不可控延迟。

---

## 维度 C：交易业务逻辑缺陷 (TRADING-BUG)

### C1. `execution_subscriber.py` 强行做多与止损反向
* **问题描述**：下单时硬编码 `"side": "buy"`，且止损价为 `entry * (1 - pct)`。做空信号会导致灾难性错误。
* **方案 A**：**动态解析方向并分支计算**。读取 `side`，若为 `sell` 则主单为 SELL，止损为 BUY 且价格为 `entry * (1 + pct)`。
* **方案 B**：**将价格计算逻辑上移至风控层**。Subscriber 只负责接收具体价格，不负责计算。
* **👑 最终决策：方案 B (结合 A)**。
  * **原因**：原则上执行层 (`execution_subscriber`) 应该是 "哑终端"，只负责翻译指令。具体的止盈止损绝对价格应该由 `risk_engine` 或 `high_lane` 计算完毕后传入。由于当前 `high.py` 已有结构检查，应直接使用 Payload 传递的精确价格，并根据 `side` 动态映射 IBKR 的 `action`。

### C2. `execution_subscriber.py` 缺失信号过期保护
* **问题描述**：对积压的 `ultra_signal` 盲目下单，未校验 `signal_ts` 到当前的时间差。
* **方案 A**：**在 Subscriber 消费时校验延迟**。`if (now - signal_ts) > max_latency: continue`。
* **方案 B**：**利用 IBKR 的 `goodAfterTime`/`goodTillDate`**。让订单自带生命周期。
* **👑 最终决策：方案 A**。
  * **原因**：在本地提早拦截过期信号，可以避免向交易所发送无用请求，降低 API 负载。对于超高频信号，哪怕晚了 5 秒都可能面临完全不同的盘口，本地拦截最敏捷。

### C3. `high.py` 冷却期未考虑非交易日
* **问题描述**：`timedelta(hours=24)` 直接使用自然日，周五清仓的标的周一会直接突破冷却期防线。
* **方案 A**：**引入 `pandas_market_calendars`**。精确计算市场开盘时间。
* **方案 B**：**复用 `market_data.py` 中的节假日表**。手写逻辑剔除周末和 `us_market_holidays`。
* **👑 最终决策：方案 B**。
  * **原因**：项目中已经包含了 `us_market_holidays` 的逻辑。为单一功能引入庞大的 `pandas_market_calendars` 依赖不符合资源受限的部署环境。通过简单的日历跳过算法即可实现精确到交易日的计算。

### C4. `ibkr_execution.py` 提交前无断线校验
* **问题描述**：`submit_bracket_signal` 未检查 `self._ib.isConnected()`，断线时发单陷入黑洞。
* **方案 A**：**发单前校验并返回明确错误**。`if not isConnected: return error`。
* **方案 B**：**发单前尝试自动重连**。`if not isConnected: self._ib.connect(...)`。
* **👑 最终决策：方案 A**。
  * **原因**：执行适配器应保持状态纯粹。如果自动重连（方案B），可能导致主线程阻塞长达数十秒，影响其他并发任务。正确的做法是返回错误，由外层的守护进程（如 `app.py` 的重连机制）统一处理连接恢复，然后通过重试队列再下发。

---

## 维度 D：数学与数值处理 (MATH-BUG)

### D1. `market_data.py` 5日Z-score计算分母错误
* **问题描述**：`z_score_5d = (ref_price - mean_5) / std_20` 误用了 20日标准差。
* **方案 A**：**修正为 5日标准差**。计算 `std_5` 并作为分母。
* **方案 B**：**直接使用 pandas 的滚动 z-score 扩展包**。
* **👑 最终决策：方案 A**。
  * **原因**：只需修改一行代码 `std_5 = float(closes.tail(5).std())` 即可修复统计学逻辑错误，无需引入新依赖，且运行开销极小。

### D2. `ultra.py` 样本标准差使用总体自由度
* **问题描述**：`np.std(volumes)` 默认为总体标准差 (`ddof=0`)，在金融小样本中存在向下偏差。
* **方案 A**：**修正参数**：`np.std(volumes, ddof=1)`。
* **方案 B**：**改用 `statistics.stdev`**。Python 标准库默认计算样本标准差。
* **👑 最终决策：方案 A**。
  * **原因**：上下文已经导入了 `numpy`，直接增加 `ddof=1` 参数是性能最高且改动最小的方案，`numpy` 在处理数组时比标准库 `statistics` 快一个数量级。

### D3. `high.py` 资金计算使用浮点数
* **问题描述**：计算 `risk_budget = payload["equity"] * pct` 使用原生 `float`，易导致精度丢失和除法取整偏差。
* **方案 A**：**全链路引入 `decimal.Decimal`**。
* **方案 B**：**将金额统一转换为整数（美分/基点）运算**。
* **👑 最终决策：方案 A**。
  * **原因**：虽然美分转换（方案B）在极客圈流行，但处理股票的细微差价（如 $0.005/share 佣金）时，单纯的美分可能依然不够（需要万分之一美元级别）。`decimal.Decimal` 原生支持任意精度控制和确定的舍入模式（如 `ROUND_DOWN`），是金融系统的行业标准做法。
