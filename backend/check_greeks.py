
import sys
import os
import pandas as pd
from pathlib import Path

# Setup paths
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

try:
    from app.api.data import _load_date_data
except ImportError:
    # Try adding current dir to path explicitly again?
    sys.path.append(os.getcwd())
    from app.api.data import _load_date_data

def check_greeks(date="2020-07-09"):
    print(f"DTO Checking Greeks for {date}...")
    try:
        df = _load_date_data(date, "510050_SH")
        cols = sorted(df.columns.tolist())
        with open("cols.txt", "w") as f:
            f.write("\n".join(cols))
        print("Columns written to cols.txt")
        has_gamma = any(c in cols for c in ['gamma', 'Gamma'])
        has_delta = any(c in cols for c in ['delta', 'Delta'])
        has_oi = any(c in cols for c in ['oi', 'OI', 'open_interest', 'position'])
        
        print(f"Has Gamma: {has_gamma} (Cols: {[c for c in cols if 'gamma' in c.lower()]})")
        print(f"Has Delta: {has_delta}")
        print(f"Has OI: {has_oi} (Cols: {[c for c in cols if 'oi' in c.lower() or 'open' in c.lower()]})")
        
        # Check sample values if present
        if has_gamma:
             g_col = next(c for c in cols if 'gamma' in c.lower())
             print(f"Sample Gamma: {df[g_col].dropna().head().tolist()}")
             
        if has_oi:
             oi_col = next(c for c in cols if 'oi' in c.lower() or 'open' in c.lower())
             print(f"Sample OI: {df[oi_col].dropna().head().tolist()}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_greeks()
