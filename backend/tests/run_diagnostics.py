import sys
import os
import pandas as pd

# Add the root directory, so "backend" package is discoverable
root_path = os.path.dirname(os.getcwd())
if root_path not in sys.path:
    sys.path.insert(0, root_path)
    
sys.path.insert(0, os.getcwd()) 

from backend.app.engines.backtest import BacktestEngine
from backend.strategies.diagnostic_strategy import DiagnosticStrategy

def run_diagnostics():
    print("="*60)
    print("BACKTEST ENGINE DIAGNOSTICS RUN")
    print("="*60)
    
    # Run with SSE Margin Scheme and 12% ratio
    engine = BacktestEngine(
        dataset_id="510050_SH", 
        initial_capital=1000000,
        margin_scheme="SSE",
        margin_ratio=0.12,
        maintenance_margin=0.07
    )
    
    print(f"Engine Initialized: Multiplier = {engine.account.multiplier}")
    
    df, trades = engine.run(
        strategy_cls=DiagnosticStrategy, 
        strategy_config={}, 
        start_date="2020-01-02", 
        end_date="2020-01-15"
    )
    
    print("\n" + "="*60)
    print("TRADE LOG VERIFICATION")
    print("="*60)
    trade_df = pd.DataFrame(trades)
    print(trade_df.to_string())
    
    print("\n" + "="*60)
    print("EQUITY CURVE HEAD")
    print("="*60)
    print(df[['equity', 'cash', 'margin_utilization', 'position_count']].head(8).to_string())
    
if __name__ == "__main__":
    run_diagnostics()
