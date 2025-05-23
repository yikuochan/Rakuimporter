#!/usr/bin/env python3
"""
VicOne ERP API Integration Script

This script processes JSON files containing journal entries and posts them to the VicOne ERP API.
For each entry in the input file, it generates two journal lines (debit and credit) and posts them
to the ERP API endpoint.

Usage:
    python process_japan_exports.py <input_json_file>

Example:
    python process_japan_exports.py jp-test-Evelyn\\ Raku\\ export_journal_data.json
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, List, Any, Optional, Tuple

# Force reset the logging configuration
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

import certifi
import requests
import urllib3

# Import currency converter
from currency_converter import convert_amount, get_region_currency

# Disable SSL warnings (for testing only)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import environment configuration utility
try:
    from env_config import get_env_var
except ImportError:
    # Fallback if env_config.py is not available
    def get_env_var(name, default=None, required=False, as_type=str):
        value = os.environ.get(name)
        if value is None:
            if required:
                raise ValueError(f"Required environment variable '{name}' is not set")
            return default
        return value

def setup_logging():
    """Set up logging with both file and console handlers."""
    # Remove any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create logger
    logger = logging.getLogger("erp_api_integration")
    logger.setLevel(logging.INFO)
    logger.handlers = []  # Remove any existing handlers
    
    # Create handlers
    try:
        file_handler = logging.FileHandler("erp_api_integration.log")
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        # Add file handler to logger
        logger.addHandler(file_handler)
        logger.info("File logging handler initialized successfully")
    except Exception as e:
        print(f"Error setting up log file: {str(e)}")
        print("Falling back to console-only logging")
    
    # Always add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Set up logging
logger = setup_logging()

# API Configuration from environment variables
TOKEN_URL = get_env_var(
    "ERP_TOKEN_URL", 
    default="https://login.microsoftonline.com/6b83c27c-aa6d-475a-9933-5c34bb008d73/oauth2/v2.0/token"
)
API_URL = get_env_var(
    "ERP_API_URL", 
    default="https://api.businesscentral.dynamics.com/v2.0/6b83c27c-aa6d-475a-9933-5c34bb008d73/Staging/ODataV4/Company('VCT')/PurchaseJournals"
)
CLIENT_ID = get_env_var("ERP_CLIENT_ID", required=True)
CLIENT_SECRET = get_env_var("ERP_CLIENT_SECRET", required=True)
SCOPE = get_env_var(
    "ERP_SCOPE", 
    default="https://api.businesscentral.dynamics.com/.default"
)

# Fixed values for journal entries
JOURNAL_TEMPLATE_NAME = "PURCHASES"
JOURNAL_BATCH_NAME = "PURCHASE"
DOCUMENT_TYPE = "Invoice"


def get_access_token() -> str:
    """
    Get OAuth2 access token using client credentials flow.
    
    Returns:
        str: Access token
    
    Raises:
        Exception: If token acquisition fails
    """
    logger.info("Getting access token...")
    
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": SCOPE
    }
    
    try:
        # Log the token request data
        logger.info(f"Token request body: {data}")
        # Temporarily disable SSL verification for testing
        response = requests.post(TOKEN_URL, data=data, verify=False)
        # Log response status and headers
        logger.info(f"Token response status code: {response.status_code}")
        logger.info(f"Token response headers: {json.dumps(dict(response.headers), indent=2)}")
        response.raise_for_status()
        token_data = response.json()
        # Log token response (excluding the actual token for security)
        safe_token_data = token_data.copy()
        if "access_token" in safe_token_data:
            safe_token_data["access_token"] = "[REDACTED]"
        logger.info(f"Token response: {json.dumps(safe_token_data, indent=2)}")
        logger.info("Access token acquired successfully")
        return token_data["access_token"]
    except Exception as e:
        logger.error(f"Failed to get access token: {str(e)}")
        raise


def transform_currency(company_code: str, currency_code: str, amount: float) -> Tuple[str, float]:
    """
    Transform currency code based on company code and convert amount according to business rules.
    
    Args:
        company_code: The company code (e.g., VCT, VCP, etc.)
        currency_code: The original currency code from the JSON
        amount: The amount to convert
        
    Returns:
        Tuple[str, float]: The transformed currency code and converted amount
    """
    # Define the mapping of company codes to their respective "home" currencies
    # Updated to align with currency_converter.py
    company_currency_map = {
        "VCT": "NTD",
        "VCP": "PHP",  # Removed "R-" prefix
        "VCA": "USD",  # Removed "R-" prefix
        "VCG": "EUR",  # Removed "R-" prefix
        "VCJ": "JPY"
    }
    
    # Handle "R-" prefix in currency codes
    normalized_currency = currency_code
    if currency_code and currency_code.startswith("R-"):
        normalized_currency = currency_code[2:]  # Remove "R-" prefix
        logger.info(f"Normalized currency code by removing R- prefix: {currency_code} -> {normalized_currency}")
    
    # Special case for XEU with VCG (treat XEU as EUR)
    if company_code == "VCG" and (normalized_currency == "XEU"):
        logger.info(f"Transforming currency code for company {company_code}: {currency_code} -> 'R-EUR'")
        return "R-EUR", amount
    
    # If the company code exists in our mapping
    if company_code in company_currency_map:
        target_currency = company_currency_map[company_code]
        
        # If the currency already matches the target (home currency)
        if normalized_currency == target_currency:
            logger.info(f"Transforming currency code for company {company_code}: {currency_code} -> ''")
            # Always return empty string when currency matches home currency, regardless of which currency it is
            return "", amount
        
        # If we have a different currency, convert the amount to the target currency
        elif normalized_currency:
            try:
                # Convert amount to target currency, passing company_code
                # Use the normalized currency for conversion, not the original with R- prefix
                converted_amount, success = convert_amount(amount, normalized_currency, target_currency, company_code=company_code)
                logger.info(f"Converted {amount} {normalized_currency} to {converted_amount:.2f} {target_currency} for company {company_code}")
                
                # After conversion, the currency is now the home currency, so return empty string
                return "", converted_amount
            except Exception as e:
                logger.warning(f"Failed to convert {amount} from {normalized_currency} to {target_currency}: {str(e)}")
                # Return original currency code and amount if conversion fails
                return currency_code, amount
    
    # For non-home currencies, apply special rules
    if normalized_currency == "USD":
        logger.info(f"Adding R- prefix to USD: {currency_code} -> 'R-USD'")
        return "R-USD", amount
    elif normalized_currency == "RMB":
        logger.info(f"Adding R- prefix to RMB: {currency_code} -> 'R-RMB'")
        return "R-RMB", amount
    elif normalized_currency == "XEU" or normalized_currency == "EUR":
        logger.info(f"Adding R- prefix to {normalized_currency}: {currency_code} -> 'R-EUR'")
        return "R-EUR", amount
    elif normalized_currency == "NTD":
        logger.info(f"Adding R- prefix to NTD: {currency_code} -> 'R-NTD'")
        return "R-NTD", amount
    elif normalized_currency == "JPY":
        logger.info(f"Adding R- prefix to JPY: {currency_code} -> 'R-JPY'")
        return "R-JPY", amount
    elif normalized_currency == "PHP":
        logger.info(f"Adding R- prefix to PHP: {currency_code} -> 'R-PHP'")
        return "R-PHP", amount
    
    # If company code not in mapping or other issues, return original values
    return currency_code, amount