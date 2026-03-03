import sys
import os
# Add project root to sys path
project_root = os.path.dirname(os.getcwd())
if project_root not in sys.path:
    sys.path.insert(0, project_root)
sys.path.insert(0, os.getcwd()) 

from backend.app.engines.backtest import BacktestEngine
from strategies.base_strategy import BaseStrategy

class SmokeStrategy(BaseStrategy):
    def on_init(self, context):
        self.traded = False

    def on_bar(self, context, data):
        # simple buy order
        if not self.traded:
            opts = data['options']
            if not opts.empty:
                sym = opts.iloc[0]['symbol']
                context.order(sym, 2) # buy 2 
                
                context.order(sym, -1) # try to sell 1 to test margin
            self.traded = True
        
if __name__ == "__main__":
    engine = BacktestEngine(dataset_id="510050_SH", initial_capital=1000000)
    df, trades = engine.run(SmokeStrategy, {}, start_date="2020-01-02", end_date="2020-01-10")
    print("Trades:", trades)
    print("DF length:", len(df))
