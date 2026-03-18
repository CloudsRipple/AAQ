from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import RuntimeMode, RuntimeProfile, load_config
from phase0.errors import AppError


class ConfigTests(unittest.TestCase):
    def test_loads_llm_gateway_related_settings(self) -> None:
        env = {
            "PHASE0_PROFILE": "cloud",
            "LLM_BASE_URL": "https://gateway.example.com/v1",
            "LLM_API_KEY": "secret",
            "LLM_LOCAL_MODEL": "qwen2.5:14b",
            "LLM_CLOUD_MODEL": "gpt-4o-mini",
            "LLM_TIMEOUT_SECONDS": "30",
            "LLM_MAX_RETRIES": "5",
            "LLM_BACKOFF_SECONDS": "0.25",
            "LLM_RATE_LIMIT_PER_SECOND": "12",
            "RUNTIME_MODE": "eco",
            "RISK_SINGLE_TRADE_PCT": "0.012",
            "RISK_TOTAL_EXPOSURE_PCT": "0.28",
            "RISK_STOP_LOSS_MIN_PCT": "0.04",
            "RISK_STOP_LOSS_MAX_PCT": "0.09",
            "RISK_COOLDOWN_HOURS": "12",
            "RISK_HOLDING_DAYS": "3",
            "LANE_BUS_DEDUP_TTL_SECONDS": "90",
            "STRATEGY_ENABLED_LIST": "momentum,news_sentiment",
            "STRATEGY_ROTATION_TOP_K": "4",
            "STRATEGY_NEWS_POSITIVE_THRESHOLD": "0.25",
            "STRATEGY_NEWS_NEGATIVE_THRESHOLD": "-0.3",
            "STRATEGY_PLUGIN_MODULES": "my_quant_pkg.strategies",
            "FACTOR_PLUGIN_MODULES": "my_quant_pkg.factors",
            "HIGH_RISK_MULTIPLIER_MIN": "0.7",
            "HIGH_RISK_MULTIPLIER_MAX": "1.4",
            "HIGH_TAKE_PROFIT_BOOST_MAX_PCT": "0.15",
            "AI_MESSAGE_MAX_AGE_MINUTES": "240",
            "AI_LOW_COMMITTEE_MODELS": "m1,m2,m3",
            "AI_LOW_COMMITTEE_MIN_SUPPORT": "2",
            "AI_HIGH_MODE": "cloud",
            "AI_HIGH_COMMITTEE_MODELS": "h1,h2,h3",
            "AI_HIGH_COMMITTEE_MIN_SUPPORT": "2",
            "AI_HIGH_CONFIDENCE_GATE": "0.6",
            "AI_STOP_LOSS_DEFAULT_PCT": "0.02",
            "AI_STOP_LOSS_BREAK_MAX_PCT": "0.05",
            "AI_STATE_DB_PATH": "artifacts/custom_state.db",
            "AI_MEMORY_DB_PATH": "artifacts/custom_memory.db",
            "AI_ENABLED": "false",
            "DISCIPLINE_MIN_ACTIONS_PER_DAY": "2",
            "DISCIPLINE_HOLD_SCORE_THRESHOLD": "0.8",
            "DISCIPLINE_ENABLE_DAILY_CYCLE": "true",
        }
        with patch.dict("os.environ", env, clear=True):
            config = load_config()
        self.assertEqual(RuntimeProfile.CLOUD, config.runtime_profile)
        self.assertEqual(RuntimeMode.ECO, config.runtime_mode)
        self.assertEqual("https://gateway.example.com/v1", config.llm_base_url)
        self.assertEqual("secret", config.llm_api_key)
        self.assertEqual("qwen2.5:14b", config.llm_local_model)
        self.assertEqual("gpt-4o-mini", config.llm_cloud_model)
        self.assertEqual(30.0, config.llm_timeout_seconds)
        self.assertEqual(5, config.llm_max_retries)
        self.assertEqual(0.25, config.llm_backoff_seconds)
        self.assertEqual(12.0, config.llm_rate_limit_per_second)
        self.assertEqual(0.012, config.risk_single_trade_pct)
        self.assertEqual(0.28, config.risk_total_exposure_pct)
        self.assertEqual(0.04, config.risk_stop_loss_min_pct)
        self.assertEqual(0.09, config.risk_stop_loss_max_pct)
        self.assertEqual(12, config.cooldown_hours)
        self.assertEqual(3, config.holding_days)
        self.assertEqual(90, config.lane_bus_dedup_ttl_seconds)
        self.assertEqual("momentum,news_sentiment", config.strategy_enabled_list)
        self.assertEqual(4, config.strategy_rotation_top_k)
        self.assertEqual(0.25, config.strategy_news_positive_threshold)
        self.assertEqual(-0.3, config.strategy_news_negative_threshold)
        self.assertEqual("my_quant_pkg.strategies", config.strategy_plugin_modules)
        self.assertEqual("my_quant_pkg.factors", config.factor_plugin_modules)
        self.assertEqual(0.7, config.high_risk_multiplier_min)
        self.assertEqual(1.4, config.high_risk_multiplier_max)
        self.assertEqual(0.15, config.high_take_profit_boost_max_pct)
        self.assertEqual(240, config.ai_message_max_age_minutes)
        self.assertEqual("m1,m2,m3", config.ai_low_committee_models)
        self.assertEqual(2, config.ai_low_committee_min_support)
        self.assertEqual("cloud", config.ai_high_mode)
        self.assertEqual("h1,h2,h3", config.ai_high_committee_models)
        self.assertEqual(2, config.ai_high_committee_min_support)
        self.assertEqual(0.6, config.ai_high_confidence_gate)
        self.assertEqual(0.02, config.ai_stop_loss_default_pct)
        self.assertEqual(0.05, config.ai_stop_loss_break_max_pct)
        self.assertEqual("artifacts/custom_state.db", config.ai_state_db_path)
        self.assertEqual("artifacts/custom_memory.db", config.ai_memory_db_path)
        self.assertFalse(config.ai_enabled)
        self.assertFalse(config.event_driven_runtime_enabled)
        self.assertEqual(2, config.discipline_min_actions_per_day)
        self.assertEqual(0.8, config.discipline_hold_score_threshold)
        self.assertTrue(config.discipline_enable_daily_cycle)

    def test_raises_when_retry_rate_is_invalid_float(self) -> None:
        with patch.dict("os.environ", {"LLM_RATE_LIMIT_PER_SECOND": "invalid"}, clear=True):
            with self.assertRaises(AppError):
                load_config()

    def test_raises_when_runtime_mode_is_invalid(self) -> None:
        with patch.dict("os.environ", {"RUNTIME_MODE": "turbo"}, clear=True):
            with self.assertRaises(AppError):
                load_config()


if __name__ == "__main__":
    unittest.main()
