
import sys
import os
import pandas as pd
import numpy as np
import math
from datetime import datetime
from scipy.interpolate import CubicSpline
from scipy.stats import norm

# Setup path
sys.path.append(os.getcwd())

# Mock required functions
def _bs_call_price(S, K, T, r, sigma):
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)

def _bs_put_price(S, K, T, r, sigma):
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def _calculate_iv_bisection(option_price, S, K, T, r, option_type, max_iterations=50, tolerance=0.0001):
    low, high = 0.01, 3.0
    price_func = _bs_call_price if option_type == 'C' else _bs_put_price
    
    for _ in range(max_iterations):
        mid = (low + high) / 2
        price = price_func(S, K, T, r, mid)
        if abs(price - option_price) < tolerance:
            return mid
        if price > option_price:
            high = mid
        else:
            low = mid
    return mid

def _calculate_implied_forward(calls, puts, T, r):
    common_strikes = set(calls.keys()) & set(puts.keys())
    if not common_strikes: return None
    min_diff = float('inf')
    best_strike = None
    for k in common_strikes:
        diff = abs(calls[k] - puts[k])
        if diff < min_diff:
            min_diff = diff
            best_strike = k
    if best_strike is None: return None
    c_atm = calls[best_strike]
    p_atm = puts[best_strike]
    F = best_strike + (c_atm - p_atm) * math.exp(r * T)
    return F * math.exp(-r * T)

def run_debug():
    with open("debug.log", "w", encoding="utf-8") as f:
        # Load Data
        date = "2022-06-01"
        file_path = f"../data/510050_SH/2022/options_{date}.parquet"
        if not os.path.exists(file_path):
            f.write(f"File not found: {file_path}\\n")
            return

        f.write(f"Loading {file_path}...\\n")
        df = pd.read_parquet(file_path)
        
        # Process
        current_date = datetime.strptime(date, "%Y-%m-%d")
        expiry_to_dte = {}
        for exp in df['expiry_date'].dropna().unique():
            exp_str = str(exp).split(' ')[0]
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d")
            dte = (exp_date - current_date).days
            if dte > 0: expiry_to_dte[exp_str] = dte
                
        dtes = sorted(list(set(expiry_to_dte.values())))
        f.write(f"Available DTEs: {dtes}\\n")
        
        # Analyze First DTE
        target_dte = dtes[2] if len(dtes) > 2 else dtes[0]
        f.write(f"\\n--- Analyzing DTE {target_dte} ---\\n")
        
        T = target_dte / 365.0
        r = 0.03
        
        target_expiry = None
        for k, v in expiry_to_dte.items():
            if v == target_dte: target_expiry = k
            
        dte_df = df[df['expiry_date'].astype(str).str.startswith(target_expiry)].copy()
        
        calls = {}
        puts = {}
        
        f.write(f"{'Strike':<10} {'Type':<5} {'Bid':<8} {'Ask':<8} {'Mid':<8} {'Raw IV':<8}\\n")
        
        data_rows = []
        
        for _, row in dte_df.iterrows():
            k = row['strike']
            
            bid = row.get('bid1', 0)
            ask = row.get('ask1', 0)
            mid = (bid + ask) / 2 if bid > 0 and ask > 0 else row['close']
            
            t = 'P' if 'P' in str(row['type']).upper() or '沽' in str(row['symbol']) else 'C'
            
            if t == 'C': calls[k] = mid
            else: puts[k] = mid
            
            data_rows.append({'k': k, 't': t, 'mid': mid, 'bid': bid, 'ask': ask})

        # Implied Forward
        implied_S = _calculate_implied_forward(calls, puts, T, r)
        f.write(f"Implied S: {implied_S:.4f}\\n")
        
        # IV Calculation loop
        strikes = sorted(list(set([r['k'] for r in data_rows])))
        
        ivs_raw = []
        ivs_smoothed = []
        
        f.write(f"\\n{'Strike':<8} {'Used':<4} {'MidPrice':<10} {'IV_Raw':<10}\\n")
        
        valid_strikes = []
        valid_ivs = []
        
        for k in strikes:
            is_call = k > implied_S
            target_type = 'C' if is_call else 'P'
            
            # Find matching row
            row_data = next((x for x in data_rows if x['k'] == k and x['t'] == target_type), None)
            
            iv = 0
            if row_data:
                iv = _calculate_iv_bisection(row_data['mid'], implied_S, k, T, r, target_type)
                if iv is None: iv = 0
                
            ivs_raw.append(iv)
            if iv > 0.01 and iv < 2.0:
                valid_strikes.append(k)
                valid_ivs.append(iv)
                
            f.write(f"{k:<8.3f} {target_type:<4} {row_data['mid'] if row_data else 0:<10.4f} {iv:<10.4f}\\n")

        # Smoothing check
        if len(valid_strikes) > 4:
            cs = CubicSpline(valid_strikes, valid_ivs, bc_type='natural')
            f.write("\\n--- Smoothing Check ---\\n")
            for k in strikes:
                smoothed = cs(k)
                f.write(f"Strike {k}: Raw {ivs_raw[strikes.index(k)]:.4f} -> Smooth {smoothed:.4f}\\n")
        else:
            f.write("Not enough points for smoothing\\n")

if __name__ == "__main__":
    run_debug()
