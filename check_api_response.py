
import requests
import json

def trigger_iv_surface():
    url = "http://localhost:8000/api/data/iv-surface?date=2020-07-09&dataset_id=510050_SH"
    print(f"Requesting {url}...")
    try:
        resp = requests.get(url, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print("Response Data Quality:", data.get('data_quality'))
            
            # Print spot price stats
            print(f"Returned Spot Price: {data.get('data_quality', {}).get('spot_price')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    trigger_iv_surface()
