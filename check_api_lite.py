import urllib.request
import json
import sys

def check_api():
    url = "http://localhost:8000/api/analytics/vol-cone?date=2026-02-03&symbol=510050_SH"
    
    try:
        print(f"Requesting {url}...")
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                print(f"Error: {response.status}")
                return
                
            data = json.loads(response.read().decode())
        
        print("\n--- API Response Check ---")
        
        # Check Spot
        spot = data.get('spot_ref')
        print(f"Spot Price (spot_ref): {spot}")
        
        if spot is None or spot == 0 or spot == 3.0:
             print("❌ Warning: Spot price is still 0 or default 3.0!")
        else:
             print("✅ Spot price is valid.")
             
        # Check Curve
        curves = data.get('cone', {}).get('cone_curves', [])
        if not curves:
            print("❌ No cone curves returned.")
            # Verify current_curve
            cc = data.get('current_curve', [])
            print(f"Current Curve Points: {len(cc)}")
            if cc:
                print(f"First point: {cc[0]}")
        else:
            first = curves[0]
            print(f"First Cone Window ({first.get('window')} days):")
            print(f" - Min: {first.get('min')}")
            print(f" - Current IV (Interpolated): {first.get('current_iv')}")
            
            if first.get('current_iv') == 0:
                print("❌ Current IV is 0!")
            else:
                print("✅ Current IV is non-zero.")

    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    check_api()
