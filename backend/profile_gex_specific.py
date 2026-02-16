
import sys
import os
import time
import pandas as pd
from pathlib import Path

# Setup assertions
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))
    
# Mock app import
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

def profile_date(date):
    print(f"Profiling GEX for {date}...")
    
    t0 = time.time()
    try:
        df = _load_date_data(date, "510050_SH")
        rows = len(df)
        t_load = time.time()
        print(f"Data Load: {t_load - t0:.4f}s. Rows: {rows}")
        
        if rows == 0:
            print("WARNING: No rows found.")
            return

        spot = 3.0 # Mock
        
        t_start_calc = time.time()
        gex = calculate_gex_profile(df, spot)
        t_end_calc = time.time()
        
        print(f"Calculation: {t_end_calc - t_start_calc:.4f}s")
        print(f"Total Time: {t_end_calc - t0:.4f}s")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    profile_date("2020-06-17")
