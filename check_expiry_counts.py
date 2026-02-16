import httpx

def check_date_data(date_str):
    base_url = "http://localhost:8000"
    print(f"Checking assets for date: {date_str}")
    
    try:
        resp = httpx.get(f"{base_url}/api/data/assets?date={date_str}")
        if resp.status_code != 200:
            print(f"Error: {resp.status_code}")
            return
            
        assets = resp.json().get("assets", [])
        
        counts = {}
        for a in assets:
            exp = a.get("expiry")
            if exp not in counts: counts[exp] = 0
            counts[exp] += 1
            
        print(f"Found {len(assets)} total assets.")
        print("-" * 30)
        print(f"{'Expiry':<15} | {'Count':<5}")
        print("-" * 30)
        
        sorted_exps = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        for exp, count in sorted_exps:
            print(f"{exp:<15} | {count:<5}")
            
        print("-" * 30)
        print("Logic Selection:", sorted_exps[0][0] if sorted_exps else "None")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_date_data("2020-01-06")
