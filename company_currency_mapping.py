"""
Module for mapping company codes to their home currencies and handling currency code normalization.
"""

# Map of company codes to their home currencies
COMPANY_HOME_CURRENCY = {
    "VCT": "NTD",
    "VCA": "USD",
    "VCP": "PHP",
    "VCG": "EUR",
    "VCJ": "JPY"
}

def get_home_currency(company_code):
    """
    Get the home currency for a company code.
    
    Args:
        company_code (str): Company code (e.g., VCT, VCA)
        
    Returns:
        str: Home currency code or None if not found
    """
    return COMPANY_HOME_CURRENCY.get(company_code)

def normalize_currency_code(currency_code):
    """
    Normalize currency code by removing prefixes like R- or Z-.
    
    Args:
        currency_code (str): Currency code, possibly with prefix
        
    Returns:
        str: Normalized currency code without prefix
    """
    if not currency_code:
        return ""
        
    # Remove R- or Z- prefix if present
    if currency_code.startswith("R-") or currency_code.startswith("Z-"):
        return currency_code[2:]
        
    return currency_code

def get_all_currency_variants(currency_code):
    """
    Get all possible variants of a currency code (with and without prefixes).
    
    Args:
        currency_code (str): Base currency code
        
    Returns:
        list: List of possible currency code variants
    """
    normalized = normalize_currency_code(currency_code)
    
    if not normalized:
        return []
        
    # Return all possible variants
    return [
        normalized,
        f"R-{normalized}",
        f"Z-{normalized}"
    ]
