# AAQ Project Phase 0 Code Review Report

## Executive Summary

This report details the findings from a comprehensive code review of the AAQ Phase 0 codebase. The system currently represents a foundational prototype with solid infrastructure components (IBKR connectivity, configuration, logging) but contains critical deficiencies in its core decision-making logic, specifically the AI components which are currently mocked.

**Total Issues Found:**
- **Bugs:** 20 (Critical to Low severity)
- **Problems:** 20 (Architecture, Logic, Maintainability, Security)

---

## 🐞 Bug List

### Critical Severity

| ID | Location | Description | Impact |
|:---|:---|:---|:---|
| **B01** | `src/phase0/lanes/bus.py`:73-82 | **JSON Serialization Crash**: `json.dumps` is used to generate trace IDs but lacks a default encoder for non-serializable objects (e.g., `datetime`, custom classes). | System crash when processing events containing complex objects. |
| **B02** | `src/phase0/ai/low.py` | **Fake AI Implementation**: The "Low Lane" AI logic uses character hashing (`ord(ch)`) to simulate committee votes. | Decisions are deterministic pseudorandomness, not intelligent. |
| **B03** | `src/phase0/ai/high.py` | **Fake AI Implementation**: Similar to Low Lane, the "High Lane" risk assessment is entirely mocked. | Risk controls are illusory and not based on actual model inference. |
| **B04** | `src/phase0/ai/ultra.py` | **Fake AI Implementation**: The "Ultra Lane" news authenticity check is mocked. | System cannot filter fake news or verify signal authenticity. |
| **B05** | `src/phase0/ibkr_execution.py`:247 | **Time Parsing Error**: `_parse_hhmm` returns `0` (midnight) on exception instead of raising an error or returning `None`. | Invalid time strings are treated as 00:00, potentially allowing trading during forbidden hours. |

### High Severity

| ID | Location | Description | Impact |
|:---|:---|:---|:---|
| **B06** | `src/phase0/ibkr_execution.py`:232 | **Session Window Logic**: `_is_within_session_window` relies on `_parse_hhmm`. If parsing fails (returns 0), the logic may incorrectly validate a time window. | Trading allowed outside of safe session hours. |
| **B07** | `src/phase0/lanes/__init__.py`:637 | **Silent Failure in Data Fetch**: `_load_market_snapshot_from_yfinance` catches generic `Exception` and continues without logging. | System silently falls back to stale/hardcoded data if live data fetch fails. |
| **B08** | `src/phase0/discipline.py`:86-93 | **Forced Trading Logic**: The system forces a "buy" action if daily action quotas are not met, regardless of market conditions. | Violates quantitative trading principles; incurs unnecessary risk and fees. |
| **B09** | `src/phase0/strategies/library.py`:21 | **Division by Zero Risk**: Momentum score calculation divides by `volatility`. While capped at 0.01, extremely low volatility can still produce exploded scores. | Artificial inflation of strategy scores for stagnant assets. |
| **B10** | `src/phase0/ibkr_order_adapter.py`:24 | **Quantity Truncation**: `qty = int(...)` silently truncates floating point quantities. | Loss of precision for fractional share trading or specific asset classes. |

### Medium Severity

| ID | Location | Description | Impact |
|:---|:---|:---|:---|
| **B11** | `src/phase0/strategies/library.py`:101 | **Naive Sentiment Analysis**: Uses simple keyword counting ("beat", "surge") which fails on negations (e.g., "did not beat"). | High rate of false positive/negative signals from news. |
| **B12** | `src/phase0/ibkr_execution.py`:81 | **Bracket Order Disconnect**: The client rebuilds bracket orders using `ib.bracketOrder` helper, potentially ignoring the `parentRef` linking provided by the adapter. | Order hierarchy may be lost or incorrectly structured in IBKR. |
| **B13** | `src/phase0/audit.py`:167 | **Race Condition in State**: `is_stoploss_override_used` deletes expired state. In concurrent execution, multiple processes might try to delete the same row. | Potential `database is locked` errors or race conditions. |
| **B14** | `src/phase0/config.py`:265 | **Config Crash**: `_read_bool_env` raises `AppConfig` error for unknown boolean strings instead of defaulting to False or logging warning. | Application fails to start on minor config typos. |
| **B15** | `src/phase0/lanes/high.py`:258 | **Cooldown Bypass**: If `last_exit_at` is missing or unparseable (`None`), `_check_cooldown` returns `None` (pass). | Cooldown safety mechanism fails open instead of closed. |
| **B16** | `src/phase0/lanes/high.py`:384 | **Cost Estimation Accuracy**: `_estimate_transaction_cost` ignores minimum commission fees (common in IBKR). | Profitability calculations are overly optimistic for small orders. |
| **B17** | `src/phase0/strategies/base.py`:569 | **Math Overflow**: `math.exp` in softmax calculation can overflow if score differences are large. | Runtime crash during signal weight normalization. |
| **B18** | `src/phase0/ibkr_execution.py`:97 | **Unchecked Order Status**: `placeOrder` returns a trade object, but the code doesn't verify if `trade.orderStatus` is valid before proceeding. | System assumes order acceptance even if rejected locally by API. |
| **B19** | `src/phase0/main.py`:68 | **State Sync Failure**: `_read_current_drawdown_pct` reads an env var that is never written to by the application. | Drawdown protection relies on a static/missing value, rendering it useless. |
| **B20** | `src/phase0/llm_gateway.py`:138 | **Null Content Handling**: OpenAI API can return `None` content (e.g. content filter). The code assumes `str`. | Crash when LLM refuses to answer or triggers safety filters. |

