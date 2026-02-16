
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

def inspect_names(date="2020-07-09"):
    print(f"Inspecting Symbols for {date}...")
    try:
        df = _load_date_data(date, "510050_SH")
        
        # Check for 'symbol' or 'ts_code' or 'name' columns
        cols = df.columns
        print(f"Columns: {cols}")
        
        # Select relevant cols
        display_cols = ['strike', 'close', 'vol']
        if 'symbol' in cols: display_cols.insert(0, 'symbol')
        if 'ts_code' in cols: display_cols.insert(1, 'ts_code')
        if 'name' in cols: display_cols.insert(2, 'name')
        
        # Show sample of potential adjusted contracts
        # Usually they have 'A' or 'M' in symbol or name
        
        if 'symbol' in cols:
            adj = df[df['symbol'].str.contains('A|M', regex=True, na=False)]
            print(f"\nPotential Adjusted (by Symbol 'A' or 'M'): {len(adj)}")
            if not adj.empty:
                print(adj[display_cols].head(10).to_string())
                
        if 'name' in cols:
            adj_name = df[df['name'].str.contains('A|M', regex=True, na=False)]
            print(f"\nPotential Adjusted (by Name 'A' or 'M'): {len(adj_name)}")
            if not adj_name.empty:
                print(adj_name[display_cols].head(10).to_string())
                
        # Also check for non-standard strikes (e.g. 3 decimals)
        # Standard strikes are usually 2 decimals max for 50ETF?
        # Actually 2.95 is standard. 2.952 might be adjusted.
        
        print("\nListing some weird strikes:")
        valid_rows = df.dropna(subset=['strike'])
        # Find strikes with > 3 decimal places or just weird ones
        # Actually just show head/tail of sorted strikes
        print(sorted(valid_rows['strike'].unique())[:10])
        print(sorted(valid_rows['strike'].unique())[-10:])
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_names()
