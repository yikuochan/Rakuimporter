#!/usr/bin/env python3
"""
Test script to verify that process_japan_exports.py is correctly using the fixed currency converter
with a mocked exchange rate function to avoid API calls
"""

import logging
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_process_japan_exports_mock")

# Import the transform_currency function from process_japan_exports.py
from process_japan_exports import transform_currency

# Import the currency_converter module to mock the get_exchange_rate function
import currency_converter

# Save the original get_exchange_rate function
original_get_exchange_rate = currency_converter.get_exchange_rate

# Define a mock get_exchange_rate function that returns fixed rates
def mock_get_exchange_rate(from_currency, to_currency, **kwargs):
    if (from_currency == "RMB" and to_currency == "NTD"):
        return 4.45  # Fixed rate for RMB to NTD
    elif (from_currency == "USD" and to_currency == "NTD"):
        return 31.5  # Fixed rate for USD to NTD
    return 1.0  # Default rate for other currency pairs

# Replace the get_exchange_rate function with our mock
currency_converter.get_exchange_rate = mock_get_exchange_rate

# Test cases
test_cases = [
    {"company_code": "VCT", "currency_code": "RMB", "amount": 1000.0, "expected_currency": "", "expected_rate": 4.45},
    {"company_code": "VCT", "currency_code": "USD", "amount": 100.0, "expected_currency": "", "expected_rate": 31.5},
    {"company_code": "VCT", "currency_code": "NTD", "amount": 500.0, "expected_currency": "", "expected_rate": 1.0},
]

# Run the tests
print("Testing transform_currency function with mocked exchange rates...")
all_passed = True

for i, test in enumerate(test_cases):
    print(f"\nTest {i+1}: {test['amount']} {test['currency_code']} -> NTD (company: {test['company_code']})")
    
    # Call the transform_currency function
    transformed_currency, converted_amount = transform_currency(
        test['company_code'], 
        test['currency_code'], 
        test['amount'], 
        decimal_precision=2
    )
    
    # Print the results
    print(f"  Original: {test['amount']} {test['currency_code']}")
    print(f"  Transformed: {converted_amount} {transformed_currency}")
    print(f"  Result type: {type(converted_amount)}")
    
    # Verify the result
    expected_amount = test['amount'] * test['expected_rate']
    
    # Check if the result is a Decimal
    if not isinstance(converted_amount, Decimal):
        print(f"  ✗ Result is not a Decimal type")
        all_passed = False
    
    # Check if the transformed currency is correct
    if transformed_currency != test['expected_currency']:
        print(f"  ✗ Transformed currency is incorrect: expected '{test['expected_currency']}', got '{transformed_currency}'")
        all_passed = False
    
    # Check if the converted amount is correct (with some tolerance for floating point)
    if abs(float(converted_amount) - expected_amount) > 0.01:
        print(f"  ✗ Converted amount is incorrect: expected {expected_amount}, got {float(converted_amount)}")
        all_passed = False
    
    if isinstance(converted_amount, Decimal) and transformed_currency == test['expected_currency'] and abs(float(converted_amount) - expected_amount) <= 0.01:
        print(f"  ✓ Test passed")

# Restore the original get_exchange_rate function
currency_converter.get_exchange_rate = original_get_exchange_rate

# Print the final result
if all_passed:
    print("\n✓ All tests passed! process_japan_exports.py is correctly using the fixed currency converter.")
else:
    print("\n✗ Some tests failed. Check the output above for details.")

print("\nTest completed")
