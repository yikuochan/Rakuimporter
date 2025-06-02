#!/usr/bin/env python3
"""
Simple test for the fixed currency converter
"""

import logging
from decimal import Decimal

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_fixed_converter")

# Import the fixed module
import currency_converter

# Open a file to write the test results
with open("test_fixed_converter_results.txt", "w") as f:
    # Test basic conversion
    f.write("Testing basic conversion...\n")
    amount = 100.0
    from_currency = "USD"
    to_currency = "EUR"

    converted, success = currency_converter.convert_amount(amount, from_currency, to_currency)
    f.write(f"Converted {amount} {from_currency} to {converted} {to_currency}\n")
    f.write(f"Result type: {type(converted)}\n")
    f.write(f"Success: {success}\n")

    # Test RMB to NTD conversion (specific to OBA-0000027 issue)
    f.write("\nTesting RMB to NTD conversion...\n")
    amount = 1000.0
    from_currency = "RMB"
    to_currency = "NTD"

    # Mock the exchange rate function to return a fixed rate
    original_get_exchange_rate = currency_converter.get_exchange_rate

    def mock_get_exchange_rate(from_curr, to_curr, **kwargs):
        if from_curr == "RMB" and to_curr == "NTD":
            return 4.45
        return 1.0

    # Replace the function temporarily
    currency_converter.get_exchange_rate = mock_get_exchange_rate

    # Test the conversion
    converted, success = currency_converter.convert_amount(amount, from_currency, to_currency)
    f.write(f"Converted {amount} {from_currency} to {converted} {to_currency}\n")
    f.write(f"Result type: {type(converted)}\n")
    f.write(f"Success: {success}\n")

    # Restore the original function
    currency_converter.get_exchange_rate = original_get_exchange_rate

    f.write("\nTest completed successfully!\n")

print("Test results written to test_fixed_converter_results.txt")
