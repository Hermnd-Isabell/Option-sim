
import math
import numpy as np

def calculate_implied_forward(calls, puts, T, r):
    if not calls or not puts:
        return None
        
    common_strikes = sorted(list(set(calls.keys()) & set(puts.keys())))
    if not common_strikes:
        return None
    
    implied_forwards = []
    
    for k in common_strikes:
        c = calls[k]
        p = puts[k]
        
        # F = K + (C - P) * e^(rT)
        f_val = k + (c - p) * math.exp(r * T)
        
        if f_val > 0:
            implied_forwards.append(f_val)
            
    if not implied_forwards:
        return None
        
    F_median = float(np.median(implied_forwards))
    return F_median * math.exp(-r * T)

def test_implied_forward():
    r = 0.03
    T = 30 / 365.0
    spot_true = 3.0
    forward_true = spot_true * math.exp(r * T)
    
    # Generate some theoretical prices
    calls = {}
    puts = {}
    
    strikes = [2.8, 2.9, 3.0, 3.1, 3.2]
    
    for K in strikes:
        # Simple parity: C - P = (F - K) * e^(-rT)
        # Let's say we have perfect data
        diff = (forward_true - K) * math.exp(-r * T)
        
        # Arbitrary starting price for P (doesn't matter for parity difference, checking logic)
        # But let's be realistic somewhat
        p_val = max(0, K - forward_true) + 0.05 # Add some time value
        c_val = p_val + diff
        
        calls[K] = c_val
        puts[K] = p_val
    
    # Introduce some noise to one strike
    calls[2.9] += 0.01 
    
    implied_spot = calculate_implied_forward(calls, puts, T, r)
    
    print(f"True Spot: {spot_true}")
    print(f"Implied Spot: {implied_spot}")
    print(f"Error: {abs(implied_spot - spot_true)}")
    
    assert abs(implied_spot - spot_true) < 0.005, "Implied spot should be robust to small noise"
    print("Test Passed!")

if __name__ == "__main__":
    test_implied_forward()
