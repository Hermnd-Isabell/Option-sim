
import sys
import os
import time
import pandas as pd
from pathlib import Path

# Setup
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))
    
try:
    from app.api.data import _load_date_data
    from app.analytics.gex import calculate_gex_profile
except ImportError:
    # Try alternate path
    sys.path.append(os.getcwd())
    from backend.app.api.data import _load_date_data
    from backend.app.analytics.gex import calculate_gex_profile

def profile_gex(date="2020-06-19"):
    print(f"Profiling GEX for {date}...")
    
    # Load Data
    t0 = time.time()
    try:
        df = _load_date_data(date, "510050_SH")
        print(f"Data Load Time: {time.time() - t0:.4f}s. Rows: {len(df)}")
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
        print(f"GEX Calc Time: {t2 - t1:.4f}s")
    except Exception as e:
        print(f"GEX Calc Failed: {e}")

if __name__ == "__main__":
    profile_gex()
