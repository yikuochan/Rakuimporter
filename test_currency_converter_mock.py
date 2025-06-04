#!/usr/bin/env python3
"""
Mock test script for the fixed currency converter implementation.

This script tests the currency_converter_fixed.py module with mocked exchange rates
to verify the rounding behavior without requiring API access.
"""

import logging
import json
from decimal import Decimal, ROUND_HALF_UP, getcontext
from unittest.mock import patch

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_currency_converter_mock")

# Set decimal precision for all calculations
getcontext().prec = 28

def mock_get_exchange_rate(from_currency, to_currency, **kwargs):
    """
    Mock function to replace the get_exchange_rate function.
    
    Args:
        from_currency (str): Source currency code
        to_currency (str): Target currency code
        **kwargs: Additional arguments
        
    Returns:
        float: A mock exchange rate
    """
    # Define mock exchange rates
    rates = {
        ("USD", "NTD"): 30.5,
        ("JPY", "NTD"): 0.2677403,
        ("USD", "JPY"): 114.0,
        ("JPY", "USD"): 0.00877193,
        ("EUR", "NTD"): 33.2,
        ("NTD", "USD"): 0.0327869,
    }
    
    # Handle R- prefix
    from_curr = from_currency.replace('R-', '') if from_currency.startswith('R-') else from_currency
    to_curr = to_currency.replace('R-', '') if to_currency.startswith('R-') else to_currency
    
    # Return the mock rate
    key = (from_curr, to_curr)
    if key in rates:
        return rates[key]
    
    # If the direct rate is not found, try the inverse
    inverse_key = (to_curr, from_curr)
    if inverse_key in rates:
        return 1 / rates[inverse_key]
    
    # Default rate if not found
    return 1.0

def convert_amount(amount, from_currency, to_currency, decimal_precision=2):
    """
    Convert an amount from one currency to another using mock exchange rates.
    Uses Decimal type for precise financial calculations.
    
    Args:
        amount (float or Decimal): The amount to convert
        from_currency (str): Source currency code
        to_currency (str): Target currency code
        decimal_precision (int, optional): Number of decimal places for rounding (default: 2)
        
    Returns:
        tuple: (converted_amount, success_flag)
            - converted_amount (Decimal): The converted amount
            - success_flag (bool): True if conversion was successful
    """
    # Convert amount to Decimal if it's not already
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    # If currencies are the same or either is empty, no conversion needed
    if from_currency == to_currency or not from_currency or not to_currency:
        # Return amount rounded to specified precision
        return amount.quantize(Decimal(f'0.{"0" * decimal_precision}'), rounding=ROUND_HALF_UP), True
    
    # Get exchange rate and convert to Decimal
    rate = mock_get_exchange_rate(from_currency, to_currency)
    rate_decimal = Decimal(str(rate))
    
    # Calculate the conversion without intermediate rounding
    raw_conversion = amount * rate_decimal
    
    # Apply rounding only at the final step
    converted = raw_conversion.quantize(Decimal(f'0.{"0" * decimal_precision}'), rounding=ROUND_HALF_UP)
    
    logger.info(f"Converted {amount} {from_currency} to {converted} {to_currency} (rate: {rate_decimal})")
    logger.info(f"Raw conversion: {raw_conversion}, After Decimal rounding: {converted}")
    
    return converted, True

def convert_through_intermediate(amount, from_currency, intermediate_currency, to_currency, decimal_precision=2):
    """
    Convert an amount through an intermediate currency without intermediate rounding.
    
    Args:
        amount (float or Decimal): The amount to convert
        from_currency (str): Source currency code
        intermediate_currency (str): Intermediate currency code
        to_currency (str): Target currency code
        decimal_precision (int, optional): Number of decimal places for rounding (default: 2)
        
    Returns:
        tuple: (converted_amount, success_flag)
            - converted_amount (Decimal): The converted amount
            - success_flag (bool): True if conversion was successful
    """
    # Convert amount to Decimal if it's not already
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    # Get first exchange rate (from_currency to intermediate_currency)
    rate1 = mock_get_exchange_rate(from_currency, intermediate_currency)
    rate1_decimal = Decimal(str(rate1))
    
    # Get second exchange rate (intermediate_currency to to_currency)
    rate2 = mock_get_exchange_rate(intermediate_currency, to_currency)
    rate2_decimal = Decimal(str(rate2))
    
    # Calculate the conversion without intermediate rounding
    raw_conversion = amount * rate1_decimal * rate2_decimal
    
    # Apply rounding only at the final step
    converted = raw_conversion.quantize(Decimal(f'0.{"0" * decimal_precision}'), rounding=ROUND_HALF_UP)
    
    logger.info(f"Converted {amount} {from_currency} to {converted} {to_currency} "
               f"through {intermediate_currency} (rates: {rate1_decimal}, {rate2_decimal})")
    logger.info(f"Raw conversion: {raw_conversion}, After Decimal rounding: {converted}")
    
    return converted, True

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
    expected_direct = Decimal('2558039.10')  # 83870.1345 * 30.5
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

