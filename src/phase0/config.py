from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os

from .errors import AppError, ErrorCode


class RuntimeProfile(str, Enum):
    PAPER = "paper"
    LOCAL = "local"
    CLOUD = "cloud"


class RuntimeMode(str, Enum):
    NORMAL = "normal"
    ECO = "eco"
    PERF = "perf"


@dataclass(frozen=True)
class AppConfig:
    runtime_profile: RuntimeProfile
    runtime_mode: RuntimeMode
    log_level: str
    ibkr_host: str
    ibkr_port: int
    llm_base_url: str
    llm_api_key: str
    llm_local_model: str
    llm_cloud_model: str
    llm_timeout_seconds: float
    llm_max_retries: int
    llm_backoff_seconds: float
    llm_rate_limit_per_second: float
    risk_single_trade_pct: float
    risk_total_exposure_pct: float
    risk_stop_loss_min_pct: float
    risk_stop_loss_max_pct: float
    risk_max_drawdown_pct: float
    risk_min_trade_units: int
    risk_slippage_bps: float
    risk_commission_per_share: float
    risk_exposure_softmax_temperature: float
    cooldown_hours: int
    holding_days: int
    lane_bus_dedup_ttl_seconds: int
    strategy_enabled_list: str
    strategy_rotation_top_k: int
    strategy_news_positive_threshold: float
    strategy_news_negative_threshold: float
    strategy_plugin_modules: str
    factor_plugin_modules: str
    high_risk_multiplier_min: float
    high_risk_multiplier_max: float
    high_take_profit_boost_max_pct: float
    ai_message_max_age_minutes: int
    ai_low_committee_models: str
    ai_low_committee_min_support: int
    ai_high_mode: str
    ai_high_committee_models: str
    ai_high_committee_min_support: int
    ai_high_confidence_gate: float
    ai_stop_loss_default_pct: float
    ai_stop_loss_break_max_pct: float
    ai_stoploss_override_ttl_hours: int
    ai_state_db_path: str
    ai_memory_db_path: str
    ai_enabled: bool
    discipline_min_actions_per_day: int
    discipline_hold_score_threshold: float
    discipline_enable_daily_cycle: bool
    market_data_mode: str
    market_symbols: str
    market_snapshot_json: str
    event_driven_runtime_enabled: bool
    lane_scheduler_enabled: bool
    lane_rebalance_interval_seconds: int
    lane_scheduler_cycles: int
    execution_session_guard_enabled: bool
    execution_session_start_utc: str
    execution_session_end_utc: str
    execution_good_after_seconds: int
    ultra_price_spike_threshold_pct: float = 0.02
    ultra_volume_zscore_threshold: float = 2.2
    ultra_trailing_stop_break_pct: float = 0.015
    ultra_rule_window_seconds: int = 60
    ultra_vector_similarity_threshold: float = 0.78
    ultra_embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    ultra_executor_workers: int = 2
    ultra_queue_maxsize: int = 512
    ultra_lancedb_uri: str = "src/phase0/data/lancedb_store"


