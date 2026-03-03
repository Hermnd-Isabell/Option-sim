
import sys
import os
from pathlib import Path

# Add backend directory to path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir / "backend"

if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

try:
    from backend.app.api.data import _load_date_data
except ImportError:
    try:
        from app.api.data import _load_date_data
    except ImportError:
        # Dirty hack
        sys.path.append(str(backend_dir))
        from app.api.data import _load_date_data

def inspect_duplicates(date="2020-07-09"):
    print(f"Inspecting data for {date}...")
    try:
        df = _load_date_data(date, "510050_SH")
        print(f"Loaded {len(df)} records.")
        
        if 'strike' not in df.columns or 'expiry_date' not in df.columns:
            print("Missing necessary columns.")
            return

        # Check duplicated (expiry, strike, type)
        # Type might be implicitly defined by symbol or explicit column
        df['type_norm'] = 'C'
        if 'type' in df.columns:
             df['type_norm'] = df['type'].apply(lambda x: 'P' if str(x).upper() in ['P', 'PUT', '认沽', '沽'] else 'C')
        
        # Group by expiry, strike, type
        groups = df.groupby(['expiry_date', 'strike', 'type_norm'])
        
        duplicates_found = 0
        for name, group in groups:
            if len(group) > 1:
                duplicates_found += 1
                print(f"\nDuplicate found for {name}: {len(group)} records")
                for _, row in group.iterrows():
                    symbol = row.get('symbol', 'N/A')
                    ts_code = row.get('ts_code', 'N/A')
                    close = row.get('close', 'N/A')
                    print(f"  - Symbol: {symbol}, TS_Code: {ts_code}, Price: {close}")
                    
        if duplicates_found == 0:
            print("No duplicates found based on (expiry, strike, type).")
        else:
            print(f"\nTotal duplicates groups: {duplicates_found}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_duplicates()
