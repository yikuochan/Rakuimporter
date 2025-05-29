#!/usr/bin/env python3
"""
Test script to verify the currency conversion rounding fix in currency_converter.py.

This script tests the convert_amount function in currency_converter.py to ensure
that NumPy rounding is being applied correctly.
"""

import logging
import numpy as np
from currency_converter import convert_amount

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("currency_rounding_test")

def test_numpy_rounding():
    """Test that NumPy rounding is being applied correctly in convert_amount."""
    print("Testing NumPy rounding in convert_amount function...")
    
    # Test cases with values that would show differences between standard Python rounding and NumPy rounding
    test_cases = [
        # amount, from_currency, to_currency, rate, decimal_precision
        (12.0, "RMB", "NTD", 4.45, 2),
        (1800.0, "RMB", "NTD", 4.45, 2),
        (174.0, "RMB", "NTD", 4.45, 2),
        (103.4, "RMB", "NTD", 4.45, 2),
        (0.1, "RMB", "NTD", 4.45, 2),
        (0.2, "RMB", "NTD", 4.45, 2),
        (0.3, "RMB", "NTD", 4.45, 2),
        # Edge cases
        (0.005, "USD", "EUR", 0.85, 2),  # Tests rounding at exactly half
        (0.015, "USD", "EUR", 0.85, 2),  # Tests rounding at exactly half
        (0.025, "USD", "EUR", 0.85, 2),  # Tests rounding at exactly half
        # Large numbers
        (1000000.005, "USD", "JPY", 110.0, 2),  # Large number with rounding
        # Negative numbers
        (-12.345, "EUR", "USD", 1.18, 2),  # Negative number
    ]
    
    all_passed = True
    
    for amount, from_currency, to_currency, rate, decimal_precision in test_cases:
        # Mock the exchange rate by monkey patching the get_exchange_rate function
        original_get_exchange_rate = convert_amount.__globals__['get_exchange_rate']
        convert_amount.__globals__['get_exchange_rate'] = lambda *args, **kwargs: rate
        
        try:
            # Call convert_amount
            converted, success = convert_amount(amount, from_currency, to_currency, decimal_precision=decimal_precision)
            
            # Calculate expected results
            # Standard Python arithmetic
            standard_expected = amount * rate
            # NumPy rounding
            numpy_expected = float(np.round(amount * rate, decimal_precision))
            
            print(f"\nTest case: {amount} {from_currency} to {to_currency} (rate: {rate}, precision: {decimal_precision})")
            print(f"  Converted amount: {converted}")
            print(f"  Standard expected: {standard_expected}")
            print(f"  NumPy expected: {numpy_expected}")
            
            # Check if the converted amount matches the NumPy expected amount
            numpy_matches = abs(converted - numpy_expected) < 0.0001
            standard_matches = abs(converted - standard_expected) < 0.0001
            
            print(f"  Matches standard calculation: {standard_matches}")
            print(f"  Matches NumPy calculation: {numpy_matches}")
            
            # If standard and NumPy calculations differ, check which one the result matches
            if abs(standard_expected - numpy_expected) > 0.0001:
                print(f"  Standard and NumPy calculations differ")
                if numpy_matches and not standard_matches:
                    print(f"  ✅ NumPy rounding is being applied correctly")
                elif standard_matches and not numpy_matches:
                    print(f"  ❌ Standard rounding is being applied instead of NumPy rounding")
                    all_passed = False
                else:
                    print(f"  ❓ Neither calculation matches - unexpected result")
                    all_passed = False
            else:
                print(f"  Standard and NumPy calculations are the same for this value")
                if numpy_matches:
                    print(f"  ✅ Rounding is correct (but can't determine if NumPy is being used)")
                else:
                    print(f"  ❌ Unexpected result - doesn't match either calculation")
                    all_passed = False
        
        finally:
            # Restore the original get_exchange_rate function
            convert_amount.__globals__['get_exchange_rate'] = original_get_exchange_rate
    
    if all_passed:
        print("\n✅ All tests passed! NumPy rounding is being applied correctly.")
        return True
    else:
        print("\n❌ Some tests failed. NumPy rounding may not be applied correctly in all cases.")
        return False

def main():
    """Main function to run the tests."""
    success = test_numpy_rounding()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
