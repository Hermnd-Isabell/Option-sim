
import sys
import os
import math
import numpy as np
import pandas as pd
from datetime import datetime

# Setup paths
current_dir = os.getcwd()
sys.path.append(current_dir)

try:
    from app.api.data import _load_date_data, _calculate_implied_forward
except ImportError:
    print("Import failed. Make sure you run this from backend/")
    sys.exit(1)

def debug_implied_spots(date="2020-07-09"):
    print(f"DTO Inspecting Implied Spots for {date}...")
    
    df = _load_date_data(date, "510050_SH")
    current_date = datetime.strptime(date, "%Y-%m-%d")
    r = 0.03
    
    # helper
    def get_implied_spot_for_expiry(exp_str):
        if 'expiry_date' not in df.columns: return None
        
        # Filter for expiry
        # Check string format
        mask = df['expiry_date'].astype(str).str.startswith(exp_str)
        sub = df[mask]
        
        if len(sub) == 0: return None
        
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d")
            dte = (exp_date - current_date).days
            T = dte / 365.0
        except:
            return None
            
        calls = {}
        puts = {}
        
        for _, row in sub.iterrows():
            k = float(row.get('strike', 0))
            p = float(row.get('close', 0)) # Use close for now, mid is better
            
            t = 'C'
            if str(row.get('type')).upper() in ['P', 'PUT', '沽']: t = 'P'
            
            if t == 'C': calls[k] = p
            else: puts[k] = p
            
            
        # calc forward
        # Debug why it fails
        common = set(calls.keys()) & set(puts.keys())
        if not common:
             print(f"    [FAIL] No common strikes for {exp_str}. Calls: {len(calls)}, Puts: {len(puts)}")
             if len(calls) > 0 and len(puts) > 0:
                 print(f"      Call K: {list(calls.keys())[:3]}...")
                 print(f"      Put K: {list(puts.keys())[:3]}...")
             return None
             
        F = _calculate_implied_forward(calls, puts, T, r)
        if F:
            return F * math.exp(-r * T)
        return None

    # Get expiries
    if 'expiry_date' in df.columns:
        exps = df['expiry_date'].unique()
        print(f"Raw Expiries: {exps}")
        
        # Clean
        clean_exps = sorted(list(set([str(x).split(' ')[0] for x in exps])))
        
        print(f"\nScanning {len(clean_exps)} maturities:")
        
        spots = []
        for exp in clean_exps:
            try:
                # Filter invalid dates
                ed = datetime.strptime(exp, "%Y-%m-%d")
                if ed <= current_date: continue
            except: continue
                
            s = get_implied_spot_for_expiry(exp)
            spots.append(s)
            print(f"  Expiry: {exp} -> Implied Spot: {s if s else 'FAILED'}")
            
        # Stats
        valid_spots = [x for x in spots if x is not None]
        if valid_spots:
            mean_s = np.mean(valid_spots)
            std_s = np.std(valid_spots)
            print(f"\nMean Spot: {mean_s:.4f}, Std Dev: {std_s:.4f}")
            if std_s > 0.01:
                print("WARNING: Implied spot varies significantly across maturities. This can cause jaggedness if not handled per-maturity.")
        else:
            print("No valid spots calculated!")

if __name__ == "__main__":
    debug_implied_spots()
