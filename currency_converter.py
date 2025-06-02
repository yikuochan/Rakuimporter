#!/usr/bin/env python3
"""
Currency Converter Module

This module provides functions for currency conversion using exchange rates
from an Excel file. It integrates with the exchange_rate_query module to
retrieve exchange rates and perform currency conversions.
"""

import logging
import numpy as np
from exchange_rate_query import get_exchange_rate

# Configure logging
logger = logging.getLogger("erp_api_integration")

def convert_amount(amount, from_currency, to_currency, company_code=None, excel_path=None, decimal_precision=2):
    """
    Convert an amount from one currency to another using exchange rates.
    
    Args:
        amount (float): The amount to convert
        from_currency (str): Source currency code
        to_currency (str): Target currency code
        company_code (str, optional): Company code to use for exchange rate lookup
        excel_path (str, optional): Path to the exchange rate Excel file
        decimal_precision (int, optional): Number of decimal places for rounding (default: 2)
        
    Returns:
        tuple: (converted_amount, success_flag)
            - converted_amount (float): The converted amount or original amount if conversion failed
            - success_flag (bool): True if conversion was successful, False otherwise
    """
    # If currencies are the same or either is empty, no conversion needed
    if from_currency == to_currency or not from_currency or not to_currency:
        return amount, True
    
    try:
        # Prepare arguments for get_exchange_rate
        kwargs = {}
        if excel_path:
            kwargs["file_path"] = excel_path
        
        # Handle special currency codes with 'R-' prefix
        from_curr = from_currency.replace('R-', '') if from_currency.startswith('R-') else from_currency
        to_curr = to_currency.replace('R-', '') if to_currency.startswith('R-') else to_currency
        
        # Get exchange rate and convert amount, passing company_code
        rate = get_exchange_rate(from_curr, to_curr, company_name=company_code, **kwargs)
        
        # Use NumPy for precise decimal rounding
        # Calculate the conversion
        raw_conversion = amount * rate
        
        # Apply NumPy rounding with specified decimal precision
        converted = np.round(raw_conversion, decimal_precision)
        
        logger.info(f"Converted {amount} {from_currency} to {converted:.2f} {to_currency} (rate: {rate})")
        logger.info(f"Raw conversion: {raw_conversion}, After NumPy rounding: {converted}")
        
        # Return as Python float but ensure the rounding is preserved
        return float(converted), True
        
    except Exception as e:
        error_msg = f"Failed to convert {amount} from {from_currency} to {to_currency}: {str(e)}"
        logger.warning(error_msg)
        # Return original amount and False flag if conversion fails
        return amount, False

def get_region_currency(region_code):
    """
    Get the target currency for a region code based on business rules.
    
    Args:
        region_code (str): The region code (e.g., VCT, VCP, etc.)
        
    Returns:
        str: The target currency code for the region
    """
    # Define the mapping of region codes to their respective currencies
    region_currency_map = {
        "VCT": "NTD",
        "VCA": "USD",
        "VCP": "PHP",
        "VCG": "EUR",
        "VCJ": "JPY"
    }
    
    return region_currency_map.get(region_code, "")

# Example usage
if __name__ == "__main__":
    # Example: Convert 100 USD to EUR
    converted = convert_amount(100, "USD", "EUR")
    print(f"100 USD = {converted:.2f} EUR")
    
    # Example: Get currency for region
    currency = get_region_currency("VCT")
    print(f"Currency for VCT: {currency}")
