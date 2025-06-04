#!/usr/bin/env python3
"""
Simple Debug Test for Currency Rounding Fix

This script tests the rounding behavior of the original and fixed currency_converter modules
with explicit test cases that demonstrate the rounding issue.
"""

import logging
import sys
from decimal import Decimal, ROUND_HALF_UP
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_simple_debug")

print("Test script is running")

# Import the original and fixed modules
try:
    # Import original module
    sys.path.insert(0, '.')
    import currency_converter as orig_module
    print("Successfully imported currency_converter.py")
    
    # Import fixed module
    import currency_converter_fixed as fixed_module
    print("Successfully imported currency_converter_fixed.py")
except Exception as e:
    print(f"Error importing modules: {str(e)}")
    sys.exit(1)

# Test case that demonstrates the rounding issue
test_value = 83870.135

print("\nDirect rounding test:")
# Test NumPy rounding
np_rounded = np.round(test_value, 2)
print(f"NumPy rounding of {test_value}: {np_rounded}")

# Test Decimal rounding
decimal_rounded = float(Decimal(str(test_value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
print(f"Decimal rounding of {test_value}: {decimal_rounded}")

# Mock the get_exchange_rate function to avoid API calls
def mock_get_exchange_rate(from_currency, to_currency, **kwargs):
    return 1.0  # Always return 1.0 for testing

# Patch the get_exchange_rate function in both modules
orig_module.get_exchange_rate = mock_get_exchange_rate
fixed_module.get_exchange_rate = mock_get_exchange_rate

# Test with the same currency (no conversion, just rounding)
print("\nTesting with same currency (NTD to NTD):")
amount = 83870.135
from_currency = "NTD"
to_currency = "NTD"

# Test with original module
print("\nOriginal module test:")
print(f"Input: {amount} {from_currency} to {to_currency}")
try:
    # For same currency, the convert_amount function should just return the amount
    original_result, success = orig_module.convert_amount(amount, from_currency, to_currency)
    print(f"Result: {original_result}, Success: {success}")
    print(f"Type of result: {type(original_result)}")
except Exception as e:
    print(f"Error: {str(e)}")

# Test with fixed module
print("\nFixed module test:")
print(f"Input: {amount} {from_currency} to {to_currency}")
try:
    # For same currency, the convert_amount function should just return the amount
    fixed_result, success = fixed_module.convert_amount(amount, from_currency, to_currency)
    print(f"Result: {fixed_result}, Success: {success}")
    print(f"Type of result: {type(fixed_result)}")
except Exception as e:
    print(f"Error: {str(e)}")

# Test with different currencies to force conversion and rounding
print("\nTesting with different currencies (USD to NTD):")
amount = 83870.135
from_currency = "USD"
to_currency = "NTD"

# Test with original module
print("\nOriginal module test:")
print(f"Input: {amount} {from_currency} to {to_currency}")
try:
    original_result, success = orig_module.convert_amount(amount, from_currency, to_currency)
    print(f"Result: {original_result}, Success: {success}")
    print(f"Type of result: {type(original_result)}")
except Exception as e:
    print(f"Error: {str(e)}")

# Test with fixed module
print("\nFixed module test:")
print(f"Input: {amount} {from_currency} to {to_currency}")
try:
    fixed_result, success = fixed_module.convert_amount(amount, from_currency, to_currency)
    print(f"Result: {fixed_result}, Success: {success}")
    print(f"Type of result: {type(fixed_result)}")
except Exception as e:
    print(f"Error: {str(e)}")

# Compare results
print("\nComparison:")
if original_result == fixed_result:
    print(f"Both modules returned the same result: {original_result}")
else:
    print(f"Different results: original={original_result}, fixed={fixed_result}")
    print(f"Difference: {fixed_result - original_result}")

print("\nTest completed")