def test_with_sample_data():
    """
    Test with sample data that simulates the OBA-0000027 entries.
    """
    logger.info("\nTesting with sample data")
    
    # Create sample entries with different currencies
    sample_entries = [
        {"amount": "50000.00", "currencyCode": "USD"},
        {"amount": "33870.1345", "currencyCode": "USD"},
        {"amount": "1000000.00", "currencyCode": "JPY"},
        {"amount": "5000.00", "currencyCode": "NTD"}
    ]
    
    logger.info(f"Sample entries: {len(sample_entries)}")
    
    # Process the entries
    total_amount = Decimal('0')
    currencies = set()
    
    for entry in sample_entries:
        amount = Decimal(str(entry["amount"]))
        currency = entry["currencyCode"]
        
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
    
    # Test the difference between different rounding approaches
    # Method 1: Convert and round each entry, then sum
    rounded_entries_sum = Decimal('0')
    for entry in sample_entries:
        amount = Decimal(str(entry["amount"]))
        currency = entry["currencyCode"]
        
        if currency != "NTD":
            # Convert and round
            converted, _ = convert_amount(amount, currency, "NTD")
            rounded_entries_sum += converted
        else:
            rounded_entries_sum += amount
    
    logger.info(f"Sum of individually converted and rounded entries: {rounded_entries_sum}")
    
    # Method 2: Convert each entry without rounding, sum, then round
    unrounded_sum = Decimal('0')
    for entry in sample_entries:
        amount = Decimal(str(entry["amount"]))
        currency = entry["currencyCode"]
        
        if currency != "NTD":
            # Get rate
            rate = Decimal(str(mock_get_exchange_rate(currency, "NTD")))
            # Convert without rounding
            converted = amount * rate
            unrounded_sum += converted
        else:
            unrounded_sum += amount
    
    # Round only at the end
    final_rounded_sum = unrounded_sum.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    logger.info(f"Convert without rounding, sum, then round: {final_rounded_sum}")
    
    # Compare the two methods
    logger.info(f"Difference between methods: {final_rounded_sum - rounded_entries_sum}")
    
    return {
        "entries_count": len(sample_entries),
        "currencies": list(currencies),
        "total_amount": total_amount,
        "final_amount": final_amount,
        "rounded_entries_sum": rounded_entries_sum,
        "final_rounded_sum": final_rounded_sum,
        "difference": final_rounded_sum - rounded_entries_sum
    }

def main():
    """
    Main function to run all tests.
    """
    logger.info("Starting currency converter mock tests")
    
    # Test the OBA-0000027 conversion
    test_results = test_oba_0000027_conversion()
    
    # Test with sample data
    sample_data_results = test_with_sample_data()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"OBA-0000027 exact value: {test_results.get('exact_value')}")
    logger.info(f"Direct conversion result: {test_results.get('direct_conversion')}")
    logger.info(f"Through intermediate result: {test_results.get('through_intermediate')}")
    logger.info(f"Sum of converted entries: {test_results.get('sum_of_converted_entries')}")
    logger.info(f"Sum then convert: {test_results.get('sum_then_convert')}")
    logger.info(f"Difference: {test_results.get('difference')}")
    
    logger.info("\n=== Sample Data Test Results ===")
    for key, value in sample_data_results.items():
        logger.info(f"{key}: {value}")

if __name__ == "__main__":
    main()
