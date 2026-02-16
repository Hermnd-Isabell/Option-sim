import requests
import time

def check_progress():
    url = "http://127.0.0.1:8000/api/analytics/progress"
    try:
        res = requests.get(url)
        print(f"Status: {res.status_code}")
        print(f"Body: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_progress()
