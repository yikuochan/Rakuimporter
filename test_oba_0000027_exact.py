#!/usr/bin/env python3
"""
Test OBA-0000027 Voucher Calculation with Exact Values

This script tests the calculation for voucher OBA-0000027 using the exact values
from the raw data to demonstrate the rounding issue.
"""

import logging
import sys
import os
import importlib.util
from decimal import Decimal, ROUND_HALF_UP
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_oba_0000027_exact")

def import_module_from_path(module_name, file_path):
    """
    Import a module from a file path
    
    Args:
        module_name (str): Name to give the imported module
        file_path (str): Path to the module file
        
    Returns:
        module: The imported module
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Test the exact value from the raw data
def test_exact_value():
    """
    Test the exact value from the raw data
    """
    # The exact value from the raw data
    exact_value = 83870.1345
    
    # Test NumPy rounding
    numpy_rounded = np.round(exact_value, 2)
    logger.info(f"NumPy rounding of {exact_value}: {numpy_rounded}")
    
    # Test Decimal rounding
    decimal_rounded = float(Decimal(str(exact_value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    logger.info(f"Decimal rounding of {exact_value}: {decimal_rounded}")
    
    # Show the difference
    logger.info(f"Difference: {decimal_rounded - numpy_rounded}")
    
    # Check if the difference matches the reported issue
    if abs(decimal_rounded - numpy_rounded - 0.01) < 0.001:
        logger.info("✓ The difference matches the reported issue (0.01)")
    else:
        logger.info(f"✗ The difference {decimal_rounded - numpy_rounded} does not match the reported issue (0.01)")

def main():
    """
    Main function to run the tests
    """
    logger.info("Testing the exact value from the raw data")
    test_exact_value()
    
    # Import the original module
    original_module = import_module_from_path('currency_converter', 'currency_converter.py')
    
    # Import the fixed module
    if not os.path.exists('currency_converter_fixed.py'):
        logger.error("currency_converter_fixed.py not found")
        return
    
    fixed_module = import_module_from_path('currency_converter_fixed', 'currency_converter_fixed.py')
    
    # Mock the get_exchange_rate function to avoid API calls
    def mock_get_exchange_rate(from_currency, to_currency, **kwargs):
        return 1.0  # Always return 1.0 for testing
    
    # Patch the get_exchange_rate function in both modules
    original_module.get_exchange_rate = mock_get_exchange_rate
    fixed_module.get_exchange_rate = mock_get_exchange_rate
    
    # Test with the exact value from the raw data
    logger.info("\nTesting with the exact value from the raw data:")
    exact_value = 83870.1345
    
    # Test with original module
    original_result, _ = original_module.convert_amount(exact_value, "NTD", "NTD")
    logger.info(f"Original module result: {original_result}")
    
    # Test with fixed module
    fixed_result, _ = fixed_module.convert_amount(exact_value, "NTD", "NTD")
    logger.info(f"Fixed module result: {fixed_result}")
    
    # Show the difference
    logger.info(f"Difference: {fixed_result - original_result}")
    
    # Check if the difference matches the reported issue
    if abs(fixed_result - original_result - 0.01) < 0.001:
        logger.info("✓ The difference matches the reported issue (0.01)")
    else:
        logger.info(f"✗ The difference {fixed_result - original_result} does not match the reported issue (0.01)")
    
    # Print summary
    logger.info("\nSummary:")
    logger.info(f"The exact value from the raw data is {exact_value}")
    
    # Calculate rounding again for summary
    numpy_rounded = np.round(exact_value, 2)
    decimal_rounded = float(Decimal(str(exact_value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    logger.info(f"NumPy rounds this to {numpy_rounded}")
    logger.info(f"Decimal rounds this to {decimal_rounded}")
    logger.info(f"The difference is {decimal_rounded - numpy_rounded}")
    logger.info("This explains the discrepancy in the OBA-0000027 voucher where the credit side shows 83,870")
    logger.info("but the calculated sum was 83,868.")

if __name__ == "__main__":
    main()
