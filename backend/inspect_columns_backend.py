
import sys
import os
from pathlib import Path
import pandas as pd

# Running from backend/
# Ensure current dir is in path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

# Also need parent if we were running as module, but here standalone is fine
# provided we can import 'app'

try:
    from app.api.data import _load_date_data
except ImportError:
    # Try adding current dir to path explicitly again?
    sys.path.append(os.getcwd())
    from app.api.data import _load_date_data

def inspect_cols(date="2020-07-09"):
    print("Starting inspection...")

    # Load data
    try:
        df = _load_date_data(date, "510050_SH")
        print(f"Loaded {len(df)} rows.")

        if 'strike' not in df.columns or 'expiry_date' not in df.columns:
            print("Missing columns!")
            return

        # Sort
        # Try to sort so that 'M' or 'A' symbols come AFTER normal ones?
        # Or just sort by symbol to see them adjacent
        df = df.sort_values(['expiry_date', 'strike', 'symbol'])
        
        last_row = None
        count = 0
        
        for idx, row in df.iterrows():
            if last_row is not None:
                exp1 = str(row['expiry_date']).split(' ')[0]
                exp2 = str(last_row['expiry_date']).split(' ')[0]
                
                k1 = float(row['strike'])
                k2 = float(last_row['strike'])
                
                # Check Type
                type1 = row.get('type', '')
                type2 = last_row.get('type', '')
                
                # Normalize type
                t1 = 'C'
                if str(type1).upper() in ['P', 'PUT', '认沽', '沽']: t1 = 'P'
                t2 = 'C'
                if str(type2).upper() in ['P', 'PUT', '认沽', '沽']: t2 = 'P'
                
                if exp1 == exp2 and abs(k1 - k2) < 0.001 and t1 == t2:
                    count += 1
                    if count < 10:
                        print(f"\n[Duplicate #{count}]")
                        print(f"  Row 1: Symbol={last_row.get('symbol')}, Name={last_row.get('name')}, Vol={last_row.get('vol',0)}")
                        print(f"  Row 2: Symbol={row.get('symbol')}, Name={row.get('name')}, Vol={row.get('vol',0)}")
            
            last_row = row
            
        print(f"\nTotal potential duplicates found: {count}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_cols()
