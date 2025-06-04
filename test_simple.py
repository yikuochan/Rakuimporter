#!/usr/bin/env python3

print("Test script is running")

# Import the currency_rounding_fix module
import importlib.util
import sys
from decimal import Decimal, ROUND_HALF_UP

spec = importlib.util.spec_from_file_location("currency_rounding_fix", "currency_rounding_fix.py")
module = importlib.util.module_from_spec(spec)
sys.modules["currency_rounding_fix"] = module
spec.loader.exec_module(module)

print("Successfully imported currency_rounding_fix.py")

# Run the fix_currency_converter function
try:
    module.fix_currency_converter()
    print("Successfully ran fix_currency_converter()")
except Exception as e:
    print(f"Error running fix_currency_converter(): {str(e)}")

# Import the original and fixed modules
try:
    spec_orig = importlib.util.spec_from_file_location("currency_converter", "currency_converter.py")
    orig_module = importlib.util.module_from_spec(spec_orig)
    sys.modules["currency_converter"] = orig_module
    spec_orig.loader.exec_module(orig_module)
    print("Successfully imported currency_converter.py")
    
    spec_fixed = importlib.util.spec_from_file_location("currency_converter_fixed", "currency_converter_fixed.py")
    fixed_module = importlib.util.module_from_spec(spec_fixed)
    sys.modules["currency_converter_fixed"] = fixed_module
    spec_fixed.loader.exec_module(fixed_module)
    print("Successfully imported currency_converter_fixed.py")
except Exception as e:
    print(f"Error importing modules: {str(e)}")

# Mock the get_exchange_rate function to avoid API calls
def mock_get_exchange_rate(from_currency, to_currency, **kwargs):
    return 1.0  # Always return 1.0 for testing

# Patch the get_exchange_rate function in both modules
orig_module.get_exchange_rate = mock_get_exchange_rate
fixed_module.get_exchange_rate = mock_get_exchange_rate

# Test cases that demonstrate the rounding issue
test_cases = [
    # amount, from_currency, to_currency, expected_original, expected_fixed
    (83870.135, "NTD", "NTD"),  # This should round differently
    (83870.5, "NTD", "NTD"),    # This should round to 83870.5 with both methods
    (83870.55, "NTD", "NTD"),   # This should round to 83870.55 with both methods
    (83870.555, "NTD", "NTD"),  # This should round differently
]

print("\nTesting rounding behavior:")
for amount, from_currency, to_currency in test_cases:
    # Test with original module
    original_result, _ = orig_module.convert_amount(amount, from_currency, to_currency)
    
    # Test with fixed module
    fixed_result, _ = fixed_module.convert_amount(amount, from_currency, to_currency)
    
    # Calculate expected results using different rounding methods
    import numpy as np
    numpy_rounded = np.round(amount, 2)
    decimal_rounded = float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    print(f"\nAmount: {amount} {from_currency} to {to_currency}")
    print(f"  Original module result: {original_result}")
    print(f"  Fixed module result: {fixed_result}")
    print(f"  NumPy rounded: {numpy_rounded}")
    print(f"  Decimal rounded: {decimal_rounded}")
    
    if original_result != fixed_result:
        print(f"  ✓ Difference detected: original={original_result}, fixed={fixed_result}")
    else:
        print(f"  ✗ No difference detected: both={original_result}")

# Test the specific calculation for OBA-0000027
print("\nTesting OBA-0000027 calculation:")
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

# Calculate the sum using both modules
original_total = 0.0
fixed_total = 0.0

for amount, from_currency, to_currency in values:
    # For R-RMB to NTD, use a fixed rate of 4.45
    if from_currency == "R-RMB" and to_currency == "NTD":
        orig_module.get_exchange_rate = lambda f, t, **kwargs: 4.45
        fixed_module.get_exchange_rate = lambda f, t, **kwargs: 4.45
    else:
        orig_module.get_exchange_rate = lambda f, t, **kwargs: 1.0
        fixed_module.get_exchange_rate = lambda f, t, **kwargs: 1.0
    
    # Convert using both modules
    original_converted, _ = orig_module.convert_amount(amount, from_currency, to_currency)
    fixed_converted, _ = fixed_module.convert_amount(amount, from_currency, to_currency)
    
    # Add to totals
    original_total += original_converted
    fixed_total += fixed_converted
    
    print(f"  {amount} {from_currency} -> {original_converted} vs {fixed_converted}")

print(f"\nOriginal total: {original_total}")
print(f"Fixed total: {fixed_total}")
print(f"Difference: {fixed_total - original_total}")

# Calculate using Decimal for comparison
decimal_total = sum(Decimal(str(amount)) for amount, from_curr, to_curr in values if from_curr == "NTD")
for amount, from_currency, to_currency in values:
    if from_currency != "NTD" and from_currency.startswith("R-"):
        # Simulate the conversion using Decimal
        rate = 4.45  # Approximate rate for RMB to NTD
        decimal_amount = Decimal(str(amount)) * Decimal(str(rate))
        decimal_amount = decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        decimal_total += decimal_amount

print(f"Decimal total: {float(decimal_total)}")
