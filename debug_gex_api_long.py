
import requests
import time

def debug_api():
    url = "http://localhost:8000/api/data/gex-profile?date=2020-06-17&dataset_id=510050_SH"
    print(f"Requesting {url} with 60s timeout...")
    try:
        t0 = time.time()
        resp = requests.get(url, timeout=60)
        t1 = time.time()
        print(f"Response Status: {resp.status_code}")
        print(f"Time Taken: {t1 - t0:.4f}s")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Data Profile Items: {len(data.get('profile', []))}")
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    debug_api()
