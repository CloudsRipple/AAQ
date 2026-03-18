# AAQ Project: Comprehensive Remediation & Evolution Plan

基于代码审查报告中识别的 40 个问题（20 Bugs + 20 Problems），本方案通过**分类聚合**的方式提出发散性解决思路，并经过可行性评估后，制定最终的实施路线图。

---

## 1. 问题分类与聚合

为了提高解决效率，我们将问题分为 5 个核心领域：

1.  **AI 核心能力缺失 (AI Core)**: 涉及 Mock 实现、伪随机决策 (B02-B04, P01)。
2.  **系统稳定性与健壮性 (Stability)**: 涉及崩溃风险、序列化错误、静默失败 (B01, B05, B06, B07, B13, B15, B20, P06)。
3.  **业务逻辑与风控 (Business Logic)**: 涉及强制交易、数学错误、成本估算 (B08, B09, B10, B11, B16, B17, P02, P09)。
4.  **数据完整性与依赖 (Data)**: 涉及数据源质量、硬编码数据 (B07, B19, P04, P08, P20)。
5.  **架构与运维 (Architecture)**: 涉及同步阻塞、配置管理、安全 (P03, P05, P10, P11-P15)。

---

## 2. 发散性解决方案与可行性评估

### 领域 1: AI 核心能力缺失 (The "Fake AI" Problem)
**问题**: AI 决策层 (Low/High/Ultra Lanes) 目前是硬编码的伪逻辑。

| 方案 | 描述 | 优点 | 缺点 | 评估 |
| :--- | :--- | :--- | :--- | :--- |
| **方案 A: 同步直连** | 在现有同步函数中直接调用 `LLMGateway`。 | 实现最快，改动最小。 | **严重阻塞**：每次 LLM 调用卡顿 3-10秒，导致行情处理延迟。 | ❌ 不推荐 (仅限调试) |
| **方案 B: 线程池卸载** | 保持主流程同步，使用 `ThreadPoolExecutor` 并发执行 LLM 请求。 | 避免主循环阻塞，无需重写架构。 | 需处理线程安全问题，调试复杂度略增。 | ⭐ **推荐 (Phase 1)** |
| **方案 C: AsyncIO 重构** | 将整个系统重构为 `async/await` 异步架构。 | 性能最佳，符合现代 Python 标准。 | **改动巨大**：涉及所有 IO 密集型模块的重写。 | 🌟 **推荐 (Phase 2)** |
| **方案 D: 独立 Agent 服务** | 将 AI 逻辑剥离为独立微服务 (FastAPI)，主程序通过 HTTP 调用。 | 解耦彻底，便于独立扩缩容。 | 部署运维复杂，增加了 IPC 通信开销。 | ❌ 过度设计 (Phase 0 阶段) |

### 领域 2: 系统稳定性 (The "Crash" Problem)
**问题**: JSON 序列化崩溃 (B01)、时间解析错误 (B05)、数据库锁 (B13)。

| 方案 | 描述 | 优点 | 缺点 | 评估 |
| :--- | :--- | :--- | :--- | :--- |
| **方案 A: 防御性编程补丁** | 针对具体报错点 (JSON, Time) 增加 `try-except` 和默认值处理。 | 快速见效，精准打击。 | 治标不治本，代码充斥着“补丁”逻辑。 | ⭐ **推荐 (紧急修复)** |
| **方案 B: 引入 Pydantic** | 使用 Pydantic 模型替换所有字典传递，利用其内置的验证和序列化能力。 | 类型安全，自动处理 JSON/Time 转换，消除一类 Bug。 | 需定义大量 Model 类，有一定的重构工作量。 | 🌟 **推荐 (长期治理)** |
| **方案 C: 数据库连接池** | 使用 `SQLAlchemy` 或单例连接管理 SQLite 连接。 | 彻底解决 `database is locked` 问题。 | 引入新依赖。 | ⭐ **推荐 (必须实施)** |

### 领域 3: 业务逻辑与风控 (The "Risky Logic" Problem)
**问题**: 强制买入逻辑 (B08)、简单关键词匹配 (B11)、浮点数精度 (B10)。

| 方案 | 描述 | 优点 | 缺点 | 评估 |
| :--- | :--- | :--- | :--- | :--- |
| **方案 A: 规则引擎化** | 将交易规则提取到 YAML/JSON 配置文件，支持动态热加载。 | 灵活，修改规则无需改代码。 | 增加了配置管理的复杂度。 | ❌ 暂缓 (Phase 3) |
| **方案 B: 逻辑修正与开关** | 删除强制买入逻辑，引入 `Decimal` 处理金额，为危险逻辑增加 Feature Flag。 | 消除直接风险，成本低。 | 逻辑依然硬编码。 | 🌟 **推荐 (立即实施)** |
| **方案 C: 影子模式 (Shadow Mode)** | 新逻辑上线后只记录日志不下单，与旧逻辑对比运行 1 周。 | 风险最低，便于验证。 | 开发周期变长。 | ⭐ **推荐 (测试策略)** |