def load_config() -> AppConfig:
    profile_raw = os.getenv("PHASE0_PROFILE", RuntimeProfile.PAPER.value).lower()
    try:
        runtime_profile = RuntimeProfile(profile_raw)
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.CONFIG_INVALID_PROFILE,
            message=f"unsupported runtime profile: {profile_raw}",
        ) from exc

    mode_raw = os.getenv("RUNTIME_MODE", RuntimeMode.NORMAL.value).lower()
    try:
        runtime_mode = RuntimeMode(mode_raw)
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.CONFIG_INVALID_VALUE,
            message=f"unsupported runtime mode: {mode_raw}",
        ) from exc

    ibkr_host = os.getenv("IBKR_HOST", "127.0.0.1")
    ibkr_port = _read_int_env("IBKR_PORT", 7497)
    llm_base_url = os.getenv("LLM_BASE_URL", "").strip()
    llm_api_key = os.getenv("LLM_API_KEY", "").strip()
    llm_local_model = os.getenv("LLM_LOCAL_MODEL", "llama3.1:8b")
    llm_cloud_model = os.getenv("LLM_CLOUD_MODEL", "gpt-4o-mini")
    llm_timeout_seconds = _read_float_env("LLM_TIMEOUT_SECONDS", 20.0)
    llm_max_retries = _read_int_env("LLM_MAX_RETRIES", 3)
    llm_backoff_seconds = _read_float_env("LLM_BACKOFF_SECONDS", 0.5)
    llm_rate_limit_per_second = _read_float_env("LLM_RATE_LIMIT_PER_SECOND", 2.0)
    risk_single_trade_pct = _read_float_env("RISK_SINGLE_TRADE_PCT", 0.01)
    risk_total_exposure_pct = _read_float_env("RISK_TOTAL_EXPOSURE_PCT", 0.30)
    risk_stop_loss_min_pct = _read_float_env("RISK_STOP_LOSS_MIN_PCT", 0.05)
    risk_stop_loss_max_pct = _read_float_env("RISK_STOP_LOSS_MAX_PCT", 0.08)
    risk_max_drawdown_pct = _read_float_env("RISK_MAX_DRAWDOWN_PCT", 0.12)
    risk_min_trade_units = _read_int_env("RISK_MIN_TRADE_UNITS", 1)
    risk_slippage_bps = _read_float_env("RISK_SLIPPAGE_BPS", 2.0)
    risk_commission_per_share = _read_float_env("RISK_COMMISSION_PER_SHARE", 0.005)
    risk_exposure_softmax_temperature = _read_float_env("RISK_EXPOSURE_SOFTMAX_TEMPERATURE", 1.0)
    cooldown_hours = _read_int_env("RISK_COOLDOWN_HOURS", 24)
    holding_days = _read_int_env("RISK_HOLDING_DAYS", 2)
    lane_bus_dedup_ttl_seconds = _read_int_env("LANE_BUS_DEDUP_TTL_SECONDS", 300)
    strategy_enabled_list = os.getenv(
        "STRATEGY_ENABLED_LIST",
        "momentum,mean_reversion,sector_rotation,news_sentiment",
    )
    strategy_rotation_top_k = _read_int_env("STRATEGY_ROTATION_TOP_K", 3)
    strategy_news_positive_threshold = _read_float_env("STRATEGY_NEWS_POSITIVE_THRESHOLD", 0.2)
    strategy_news_negative_threshold = _read_float_env("STRATEGY_NEWS_NEGATIVE_THRESHOLD", -0.2)
    strategy_plugin_modules = os.getenv("STRATEGY_PLUGIN_MODULES", "")
    factor_plugin_modules = os.getenv("FACTOR_PLUGIN_MODULES", "")
    high_risk_multiplier_min = _read_float_env("HIGH_RISK_MULTIPLIER_MIN", 0.5)
    high_risk_multiplier_max = _read_float_env("HIGH_RISK_MULTIPLIER_MAX", 1.5)
    high_take_profit_boost_max_pct = _read_float_env("HIGH_TAKE_PROFIT_BOOST_MAX_PCT", 0.2)
    ai_message_max_age_minutes = _read_int_env("AI_MESSAGE_MAX_AGE_MINUTES", 180)
    ai_low_committee_models = os.getenv(
        "AI_LOW_COMMITTEE_MODELS",
        "gpt-4o-mini,claude-3-5-sonnet,gemini-2.0-flash",
    )
    ai_low_committee_min_support = _read_int_env("AI_LOW_COMMITTEE_MIN_SUPPORT", 2)
    ai_high_mode = os.getenv("AI_HIGH_MODE", "local").strip().lower()
    ai_high_committee_models = os.getenv(
        "AI_HIGH_COMMITTEE_MODELS",
        "local-risk-v1,gpt-4o-mini",
    )
    ai_high_committee_min_support = _read_int_env("AI_HIGH_COMMITTEE_MIN_SUPPORT", 1)
    ai_high_confidence_gate = _read_float_env("AI_HIGH_CONFIDENCE_GATE", 0.58)
    ai_stop_loss_default_pct = _read_float_env("AI_STOP_LOSS_DEFAULT_PCT", 0.05)
    ai_stop_loss_break_max_pct = _read_float_env("AI_STOP_LOSS_BREAK_MAX_PCT", 0.08)
    ai_stoploss_override_ttl_hours = _read_int_env("AI_STOPLOSS_OVERRIDE_TTL_HOURS", 72)
    ultra_price_spike_threshold_pct = _read_float_env("ULTRA_PRICE_SPIKE_THRESHOLD_PCT", 0.02)
    ultra_volume_zscore_threshold = _read_float_env("ULTRA_VOLUME_ZSCORE_THRESHOLD", 2.2)
    ultra_trailing_stop_break_pct = _read_float_env("ULTRA_TRAILING_STOP_BREAK_PCT", 0.015)
    ultra_rule_window_seconds = _read_int_env("ULTRA_RULE_WINDOW_SECONDS", 60)
    ultra_vector_similarity_threshold = _read_float_env("ULTRA_VECTOR_SIMILARITY_THRESHOLD", 0.78)
    ultra_embedding_model_name = os.getenv("ULTRA_EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")
    ultra_executor_workers = _read_int_env("ULTRA_EXECUTOR_WORKERS", 2)
    ultra_queue_maxsize = _read_int_env("ULTRA_QUEUE_MAXSIZE", 512)
    ultra_lancedb_uri = os.getenv("ULTRA_LANCEDB_URI", "src/phase0/data/lancedb_store")
    ai_state_db_path = os.getenv("AI_STATE_DB_PATH", "artifacts/phase0_state.db")
    ai_memory_db_path = os.getenv("AI_MEMORY_DB_PATH", "artifacts/phase0_memory.db")
    ai_enabled = _read_bool_env("AI_ENABLED", True)
    discipline_min_actions_per_day = _read_int_env("DISCIPLINE_MIN_ACTIONS_PER_DAY", 1)
    discipline_hold_score_threshold = _read_float_env("DISCIPLINE_HOLD_SCORE_THRESHOLD", 0.72)
    discipline_enable_daily_cycle = _read_bool_env("DISCIPLINE_ENABLE_DAILY_CYCLE", True)
    market_data_mode = os.getenv("MARKET_DATA_MODE", "default").strip().lower()
    market_symbols = os.getenv("MARKET_SYMBOLS", "AAPL,MSFT,NVDA,XOM")
    market_snapshot_json = os.getenv("MARKET_SNAPSHOT_JSON", "")
    event_driven_runtime_enabled = _read_bool_env("EVENT_DRIVEN_RUNTIME_ENABLED", False)
    lane_scheduler_enabled = _read_bool_env("LANE_SCHEDULER_ENABLED", False)
    lane_rebalance_interval_seconds = _read_int_env("LANE_REBALANCE_INTERVAL_SECONDS", 60)
    lane_scheduler_cycles = _read_int_env("LANE_SCHEDULER_CYCLES", 1)
    execution_session_guard_enabled = _read_bool_env("EXECUTION_SESSION_GUARD_ENABLED", True)
    execution_session_start_utc = os.getenv("EXECUTION_SESSION_START_UTC", "13:30")
    execution_session_end_utc = os.getenv("EXECUTION_SESSION_END_UTC", "20:00")
    execution_good_after_seconds = _read_int_env("EXECUTION_GOOD_AFTER_SECONDS", 5)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    return AppConfig(
        runtime_profile=runtime_profile,
        runtime_mode=runtime_mode,
        log_level=log_level,
        ibkr_host=ibkr_host,
        ibkr_port=ibkr_port,
        llm_base_url=llm_base_url,
        llm_api_key=llm_api_key,
        llm_local_model=llm_local_model,
        llm_cloud_model=llm_cloud_model,
        llm_timeout_seconds=llm_timeout_seconds,
        llm_max_retries=llm_max_retries,
        llm_backoff_seconds=llm_backoff_seconds,
        llm_rate_limit_per_second=llm_rate_limit_per_second,
        risk_single_trade_pct=risk_single_trade_pct,
        risk_total_exposure_pct=risk_total_exposure_pct,
        risk_stop_loss_min_pct=risk_stop_loss_min_pct,
        risk_stop_loss_max_pct=risk_stop_loss_max_pct,
        risk_max_drawdown_pct=risk_max_drawdown_pct,
        risk_min_trade_units=risk_min_trade_units,
        risk_slippage_bps=risk_slippage_bps,
        risk_commission_per_share=risk_commission_per_share,
        risk_exposure_softmax_temperature=risk_exposure_softmax_temperature,
        cooldown_hours=cooldown_hours,
        holding_days=holding_days,
        lane_bus_dedup_ttl_seconds=lane_bus_dedup_ttl_seconds,
        strategy_enabled_list=strategy_enabled_list,
        strategy_rotation_top_k=strategy_rotation_top_k,
        strategy_news_positive_threshold=strategy_news_positive_threshold,
        strategy_news_negative_threshold=strategy_news_negative_threshold,
        strategy_plugin_modules=strategy_plugin_modules,
        factor_plugin_modules=factor_plugin_modules,
        high_risk_multiplier_min=high_risk_multiplier_min,
        high_risk_multiplier_max=high_risk_multiplier_max,
        high_take_profit_boost_max_pct=high_take_profit_boost_max_pct,
        ai_message_max_age_minutes=ai_message_max_age_minutes,
        ai_low_committee_models=ai_low_committee_models,
        ai_low_committee_min_support=ai_low_committee_min_support,
        ai_high_mode=ai_high_mode,
        ai_high_committee_models=ai_high_committee_models,
        ai_high_committee_min_support=ai_high_committee_min_support,
        ai_high_confidence_gate=ai_high_confidence_gate,
        ai_stop_loss_default_pct=ai_stop_loss_default_pct,
        ai_stop_loss_break_max_pct=ai_stop_loss_break_max_pct,
        ai_stoploss_override_ttl_hours=ai_stoploss_override_ttl_hours,
        ultra_price_spike_threshold_pct=ultra_price_spike_threshold_pct,
        ultra_volume_zscore_threshold=ultra_volume_zscore_threshold,
        ultra_trailing_stop_break_pct=ultra_trailing_stop_break_pct,
        ultra_rule_window_seconds=ultra_rule_window_seconds,
        ultra_vector_similarity_threshold=ultra_vector_similarity_threshold,
        ultra_embedding_model_name=ultra_embedding_model_name,
        ultra_executor_workers=ultra_executor_workers,
        ultra_queue_maxsize=ultra_queue_maxsize,
        ultra_lancedb_uri=ultra_lancedb_uri,
        ai_state_db_path=ai_state_db_path,
        ai_memory_db_path=ai_memory_db_path,
        ai_enabled=ai_enabled,
        discipline_min_actions_per_day=discipline_min_actions_per_day,
        discipline_hold_score_threshold=discipline_hold_score_threshold,
        discipline_enable_daily_cycle=discipline_enable_daily_cycle,
        market_data_mode=market_data_mode,
        market_symbols=market_symbols,
        market_snapshot_json=market_snapshot_json,
        event_driven_runtime_enabled=event_driven_runtime_enabled,
        lane_scheduler_enabled=lane_scheduler_enabled,
        lane_rebalance_interval_seconds=lane_rebalance_interval_seconds,
        lane_scheduler_cycles=lane_scheduler_cycles,
        execution_session_guard_enabled=execution_session_guard_enabled,
        execution_session_start_utc=execution_session_start_utc,
        execution_session_end_utc=execution_session_end_utc,
        execution_good_after_seconds=execution_good_after_seconds,
    )


def _read_int_env(name: str, default_value: int) -> int:
    raw = os.getenv(name, str(default_value))
    try:
        return int(raw)
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.CONFIG_INVALID_VALUE,
            message=f"{name} must be integer, got: {raw}",
        ) from exc


def _read_float_env(name: str, default_value: float) -> float:
    raw = os.getenv(name, str(default_value))
    try:
        return float(raw)
    except ValueError as exc:
        raise AppError(
            code=ErrorCode.CONFIG_INVALID_VALUE,
            message=f"{name} must be float, got: {raw}",
        ) from exc


def _read_bool_env(name: str, default_value: bool) -> bool:
    raw = os.getenv(name, "true" if default_value else "false").strip().lower()
    if raw in {"1", "true", "yes", "on", "y", "t", "enabled"}:
        return True
    if raw in {"0", "false", "no", "off", "n", "f", "disabled"}:
        return False
    if raw == "":
        return default_value
    raise AppError(
        code=ErrorCode.CONFIG_INVALID_VALUE,
        message=f"{name} must be bool, got: {raw}",
    )
