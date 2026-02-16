
import requests
import json
import sys

def test_cone_fix():
    url = "http://localhost:8000/api/data/volatility-cone"
    # 2020-07-11 is a Saturday, so no data.
    # Previously this returned 404 or 0 current_iv.
    params = {
        "current_date": "2020-07-11",
        "lookback_days": 60,
        "dataset_id": "510050_SH"
    }
    
    try:
        print(f"Requesting {url} with params {params}...")
        response = requests.get(url, params=params)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print("FAILED: Expected 200 OK, got", response.status_code)
            print("Response:", response.text)
            return
        
        data = response.json()
        print("Response received.")
        
        if "cone" not in data:
            print("FAILED: 'cone' key missing in response")
            return
            
        cone = data["cone"]
        if not cone:
            print("FAILED: cone list is empty")
            return
            
        # Check first bucket
        first_bucket = cone[0]
        print("First Bucket:", first_bucket)
        
        current_iv = first_bucket.get("current_iv")
        print(f"current_iv: {current_iv}")
        
        if current_iv is None:
            print("TEST RESULT: PASS (current_iv is None)")
        elif current_iv == 0:
            print("TEST RESULT: FAIL (current_iv is 0)")
        else:
            print(f"TEST RESULT: WARNING (current_iv={current_iv})")

        # Check buckets
        dtes = [item['dte'] for item in cone]
        expected_buckets = [20, 30, 60, 90, 120]
        if dtes == expected_buckets:
             print("BUCKETS: PASS")
        else:
             print(f"BUCKETS: FAIL {dtes}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cone_fix()
