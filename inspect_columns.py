
import sys
import os
from pathlib import Path
import pandas as pd

# Add backend directory to path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir / "backend"

if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

def inspect_cols(date="2020-07-09"):
    print("Starting inspection...")
    try:
        from app.api.data import _load_date_data
    except ImportError:
        sys.path.append(str(backend_dir))
        from app.api.data import _load_date_data

    # Load data
    try:
        df = _load_date_data(date, "510050_SH")
        print(f"Loaded {len(df)} rows.")

        # Ensure we have necessary columns
        if 'strike' not in df.columns or 'expiry_date' not in df.columns:
            print("Missing columns!")
            return

        # Sort
        df = df.sort_values(['expiry_date', 'strike', 'symbol'])
        
        # Iterate and find duplicates
        last_row = None
        count = 0
        
        for idx, row in df.iterrows():
            if last_row is not None:
                # Check for same expiry and strike
                # Use string comparison for expiry to be safe
                exp1 = str(row['expiry_date']).split(' ')[0]
                exp2 = str(last_row['expiry_date']).split(' ')[0]
                
                k1 = float(row['strike'])
                k2 = float(last_row['strike'])
                
                # Check Type
                type1 = row.get('type', '')
                type2 = last_row.get('type', '')
                
                # Normalize type
                if str(type1).upper() in ['C', 'CALL', '认购', '购']: t1 = 'C'
                elif str(type1).upper() in ['P', 'PUT', '认沽', '沽']: t1 = 'P'
                else: t1 = 'C' # Default

                if str(type2).upper() in ['C', 'CALL', '认购', '购']: t2 = 'C'
                elif str(type2).upper() in ['P', 'PUT', '认沽', '沽']: t2 = 'P'
                else: t2 = 'C'
                
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
