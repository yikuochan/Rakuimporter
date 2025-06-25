#!/usr/bin/env python3
"""
Test script to verify zero decimal rounding functionality.

This script tests the currency converter with the new default decimal precision of 0
to ensure amounts are rounded to whole numbers.
"""

import sys
import os

# Add the current directory to the Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.currency_converter import convert_amount, convert_through_intermediate
from decimal import Decimal

def test_zero_decimal_rounding():
    """Test that currency conversion uses zero decimal precision by default."""
    print("Testing Zero Decimal Rounding")
    print("=" * 50)
    
    # Test cases with fractional amounts
    test_cases = [
        {
            "amount": 100.75,
            "from_currency": "USD",
            "to_currency": "USD",
            "expected": 101,  # Should round 100.75 to 101
            "description": "Same currency conversion with rounding"
        },
        {
            "amount": 50.25,
            "from_currency": "NTD",
            "to_currency": "NTD", 
            "expected": 50,  # Should round 50.25 to 50
            "description": "Same currency conversion with rounding down"
        },
        {
            "amount": 99.5,
            "from_currency": "EUR",
            "to_currency": "EUR",
            "expected": 100,  # Should round 99.5 to 100
            "description": "Same currency conversion with exact half rounding"
        }
    ]
    
    print("Test 1: Default decimal precision (should be 0)")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['description']}")
        print(f"Input: {test_case['amount']} {test_case['from_currency']} -> {test_case['to_currency']}")
        
        converted_amount, success = convert_amount(
            test_case['amount'],
            test_case['from_currency'],
            test_case['to_currency']
        )
        
        print(f"Result: {converted_amount} (Success: {success})")
        print(f"Expected: {test_case['expected']}")
        
        if success and float(converted_amount) == test_case['expected']:
            print("✅ PASS")
        else:
            print("❌ FAIL")
    
    print("\n" + "=" * 50)
    print("Test 2: Explicit decimal precision = 0")
    
    # Test with explicit decimal_precision=0
    test_amount = 123.789
    converted_amount, success = convert_amount(
        test_amount, "USD", "USD", decimal_precision=0
    )
    
    print(f"Input: {test_amount} USD -> USD (decimal_precision=0)")
    print(f"Result: {converted_amount} (Success: {success})")
    print(f"Expected: 124")
    
    if success and float(converted_amount) == 124:
        print("✅ PASS")
    else:
        print("❌ FAIL")
    
    print("\n" + "=" * 50)
    print("Test 3: Explicit decimal precision = 2 (old behavior)")
    
    # Test with explicit decimal_precision=2
    converted_amount, success = convert_amount(
        test_amount, "USD", "USD", decimal_precision=2
    )
    
    print(f"Input: {test_amount} USD -> USD (decimal_precision=2)")
    print(f"Result: {converted_amount} (Success: {success})")
    print(f"Expected: 123.79")
    
    if success and float(converted_amount) == 123.79:
        print("✅ PASS")
    else:
        print("❌ FAIL")
    
    print("\n" + "=" * 50)
    print("Test 4: Through intermediate currency with default precision")
    
    # Test convert_through_intermediate with default precision
    test_amount = 456.67
    converted_amount, success = convert_through_intermediate(
        test_amount, "USD", "EUR", "USD"
    )
    
    print(f"Input: {test_amount} USD -> EUR -> USD (default precision)")
    print(f"Result: {converted_amount} (Success: {success})")
    print("Expected: Whole number (rounded)")
    
    if success:
        # Check if it's a whole number
        is_whole = float(converted_amount) == int(float(converted_amount))
        if is_whole:
            print("✅ PASS - Result is a whole number")
        else:
            print("❌ FAIL - Result has decimal places")
    else:
        print("❌ FAIL - Conversion failed")

if __name__ == "__main__":
    test_zero_decimal_rounding()
