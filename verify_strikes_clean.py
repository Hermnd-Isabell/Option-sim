
import requests
import json

def verify_strikes():
    url = "http://localhost:8000/api/data/iv-surface?date=2020-07-09&dataset_id=510050_SH"
    print(f"Checking {url}...")
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"Failed: {resp.status_code}")
            return
            
        data = resp.json()
        strikes = data.get('strikes', [])
        print(f"Returned {len(strikes)} strikes.")
        print(f"Strikes: {strikes}")
        
        # Check for weird decimals (standard are usually x.xx0 or x.x00 or x.x50)
        # Adjusted often have 3-4 decimal places like 2.342
        
        weird_strikes = []
        for s in strikes:
            # Check if it's "nice" (multiple of 0.001? actually strict multiple of 0.05 usually)
            # But let's just check string length or mod
            rem = s % 0.001
            if rem > 0.0001 and rem < 0.0009: # if not close to 0
                 weird_strikes.append(s)
                 
        if weird_strikes:
            print(f"FAILED: Found weird strikes: {weird_strikes}")
        else:
            print("PASSED: All strikes appear standard.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_strikes()
