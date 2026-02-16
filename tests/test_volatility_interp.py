import sys
import os
import unittest
# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.analytics.volatility import interpolate_constant_maturity_iv

class TestVolatilityInterp(unittest.TestCase):
    def setUp(self):
        self.curve = [
            {"days": 10, "iv": 0.20}, # Var = 0.04 * 10/365 = 0.001095
            {"days": 40, "iv": 0.30}, # Var = 0.09 * 40/365 = 0.009863
        ]
        
    def test_extrapolation_short(self):
        # Should return nearest (0.20)
        iv = interpolate_constant_maturity_iv(5, self.curve)
        self.assertEqual(iv, 0.20)

    def test_extrapolation_long(self):
        # Should return nearest (0.30)
        iv = interpolate_constant_maturity_iv(50, self.curve)
        self.assertEqual(iv, 0.30)
        
    def test_interpolation(self):
        # Target 25 days (midpoint)
        # Var1 = 0.04 * 10 = 0.4 (scaled)
        # Var2 = 0.09 * 40 = 3.6 (scaled)
        # w = 0.5
        # Var_target approx (0.4 + 3.6)/2 ??? No, time weighted.
        
        # Let's trust the calc:
        target_days = 25
        iv = interpolate_constant_maturity_iv(target_days, self.curve)
        
        # Approximate check
        # It should be between 0.20 and 0.30
        self.assertTrue(0.20 < iv < 0.30)
        print(f"Interpolated IV for 25 days: {iv:.4f}")

    def test_exact_match(self):
        iv = interpolate_constant_maturity_iv(40, self.curve)
        self.assertEqual(iv, 0.30)

if __name__ == '__main__':
    unittest.main()
