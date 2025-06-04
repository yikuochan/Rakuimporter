#!/usr/bin/env python3
"""
Test script to demonstrate the rounding discrepancy in OBA-0000027 voucher.

This script shows how different rounding methods and intermediate calculations
can lead to the observed discrepancy between 83,868 and 83,870.
"""

import logging
import numpy as np
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN, getcontext

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_rounding_discrepancy")

# Set decimal precision
getcontext().prec = 28

def main():
    """
    Main function to demonstrate the rounding discrepancy.
    """
    logger.info("Demonstrating the rounding discrepancy in OBA-0000027 voucher")
    
    # The exact value from the raw data
    exact_value = 83870.1345
    logger.info(f"Exact value from raw data: {exact_value}")
    
    # Test different rounding methods
    test_rounding_methods(exact_value)
    
    # Demonstrate how intermediate calculations can cause discrepancies
    demonstrate_intermediate_calculations()
    
    # Show how the fix would work
    demonstrate_fix()

def test_rounding_methods(value):
    """
    Test different rounding methods on the given value.
    
    Args:
        value (float): The value to round
    """
    logger.info("\n=== Testing Different Rounding Methods ===")
    
    # Python's built-in round function
    python_rounded = round(value, 2)
    logger.info(f"Python's round(): {python_rounded}")
    
    # NumPy rounding
    numpy_rounded = np.round(value, 2)
    logger.info(f"NumPy's round(): {numpy_rounded}")
    
    # Decimal rounding with ROUND_HALF_UP
    decimal_rounded = float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    logger.info(f"Decimal with ROUND_HALF_UP: {decimal_rounded}")
    
    # Decimal rounding with ROUND_HALF_EVEN (Banker's rounding)
    decimal_rounded_banker = float(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN))
    logger.info(f"Decimal with ROUND_HALF_EVEN (Banker's): {decimal_rounded_banker}")
    
    # Manual rounding by truncation and adjustment
    truncated = int(value * 100) / 100
    logger.info(f"Simple truncation: {truncated}")
    
    # Manual rounding by adding 0.5 and truncating
    manual_rounded = int(value * 100 + 0.5) / 100
    logger.info(f"Manual rounding (add 0.5 and truncate): {manual_rounded}")

def demonstrate_intermediate_calculations():
    """
    Demonstrate how intermediate calculations can cause discrepancies.
    """
    logger.info("\n=== Demonstrating Intermediate Calculation Issues ===")
    
    # Simulate a scenario where we have multiple currency conversions
    # For example, converting from JPY -> USD -> NTD
    
    # Original amount in JPY
    original_amount_jpy = 500000
    logger.info(f"Original amount (JPY): {original_amount_jpy}")
    
    # Method 1: Convert directly with proper rounding at the end
    # JPY -> NTD rate: 0.2677403
    direct_rate = 0.2677403
    direct_result = original_amount_jpy * direct_rate
    logger.info(f"Direct conversion result (unrounded): {direct_result}")
    direct_result_rounded = round(direct_result, 2)
    logger.info(f"Direct conversion result (rounded): {direct_result_rounded}")
    
    # Method 2: Convert with intermediate step and rounding at each step
    # JPY -> USD rate: 0.0091
    # USD -> NTD rate: 29.42
    jpy_to_usd_rate = 0.0091
    usd_to_ntd_rate = 29.42
    
    # Intermediate conversion to USD with rounding
    intermediate_usd = round(original_amount_jpy * jpy_to_usd_rate, 2)
    logger.info(f"Intermediate USD amount (rounded): {intermediate_usd}")
    
    # Final conversion to NTD with rounding
    final_ntd = round(intermediate_usd * usd_to_ntd_rate, 2)
    logger.info(f"Final NTD amount with intermediate rounding: {final_ntd}")
    
    # Method 3: Convert with intermediate step but no intermediate rounding
    intermediate_usd_unrounded = original_amount_jpy * jpy_to_usd_rate
    final_ntd_no_intermediate_rounding = round(intermediate_usd_unrounded * usd_to_ntd_rate, 2)
    logger.info(f"Final NTD amount without intermediate rounding: {final_ntd_no_intermediate_rounding}")
    
    # Show the difference
    logger.info(f"Difference between methods 2 and 3: {final_ntd - final_ntd_no_intermediate_rounding}")
    logger.info(f"Difference between direct and method 2: {direct_result_rounded - final_ntd}")
    logger.info(f"Difference between direct and method 3: {direct_result_rounded - final_ntd_no_intermediate_rounding}")

