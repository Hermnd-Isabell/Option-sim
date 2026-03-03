import sys
import os
import time
import threading
from pathlib import Path

# Setup paths to mimic backend environment
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "backend"))

# Mock DataLoader to avoid full data dependency if needed, 
# but we want to test real logic.
# ensuring backend.app.analytics.volatility is imported consistently

try:
    from backend.app.analytics import volatility
except ImportError:
    # Try alternate structure if running from root
    import backend.app.analytics.volatility as volatility

print(f"Loaded volatility module: {volatility}")

def trigger_calculation():
    print("Triggering calculation...")
    # Force rebuild to ensure it takes time
    try:
        # We delete cache first?
        cache_path = Path("data/price_history_cache.csv")
        if cache_path.exists():
            os.remove(cache_path)
    except:
        pass
        
    volatility.get_price_history(force_rebuild=True)
    print("Calculation done.")

def poll_progress():
    print("Starting poller...")
    for _ in range(20):
        prog = volatility.get_progress()
        print(f"Progress: {prog}")
        if prog['status'] == 'done':
            break
        time.sleep(0.5)

if __name__ == "__main__":
    # Create threads
    t1 = threading.Thread(target=trigger_calculation)
    t2 = threading.Thread(target=poll_progress)
    
    t1.start()
    time.sleep(0.5) # Give it a moment to start
    t2.start()
    
    t1.join()
    t2.join()
