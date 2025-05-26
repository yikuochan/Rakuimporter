#!/usr/bin/env python3
"""
Exchange Rate API Demo

This script demonstrates how to use the API-based exchange rate functionality.
It shows examples of different types of currency conversions using the Business Central API.
"""

import logging
import sys
from datetime import datetime
from exchange_rate_query import get_exchange_rate
from exchange_rate_api import ExchangeRateAPI
from company_currency_mapping import COMPANY_HOME_CURRENCY

# Initialize the API client
api_client = ExchangeRateAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"exchange_rate_demo_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("exchange_rate_demo")

def main():
    """Run the exchange rate API demo."""
    print("Exchange Rate API Demo")
    print("=====================")
    
    try:
        # Example 1: Basic currency conversion
        print("\nExample 1: Basic currency conversion")
        from_currency = "USD"
        to_currency = "EUR"
        rate = get_exchange_rate(from_currency, to_currency, debug=True)
        print(f"Exchange rate from {from_currency} to {to_currency}: {rate:.4f}")
        
        # Example 2: Converting with different company
        print("\nExample 2: Converting with different company")
        # List all companies and their home currencies
        print("Available companies and their home currencies:")
        for company, currency in COMPANY_HOME_CURRENCY.items():
            print(f"  {company}: {currency}")
        
        # Convert using VCT (NTD is home currency)
        from_currency = "USD"
        to_currency = "NTD"
        company = "VCT"
        rate = get_exchange_rate(from_currency, to_currency, debug=True)
        print(f"Exchange rate from {from_currency} to {to_currency} using {company}: {rate:.4f}")
        
        # Example 3: Converting between two foreign currencies
        print("\nExample 3: Converting between two foreign currencies")
        from_currency = "USD"
        to_currency = "EUR"
        company = "VCJ"  # JPY is home currency
        rate = get_exchange_rate(from_currency, to_currency, debug=True)
        print(f"Exchange rate from {from_currency} to {to_currency} using {company}: {rate:.4f}")
        
        # Example 4: Handling currency code prefixes
        print("\nExample 4: Handling currency code prefixes")
        from_currency = "R-USD"
        to_currency = "JPY"
        company = "VCJ"  # JPY is home currency
        # Pass the company name explicitly to ensure we use the right company for JPY
        rate = api_client.get_exchange_rate(from_currency, to_currency, company)
        print(f"Exchange rate from {from_currency} to {to_currency} using {company}: {rate:.4f}")
        
        # Example 5: Using first day of the month for exchange rates
        print("\nExample 5: Using first day of the month for exchange rates")
        from_currency = "USD"
        to_currency = "EUR"
        # Get exchange rate using the first day of the current month
        rate = get_exchange_rate(from_currency, to_currency, debug=True, use_month_start=True)
        print(f"Exchange rate from {from_currency} to {to_currency} (using first day of month): {rate:.4f}")
        
        # Using the API client directly with a specific date and company
        current_date = datetime.now().strftime("%Y-%m-%d")
        rate = api_client.get_exchange_rate(
            from_currency=from_currency,
            to_currency=to_currency,
            company_name="VCT",
            date=current_date,
            use_month_start=True
        )
        print(f"Exchange rate from {from_currency} to {to_currency} using VCT (first day of month): {rate:.4f}")
        
    except Exception as e:
        logger.error(f"Error in demo: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        print("\nNote: Make sure you have set up the .env file with your API credentials.")
        print("You can copy .env.example to .env and update the values.")

if __name__ == "__main__":
    main()
