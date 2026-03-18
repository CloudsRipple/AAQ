
import os
import json
import sys
from datetime import datetime, timezone
import logging

# Add src to sys.path to allow importing phase0
sys.path.append(os.path.join(os.getcwd(), "src"))

from phase0.config import load_config
from phase0.lanes import run_lane_cycle
from phase0.logger import setup_logging

def fetch_real_data(symbols):
    import yfinance as yf
    snapshot = {}
    for symbol in symbols:
        print(f"Downloading data for {symbol}...")
        try:
            ticker = yf.Ticker(symbol)
            history = ticker.history(period="3mo", interval="1d")
            if history.empty or len(history) < 25:
                print(f"Warning: Not enough data for {symbol}")
                continue
            
            closes = history["Close"].dropna()
            ref_price = float(closes.iloc[-1])
            momentum_20d = (ref_price - float(closes.iloc[-21])) / max(1e-6, float(closes.iloc[-21]))
            returns = closes.pct_change().dropna()
            volatility = float(returns.tail(20).std()) if len(returns) >= 20 else 0.2
            mean_5 = float(closes.tail(5).mean())
            std_20 = float(closes.tail(20).std()) if len(closes) >= 20 else 1.0
            z_score_5d = (ref_price - mean_5) / max(1e-6, std_20)
            
            snapshot[symbol] = {
                "momentum_20d": round(momentum_20d, 6),
                "z_score_5d": round(z_score_5d, 6),
                "relative_strength": round(max(0.0, momentum_20d), 6),
                "volatility": round(max(0.01, volatility), 6),
                "reference_price": round(ref_price, 6),
                "liquidity_score": 0.8,
                "sector": "tech" if symbol in ["AAPL", "MSFT", "GOOGL"] else "auto",
            }
        except Exception as e:
            print(f"Error downloading {symbol}: {e}")
    return snapshot

def run_non_ai_test():
    # 1. Setup environment to bypass AI
    os.environ["AI_ENABLED"] = "false"
    os.environ["MARKET_DATA_MODE"] = "manual" # We'll provide it manually
    os.environ["LOG_LEVEL"] = "INFO"
    
    # 2. Load config
    config = load_config()
    
    # 3. Setup logger
    setup_logging(config.log_level)
    
    symbols_to_test = ["AAPL", "MSFT", "GOOGL", "TSLA"]
    
    print("=== Starting Non-AI Full Test Round with Real Data ===")
    print(f"AI Enabled: {config.ai_enabled}")
    print(f"Symbols: {', '.join(symbols_to_test)}")
    print("====================================================\n")
    
    # 4. Fetch real data
    real_snapshot = fetch_real_data(symbols_to_test)
    
    if not real_snapshot:
        print("Using simulated market data due to rate limiting...")
        real_snapshot = {
            "AAPL": {
                "momentum_20d": 0.12,
                "z_score_5d": 1.5, # Overbought
                "relative_strength": 0.45,
                "volatility": 0.25,
                "reference_price": 190.5,
                "sector": "tech"
            },
            "MSFT": {
                "momentum_20d": 0.05,
                "z_score_5d": -1.8, # Oversold
                "relative_strength": 0.15,
                "volatility": 0.18,
                "reference_price": 410.2,
                "sector": "tech"
            },
            "GOOGL": {
                "momentum_20d": -0.02,
                "z_score_5d": 0.2,
                "relative_strength": 0.0,
                "volatility": 0.22,
                "reference_price": 155.8,
                "sector": "tech"
            },
            "TSLA": {
                "momentum_20d": 0.25,
                "z_score_5d": 2.2, # Extremely overbought
                "relative_strength": 0.85,
                "volatility": 0.45,
                "reference_price": 185.0,
                "sector": "auto"
            }
        }

    # 5. Run cycle for each symbol using the real data
    for symbol in symbols_to_test:
        if symbol not in real_snapshot:
            continue
            
        print(f"--- Processing {symbol} ---")
        try:
            # We pass the real_snapshot here
            result = run_lane_cycle(
                symbol=symbol, 
                config=config, 
                market_snapshot=real_snapshot
            )
            
            # Print summary of results
            decision = result["decisions"][0] if result["decisions"] else None
            
            if decision:
                status = decision.get("status")
                actual_symbol = decision.get("symbol")
                strategy = decision.get("strategy", "unknown")
                score = decision.get("strategy_score", 0)
                
                print(f"Target: {symbol} -> Decision for: {actual_symbol}")
                print(f"Result: {status}")
                print(f"Strategy: {strategy} (Score: {score})")
                
                if status == "accepted":
                    order = decision.get("bracket_order", {})
                    parent = order.get("parent", {})
                    print(f"Action: {parent.get('action')} {parent.get('quantity')} shares @ {parent.get('limit_price')}")
                    print(f"Stop Loss: {order.get('stop_loss', {}).get('stop_price')}")
                    print(f"Take Profit: {order.get('take_profit', {}).get('limit_price')}")
                else:
                    reasons = decision.get("reject_reasons", [])
                    print(f"Rejection Reasons: {', '.join(reasons)}")
            else:
                print("No decision generated.")
                
            print(f"AI Bypassed: {result.get('ai_bypassed')}")
            print("-" * 30 + "\n")
            
        except Exception as e:
            print(f"Error processing {symbol}: {e}")

if __name__ == "__main__":
    run_non_ai_test()
