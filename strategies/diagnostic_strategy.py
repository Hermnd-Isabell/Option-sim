import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from typing import Dict, Any
from backend.app.engines.strategy import BaseStrategy, BacktestContext

# 策略元数据
STRATEGY_META = {
    'name': 'diagnostic',
    'display_name': '回测诊断与检验策略',
    'type': 'test',
    'risk_level': 1,
    'description': '严格验证回测引擎中保证金、滑点以及可用资金复式计算的系统校验工具。'
}

class DiagnosticStrategy(BaseStrategy):
    """
    A specialized strategy to explicitly verify backtest engine correctness.
    
    Test Cases Covered:
    1. Day 1: Buy 1 Call (Check Cash Deduction, Unrealized PnL scaling)
    2. Day 2: Sell 1 Put (Check Margin Requirement allocation, Leverage impact)
    3. Day 3: Close Call (Check Realized PnL calculation)
    4. Market Moves: Track Equity = Cash + Position Value accurately.
    """
    
    def on_init(self, context: BacktestContext):
        self.step = 0
        self.target_call = None
        self.target_put = None
        self.call_entry_price = 0
        self.put_entry_price = 0
        print("🔍 DiagnosticStrategy Initialized")

    def on_bar(self, context: BacktestContext, data: Dict[str, Any]):
        options = data['options']
        if options.empty:
            return
            
        current_date = context.current_date.strftime("%Y-%m-%d")
        underlying = data['underlying_price']
        
        self.step += 1
        
        # Select ATM options on Day 1
        if self.step == 1:
            # Type might be 'C', 'P' or 'CALL', 'PUT' depending on data source
            call_opts = options[options['type'].str.upper().isin(['C', 'CALL'])]
            put_opts = options[options['type'].str.upper().isin(['P', 'PUT'])]
            
            if call_opts.empty or put_opts.empty:
                print(f"  [Error] Could not find Call/Put options for date {current_date}")
                return
                
            atm_call = call_opts.iloc[0]
            atm_put = put_opts.iloc[0]
            
            self.target_call = atm_call['symbol']
            self.target_put = atm_put['symbol']
            
            print(f"\n[{current_date}] --- STEP 1: Buy 1 Call ---")
            print(f"  Underlying Price: {underlying:.2f}")
            print(f"  Selected Call: {self.target_call} @ {atm_call['close']:.4f}")
            
            # Execute Buy
            context.order(self.target_call, 1)
            self.call_entry_price = atm_call['close']
            
        elif self.step == 2:
            print(f"\n[{current_date}] --- STEP 2: Sell 1 Put (Margin Test) ---")
            put_market = options[options['symbol'] == self.target_put]
            if not put_market.empty:
                price = put_market.iloc[0]['close']
                print(f"  Selected Put: {self.target_put} @ {price:.4f}")
                # Execute Short Sell
                context.order(self.target_put, -1)
                self.put_entry_price = price
                
            # Log Account State from Day 1
            call_pos = context.get_position(self.target_call)
            if call_pos:
                print(f"  Call Pos Value: {call_pos.market_value:.2f} (Entry: {call_pos.entry_price:.4f}, Curr: {call_pos.current_price:.4f})")
            
        elif self.step == 3:
            print(f"\n[{current_date}] --- STEP 3: Close Call (Realized PnL Test) ---")
            call_pos = context.get_position(self.target_call)
            if call_pos and call_pos.quantity > 0:
                # Close the call
                context.order(self.target_call, -1)
                
            # Log Margin state from Day 2 short put
            margin_used = self.account.maintenance_margin if hasattr(self, 'account') else 0
            print(f"  Margin Used for Short Put: {margin_used:.2f}")
            
        elif self.step == 6:
            print(f"\n[{current_date}] --- STEP 4: Close Put & End Test ---")
            put_pos = context.get_position(self.target_put)
            if put_pos and put_pos.quantity < 0:
                context.order(self.target_put, 1) # Buy to close
                
        # Continual Logging
        if self.step > 0:
            print(f"  [EOD {current_date}] Equity: {context.portfolio_value:.2f} | Cash: {context.cash:.2f}")
            if hasattr(self, 'account'):
                print(f"  [EOD {current_date}] Margin: {self.account.maintenance_margin:.2f} | Util: {self.account.margin_utilization:.2f}")