def demonstrate_fix():
    """
    Demonstrate how using Decimal throughout the process fixes the issue.
    """
    logger.info("\n=== Demonstrating the Fix with Decimal ===")
    
    # Original amount in JPY
    original_amount_jpy = Decimal('500000')
    logger.info(f"Original amount (JPY): {original_amount_jpy}")
    
    # Method 1: Convert directly with Decimal
    direct_rate = Decimal('0.2677403')
    direct_result = original_amount_jpy * direct_rate
    logger.info(f"Direct conversion result (unrounded): {direct_result}")
    direct_result_rounded = direct_result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    logger.info(f"Direct conversion result (rounded): {direct_result_rounded}")
    
    # Method 2: Convert with intermediate step and Decimal throughout
    jpy_to_usd_rate = Decimal('0.0091')
    usd_to_ntd_rate = Decimal('29.42')
    
    # Intermediate conversion to USD with Decimal
    intermediate_usd = (original_amount_jpy * jpy_to_usd_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    logger.info(f"Intermediate USD amount (rounded): {intermediate_usd}")
    
    # Final conversion to NTD with Decimal
    final_ntd = (intermediate_usd * usd_to_ntd_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    logger.info(f"Final NTD amount with intermediate rounding: {final_ntd}")
    
    # Method 3: Convert with intermediate step but no intermediate rounding
    intermediate_usd_unrounded = original_amount_jpy * jpy_to_usd_rate
    final_ntd_no_intermediate_rounding = (intermediate_usd_unrounded * usd_to_ntd_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    logger.info(f"Final NTD amount without intermediate rounding: {final_ntd_no_intermediate_rounding}")
    
    # Show the difference
    logger.info(f"Difference between methods 2 and 3: {final_ntd - final_ntd_no_intermediate_rounding}")
    logger.info(f"Difference between direct and method 2: {direct_result_rounded - final_ntd}")
    logger.info(f"Difference between direct and method 3: {direct_result_rounded - final_ntd_no_intermediate_rounding}")
    
    # Demonstrate with the actual value from OBA-0000027
    logger.info("\n=== Demonstrating with the actual OBA-0000027 value ===")
    
    # The exact value from the raw data
    exact_value = Decimal('83870.1345')
    logger.info(f"Exact value from raw data: {exact_value}")
    
    # Round with Decimal
    decimal_rounded = exact_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    logger.info(f"Rounded with Decimal ROUND_HALF_UP: {decimal_rounded}")
    
    # Simulate the issue by doing intermediate calculations
    # Let's say this value was calculated from multiple currency conversions
    # For example, if we had 10 entries of 8387.01345 each
    entry_value = Decimal('8387.01345')
    num_entries = 10
    
    # Method 1: Sum first, then round
    sum_then_round = (entry_value * num_entries).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    logger.info(f"Sum first, then round: {sum_then_round}")
    
    # Method 2: Round each entry, then sum
    round_then_sum = sum([entry_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) for _ in range(num_entries)])
    logger.info(f"Round each entry, then sum: {round_then_sum}")
    
    # Show the difference
    logger.info(f"Difference: {sum_then_round - round_then_sum}")
    
    # This demonstrates how the order of operations (when rounding is applied)
    # can lead to different results, potentially explaining the 83,868 vs 83,870 discrepancy

if __name__ == "__main__":
    main()
