#!/usr/bin/env python3
"""
Test script to verify that process_japan_exports.py is correctly using the fixed currency converter
"""

import logging
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_process_japan_exports")

# Import the transform_currency function from process_japan_exports.py
from process_japan_exports import transform_currency

# Test the transform_currency function with a sample RMB to NTD conversion
print("Testing transform_currency function with RMB to NTD conversion...")
company_code = "VCT"
currency_code = "RMB"
amount = 1000.0
decimal_precision = 2

# Call the transform_currency function
transformed_currency, converted_amount = transform_currency(company_code, currency_code, amount, decimal_precision)

# Print the results
print(f"Original: {amount} {currency_code}")
print(f"Transformed: {converted_amount} {transformed_currency}")
print(f"Result type: {type(converted_amount)}")

# Verify that the result is a Decimal (from the fixed currency converter)
if isinstance(converted_amount, Decimal):
    print("✓ Result is a Decimal type (using fixed currency converter)")
else:
    print("✗ Result is not a Decimal type (not using fixed currency converter)")

print("\nTest completed")
