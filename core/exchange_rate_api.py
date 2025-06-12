"""
Exchange Rate API Client

This module provides a client for accessing currency exchange rates from the Business Central API.
It handles authentication, API calls, and rate calculations between different currencies.
"""

import logging
import requests
from datetime import datetime
from utils.oauth_token_helper import OAuthTokenHelper
from utils.env_config import get_env_var
from utils.company_currency_mapping import get_home_currency, normalize_currency_code, get_all_currency_variants, COMPANY_HOME_CURRENCY

# Configure logging
logger = logging.getLogger("erp_api_integration")

class ExchangeRateAPI:
    """
    Client for accessing currency exchange rates from Business Central API.
    """
    
    def __init__(self):
        """Initialize the Exchange Rate API client with configuration from environment variables."""
        # Get configuration from environment variables
        self.tenant_id = get_env_var("BC_TENANT_ID", 
                                     default="6b83c27c-aa6d-475a-9933-5c34bb008d73")
        self.client_id = get_env_var("BC_CLIENT_ID", required=True)
        self.client_secret = get_env_var("BC_CLIENT_SECRET", required=True)
        self.scope = get_env_var("BC_SCOPE", 
                                default="https://api.businesscentral.dynamics.com/.default")
        self.verify_ssl = get_env_var("BC_VERIFY_SSL", default="True", as_type=bool)
        
        # Initialize OAuth helper
        self.oauth_helper = OAuthTokenHelper(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=self.scope
        )
        
        # Base URL for API calls
        self.base_url = f"https://api.businesscentral.dynamics.com/v2.0/{self.tenant_id}/Staging/ODataV4"
        
        # Cache for exchange rates to minimize API calls
        self.rate_cache = {}
    
    def _get_company_rates(self, company_name, currency_code=None, date=None, use_month_start=False):
        """
        Get all exchange rates for a company, optionally filtered by currency and date.
        
        Args:
            company_name (str): Company name in Business Central
            currency_code (str, optional): Filter by currency code
            date (str, optional): Filter by date in format YYYY-MM-DD
            use_month_start (bool, optional): If True, use the first day of the month for the date filter
            
        Returns:
            list: List of exchange rate records
        """
        try:
            # Handle date parameter
            if date is None:
                current_date = datetime.now()
            else:
                current_date = datetime.strptime(date, "%Y-%m-%d")
            
            # If use_month_start is True, set to first day of the month
            if use_month_start:
                current_date = current_date.replace(day=1)
            
            # Format the date as string
            date = current_date.strftime("%Y-%m-%d")
            
            # Generate cache key
            cache_key = f"{company_name}_{currency_code}_{date}"
            
            # Check if we have cached results
            if cache_key in self.rate_cache:
                return self.rate_cache[cache_key]
            
            # Get access token
            token_data = self.oauth_helper.acquire_token(verify_ssl=self.verify_ssl)
            if not token_data:
                raise Exception("Failed to acquire access token")
            
            # Prepare headers
            headers = {
                "Authorization": self.oauth_helper.get_token_header(),
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Construct API URL for the company
            api_url = f"{self.base_url}/Company('{company_name}')/CurrencyExchangeRates"
            
            # Prepare filter query
            filter_parts = []
            
            # Add currency filter if provided
            if currency_code:
                # Get all possible variants of the currency code
                currency_variants = get_all_currency_variants(currency_code)
                if currency_variants:
                    currency_filter = " or ".join([f"Currency_Code eq '{code}'" for code in currency_variants])
                    filter_parts.append(f"({currency_filter})")
            
            # Add date filter
            filter_parts.append(f"Starting_Date le {date}")
            
            # Combine filter parts
            filter_query = "$filter=" + " and ".join(filter_parts)
            
            # Order by date descending to get the most recent rates first
            filter_query += "&$orderby=Starting_Date desc"
            
            # Make API request
            logger.info(f"Requesting exchange rates for company {company_name}")
            response = requests.get(
                f"{api_url}?{filter_query}",
                headers=headers,
                verify=self.verify_ssl
            )
            
            # Check for successful response
            response.raise_for_status()
            data = response.json()
            
            # Cache the results
            self.rate_cache[cache_key] = data.get("value", [])
            
            return self.rate_cache[cache_key]
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"API error response: {error_data}")
                except:
                    logger.error(f"API error status code: {e.response.status_code}")
            raise Exception(f"Error retrieving exchange rates: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error retrieving exchange rates: {str(e)}")
            raise
    
    def _find_rate(self, rates, currency_code):
        """
        Find the exchange rate for a specific currency in a list of rates.
        
        Args:
            rates (list): List of exchange rate records
            currency_code (str): Currency code to find
            
        Returns:
            dict: Exchange rate record or None if not found
        """
        # Try exact match first
        for rate in rates:
            if rate.get("Currency_Code") == currency_code:
                return rate
        
        # Try normalized match
        normalized_code = normalize_currency_code(currency_code)
        for rate in rates:
            if normalize_currency_code(rate.get("Currency_Code")) == normalized_code:
                return rate
        
        return None
    
    def _calculate_rate(self, from_rate, to_rate=None):
        """
        Calculate exchange rate between currencies based on their rates to the home currency.
        
        Args:
            from_rate (dict): Exchange rate record for source currency
            to_rate (dict, optional): Exchange rate record for target currency
                                     If None, target is assumed to be home currency
            
        Returns:
            float: Calculated exchange rate
        """
        # Extract values from source rate
        from_amount = float(from_rate.get("Exchange_Rate_Amount", 1))
        from_value = float(from_rate.get("Relational_Exch_Rate_Amount", 0))
        
        # If target is home currency, conversion is straightforward
        if to_rate is None:
            # Rate is (home currency amount) / (foreign currency amount)
            # For example, if 100 USD = 3233 NTD, then 1 USD = 32.33 NTD
            return from_value / from_amount
        
        # Extract values from target rate
        to_amount = float(to_rate.get("Exchange_Rate_Amount", 1))
        to_value = float(to_rate.get("Relational_Exch_Rate_Amount", 0))
        
        # Calculate cross rate
        # If 100 USD = 3233 NTD and 100 EUR = 3500 NTD
        # Then 1 USD = 3233/100 NTD and 1 EUR = 3500/100 NTD
        # So 1 USD = (3233/100)/(3500/100) EUR = 3233/3500 EUR
        return (from_value / from_amount) / (to_value / to_amount)
    
    def get_exchange_rate(self, from_currency, to_currency, company_name=None, date=None, use_month_start=False):
        """
        Get exchange rate between two currencies from the Business Central API.
        
        Args:
            from_currency (str): Source currency code
            to_currency (str): Target currency code
            company_name (str, optional): Company name in Business Central
                                         If None, tries to determine from currency codes
            date (str, optional): Date for the exchange rate in format YYYY-MM-DD
                                 If None, uses current date
            use_month_start (bool, optional): If True, use the first day of the month for the date filter
        
        Returns:
            float: Exchange rate from source to target currency
        
        Raises:
            ValueError: If exchange rate cannot be found
            Exception: For other errors
        """
        try:
            # If currencies are the same, return 1.0
            if normalize_currency_code(from_currency) == normalize_currency_code(to_currency):
                return 1.0
            
            # Set default date to today if not provided
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # If company not specified, try to determine based on currencies
            if company_name is None:
                # Try to find a company where one of the currencies is the home currency
                for comp, home_curr in COMPANY_HOME_CURRENCY.items():
                    if normalize_currency_code(from_currency) == home_curr or normalize_currency_code(to_currency) == home_curr:
                        company_name = comp
                        break
                
                # If still not found, default to VCJ (as it seems to have most currencies)
                if company_name is None:
                    company_name = "VCJ"
            
            # Get the home currency for this company
            home_currency = get_home_currency(company_name)
            if not home_currency:
                raise ValueError(f"Unknown company code: {company_name}")
            
            # Get all rates for this company
            rates = self._get_company_rates(company_name, date=date, use_month_start=use_month_start)
            if not rates:
                raise ValueError(f"No exchange rates found for company {company_name}")
            
            # Normalize currency codes
            norm_from = normalize_currency_code(from_currency)
            norm_to = normalize_currency_code(to_currency)
            
            # Case 1: Direct conversion from foreign currency to home currency
            if norm_to == home_currency:
                from_rate = self._find_rate(rates, from_currency)
                if from_rate:
                    return self._calculate_rate(from_rate)
            
            # Case 2: Direct conversion from home currency to foreign currency
            if norm_from == home_currency:
                to_rate = self._find_rate(rates, to_currency)
                if to_rate:
                    # Invert the rate
                    return 1.0 / self._calculate_rate(to_rate)
            
            # Case 3: Cross-conversion between two foreign currencies
            from_rate = self._find_rate(rates, from_currency)
            to_rate = self._find_rate(rates, to_currency)
            
            if from_rate and to_rate:
                return self._calculate_rate(from_rate, to_rate)
            
            # If we get here, we couldn't find the necessary rates
            raise ValueError(f"Could not find exchange rates for {from_currency} to {to_currency} in company {company_name}")
                
        except Exception as e:
            logger.error(f"Error calculating exchange rate: {str(e)}")
            raise
