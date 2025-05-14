#!/usr/bin/env python3
"""
Currency Converter Module

This module provides functions for currency conversion using exchange rates
from an Excel file. It integrates with the exchange_rate_query module to
retrieve exchange rates and perform currency conversions.
"""

import logging
from exchange_rate_query import get_exchange_rate

# Configure logging
logger = logging.getLogger("erp_api_integration")

def convert_amount(amount, from_currency, to_currency, excel_path=None):
    """
    Convert an amount from one currency to another using exchange rates.
    
    Args:
        amount (float): The amount to convert
        from_currency (str): Source currency code
        to_currency (str): Target currency code
        excel_path (str, optional): Path to the exchange rate Excel file
        
    Returns:
        float: The converted amount
    """
    # If currencies are the same or either is empty, no conversion needed
    if from_currency == to_currency or not from_currency or not to_currency:
        return amount
    
    try:
        # Prepare arguments for get_exchange_rate
        kwargs = {}
        if excel_path:
            kwargs["file_path"] = excel_path
        
        # Handle special currency codes with 'R-' prefix
        from_curr = from_currency.replace('R-', '') if from_currency.startswith('R-') else from_currency
        to_curr = to_currency.replace('R-', '') if to_currency.startswith('R-') else to_currency
        
        # Get exchange rate and convert amount
        rate = get_exchange_rate(from_curr, to_curr, **kwargs)
        converted = amount * rate
        
        logger.info(f"Converted {amount} {from_currency} to {converted:.2f} {to_currency} (rate: {rate})")
        return converted
        
    except Exception as e:
        logger.warning(f"Failed to convert {amount} from {from_currency} to {to_currency}: {str(e)}")
        # Return original amount if conversion fails
        return amount

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