### 领域 4: 数据完整性 (The "Bad Data" Problem)
**问题**: yfinance 静默失败、硬编码数据依赖。

| 方案 | 描述 | 优点 | 缺点 | 评估 |
| :--- | :--- | :--- | :--- | :--- |
| **方案 A: 数据源切换** | 切换到 IBKR 原生行情 API (已连接) 或 AlphaVantage。 | 数据质量高，实时性好。 | IBKR 行情订阅需要付费且有并发限制。 | ⭐ **推荐 (作为首选)** |
| **方案 B: 本地数据缓存层** | 建立 SQLite/CSV 缓存，通过定时任务更新数据，交易主进程只读缓存。 | 解耦数据获取与交易逻辑，稳定性高。 | 数据存在滞后性。 | 🌟 **推荐 (作为兜底)** |
| **方案 C: 增强型 yfinance** | 增加重试机制、代理池和详细的错误日志。 | 成本最低 (免费)。 | yfinance 仍非官方 API，不稳定。 | ⚠️ 仅做备选 |

---

## 3. 最终综合修复方案 (The Master Plan)

基于上述评估，我们制定分阶段实施计划。

### 📅 Phase 1: 止血与稳定 (Week 1)
**目标**: 修复所有 Critical/High Bug，确保系统不会崩溃或产生危险交易。

1.  **修复基础库 Bug (Stability)**:
    *   [B01] 修复 `bus.py` 中的 JSON 序列化器，支持 `datetime` 和自定义对象。
    *   [B05, B06] 重写 `_parse_hhmm`，增加异常处理，确保时间窗口校验在失败时“Fail Safe” (默认关闭)。
    *   [B14] 增强 `config.py` 的布尔值解析鲁棒性。
2.  **消除业务风险 (Logic)**:
    *   [B08] **彻底删除** `discipline.py` 中“未达标则强制买入”的逻辑。
    *   [B10] 将所有涉及金额/数量计算的逻辑迁移到 `decimal.Decimal` 或增加显式精度控制 (`round(x, 4)`)。
3.  **数据源加固 (Data)**:
    *   [B07] 在 `yfinance` 加载逻辑中增加 `try-except` 和 `logger.error`，并显式标记数据来源状态。

### 🧠 Phase 2: 注入灵魂 (Week 2)
**目标**: 移除 AI Mock 代码，接入真实 LLM 能力。

1.  **引入线程池 (Concurrency)**:
    *   在 `AppConfig` 中增加 `max_workers` 配置。
    *   在 `main.py` 初始化 `ThreadPoolExecutor`。
2.  **接入 LLM Gateway (AI Integration)**:
    *   修改 `low.py`, `high.py`, `ultra.py`，移除 `sum(ord(ch))` 等伪逻辑。
    *   注入 `UnifiedLLMGateway` 实例。
    *   使用 `executor.submit()` 将 LLM 请求提交到线程池，实现非阻塞调用（或在短期内接受同步调用，如果 QPS 较低）。
3.  **Prompt 工程**:
    *   为 Low/High/Ultra Lane 编写真实的 System Prompts，确保输出 JSON 格式便于解析。

### 🏗️ Phase 3: 架构升级 (Week 3-4)
**目标**: 提升代码质量和可维护性。

1.  **Pydantic 重构**:
    *   定义 `MarketSnapshot`, `Signal`, `Order` 等 Pydantic 模型，替换杂乱的 `dict` 传递。
2.  **数据库治理**:
    *   引入 `SQLAlchemy` 或简单的 Context Manager 连接池，修复 B13 (Race Condition)。
3.  **测试覆盖**:
    *   编写集成测试，Mock 外部网络请求 (IBKR/OpenAI)，但测试真实的业务逻辑流。

---

## 4. 实施清单 (Action Items)

为了启动 Phase 1，建议立即执行以下变更：

1.  **Create** `src/phase0/utils.py`: 存放安全的 JSON encoder 和时间解析函数。
2.  **Modify** `src/phase0/lanes/bus.py`: 引用新的 JSON encoder。
3.  **Modify** `src/phase0/ibkr_execution.py`: 修复时间解析逻辑。
4.  **Modify** `src/phase0/discipline.py`: 删除强制交易逻辑。
5.  **Modify** `src/phase0/lanes/__init__.py`: 增加数据加载的错误日志。

是否需要我为您生成 Phase 1 的具体代码补丁？
