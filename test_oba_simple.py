#!/usr/bin/env python3
"""
Simple test for the OBA-0000027 issue with the fixed currency converter
"""

import logging
from decimal import Decimal, ROUND_HALF_UP

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_oba_simple")

# Import the fixed module
import currency_converter

# Values from the OBA-0000027 voucher (simplified for testing)
values = [
    (25100.0, "NTD", "NTD"),  # Air fare
    (1900.0, "NTD", "NTD"),   # Gift for Chery, Mr. Du
    (1100.0, "NTD", "NTD"),   # Gift for Cariad CN
    (1800.0, "R-RMB", "NTD"), # RMB amount
    (174.0, "R-RMB", "NTD"),  # RMB amount
    (340.0, "NTD", "NTD"),    # NTD amount
]

# Mock the get_exchange_rate function to return a fixed rate for RMB to NTD
original_get_exchange_rate = currency_converter.get_exchange_rate

def mock_get_exchange_rate(from_currency, to_currency, **kwargs):
    if (from_currency == "RMB" and to_currency == "NTD") or (from_currency == "R-RMB" and to_currency == "NTD"):
        return 4.45  # Fixed rate for RMB to NTD
    return 1.0  # Default rate for other currency pairs

# Replace the function temporarily
currency_converter.get_exchange_rate = mock_get_exchange_rate

# Calculate the sum
print("Calculating with fixed currency converter:")
total = Decimal('0')

for amount, from_currency, to_currency in values:
    converted, success = currency_converter.convert_amount(amount, from_currency, to_currency)
    total += converted
    print(f"  {amount} {from_currency} -> {converted} {to_currency}")

print(f"\nTotal: {total}")

# Calculate expected total manually
ntd_total = 25100.0 + 1900.0 + 1100.0 + 340.0
rmb_total = 1800.0 + 174.0
rmb_to_ntd = rmb_total * 4.45
expected_total = Decimal(str(ntd_total)) + Decimal(str(rmb_to_ntd)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

print(f"Expected total: {expected_total}")
print(f"Difference: {total - expected_total}")

# Restore the original function
currency_converter.get_exchange_rate = original_get_exchange_rate

print("\nTest completed")
