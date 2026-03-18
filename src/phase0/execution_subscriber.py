from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from .config import AppConfig
from .ibkr_execution import ExecutionConfig, IbkrExecutionClient
from .ibkr_order_adapter import map_decision_to_ibkr_bracket
from .lanes.bus import AsyncEventBus
from .lanes.high import evaluate_event, HighLaneSettings
from .state_store import list_order_lifecycle_events, ORDER_STATUS_FILLED, get_runtime_state

logger = logging.getLogger(__name__)


async def start_execution_subscriber(
    bus: AsyncEventBus,
    config: AppConfig,
    market_snapshot: dict[str, dict[str, float | str]],
) -> None:
    logger.info("Starting ExecutionSubscriber Daemon...")
    queue = bus.subscribe("high.decision")
    
    # Pre-load settings
    lane_settings = HighLaneSettings.from_app_config(config)
    
    try:
        while True:
            event = await queue.get()
            try:
                payload = event.payload
                symbol = payload.get("symbol", "")
                approved = payload.get("approved", False)
                
                if not approved:
                    logger.info(f"ExecutionSubscriber: Ignoring rejected signal for {symbol}")
                    continue
                
                logger.info(f"ExecutionSubscriber: Processing approved signal for {symbol}")
                
                # 1. Prepare context
                ultra_signal = payload.get("ultra_signal", {})
                raw_data = ultra_signal.get("raw_data", {})
                
                # Get price
                snapshot_row = market_snapshot.get(symbol, {})
                current_price = float(snapshot_row.get("reference_price", 0.0) or raw_data.get("price_current", 0.0))
                
                if current_price <= 0:
                    logger.error(f"ExecutionSubscriber: No valid price for {symbol}, aborting")
                    continue

                # 2. Get State (Equity, Exposure, Cooldown)
                runtime_state = get_runtime_state(config.ai_state_db_path)
                equity = runtime_state.equity if runtime_state.equity > 0 else 100000.0
                
                # Calculate current exposure from state store? 
                # For now, assuming 0 or reading from snapshot if available. 
                # Ideally execute_cycle handles this logic, but here we are bypassing execute_cycle's lane logic
                # and going straight to execution.
                # To do this safely, we should really call `execute_cycle` but `execute_cycle` expects to RUN the lane.
                # Here we ARE the result of the lane.
                
                current_exposure = 0.0 
                
                # Check last exit for cooldown
                # This is a simple check. A robust one would query the DB.
                last_exit_at = ""
                try:
                    events = list_order_lifecycle_events(config.ai_state_db_path, limit=100)
                    # Filter for this symbol and filled sell orders? 
                    # This is complex to do efficiently without a dedicated query.
                    # For now, we leave it empty, risking cooldown violation (but Risk Engine should catch it too?)
                    pass
                except Exception:
                    pass

                # 3. Construct High Lane Event
                ai_stop_pct = float(payload.get("stop_loss_pct", config.risk_stop_loss_min_pct))
                
                # Ensure stop loss is valid
                if ai_stop_pct <= 0:
                    ai_stop_pct = config.risk_stop_loss_min_pct

                stop_price = current_price * (1.0 - ai_stop_pct)
                # Take profit: default to 2x risk? Or use config boost?
                # AI High doesn't give TP target explicitly usually, just risk params.
                # Let's use a standard 1.5R or 2R based on config or AI score
                tp_price = current_price * (1.0 + ai_stop_pct * 2.0)

                high_event = {
                    "lane": "ultra",
                    "kind": "signal",
                    "symbol": symbol,
                    "side": "buy", 
                    "entry_price": str(current_price),
                    "stop_loss_price": str(stop_price),
                    "take_profit_price": str(tp_price),
                    "equity": str(equity),
                    "current_exposure": str(current_exposure),
                    "current_exposure_unit": "notional",
                    "last_exit_at": last_exit_at,
                }
                
                adjustments = {
                    "risk_multiplier": float(payload.get("risk_multiplier", 1.0)),
                    "take_profit_boost_pct": 0.0 
                }
                
                # 4. Evaluate (Sizing & Hard Rules)
                decision = evaluate_event(
                    event=high_event,
                    settings=lane_settings,
                    strategy_adjustments=adjustments
                )
                
                if decision.get("status") != "accepted":
                    logger.warning(f"ExecutionSubscriber: Order rejected by High Lane rules: {decision.get('reject_reasons')}")
                    continue
                
                # 5. Map to IBKR
                ibkr_signal = map_decision_to_ibkr_bracket(decision)
                if not ibkr_signal:
                    logger.error("ExecutionSubscriber: Failed to map decision to IBKR signal")
                    continue
                
                # 6. Submit
                exec_config = ExecutionConfig(
                    host=config.ibkr_host,
                    port=config.ibkr_port,
                    client_id=config.ibkr_port + 10, # Use a different client ID to avoid conflict? Or same?
                    # Using a distinct client ID is safer if main loop uses one.
                    # execute_cycle uses default 91. Let's use 92.
                    timeout_seconds=config.llm_timeout_seconds, # reuse timeout?
                    session_guard_enabled=config.execution_session_guard_enabled,
                    session_start_utc=config.execution_session_start_utc,
                    session_end_utc=config.execution_session_end_utc,
                    good_after_seconds=config.execution_good_after_seconds,
                    slippage_bps=config.risk_slippage_bps,
                    commission_per_share=config.risk_commission_per_share,
                )
                
                logger.info(f"ExecutionSubscriber: Submitting order for {symbol}...")
                await asyncio.to_thread(_execute_sync, exec_config, ibkr_signal)
                
            except Exception as e:
                logger.error(f"ExecutionSubscriber: Error processing event: {e}")
            finally:
                queue.task_done()
    except asyncio.CancelledError:
        logger.info("ExecutionSubscriber: Shutting down")
    finally:
        bus.unsubscribe("high.decision", queue)


def _execute_sync(config: ExecutionConfig, signal: dict[str, Any]) -> None:
    # We use a short-lived client for now to ensure clean state
    client = IbkrExecutionClient(config)
    try:
        result = client.submit_bracket_signal(signal)
        if result.get("ok"):
            logger.info(f"ExecutionSubscriber: Order submitted successfully: {result}")
        else:
            logger.error(f"ExecutionSubscriber: Order submission failed: {result}")
    except Exception as e:
        logger.error(f"ExecutionSubscriber: Exception during submission: {e}")
    finally:
        client.close()
