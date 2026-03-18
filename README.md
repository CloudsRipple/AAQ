# AAQ Phase 0

Phase 0 的最小可运行骨架，包含：
- 项目目录与三层车道模块（Ultra / High / Low）
- 环境变量配置加载
- JSON 结构化日志
- 统一错误码
- 健康检查入口
- OpenAI SDK 统一网关（兼容 Ollama 与云端模型）
- LLM 请求重试与限流

## 目录

```text
.
├── pyproject.toml
├── src/phase0
│   ├── app.py
│   ├── config.py
│   ├── errors.py
│   ├── llm_connectivity_check.py
│   ├── llm_gateway.py
│   ├── logger.py
│   ├── main.py
│   └── lanes/
└── scripts
    ├── healthcheck.py
    ├── ibkr_paper_check.py
    └── llm_connectivity_check.py
```

## 快速开始

需使用 Python `3.10+`（推荐 `3.11`）。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python -m phase0.main
```

如果本机没有打开 IBKR Paper Gateway 7497 端口，健康检查会返回 `CONNECTIVITY_UNREACHABLE`，这是预期行为。

## 配置项

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PHASE0_PROFILE` | `paper` | 运行环境：`paper/local/cloud` |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `IBKR_HOST` | `127.0.0.1` | IBKR Gateway 地址 |
| `IBKR_PORT` | `7497` | IBKR Gateway 端口 |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI 兼容网关地址 |
| `LLM_API_KEY` | `dummy` | 网关密钥（日志中会脱敏） |
| `LLM_LOCAL_MODEL` | `llama3.1:8b` | 本地模型名（如 Ollama） |
| `LLM_CLOUD_MODEL` | `gpt-4o-mini` | 云端模型名 |
| `LLM_TIMEOUT_SECONDS` | `20` | LLM 请求超时秒数 |
| `LLM_MAX_RETRIES` | `3` | 可重试错误的最大重试次数 |
| `LLM_BACKOFF_SECONDS` | `0.5` | 重试指数退避基础秒数 |
| `LLM_RATE_LIMIT_PER_SECOND` | `2` | 请求限流（每秒请求数） |

## 错误码

| 错误码 | 含义 |
|---|---|
| `CONFIG_INVALID_PROFILE` | `PHASE0_PROFILE` 非法 |
| `CONFIG_INVALID_VALUE` | 配置值类型错误（如端口不是整数） |
| `CONNECTIVITY_UNREACHABLE` | 无法连接 IBKR Gateway |
| `INTERNAL_ERROR` | 未预期的内部错误 |

## 运行入口

- 命令行：`python -m phase0.main`
- 脚本：`python scripts/healthcheck.py`
- 安装后命令：`phase0-health`
- 回放脚本：`python scripts/replay.py --mode all`
- 安装后命令：`phase0-replay --mode all`
- IBKR Paper 联通脚本：`python scripts/ibkr_paper_check.py --symbol AAPL`
- 安装后命令：`phase0-ibkr-paper-check --symbol AAPL`
- IBKR 执行层脚本（默认 dry-run）：`python scripts/ibkr_execute.py --symbol AAPL`
- 安装后命令：`phase0-ibkr-execute --symbol AAPL`
- LLM 联通脚本：`python scripts/llm_connectivity_check.py --profile local`
- 安装后命令：`phase0-llm-check --profile local`

## IBKR 执行层（参考 ib_insync/IBKR Bracket 语义）

默认是 dry-run，仅输出将发送的 bracket 信号：

```bash
phase0-ibkr-execute --symbol AAPL
```

真实发送（Paper 账户）：

```bash
phase0-ibkr-execute --symbol AAPL --send
```

该执行层遵循 IBKR Bracket 的 parent/takeProfit/stopLoss 三腿语义，并使用最后一腿 `transmit=true` 的发送方式。

## IBKR Paper 联通验证

```bash
phase0-ibkr-paper-check --host 127.0.0.1 --port 7497 --symbol AAPL --news-limit 5 --max-retries 2
```

脚本输出 JSON，包含以下内容：
- `port_7497`：7497 端口探活结果与时延
- `l1_market_data`：IBKR L1 快照订阅示例结果
- `news`：IBKR 新闻读取结果
- `pass_evidence`：L1/新闻通过证据（字段完整性与样本）
- `critical_path_logs`：关键路径日志（端口探测、L1/新闻请求、重试）
- `alerts`：告警事件（端口不可达、请求失败、证据缺失）
- `retry_validation`：重试验证结果（尝试次数、是否重试、重试错误）
- `fallback_market_data`：IBKR 请求失败时的 yfinance 回退结果

如需真实跑通 L1/新闻，请先安装：

```bash
pip install ib-insync yfinance
```

## 验证报告生成

```bash
phase0-validation-report --output artifacts/phase0_validation_report.json
```

输出报告除回放与风控校验外，新增：
- `ibkr_probe`：内置稳定样例的 L1/新闻探针结果
- `ibkr_validation_checks`：通过证据、关键路径日志、告警与重试的验证项

## LLM 统一网关

`phase0.llm_gateway.UnifiedLLMGateway` 使用 OpenAI SDK，通过 `base_url` 接入统一网关。
- 当 profile=`local/paper` 时默认使用 `LLM_LOCAL_MODEL`
- 当 profile=`cloud` 时默认使用 `LLM_CLOUD_MODEL`
- 对 408/409/429/5xx 与连接超时错误自动重试
- 使用每秒请求数限流，避免网关被突发流量打满

## Ultra/High 扩展

- Ultra 新增本地快速筛选分数（`quick_filter_score`），在低动量/高波动时可快速拒绝信号。
- High 支持统一的本地/云端委员会接口，输出结构化评估内容（`mode`、`committee_votes`、`prompt`）。
- 相关配置：`AI_HIGH_MODE`、`AI_HIGH_COMMITTEE_MODELS`、`AI_HIGH_COMMITTEE_MIN_SUPPORT`。
- 默认 `AI_ENABLED=false`，系统运行传统量化主链路（策略信号 + 硬风控 + 执行），LLM 不参与决策。
- 若需启用 AI 链路，请显式设置 `AI_ENABLED=true` 并配置 LLM 网关参数。

示例（Ollama 本地）：

```bash
export PHASE0_PROFILE=local
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_API_KEY=dummy
export LLM_LOCAL_MODEL=llama3.1:8b
phase0-llm-check --profile local
```

示例（云端网关）：

```bash
export PHASE0_PROFILE=cloud
export LLM_BASE_URL=https://your-gateway.example.com/v1
export LLM_API_KEY=sk-xxx
export LLM_CLOUD_MODEL=gpt-4o-mini
phase0-llm-check --profile cloud
```

## 社区策略/因子动态加载

支持在不修改核心代码的情况下，动态加载第三方策略与因子插件。

- `STRATEGY_PLUGIN_MODULES`：逗号分隔的策略插件模块名
- `FACTOR_PLUGIN_MODULES`：逗号分隔的因子插件模块名
- 同时支持 Python entry points：
  - `phase0.strategies`
  - `phase0.factors`

插件模块可实现：

```python
def register_factors() -> dict[str, callable]:
    ...

def register_strategies() -> dict[str, callable]:
    ...
```

然后把策略名加入 `STRATEGY_ENABLED_LIST` 即可参与排序与执行。
