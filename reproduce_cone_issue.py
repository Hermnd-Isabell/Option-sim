
import sys
import os
import pandas as pd
import numpy as np
import math
from datetime import datetime
from scipy.stats import norm

# Constants matching backend
PROJECT_ROOT = r"e:\Codes\Option-sim-main"
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATASET_ID = "510050_SH"

# IV Calculation Functions (Copied from data.py)
def _bs_call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    if T <= 0 or sigma <= 0:
        return max(0, S - K)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)

def _bs_put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    if T <= 0 or sigma <= 0:
        return max(0, K - S)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def _calculate_iv_bisection(
    option_price: float, 
    S: float, 
    K: float, 
    T: float, 
    r: float, 
    option_type: str,
    max_iterations: int = 50,
    tolerance: float = 0.0001
) -> float:
    lower_vol = 0.001
    upper_vol = 5.0
    
    for _ in range(max_iterations):
        mid_vol = (lower_vol + upper_vol) / 2
        
        if option_type.lower() == 'c':
            price = _bs_call_price(S, K, T, r, mid_vol)
        else:
            price = _bs_put_price(S, K, T, r, mid_vol)
            
        if abs(price - option_price) < tolerance:
            return mid_vol
            
        if price > option_price:
            upper_vol = mid_vol
        else:
            lower_vol = mid_vol
            
    return mid_vol

def get_dataset_dir(dataset_id):
    p1 = os.path.join(DATA_DIR, dataset_id)
    if os.path.exists(p1): return p1
    return os.path.join(DATA_DIR, "510050_SH")

def load_date_data(date_str, dataset_id):
    dataset_dir = get_dataset_dir(dataset_id)
    year = date_str.split("-")[0]
    path = os.path.join(dataset_dir, year, f"options_{date_str}.parquet")
    print(f"Looking for: {path}")
    if os.path.exists(path):
        return pd.read_parquet(path)
    return None

def debug_vol_cone(current_date):
    print(f"\n--- Debugging Volatility Cone for {current_date} ---")
    
    df = load_date_data(current_date, DATASET_ID)
    if df is None:
        print(f"ERROR: Data file not found for {current_date}")
        return

    print(f"Loaded {len(df)} rows.")
    
    # 1. Spot Price Check
    spot = 3.0
    if 'underlying_close' in df.columns:
        uc = df['underlying_close'].dropna()
        if len(uc) > 0:
            spot = float(uc.iloc[0])
            print(f"Spot from underlying_close: {spot}")
        else:
            print("WARNING: underlying_close column exists but is empty/NaN")
    elif 'strike' in df.columns:
        strikes = sorted(df['strike'].dropna().unique())
        if len(strikes) > 0:
            spot = strikes[len(strikes)//2]
            print(f"Spot estimated from median strike: {spot}")
            
    # 2. Iterate and check for ATM options
    dte_buckets = [7, 14, 30, 60, 90]
    found_ivs = {dte: [] for dte in dte_buckets}
    
    trade_date = datetime.strptime(current_date, "%Y-%m-%d")
    
    row_count = 0
    atm_count = 0
    valid_iv_count = 0
    
    print(f"Using Spot Price: {spot}")
    
    for _, row in df.iterrows():
        row_count += 1
        try:
            # DTE Calculation
            if 'expiry_date' not in row: continue
            exp_str = str(row['expiry_date']).split(' ')[0]
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d")
            dte = (exp_date - trade_date).days
            
            strike = float(row['strike'])
            
            # Check ATM Logic (Same as backend)
            # if abs(strike - spot) / spot > 0.02:
            moneyness = abs(strike - spot) / spot
            
            # Debug first few rows
            if row_count < 5:
                # print(f"Row {row_count}: Strike={strike}, Spot={spot}, Moneyness={moneyness:.4f}, DTE={dte}")
                pass
                
            if moneyness > 0.02:
                continue
            atm_count += 1
            
            # Check IV
            iv = None
            for col in ['us_impliedvol', 'iv', 'implied_volatility']:
                if col in df.columns and pd.notna(row.get(col)) and float(row.get(col)) > 0.01:
                    iv = float(row[col])
                    break
            
            # Fallback IV calc
            if iv is None and 'close' in df.columns and float(row['close']) > 0:
                 opt_type = row.get('type', 'C')
                 T = dte / 365.0
                 if T > 0:
                     iv = _calculate_iv_bisection(
                         float(row['close']), spot, strike, T, 0.03, opt_type
                     )
                     # print(f"Calculated IV: {iv}")

            if iv and 0.05 < iv < 2.0:
                valid_iv_count += 1
                # Check Bucket
                closest_bucket = min(dte_buckets, key=lambda x: abs(x - dte))
                if abs(dte - closest_bucket) <= 10:
                    found_ivs[closest_bucket].append((dte, strike, iv))
                    
        except Exception as e:
            # print(f"Row error: {e}")
            pass
            
    print(f"Total Rows: {row_count}")
    print(f"ATM Options (within 2% of {spot}): {atm_count}")
    print(f"Valid IVs found (ATM & 0.05<iv<2.0): {valid_iv_count}")
    
    for bucket in dte_buckets:
        items = found_ivs[bucket]
        print(f"Bucket {bucket}d: {len(items)} items found.")
        if len(items) > 0:
            print(f"  Sample: {items[0]}")
        else:
            print(f"  WARNING: No IV found for Current Date in {bucket}d bucket!")

if __name__ == "__main__":
    debug_vol_cone("2020-07-11") # Reported issue date
    # debug_vol_cone("2020-01-06") # Working date
