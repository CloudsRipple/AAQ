from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import AppConfig, RuntimeMode, RuntimeProfile
from phase0.llm_connectivity_check import run_llm_probe


class FakeGateway:
    def __init__(self, settings: object, profile: RuntimeProfile) -> None:
        self.model = "test-model-cloud" if profile == RuntimeProfile.CLOUD else "test-model-local"

    def check_connectivity(self) -> dict[str, object]:
        return {
            "ok": True,
            "base_url": "http://localhost:11434/v1",
            "model": self.model,
            "latency_ms": 10.2,
            "reply": "pong",
        }


class LLMConnectivityCheckTests(unittest.TestCase):
    def test_run_probe_returns_success_report(self) -> None:
        config = AppConfig(
            runtime_profile=RuntimeProfile.LOCAL,
            runtime_mode=RuntimeMode.NORMAL,
            log_level="INFO",
            ibkr_host="127.0.0.1",
            ibkr_port=7497,
            llm_base_url="http://localhost:11434/v1",
            llm_api_key="dummy",
            llm_local_model="llama3.1:8b",
            llm_cloud_model="gpt-4o-mini",
            llm_timeout_seconds=20.0,
            llm_max_retries=3,
            llm_backoff_seconds=0.5,
            llm_rate_limit_per_second=2.0,
            risk_single_trade_pct=0.01,
            risk_total_exposure_pct=0.3,
            risk_stop_loss_min_pct=0.05,
            risk_stop_loss_max_pct=0.08,
            risk_max_drawdown_pct=0.12,
            risk_min_trade_units=1,
            risk_slippage_bps=2.0,
            risk_commission_per_share=0.005,
            risk_exposure_softmax_temperature=1.0,
            cooldown_hours=24,
            holding_days=2,
            lane_bus_dedup_ttl_seconds=300,
            strategy_enabled_list="momentum,news_sentiment",
            strategy_rotation_top_k=3,
            strategy_news_positive_threshold=0.2,
            strategy_news_negative_threshold=-0.2,
            strategy_plugin_modules="",
            factor_plugin_modules="",
            high_risk_multiplier_min=0.5,
            high_risk_multiplier_max=1.5,
            high_take_profit_boost_max_pct=0.2,
            ai_message_max_age_minutes=180,
            ai_low_committee_models="gpt-4o-mini,claude-3-5-sonnet,gemini-2.0-flash",
            ai_low_committee_min_support=2,
            ai_high_mode="local",
            ai_high_committee_models="local-risk-v1,gpt-4o-mini",
            ai_high_committee_min_support=1,
            ai_high_confidence_gate=0.58,
            ai_stop_loss_default_pct=0.02,
            ai_stop_loss_break_max_pct=0.05,
            ai_stoploss_override_ttl_hours=72,
            ai_state_db_path="artifacts/test_state.db",
            ai_memory_db_path="artifacts/test_memory.db",
            ai_enabled=True,
            discipline_min_actions_per_day=1,
            discipline_hold_score_threshold=0.72,
            discipline_enable_daily_cycle=True,
            market_data_mode="default",
            market_symbols="AAPL,MSFT,NVDA,XOM",
            market_snapshot_json="",
            event_driven_runtime_enabled=False,
            lane_scheduler_enabled=False,
            lane_rebalance_interval_seconds=60,
            lane_scheduler_cycles=1,
            execution_session_guard_enabled=True,
            execution_session_start_utc="13:30",
            execution_session_end_utc="20:00",
            execution_good_after_seconds=5,
        )
        with patch("phase0.llm_connectivity_check.load_config", return_value=config), patch(
            "phase0.llm_connectivity_check.UnifiedLLMGateway",
            FakeGateway,
        ):
            report = run_llm_probe(profile=RuntimeProfile.CLOUD)
        self.assertTrue(report["ok"])
        self.assertEqual("cloud", report["profile"])
        self.assertEqual("test-model-cloud", report["model"])

    def test_run_probe_returns_structured_error(self) -> None:
        config = AppConfig(
            runtime_profile=RuntimeProfile.LOCAL,
            runtime_mode=RuntimeMode.NORMAL,
            log_level="INFO",
            ibkr_host="127.0.0.1",
            ibkr_port=7497,
            llm_base_url="http://localhost:11434/v1",
            llm_api_key="dummy",
            llm_local_model="llama3.1:8b",
            llm_cloud_model="gpt-4o-mini",
            llm_timeout_seconds=20.0,
            llm_max_retries=3,
            llm_backoff_seconds=0.5,
            llm_rate_limit_per_second=2.0,
            risk_single_trade_pct=0.01,
            risk_total_exposure_pct=0.3,
            risk_stop_loss_min_pct=0.05,
            risk_stop_loss_max_pct=0.08,
            risk_max_drawdown_pct=0.12,
            risk_min_trade_units=1,
            risk_slippage_bps=2.0,
            risk_commission_per_share=0.005,
            risk_exposure_softmax_temperature=1.0,
            cooldown_hours=24,
            holding_days=2,
            lane_bus_dedup_ttl_seconds=300,
            strategy_enabled_list="momentum,news_sentiment",
            strategy_rotation_top_k=3,
            strategy_news_positive_threshold=0.2,
            strategy_news_negative_threshold=-0.2,
            strategy_plugin_modules="",
            factor_plugin_modules="",
            high_risk_multiplier_min=0.5,
            high_risk_multiplier_max=1.5,
            high_take_profit_boost_max_pct=0.2,
            ai_message_max_age_minutes=180,
            ai_low_committee_models="gpt-4o-mini,claude-3-5-sonnet,gemini-2.0-flash",
            ai_low_committee_min_support=2,
            ai_high_mode="local",
            ai_high_committee_models="local-risk-v1,gpt-4o-mini",
            ai_high_committee_min_support=1,
            ai_high_confidence_gate=0.58,
            ai_stop_loss_default_pct=0.02,
            ai_stop_loss_break_max_pct=0.05,
            ai_stoploss_override_ttl_hours=72,
            ai_state_db_path="artifacts/test_state.db",
            ai_memory_db_path="artifacts/test_memory.db",
            ai_enabled=True,
            discipline_min_actions_per_day=1,
            discipline_hold_score_threshold=0.72,
            discipline_enable_daily_cycle=True,
            market_data_mode="default",
            market_symbols="AAPL,MSFT,NVDA,XOM",
            market_snapshot_json="",
            event_driven_runtime_enabled=False,
            lane_scheduler_enabled=False,
            lane_rebalance_interval_seconds=60,
            lane_scheduler_cycles=1,
            execution_session_guard_enabled=True,
            execution_session_start_utc="13:30",
            execution_session_end_utc="20:00",
            execution_good_after_seconds=5,
        )
        with patch("phase0.llm_connectivity_check.load_config", return_value=config), patch(
            "phase0.llm_connectivity_check.UnifiedLLMGateway",
            side_effect=RuntimeError("boom"),
        ):
            report = run_llm_probe(profile=RuntimeProfile.CLOUD)
        self.assertFalse(report["ok"])
        self.assertEqual("RuntimeError", report["error"])
        self.assertEqual("RuntimeError", report["error_type"])
        self.assertEqual("INTERNAL_ERROR", report["error_code"])

    def test_run_probe_skips_when_placeholder_config(self) -> None:
        config = AppConfig(
            runtime_profile=RuntimeProfile.LOCAL,
            runtime_mode=RuntimeMode.NORMAL,
            log_level="INFO",
            ibkr_host="127.0.0.1",
            ibkr_port=7497,
            llm_base_url="",
            llm_api_key="",
            llm_local_model="llama3.1:8b",
            llm_cloud_model="gpt-4o-mini",
            llm_timeout_seconds=20.0,
            llm_max_retries=3,
            llm_backoff_seconds=0.5,
            llm_rate_limit_per_second=2.0,
            risk_single_trade_pct=0.01,
            risk_total_exposure_pct=0.3,
            risk_stop_loss_min_pct=0.05,
            risk_stop_loss_max_pct=0.08,
            risk_max_drawdown_pct=0.12,
            risk_min_trade_units=1,
            risk_slippage_bps=2.0,
            risk_commission_per_share=0.005,
            risk_exposure_softmax_temperature=1.0,
            cooldown_hours=24,
            holding_days=2,
            lane_bus_dedup_ttl_seconds=300,
            strategy_enabled_list="momentum,news_sentiment",
            strategy_rotation_top_k=3,
            strategy_news_positive_threshold=0.2,
            strategy_news_negative_threshold=-0.2,
            strategy_plugin_modules="",
            factor_plugin_modules="",
            high_risk_multiplier_min=0.5,
            high_risk_multiplier_max=1.5,
            high_take_profit_boost_max_pct=0.2,
            ai_message_max_age_minutes=180,
            ai_low_committee_models="gpt-4o-mini,claude-3-5-sonnet,gemini-2.0-flash",
            ai_low_committee_min_support=2,
            ai_high_mode="local",
            ai_high_committee_models="local-risk-v1,gpt-4o-mini",
            ai_high_committee_min_support=1,
            ai_high_confidence_gate=0.58,
            ai_stop_loss_default_pct=0.02,
            ai_stop_loss_break_max_pct=0.05,
            ai_stoploss_override_ttl_hours=72,
            ai_state_db_path="artifacts/test_state.db",
            ai_memory_db_path="artifacts/test_memory.db",
            ai_enabled=True,
            discipline_min_actions_per_day=1,
            discipline_hold_score_threshold=0.72,
            discipline_enable_daily_cycle=True,
            market_data_mode="default",
            market_symbols="AAPL,MSFT,NVDA,XOM",
            market_snapshot_json="",
            event_driven_runtime_enabled=False,
            lane_scheduler_enabled=False,
            lane_rebalance_interval_seconds=60,
            lane_scheduler_cycles=1,
            execution_session_guard_enabled=True,
            execution_session_start_utc="13:30",
            execution_session_end_utc="20:00",
            execution_good_after_seconds=5,
        )
        with patch("phase0.llm_connectivity_check.load_config", return_value=config):
            report = run_llm_probe()
        self.assertFalse(report["ok"])
        self.assertTrue(report["skipped"])
        self.assertEqual("LLM_PLACEHOLDER_CONFIG", report["reason"])


if __name__ == "__main__":
    unittest.main()
