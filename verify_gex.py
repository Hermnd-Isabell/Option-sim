
import sys
import os
import pandas as pd
from pathlib import Path

# Setup
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))
    
# Import
try:
    from app.api.data import _load_date_data
    from app.analytics.gex import calculate_gex_profile, plot_gex_profile
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def verify_gex(date="2020-07-09"):
    print(f"Verifying GEX for {date}...")
    
    # 1. Load Data
    try:
        df = _load_date_data(date, "510050_SH")
        print(f"Loaded {len(df)} rows.")
        
        # 2. Get Spot Price
        spot = 3.46 # Approximate from previous checks
        if 'underlying_close' in df.columns:
            uc = df['underlying_close'].dropna()
            if len(uc) > 0:
                spot = float(uc.iloc[0])
        print(f"Using Spot Price: {spot}")
        
        # 3. Calculate GEX
        # Note: OI is likely missing, so it will warn and use Volume
        gex_df = calculate_gex_profile(df, spot)
        
        print("\nGEX Profile Head:")
        print(gex_df.head())
        
        print("\nGEX Profile Tail:")
        print(gex_df.tail())
        
        total_gex = gex_df['gex_dollar'].sum()
        print(f"\nTotal Net GEX: ${total_gex:,.2f}")
        
        # 4. Plot
        fig = plot_gex_profile(gex_df, spot)
        fig.write_html("gex_chart.html")
        print("Chart saved to gex_chart.html")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_gex()
