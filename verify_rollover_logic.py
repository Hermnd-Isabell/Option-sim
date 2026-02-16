import httpx
import datetime

def get_dte(expiry_str, current_date_str):
    try:
        exp = datetime.datetime.strptime(expiry_str, "%Y-%m-%d")
        curr = datetime.datetime.strptime(current_date_str, "%Y-%m-%d")
        return (exp - curr).days
    except:
        return 999

def simulate_frontend_logic(assets, current_date):
    # 1. Group
    groups = {}
    for a in assets:
        exp = a.get("expiry")
        if not exp: continue
        if exp not in groups: groups[exp] = []
        groups[exp].append(a)
    
    expiries = list(groups.keys())
    if not expiries: return None
    
    # 2. Filter > 10
    candidates = [exp for exp in expiries if len(groups[exp]) >= 10]
    if not candidates: candidates = expiries
    
    # 3. Sort by DTE
    candidates.sort(key=lambda x: get_dte(x, current_date))
    
    # 4. Roll-over Logic
    nearest = candidates[0]
    nearest_dte = get_dte(nearest, current_date)
    
    print(f"   [Logic Debug] Nearest: {nearest} (DTE={nearest_dte} days)")
    
    if nearest_dte < 3 and len(candidates) > 1:
        print(f"   [Logic Debug] Rollover Triggered! Skipping {nearest} for {candidates[1]}")
        return candidates[1]
        
    return nearest

def verify():
    base_url = "http://localhost:8000"
    target_date = "2020-01-06"
    
    print(f"--------------------------------------------------")
    print(f"Verifying Smart Logic for date: {target_date}")
    print(f"--------------------------------------------------")
    
    # 1. Real Data Test
    print(f"1. Fetching assets from API...")
    try:
        resp = httpx.get(f"{base_url}/api/data/assets?date={target_date}")
        assets = resp.json().get("assets", [])
        print(f"   Assets loaded: {len(assets)}")
        
        selected = simulate_frontend_logic(assets, target_date)
        print(f"   => Selected Expiry: {selected}")
        
        # Expectation: 2020-01-22 (Nearest) instead of 2020-03-25 (Max Count)
        if selected == "2020-01-22":
            print("   SUCCESS: Logic selected the Nearest Expiry (Jan) correctly.")
        else:
            print(f"   FAILURE: Logic selected {selected}. Expected 2020-01-22.")
            
    except Exception as e:
        print(f"   Error: {e}")

    # 2. Mock Rollover Test
    print(f"\n2. Testing Mock Rollover Scenario (DTE < 3)...")
    mock_current = "2023-01-01"
    mock_assets = []
    # Expiring tomorrow (2023-01-02, DTE=1)
    for _ in range(20): mock_assets.append({"expiry": "2023-01-02", "id": "A"})
    # Next Month (2023-02-01, DTE=31)
    for _ in range(20): mock_assets.append({"expiry": "2023-02-01", "id": "B"})
    
    selected_mock = simulate_frontend_logic(mock_assets, mock_current)
    print(f"   => Selected Expiry: {selected_mock}")
    
    if selected_mock == "2023-02-01":
        print("   SUCCESS: Rollover logic worked (Skipped Jan-02, selected Feb-01).")
    else:
        print(f"   FAILURE: Rollover logic failed. Selected {selected_mock}")

if __name__ == "__main__":
    verify()
