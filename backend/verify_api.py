
import urllib.request
import json
import time

def verify():
    # date and dataset matching the mock data or real data availability
    url = "http://localhost:8000/api/data/iv-surface?date=2021-01-04&dataset_id=510050_SH"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            print("API Response Received")
            print(f"Data Quality: {data.get('data_quality')}")
            # We can't see the internal logs here, but we ensure the request happened.
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    verify()
