
import sys
import os
import pandas as pd
from pathlib import Path

# Setup
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

try:
    from app.api.data import _load_date_data
except ImportError:
    # Try adding current dir to path explicitly again?
    sys.path.append(os.getcwd())
    from app.api.data import _load_date_data

def check_greeks(date="2020-07-09"):
    print(f"Checking Greeks for {date}...")
    try:
        df = _load_date_data(date, "510050_SH")
        cols = df.columns.tolist()
        print(f"Columns: {cols}")
        
        # Check specific columns
        has_gamma = any(c in cols for c in ['gamma', 'Gamma'])
        has_delta = any(c in cols for c in ['delta', 'Delta'])
        has_oi = any(c in cols for c in ['oi', 'OI', 'open_interest', 'position'])
        
        print(f"Has Gamma: {has_gamma}")
        print(f"Has Delta: {has_delta}")
        print(f"Has OI: {has_oi}")
        
        if has_gamma and has_oi:
            print("\nSample Data (first 5 rows with gamma/oi):")
            sample_cols = ['strike', 'close']
            if 'gamma' in cols: sample_cols.append('gamma')
            elif 'Gamma' in cols: sample_cols.append('Gamma')
            
            if 'oi' in cols: sample_cols.append('oi')
            elif 'open_interest' in cols: sample_cols.append('open_interest')
            
            print(df[sample_cols].dropna().head().to_string())
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_greeks()