---

## ⚠️ Problem List

### Architecture & Design

1.  **Mocked Core Logic**: The entire `src/phase0/ai` directory is a placeholder. The `LLMGateway` is implemented but never connected to the decision logic.
2.  **Synchronous Blocking Loop**: The main `run_lane_cycle` is synchronous. Integrating real LLM calls (2-10s latency) will block the entire trading loop.
3.  **Monolithic Lane Controller**: `src/phase0/lanes/__init__.py` acts as a massive controller, mixing data fetching, strategy execution, and AI orchestration.
4.  **Hardcoded Dependencies**: The system relies heavily on `_default_market_snapshot` hardcoded data, making it fragile for any real-world testing.
5.  **Single-Threaded Bus**: `InMemoryLaneBus` is process-local. Restarting the process loses all event history and state.

### Reliability & Maintenance

6.  **Unmanaged SQLite Connections**: `audit.py` opens/closes DB connections on every write without pooling, risking `database is locked` errors under load.
7.  **Implicit Schema Migration**: Database schema changes (e.g., adding `expires_at`) are hardcoded in the startup check (`ensure_audit_db`) rather than a proper migration tool.
8.  **Fragile Data Source**: Reliance on `yfinance` (unofficial API) without robust error handling or fallback strategies is risky for a financial app.
9.  **Magic Numbers**: Strategy parameters (e.g., `20d` momentum, `0.45` weight) are hardcoded in `library.py` rather than configurable.
10. **Huge Config Class**: `AppConfig` is a god-class with mixed concerns (runtime, risk, strategy, ai), making it hard to manage.

### Security & Safety

11. **Insecure Defaults**: `LLM_API_KEY` defaults to "dummy". In a production build, this should fail fast if not provided.
12. **Environment Variable Injection**: Reading config via `os.getenv` scattered throughout the code makes it hard to track all configuration sources.
13. **Lack of Secret Management**: No integration with secret managers; relies purely on plaintext env vars.

### Performance & Scalability

14. **Serial Strategy Execution**: Strategies are run sequentially. As the number of strategies or symbols grows, this will become a bottleneck.
15. **No Async IO**: Network operations (IBKR, LLM) are blocking, wasting CPU cycles waiting for IO.

### Code Quality

16. **Lack of Structured Logging**: While `logger.py` exists, much of the logging is done via `json.dumps` in `main.py`, inconsistent with standard logging practices.
17. **Insufficient Testing**: Tests cover the mocked logic, giving a false sense of security. Integration tests with real components are missing.
18. **Type Hinting Only**: Python type hints are used but not enforced at runtime (e.g., no Pydantic for data validation at API boundaries).
19. **Missing Documentation**: Complex logic in `high.py` and `strategies` lacks docstrings explaining the financial rationale.
20. **Duplicate Logic**: `Relative Strength` in `yfinance` loader is calculated identically to `Momentum`, suggesting a misunderstanding or simplification of the indicator.

---

## Next Steps

1.  **Fix Critical Bugs**: Prioritize B01 (JSON Crash) and B05/B06 (Time Parsing) to prevent runtime failures.
2.  **Wire Up AI**: Replace the mocked AI implementations in `src/phase0/ai/` with calls to `UnifiedLLMGateway`.
3.  **Refactor Main Loop**: Convert `run_lane_cycle` to an asynchronous model to handle LLM latency.
4.  **Harden Data Layer**: Implement proper SQLite connection pooling and a migration system.
