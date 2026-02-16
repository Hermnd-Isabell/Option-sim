
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def check(url, name):
    print(f"Checking {name}: {url}")
    try:
        t0 = time.time()
        resp = requests.get(url, timeout=5)
        t1 = time.time()
        print(f"  Status: {resp.status_code}")
        print(f"  Time: {t1 - t0:.4f}s")
        if resp.status_code == 200:
             print("  Success")
        else:
             print(f"  Fail: {resp.text[:100]}")
    except Exception as e:
        print(f"  Error: {e}")

def run():
    # 1. Health Check
    check(f"{BASE_URL}/api/data/dates?dataset_id=510050_SH", "Dates Endpoint")
    
    # 2. Known Good Date (from profile)
    check(f"{BASE_URL}/api/data/gex-profile?date=2020-06-19&dataset_id=510050_SH", "GEX 2020-06-19")
    
    # 3. Problematic Date
    check(f"{BASE_URL}/api/data/gex-profile?date=2020-06-17&dataset_id=510050_SH", "GEX 2020-06-17")

if __name__ == "__main__":
    run()
