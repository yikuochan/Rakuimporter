import logging
from env_config import get_env_var
from company_currency_mapping import get_home_currency, COMPANY_HOME_CURRENCY

# Configure logging
logger = logging.getLogger("erp_api_integration")

# Import the API client
try:
    from exchange_rate_api import ExchangeRateAPI
    api_client = ExchangeRateAPI()
    api_available = True
except ImportError:
    logger.error("ExchangeRateAPI not available. Cannot retrieve exchange rates.")
    api_available = False

# Check if we should use the API
USE_API = get_env_var("USE_EXCHANGE_RATE_API", default="True", as_type=bool)
DEFAULT_COMPANY = get_env_var("BC_COMPANY", default="VCJ")

def get_exchange_rate(from_currency, to_currency, company_name=None, debug=False, use_month_start=False, **kwargs):
    """
    Get the exchange rate between two currencies using the Business Central API.
    
    Parameters:
    from_currency (str): The source currency code
    to_currency (str): The target currency code
    company_name (str, optional): Company name in Business Central
    debug (bool): Whether to print debug information
    use_month_start (bool): If True, use the first day of the month for the date filter
    **kwargs: Additional parameters (ignored, kept for backward compatibility)
    
    Returns:
    float: The exchange rate from source to target currency
    
    Raises:
    Exception: If the API is not available or fails to retrieve the exchange rate
    """
    # If currencies are the same, return 1.0
    if from_currency == to_currency:
        return 1.0
    
    # Add logging for input currencies
    logger.info(f"Exchange rate request: from_currency={from_currency}, to_currency={to_currency}")
    
    # Check if API is enabled and available
    if not USE_API:
        raise Exception("Exchange Rate API is disabled. Enable it by setting USE_EXCHANGE_RATE_API=True in .env file.")
    
    if not api_available:
        raise Exception("Exchange Rate API is not available. Check if exchange_rate_api.py is properly installed.")
    
    try:
        if debug:
            logger.debug(f"Attempting to get exchange rate from API: {from_currency} to {to_currency}")
        
        # Get company name from parameter or use default
        if not company_name:
            company_name = DEFAULT_COMPANY
            
        # If company_name is a region code (e.g., VCT), use it directly
        if company_name in COMPANY_HOME_CURRENCY:
            logger.info(f"Using company {company_name} for exchange rate lookup")
        else:
            logger.info(f"Company {company_name} not recognized, using default {DEFAULT_COMPANY}")
            company_name = DEFAULT_COMPANY
        
        # Get home currency for this company
        home_currency = get_home_currency(company_name)
        logger.info(f"Home currency for company {company_name}: {home_currency}")
        
        # Ensure currencies have R- prefix when needed (only for non-home currencies)
        from_currency_modified = from_currency
        to_currency_modified = to_currency
        
        # Add R- prefix to from_currency if it's not the home currency and doesn't already have the prefix
        if from_currency != home_currency and not from_currency.startswith("R-"):
            from_currency_modified = f"R-{from_currency}"
            logger.info(f"Added R- prefix to from_currency: {from_currency} -> {from_currency_modified}")
        
        # Add R- prefix to to_currency if it's not the home currency and doesn't already have the prefix
        if to_currency != home_currency and not to_currency.startswith("R-"):
            to_currency_modified = f"R-{to_currency}"
            logger.info(f"Added R- prefix to to_currency: {to_currency} -> {to_currency_modified}")
        
        # Call the API client with potentially modified currency codes
        rate = api_client.get_exchange_rate(from_currency_modified, to_currency_modified, company_name, use_month_start=use_month_start)
        
        if debug:
            logger.debug(f"API returned exchange rate: {rate}")
            
        return rate
        
    except Exception as api_error:
        # Log the API error and re-raise
        logger.error(f"API error: {str(api_error)}")
        raise Exception(f"Error retrieving exchange rate from API: {str(api_error)}")


# Example usage
if __name__ == "__main__":
    try:
        # Example: Get exchange rate from USD to EUR
        rate = get_exchange_rate("USD", "EUR")
        print(f"Exchange rate from USD to EUR: {rate}")
        
        # Example: Get exchange rate using first day of the month
        rate = get_exchange_rate("USD", "EUR", use_month_start=True)
        print(f"Exchange rate from USD to EUR (using first day of month): {rate}")
        
        # You can also enable debug output
        # rate = get_exchange_rate("USD", "EUR", debug=True, use_month_start=True)
        
    except Exception as e:
        print(f"Error: {e}")
