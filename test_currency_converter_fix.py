#!/usr/bin/env python3
"""
Test script to verify the fixed currency converter implementation.

This script tests the currency_converter_fixed.py module to ensure it correctly
handles rounding in currency conversions, particularly for the OBA-0000027 case.
"""

import logging
import json
from decimal import Decimal, ROUND_HALF_UP
from currency_converter_fixed import convert_amount, convert_through_intermediate

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_currency_converter_fix")

def load_test_data(file_path):
    """
    Load test data from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        dict: The loaded JSON data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load test data from {file_path}: {str(e)}")
        return {}

def test_oba_0000027_conversion():
    """
    Test the currency conversion for OBA-0000027 using the fixed converter.
    """
    logger.info("Testing OBA-0000027 currency conversion with fixed converter")
    
    # The exact value from the raw data
    exact_value = Decimal('83870.1345')
    logger.info(f"Exact value from raw data: {exact_value}")
    
    # Test direct conversion with the fixed converter
    converted, success = convert_amount(exact_value, "USD", "NTD")
    logger.info(f"Direct conversion result: {converted} (Success: {success})")
    
    # Test conversion through an intermediate currency
    converted_through_intermediate, success = convert_through_intermediate(
        exact_value, "USD", "JPY", "NTD"
    )
    logger.info(f"Conversion through intermediate currency: {converted_through_intermediate} (Success: {success})")
    
    # Compare with the expected values
    expected_direct = Decimal('83870.13')
    logger.info(f"Expected direct conversion result: {expected_direct}")
    logger.info(f"Difference: {converted - expected_direct}")
    
    # Test with multiple entries that sum to the same total
    logger.info("\nTesting with multiple entries")
    
    # Create 10 entries that sum to the exact value
    entry_value = exact_value / 10
    logger.info(f"Individual entry value: {entry_value}")
    
    # Method 1: Convert each entry separately, then sum
    converted_entries = []
    for _ in range(10):
        entry_converted, _ = convert_amount(entry_value, "USD", "NTD")
        converted_entries.append(entry_converted)
    
    sum_of_converted = sum(converted_entries)
    logger.info(f"Sum of individually converted entries: {sum_of_converted}")
    
    # Method 2: Sum first, then convert
    sum_then_convert, _ = convert_amount(exact_value, "USD", "NTD")
    logger.info(f"Sum first, then convert: {sum_then_convert}")
    
    # Compare the two methods
    logger.info(f"Difference between methods: {sum_then_convert - sum_of_converted}")
    
    return {
        "exact_value": exact_value,
        "direct_conversion": converted,
        "through_intermediate": converted_through_intermediate,
        "sum_of_converted_entries": sum_of_converted,
        "sum_then_convert": sum_then_convert,
        "difference": sum_then_convert - sum_of_converted
    }

def test_with_real_data():
    """
    Test the currency converter with real data from the JSON file.
    """
    logger.info("\nTesting with real data from JSON file")
    
    # Load the JSON data
    data_file = "0527-Raku export- VCT PR 1-2.utf8.json"
    data = load_test_data(data_file)
    
    if not data:
        logger.error(f"No data loaded from {data_file}")
        return {}
    
    # Find entries related to OBA-0000027
    oba_entries = []
    for entry in data.get("value", []):
        if entry.get("documentNo") == "OBA-0000027":
            oba_entries.append(entry)
    
    logger.info(f"Found {len(oba_entries)} entries for OBA-0000027")
    
    # Process the entries
    if oba_entries:
        # Extract relevant information
        total_amount = Decimal('0')
        currencies = set()
        
        for entry in oba_entries:
            amount = Decimal(str(entry.get("amount", 0)))
            currency = entry.get("currencyCode", "")
            
            logger.info(f"Entry: Amount={amount}, Currency={currency}")
            currencies.add(currency)
            
            # Convert to NTD if needed
            if currency != "NTD":
                converted, success = convert_amount(amount, currency, "NTD")
                if success:
                    logger.info(f"Converted {amount} {currency} to {converted} NTD")
                    total_amount += converted
                else:
                    logger.warning(f"Failed to convert {amount} {currency} to NTD")
            else:
                total_amount += amount
        
        logger.info(f"Total amount in NTD: {total_amount}")
        logger.info(f"Currencies involved: {currencies}")
        
        # Round to 2 decimal places for final display
        final_amount = total_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        logger.info(f"Final rounded amount: {final_amount}")
        
        return {
            "entries_count": len(oba_entries),
            "currencies": list(currencies),
            "total_amount": total_amount,
            "final_amount": final_amount
        }
    
    return {"error": "No entries found for OBA-0000027"}

def main():
    """
    Main function to run all tests.
    """
    logger.info("Starting currency converter fix tests")
    
    # Test the OBA-0000027 conversion
    test_results = test_oba_0000027_conversion()
    
    # Test with real data if available
    real_data_results = test_with_real_data()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"OBA-0000027 exact value: {test_results.get('exact_value')}")
    logger.info(f"Direct conversion result: {test_results.get('direct_conversion')}")
    logger.info(f"Through intermediate result: {test_results.get('through_intermediate')}")
    logger.info(f"Sum of converted entries: {test_results.get('sum_of_converted_entries')}")
    logger.info(f"Sum then convert: {test_results.get('sum_then_convert')}")
    logger.info(f"Difference: {test_results.get('difference')}")
    
    if real_data_results:
        logger.info("\n=== Real Data Test Results ===")
        for key, value in real_data_results.items():
            logger.info(f"{key}: {value}")

if __name__ == "__main__":
    main()
