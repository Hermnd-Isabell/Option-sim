import sys
import os
import pandas as pd
sys.path.append(os.getcwd())

from backend.app.analytics.volatility import calculate_volatility_cone, get_price_history

def verify():
    print("1. Testing Price History & Implied Spot...")
    try:
        # Force rebuild to test logic
        df = get_price_history(force_rebuild=True)
        print(f"Price History: {len(df)} records")
        print(df.head())
        print(df.tail())
        
        # Check source distribution
        print("\nSource Distribution:")
        print(df['source'].value_counts())
        
        # Check for NaNs
        na_count = df['close'].isna().sum()
        print(f"NaN Prices: {na_count}")
        
    except Exception as e:
        print(f"Error in price history: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n2. Testing Volatility Cone Calculation...")
    try:
        # Use a date in 2022
        test_date = "2022-06-01"
        res = calculate_volatility_cone(test_date)
        
        if "error" in res:
            print(f"Error: {res['error']}")
        else:
            print(f"Latest Price: {res['latest_price']}")
            print("Cone Curves (First 3):")
            for c in res['cone_curves'][:3]:
                print(c)
                
    except Exception as e:
        print(f"Error in cone calc: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    verify()
