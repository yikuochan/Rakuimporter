#!/usr/bin/env python3
"""
Test OBA-0000027 Voucher Calculation

This script tests the calculation for voucher OBA-0000027 using both the original
and fixed currency_converter modules to demonstrate the rounding issue.
"""

import logging
import sys
from decimal import Decimal, ROUND_HALF_UP

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_oba_0000027")

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

# Values from the OBA-0000027 voucher
values = [
    (25100.0, "NTD", "NTD"),  # Air fare
    (1900.0, "NTD", "NTD"),   # Gift for Chery, Mr. Du
    (1100.0, "NTD", "NTD"),   # Gift for Cariad CN
    (12.0, "R-RMB", "NTD"),   # Postage for the docs for 極飛
    (1800.0, "R-RMB", "NTD"), # 375 x 6 - 450 (3 meals) = RMB 1,800
    (174.0, "R-RMB", "NTD"),  # Lunch with Max Jiang
    (103.4, "R-RMB", "NTD"),  # Taxi
    (440.86, "R-RMB", "NTD"), # Taxi
    (55.97, "R-RMB", "NTD"),  # Coffee for Dan/Allianz
    (134.0, "R-RMB", "NTD"),  # Lunch with Allianz Dan
    (103.0, "R-RMB", "NTD"),  # Coffee for Dan/Allianz
    (100.0, "R-RMB", "NTD"),  # Shanghai subway refill
    (35.49, "R-RMB", "NTD"),  # Taxi
    (62.06, "R-RMB", "NTD"),  # Taxi
    (49.37, "R-RMB", "NTD"),  # Taxi
    (131.26, "R-RMB", "NTD"), # Taxi
    (352.2, "R-RMB", "NTD"),  # Taxi
    (283.0, "R-RMB", "NTD"),  # HSR, Shanghai to Wuhu
    (7612.8, "R-RMB", "NTD"), # 4/20 - 4/26 hotel accommodation
    (116.8, "R-RMB", "NTD"),  # Taxi
    (657.0, "R-RMB", "NTD"),  # HSR, Wuhu to Shanghai
    (340.0, "NTD", "NTD"),    # 車公用 17 x 2 x 10= 340
    (163.0, "R-RMB", "NTD"),  # Lunch with Dan/Alliaz
    (70.0, "R-RMB", "NTD"),   # Coffee with Dan/Allianz
]

# Mock the get_exchange_rate function to return a fixed rate for RMB to NTD
def mock_get_exchange_rate(from_currency, to_currency, **kwargs):
    if (from_currency == "RMB" and to_currency == "NTD") or (from_currency == "R-RMB" and to_currency == "NTD"):
        return 4.45  # Fixed rate for RMB to NTD
    return 1.0  # Default rate for other currency pairs

# Patch the get_exchange_rate function in both modules
orig_module.get_exchange_rate = mock_get_exchange_rate
fixed_module.get_exchange_rate = mock_get_exchange_rate

# Calculate the sum using the original module
print("\nCalculating with original module:")
original_total = Decimal('0')
original_items = []

for amount, from_currency, to_currency in values:
    original_converted, success = orig_module.convert_amount(amount, from_currency, to_currency)
    original_total += original_converted
    original_items.append((amount, from_currency, original_converted))
    print(f"  {amount} {from_currency} -> {original_converted} NTD")

print(f"\nOriginal total: {original_total}")

# Calculate the sum using the fixed module
print("\nCalculating with fixed module:")
fixed_total = Decimal('0')
fixed_items = []

for amount, from_currency, to_currency in values:
    fixed_converted, success = fixed_module.convert_amount(amount, from_currency, to_currency)
    fixed_total += fixed_converted
    fixed_items.append((amount, from_currency, fixed_converted))
    print(f"  {amount} {from_currency} -> {fixed_converted} NTD")

print(f"\nFixed total: {fixed_total}")

# Calculate using Decimal for comparison
print("\nCalculating with Decimal:")
decimal_total = Decimal('0')
decimal_items = []

for amount, from_currency, to_currency in values:
    if from_currency == "NTD":
        # No conversion needed
        decimal_amount = Decimal(str(amount))
    else:
        # Convert using Decimal
        rate = Decimal('4.45')  # Fixed rate for RMB to NTD
        decimal_amount = Decimal(str(amount)) * rate
        decimal_amount = decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    decimal_total += decimal_amount
    decimal_items.append((amount, from_currency, float(decimal_amount)))
    print(f"  {amount} {from_currency} -> {float(decimal_amount)} NTD")

print(f"\nDecimal total: {float(decimal_total)}")

# Compare results
print("\nComparison:")
print(f"Original total: {float(original_total)}")
print(f"Fixed total: {float(fixed_total)}")
print(f"Decimal total: {float(decimal_total)}")
print(f"Difference (fixed - original): {float(fixed_total - original_total)}")
print(f"Expected consolidated amount: 83870.14")

# Check if the fixed calculation matches the expected consolidated amount
if abs(float(fixed_total) - 83870.14) < 0.01:
    print("\n✓ Fixed calculation matches expected consolidated amount")
else:
    print(f"\n✗ Fixed calculation {float(fixed_total)} does not match expected consolidated amount 83870.14")

# Check if the original calculation matches the reported issue
if abs(float(original_total) - 83868.0) < 2.0:
    print("✓ Original calculation matches the reported issue (83868)")
else:
    print(f"✗ Original calculation {float(original_total)} does not match the reported issue (83868)")

print("\nTest completed")
