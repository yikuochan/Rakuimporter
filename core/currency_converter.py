#!/usr/bin/env python3
"""
Currency Converter Module (Fixed Version)

This module provides functions for currency conversion using exchange rates
from an Excel file. It integrates with the exchange_rate_query module to
retrieve exchange rates and perform currency conversions.

This version uses the Decimal type throughout to ensure precise currency calculations
and applies rounding only at the final step to avoid cumulative rounding errors.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP, getcontext
from core.exchange_rate_query import get_exchange_rate

# Configure logging
logger = logging.getLogger("erp_api_integration")

# Set decimal precision for all calculations
getcontext().prec = 28

def convert_amount(amount, from_currency, to_currency, company_code=None, excel_path=None, decimal_precision=0):
    """
    Convert an amount from one currency to another using exchange rates.
    Uses Decimal type for precise financial calculations.
    
    Args:
        amount (float or Decimal): The amount to convert
        from_currency (str): Source currency code
        to_currency (str): Target currency code
        company_code (str, optional): Company code to use for exchange rate lookup
        excel_path (str, optional): Path to the exchange rate Excel file
        decimal_precision (int, optional): Number of decimal places for rounding (default: 0)
        
    Returns:
        tuple: (converted_amount, success_flag)
            - converted_amount (Decimal): The converted amount or original amount if conversion failed
            - success_flag (bool): True if conversion was successful, False otherwise
    """
    # Convert amount to Decimal if it's not already
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    # If currencies are the same or either is empty, no conversion needed
    if from_currency == to_currency or not from_currency or not to_currency:
        # Return amount rounded to specified precision
        return amount.quantize(Decimal(f'0.{"0" * decimal_precision}'), rounding=ROUND_HALF_UP), True
    
    try:
        # Prepare arguments for get_exchange_rate
        kwargs = {}
        if excel_path:
            kwargs["file_path"] = excel_path
        
        # Handle special currency codes with 'R-' prefix
        from_curr = from_currency.replace('R-', '') if from_currency.startswith('R-') else from_currency
        to_curr = to_currency.replace('R-', '') if to_currency.startswith('R-') else to_currency
        
        # Get exchange rate and convert to Decimal
        rate = get_exchange_rate(from_curr, to_curr, company_name=company_code, **kwargs)
        rate_decimal = Decimal(str(rate))
        
        # Calculate the conversion without intermediate rounding
        raw_conversion = amount * rate_decimal
        
        # Apply rounding only at the final step
        converted = raw_conversion.quantize(Decimal(f'0.{"0" * decimal_precision}'), rounding=ROUND_HALF_UP)
        
        logger.info(f"Converted {amount} {from_currency} to {converted} {to_currency} (rate: {rate_decimal})")
        logger.info(f"Raw conversion: {raw_conversion}, After Decimal rounding: {converted}")
        
        return converted, True
        
    except Exception as e:
        error_msg = f"Failed to convert {amount} from {from_currency} to {to_currency}: {str(e)}"
        logger.warning(error_msg)
        # Return original amount and False flag if conversion fails
        return amount, False

def convert_through_intermediate(amount, from_currency, intermediate_currency, to_currency, 
                                company_code=None, excel_path=None, decimal_precision=0):
    """
    Convert an amount through an intermediate currency without intermediate rounding.
    
    Args:
        amount (float or Decimal): The amount to convert
        from_currency (str): Source currency code
        intermediate_currency (str): Intermediate currency code
        to_currency (str): Target currency code
        company_code (str, optional): Company code to use for exchange rate lookup
        excel_path (str, optional): Path to the exchange rate Excel file
        decimal_precision (int, optional): Number of decimal places for rounding (default: 0)
        
    Returns:
        tuple: (converted_amount, success_flag)
            - converted_amount (Decimal): The converted amount or original amount if conversion failed
            - success_flag (bool): True if conversion was successful, False otherwise
    """
    # Convert amount to Decimal if it's not already
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    try:
        # Prepare arguments for get_exchange_rate
        kwargs = {}
        if excel_path:
            kwargs["file_path"] = excel_path
        
        # Get first exchange rate (from_currency to intermediate_currency)
        rate1 = get_exchange_rate(from_currency, intermediate_currency, company_name=company_code, **kwargs)
        rate1_decimal = Decimal(str(rate1))
        
        # Get second exchange rate (intermediate_currency to to_currency)
        rate2 = get_exchange_rate(intermediate_currency, to_currency, company_name=company_code, **kwargs)
        rate2_decimal = Decimal(str(rate2))
        
        # Calculate the conversion without intermediate rounding
        raw_conversion = amount * rate1_decimal * rate2_decimal
        
        # Apply rounding only at the final step
        converted = raw_conversion.quantize(Decimal(f'0.{"0" * decimal_precision}'), rounding=ROUND_HALF_UP)
        
        logger.info(f"Converted {amount} {from_currency} to {converted} {to_currency} "
                   f"through {intermediate_currency} (rates: {rate1_decimal}, {rate2_decimal})")
        logger.info(f"Raw conversion: {raw_conversion}, After Decimal rounding: {converted}")
        
        return converted, True
        
    except Exception as e:
        error_msg = f"Failed to convert {amount} from {from_currency} to {to_currency} through {intermediate_currency}: {str(e)}"
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
    # Configure logging for standalone execution
    import logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Example: Convert 100 USD to EUR
    converted, success = convert_amount(100, "USD", "EUR")
    print(f"100 USD = {converted} EUR (Success: {success})")
    
    # Example: Convert through intermediate currency
    converted, success = convert_through_intermediate(100, "JPY", "USD", "NTD")
    print(f"100 JPY = {converted} NTD via USD (Success: {success})")
    
    # Example: Get currency for region
    currency = get_region_currency("VCT")
    print(f"Currency for VCT: {currency}")
