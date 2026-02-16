
import sys
import os
import time
import pandas as pd
from pathlib import Path

# Setup
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))
    
try:
    from app.api.data import _load_date_data
    from app.analytics.gex import calculate_gex_profile
except ImportError:
    # Try alternate path
    sys.path.append(str(current_dir.parent))
    try:
        from backend.app.api.data import _load_date_data
        from backend.app.analytics.gex import calculate_gex_profile
    except:
        sys.exit(1)

def profile_gex(date="2020-06-19"):
    print(f"Profiling GEX for {date}...")
    
    # Load Data
    t0 = time.time()
    try:
        df = _load_date_data(date, "510050_SH")
        rows = len(df)
        print(f"DTO Data Load Time: {time.time() - t0:.4f}s. Rows: {rows}")
        if rows == 0:
             print("WARNING: 0 Rows Loaded!")
    except Exception as e:
        print(f"Failed to load data: {e}")
        return

    # Spot Price (Mock)
    spot = 3.0
    
    # Calculate GEX
    t1 = time.time()
    try:
        gex_df = calculate_gex_profile(df, spot)
        t2 = time.time()
        
        with open("gex_profile.txt", "w") as f:
            f.write(f"Date: {date}\n")
            f.write(f"Rows: {rows}\n")
            f.write(f"Load Time: {t1 - t0:.4f}s\n")
            f.write(f"Calc Time: {t2 - t1:.4f}s\n")
            f.write(f"Total Time: {t2 - t0:.4f}s\n")
            
        print(f"GEX Calc Time: {t2 - t1:.4f}s")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"GEX Calc Failed: {e}")

if __name__ == "__main__":
    profile_gex()
