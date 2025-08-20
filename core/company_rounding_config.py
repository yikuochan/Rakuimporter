#!/usr/bin/env python3
"""
Company-Specific Rounding Configuration Module

This module defines rounding rules for different companies based on their
home currencies and business requirements.

Requirements:
- VCA, VCP: Round down to 2 decimal places (e.g., 10.118 → 10.11)
- VCT: Round down to 0 decimal places (e.g., 99.9 → 99)
- Other companies: Use standard rounding rules
"""

from decimal import ROUND_DOWN, ROUND_HALF_UP
from enum import Enum
import logging

# Configure logging
logger = logging.getLogger("erp_api_integration")

class RoundingMethod(Enum):
    """Enumeration of supported rounding methods."""
    ROUND_DOWN = ROUND_DOWN
    ROUND_HALF_UP = ROUND_HALF_UP

# Company-specific rounding rules configuration
COMPANY_ROUNDING_RULES = {
    "VCA": {
        "decimal_places": 2,
        "rounding_method": RoundingMethod.ROUND_DOWN,
        "home_currency": "USD",
        "description": "VCA: Round down to 2 decimal places (e.g., 10.118 → 10.11)"
    },
    "VCP": {
        "decimal_places": 2,
        "rounding_method": RoundingMethod.ROUND_DOWN,
        "home_currency": "PHP",
        "description": "VCP: Round down to 2 decimal places (e.g., 10.118 → 10.11)"
    },
    "VCT": {
        "decimal_places": 0,
        "rounding_method": RoundingMethod.ROUND_DOWN,
        "home_currency": "NTD",
        "description": "VCT: Round down to 0 decimal places (e.g., 99.9 → 99)"
    },
    "VCG": {
        "decimal_places": 2,
        "rounding_method": RoundingMethod.ROUND_HALF_UP,
        "home_currency": "EUR",
        "description": "VCG: Standard rounding to 2 decimal places"
    },
    "VCJ": {
        "decimal_places": 0,
        "rounding_method": RoundingMethod.ROUND_HALF_UP,
        "home_currency": "JPY",
        "description": "VCJ: Standard rounding to 0 decimal places"
    }
}

# Default rounding configuration for unknown companies
DEFAULT_ROUNDING_CONFIG = {
    "decimal_places": 2,
    "rounding_method": RoundingMethod.ROUND_HALF_UP,
    "home_currency": None,
    "description": "Default: Standard rounding to 2 decimal places"
}

def get_company_rounding_config(company_code, target_currency=None):
    """
    Get rounding configuration for a specific company.
    
    Args:
        company_code (str): Company code (e.g., VCT, VCA, VCP)
        target_currency (str, optional): Target currency (for future use)
        
    Returns:
        dict: Rounding configuration with keys:
            - decimal_places (int): Number of decimal places
            - rounding_method (RoundingMethod): Rounding method to use
            - home_currency (str): Company's home currency
            - description (str): Human-readable description
    """
    if not company_code:
        logger.warning("No company code provided, using default rounding configuration")
        return DEFAULT_ROUNDING_CONFIG.copy()
    
    # Get company-specific configuration
    config = COMPANY_ROUNDING_RULES.get(company_code.upper())
    
    if config:
        logger.debug(f"Found rounding config for company {company_code}: {config['description']}")
        return config.copy()
    else:
        logger.warning(f"No rounding configuration found for company {company_code}, using default")
        return DEFAULT_ROUNDING_CONFIG.copy()

def get_company_home_currency(company_code):
    """
    Get the home currency for a specific company.
    
    Args:
        company_code (str): Company code (e.g., VCT, VCA, VCP)
        
    Returns:
        str: Home currency code or None if not found
    """
    config = get_company_rounding_config(company_code)
    return config.get("home_currency")

def list_all_company_configs():
    """
    Get all company rounding configurations.
    
    Returns:
        dict: All company configurations
    """
    return COMPANY_ROUNDING_RULES.copy()

def validate_company_config(company_code):
    """
    Validate that a company has a proper rounding configuration.
    
    Args:
        company_code (str): Company code to validate
        
    Returns:
        tuple: (is_valid, validation_message)
    """
    if not company_code:
        return False, "Company code cannot be empty"
    
    config = COMPANY_ROUNDING_RULES.get(company_code.upper())
    if not config:
        return False, f"No configuration found for company {company_code}"
    
    required_keys = ["decimal_places", "rounding_method", "home_currency", "description"]
    for key in required_keys:
        if key not in config:
            return False, f"Missing required key '{key}' in configuration for {company_code}"
    
    if not isinstance(config["decimal_places"], int) or config["decimal_places"] < 0:
        return False, f"Invalid decimal_places value for {company_code}: must be non-negative integer"
    
    if not isinstance(config["rounding_method"], RoundingMethod):
        return False, f"Invalid rounding_method for {company_code}: must be RoundingMethod enum"
    
    return True, f"Configuration for {company_code} is valid"

# Example usage and testing
if __name__ == "__main__":
    # Configure logging for standalone execution
    import logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Test all company configurations
    print("Company Rounding Configurations:")
    print("=" * 50)
    
    for company_code in ["VCT", "VCA", "VCP", "VCG", "VCJ", "UNKNOWN"]:
        config = get_company_rounding_config(company_code)
        print(f"{company_code}: {config['description']}")
        
        # Validate configuration
        is_valid, message = validate_company_config(company_code)
        print(f"  Validation: {message}")
        print()
    
    # Test home currency lookup
    print("Home Currency Mapping:")
    print("-" * 30)
    for company_code in ["VCT", "VCA", "VCP"]:
        home_currency = get_company_home_currency(company_code)
        print(f"{company_code} → {home_currency}")