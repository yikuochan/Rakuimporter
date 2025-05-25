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
    default="https://api.businesscentral.dynamics.com/v2.0/6b83c27c-aa6d-475a-9933-5c34bb008d73/Production/ODataV4/Company('VCT')/PurchaseJournals"
)
CLIENT_ID = get_env_var("ERP_CLIENT_ID", required=True)
CLIENT_SECRET = get_env_var("ERP_CLIENT_SECRET", required=True)
SCOPE = get_env_var(
    "ERP_SCOPE", 
    default="https://api.businesscentral.dynamics.com/.default"
)

# Fixed values for journal entries
JOURNAL_TEMPLATE_NAME = "PURCHASES"
# for Employee expense Journal , we can set journal batch name to GEE
# JOURNAL_BATCH_NAME = "GEE"
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

def transform_currency_code(company_code: str, currency_code: str) -> str:
    """
    Legacy function for backward compatibility.
    Transform currency code based on company code according to business rules.
    
    Args:
        company_code: The company code (e.g., VCT, VCP, etc.)
        currency_code: The original currency code from the JSON
        
    Returns:
        str: The transformed currency code (empty string if it matches the rule,
             or R-prefixed version for specific currencies)
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
        return "R-EUR"
    
    # If the company code exists in our mapping and the currency matches the home currency
    if company_code in company_currency_map and normalized_currency == company_currency_map[company_code]:
        logger.info(f"Transforming currency code for company {company_code}: {currency_code} -> ''")
        # Always return empty string when currency matches home currency, regardless of which currency it is
        return ""
    
    # For non-home currencies, apply special rules
    if normalized_currency == "USD":
        logger.info(f"Adding R- prefix to USD: {currency_code} -> 'R-USD'")
        return "R-USD"
    elif normalized_currency == "RMB":
        logger.info(f"Adding R- prefix to RMB: {currency_code} -> 'R-RMB'")
        return "R-RMB"
    elif normalized_currency == "XEU" or normalized_currency == "EUR":
        logger.info(f"Adding R- prefix to {normalized_currency}: {currency_code} -> 'R-EUR'")
        return "R-EUR"
    elif normalized_currency == "NTD":
        logger.info(f"Adding R- prefix to NTD: {currency_code} -> 'R-NTD'")
        return "R-NTD"
    elif normalized_currency == "JPY":
        logger.info(f"Adding R- prefix to JPY: {currency_code} -> 'R-JPY'")
        return "R-JPY"
    elif normalized_currency == "PHP":
        logger.info(f"Adding R- prefix to PHP: {currency_code} -> 'R-PHP'")
        return "R-PHP"
    
    return currency_code


def convert_date_format(date_str):
    """
    Convert date from YYYY/MM/DD to YYYY-MM-DD format
    
    Args:
        date_str (str): Date string in YYYY/MM/DD format
        
    Returns:
        str: Date string in YYYY-MM-DD format
    """
    if not date_str:
        return ""
    
    try:
        # Split by / and rejoin with -
        parts = date_str.split('/')
        if len(parts) == 3:
            return f"{parts[0]}-{parts[1]}-{parts[2]}"
        return date_str  # Return original if not in expected format
    except Exception as e:
        logger.warning(f"Failed to convert date format for {date_str}: {str(e)}")
        return date_str  # Return original on error

def create_journal_line(entry: Dict[str, Any], entry_type: str) -> Dict[str, Any]:
    """
    Create a journal line payload for the API from an entry.
    
    Args:
        entry: The journal entry data
        entry_type: Either 'debit' or 'credit'
    
    Returns:
        Dict[str, Any]: The journal line payload
        
    Note:
        For debit lines, the transform_currency_code logic is applied to potentially make the currency code empty,
        but the original amount is kept without conversion, as per business requirements.
    """
    # Get the entry data based on type
    entry_data = entry[entry_type]
    
    # Get original amount
    original_amount = entry_data["amount"] if entry_type == "debit" else -entry_data["amount"]
    
    # Add voucher number to description
    description = entry.get("description", "")
    voucher_no = entry.get("voucher_no", "Unknown")
    
    # Add a note for consolidated entries
    if entry_type == "credit" and entry_data.get("consolidated", False):
        consolidation_note = entry_data.get("consolidation_note", f"Consolidated from {entry_data.get('original_entries_count', 1)} entries")
        if description and len(description) + len(consolidation_note) + 3 <= 100:  # +3 for " - "
            description = f"{description} - {consolidation_note}"
        elif len(consolidation_note) <= 100:
            description = consolidation_note
        logger.info(f"Added consolidation note to description: {description}")
    
    # Removed adding voucher number to description as per requirement
    # description = f"{voucher_no} - {description}"
    # logger.info(f"Added voucher number to description: {description}")
    
    # Determine ShortcutDimCode4 based on account type and source of account_no
    if entry_data.get("gl_account", "") == "Vendor" or entry.get("credit", {}).get("gl_account", "") == "Vendor":
        # For Vendor accounts or entries with Vendor credit, check the source of account_no
        # For debit lines of vendor payments, we need to check the credit side's account_source
        if entry_type == "debit" and entry.get("credit", {}).get("account_source") == "vendor_code":
            # If the credit side's account_no comes from column O (支払先CD), set ShortcutDimCode4 to empty
            shortcut_dim_code4 = ""
            logger.info(f"Setting ShortcutDimCode4 to empty for debit line of Vendor payment (支払先CD) - Voucher: {entry.get('voucher_no', 'Unknown')}")
        elif entry_type == "credit" and entry_data.get("account_source") == "vendor_code":
            # If the credit side's account_no comes from column O (支払先CD), set ShortcutDimCode4 to empty
            shortcut_dim_code4 = ""
            logger.info(f"Setting ShortcutDimCode4 to empty for Vendor payment (支払先CD) - Voucher: {entry.get('voucher_no', 'Unknown')}")
        else:
            # If account_no comes from column N (申請者CD/支払先CD), use applicant_code
            shortcut_dim_code4 = entry_data.get("applicant_code", "")
            logger.info(f"Using applicant_code for ShortcutDimCode4 for Employee payment (申請者CD/支払先CD) - Voucher: {entry.get('voucher_no', 'Unknown')}")
    else:
        # For non-Vendor accounts, keep using applicant_code
        shortcut_dim_code4 = entry_data.get("applicant_code", "")
    
    # Ensure shortcut_dim_code4 is not too long (max 100 chars)
    if len(shortcut_dim_code4) > 100:
        shortcut_dim_code4 = shortcut_dim_code4[:100]
        logger.warning(f"Truncated ShortcutDimCode4 to 100 characters: {shortcut_dim_code4}")
    
    # Determine Shortcut_Dimension_2_Code based on account type
    if entry_data.get("gl_account", "") == "Vendor":
        # Get the original department_code
        original_dept_code = entry_data.get("department_code", "")
        
        # Transform department_code for Vendor accounts
        if original_dept_code and len(original_dept_code) >= 3:
            # Take first 3 characters and append .9999
            shortcut_dim_2_code = original_dept_code[:3] + ".9999"
        else:
            # Fallback if department_code is missing or too short
            shortcut_dim_2_code = original_dept_code
    else:
        shortcut_dim_2_code = entry_data.get("department", "")
    
    # Determine Account_No based on the account type
    # For Vendor accounts, use vendor_code
    # For other accounts, use the account field
    if entry_data.get("gl_account", "") == "Vendor":
        account_no = entry_data.get("vendor_code", "")
    else:
        account_no = entry_data.get("account", "")
    
    # Ensure account_no is not too long (max 100 chars)
    if len(account_no) > 100:
        account_no = account_no[:100]
        logger.warning(f"Truncated Account_No to 100 characters: {account_no}")
    
    # Ensure description is not too long
    if len(description) > 100:
        description = description[:100]
        logger.warning(f"Truncated Description to 100 characters: {description}")
    
    # Get External_Document_No from the entry or fallback to voucher_no
    external_document_no = entry.get("External_Document_No", "") or entry.get("voucher_no", "")
    if len(external_document_no) > 100:
        external_document_no = external_document_no[:100]
        logger.warning(f"Truncated External_Document_No to 100 characters: {external_document_no}")
    
    # Get Document_No from voucher_no
    document_no = entry.get("voucher_no", "")
    if len(document_no) > 100:
        document_no = document_no[:100]
        logger.warning(f"Truncated Document_No to 100 characters: {document_no}")
    
    # Get Document_Date and convert format
    document_date = entry.get("Document_Date", "")
    formatted_document_date = convert_date_format(document_date)
    
    # Determine the company code from the department field
    department = entry_data.get("department", "")
    company_code = department[:3] if department else ""
    
    # Define the mapping of company codes to their respective "home" currencies
    # Updated to align with currency_converter.py
    company_currency_map = {
        "VCT": "NTD",
        "VCP": "PHP",  # Removed "R-" prefix
        "VCA": "USD",  # Removed "R-" prefix
        "VCG": "EUR",  # Removed "R-" prefix
        "VCJ": "JPY"
    }
    
    # Check if we have original_currency and original_amount fields for debit lines
    if entry_type == "debit" and "original_currency" in entry_data and "original_amount" in entry_data:
        # Use the true original values before any conversion
        currency_to_use = entry_data.get("original_currency", "")
        amount_to_use = entry_data.get("original_amount", original_amount)
        
        # Apply transform_currency_code to the original currency
        # This will handle all special cases consistently with our updated logic
        transformed_currency = transform_currency_code(company_code, currency_to_use)
        logger.info(
            f"Applied transform_currency_code for debit line - Voucher: {entry.get('voucher_no', 'Unknown')}, "
            f"Company: {company_code}, Original Currency: {currency_to_use}, Transformed Currency: {transformed_currency}"
        )
        
        converted_amount = amount_to_use  # Use the original amount
        
        logger.info(
            f"Using original currency and amount for debit line - Voucher: {entry.get('voucher_no', 'Unknown')}, "
            f"Original Currency: {currency_to_use}, Original Amount: {amount_to_use}, "
            f"Transformed Currency: {transformed_currency}"
        )
    else:
        # Get the currency code from the entry data (may be already converted)
        currency_to_use = entry_data.get("currency", "")
        
        # For debit lines without original_currency/original_amount, use existing logic
        if entry_type == "debit":
            # Apply transform_currency_code to potentially make currency code empty
            transformed_currency = transform_currency_code(company_code, currency_to_use)
            converted_amount = original_amount  # Keep original amount
        else:
            # For credit lines, use the existing transformation logic
            transformed_currency, converted_amount = transform_currency(
                company_code, 
                currency_to_use, 
                abs(original_amount)
            )
            # Apply sign based on entry type
            converted_amount = -converted_amount if entry_type == "credit" else converted_amount
    
    # Use the final amount
    amount = converted_amount
    
    # Create the journal line payload
    journal_line = {
        "Journal_Template_Name": JOURNAL_TEMPLATE_NAME,
        "Journal_Batch_Name": JOURNAL_BATCH_NAME,
        "Document_Type": DOCUMENT_TYPE,
        "External_Document_No": external_document_no,
        "Document_No": document_no,
        "Document_Date": formatted_document_date,
        "Account_Type": entry_data.get("gl_account", ""),
        "Account_No": account_no,
        "Description": description,
        "Currency_Code": transformed_currency,
        "Amount": amount,
        "Shortcut_Dimension_1_Code": company_code,
        "Shortcut_Dimension_2_Code": shortcut_dim_2_code,
        "ShortcutDimCode3": "",
        "ShortcutDimCode4": shortcut_dim_code4,
        "ShortcutDimCode5": "",
        "ShortcutDimCode6": "",
        "ShortcutDimCode7": "",
        "ShortcutDimCode8": "",
        "ShortcutDimCode9": "",
        "ShortcutDimCode10": "",
        "ShortcutDimCode11": "",
        "ShortcutDimCode12": "",
        "ShortcutDimCode13": "",
        "ShortcutDimCode14": "",
        "ShortcutDimCode15": ""
    }
    
    # Check if this is a debit entry with department VCT.1342G
    if entry_type == "debit" and entry_data.get("department") == "VCT.1342G":
        journal_line["ShortcutDimCode14"] = "VCT_TW0001"
        logger.info(f"Set ShortcutDimCode14 to VCT_TW0001 for debit entry with department VCT.1342G - Voucher: {entry.get('voucher_no', 'Unknown')}")
    
    return journal_line


# The apply_currency_code_rules function has been removed as part of the refactoring
# Currency code rules are now handled in exchange_rate_query.py


class RateLimiter:
    """
    Rate limiter class to manage API call timing and implement exponential backoff.
    """
    def __init__(self, base_delay=1.0, max_delay=10.0, backoff_factor=2.0):
        """
        Initialize the rate limiter.
        
        Args:
            base_delay: Base delay in seconds between API calls
            max_delay: Maximum delay in seconds between API calls
            backoff_factor: Factor to increase delay on failures
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.last_request_time = 0
        self.consecutive_failures = 0
    
    def wait_before_request(self):
        """
        Wait appropriate time before making a request.
        """
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # Calculate delay based on consecutive failures (exponential backoff)
        if self.consecutive_failures > 0:
            delay = min(self.base_delay * (self.backoff_factor ** (self.consecutive_failures - 1)), self.max_delay)
        else:
            delay = self.base_delay
            
        # If not enough time has passed since last request, wait
        if elapsed < delay:
            wait_time = delay - elapsed
            logger.info(f"Rate limiting: Waiting {wait_time:.2f} seconds before next API call")
            time.sleep(wait_time)
        
        # Update last request time
        self.last_request_time = time.time()
    
    def record_success(self):
        """
        Record a successful API call.
        """
        self.consecutive_failures = 0
    
    def record_failure(self):
        """
        Record a failed API call.
        """
        self.consecutive_failures += 1
        logger.info(f"Rate limiting: Recorded failure. Consecutive failures: {self.consecutive_failures}")


def post_journal_line(journal_line: Dict[str, Any], access_token: str, 
                     rate_limiter: RateLimiter = None, max_retries: int = 3) -> Tuple[bool, Dict[str, Any]]:
    """
    Post a journal line to the ERP API with rate limiting and retry logic.
    
    Args:
        journal_line: The journal line payload
        access_token: OAuth2 access token
        rate_limiter: RateLimiter instance for managing API call timing
        max_retries: Maximum number of retry attempts for failed API calls
    
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and response data
    """
    # Currency code rules application is now skipped as it's handled in exchange_rate_query.py
    logger.info(f"Currency code rules application skipped as per refactoring")
    
    # Extract company code from Shortcut_Dimension_1_Code
    shortcut_dim_code = journal_line.get("Shortcut_Dimension_1_Code", "")
    
    # Default to the environment variable if no code is found
    api_url = API_URL
    
    # If we have a shortcut dimension code, extract the company code
    if shortcut_dim_code:
        # If the code contains a period, extract only the part before the period
        company_code = shortcut_dim_code.split('.')[0] if '.' in shortcut_dim_code else shortcut_dim_code
        
        if company_code:
            # Construct the API URL with the company code
            base_url = "https://api.businesscentral.dynamics.com/v2.0/6b83c27c-aa6d-475a-9933-5c34bb008d73/Production/ODataV4/Company"
            api_url = f"{base_url}('{company_code}')/PurchaseJournals"
            logger.info(f"Using company-specific API URL for {company_code}: {api_url}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Create a default rate limiter if none provided
    if rate_limiter is None:
        rate_limiter = RateLimiter()
    
    retry_count = 0
    
    while retry_count <= max_retries:
        # Wait before making the request
        rate_limiter.wait_before_request()
        
        try:
            # Log the request body for debugging
            logger.info(f"Request body for journal line: {json.dumps(journal_line, indent=2)}")
            # Log headers (excluding Authorization header for security)
            safe_headers = headers.copy()
            if "Authorization" in safe_headers:
                safe_headers["Authorization"] = "Bearer [REDACTED]"
            logger.info(f"Request headers: {json.dumps(safe_headers, indent=2)}")
            
            # Temporarily disable SSL verification for testing
            response = requests.post(api_url, json=journal_line, headers=headers, verify=False)
            
            # Log response status and headers
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
            
            # Check for rate limit response (usually 429 Too Many Requests)
            if response.status_code == 429:
                logger.warning("Rate limit hit. Backing off...")
                rate_limiter.record_failure()
                retry_count += 1
                continue
            
            # For other errors, raise the exception
            response.raise_for_status()
            
            # Process successful response
            response_data = response.json()
            # Log the response data
            logger.info(f"API response body: {json.dumps(response_data, indent=2)}")
            
            # Record success and return
            rate_limiter.record_success()
            return True, response_data
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {str(e)}")
            
            # For 5xx errors (server errors), retry
            if 500 <= response.status_code < 600:
                logger.warning(f"Server error {response.status_code}. Retrying...")
                rate_limiter.record_failure()
                retry_count += 1
            else:
                # For other HTTP errors, don't retry
                try:
                    error_data = response.json()
                    logger.error(f"API error response: {json.dumps(error_data, indent=2)}")
                    return False, error_data
                except:
                    return False, {"error": str(e)}
                    
        except Exception as e:
            logger.error(f"Error posting journal line: {str(e)}")
            rate_limiter.record_failure()
            retry_count += 1
            
        # If we've reached max retries, give up
        if retry_count > max_retries:
            logger.error(f"Max retries ({max_retries}) exceeded. Giving up.")
            return False, {"error": f"Failed after {max_retries} attempts"}
    
    # If we exit the loop without returning, it means we've exceeded max retries
    logger.error(f"Max retries ({max_retries}) exceeded. Giving up.")
    return False, {"error": f"Failed after {max_retries} attempts"}


def verify_balanced_amounts(entry_or_entries, tolerance=0.01):
    """
    Verify that debit and credit amounts balance after currency conversion.
    
    Args:
        entry_or_entries: Single entry dict or list of entry dicts
        tolerance: Acceptable difference between debit and credit amounts
        
    Returns:
        tuple: (is_balanced, difference, debit_total, credit_total)
    """
    entries = [entry_or_entries] if isinstance(entry_or_entries, dict) else entry_or_entries
    
    # Calculate total debit and credit amounts after currency conversion
    debit_total = 0
    credit_total = 0
    
    for entry in entries:
        # Get company code from debit department
        debit_dept = entry.get("debit", {}).get("department", "")
        company_code = debit_dept[:3] if debit_dept else ""
        
        # Get debit amount and currency
        debit_amount = entry.get("debit", {}).get("amount", 0)
        debit_currency = entry.get("debit", {}).get("currency", "")
        
        # Get credit amount and currency
        credit_amount = entry.get("credit", {}).get("amount", 0)
        credit_currency = entry.get("credit", {}).get("currency", "")
        
        # Apply currency transformation to get the final amounts
        _, converted_debit = transform_currency(company_code, debit_currency, debit_amount)
        _, converted_credit = transform_currency(company_code, credit_currency, credit_amount)
        
        debit_total += converted_debit
        credit_total += converted_credit
    
    # Calculate difference
    difference = abs(debit_total - credit_total)
    
    # Check if within tolerance
    is_balanced = difference <= tolerance
    
    return is_balanced, difference, debit_total, credit_total


def generate_unbalanced_entries_report(unbalanced_entries, output_file):
    """
    Generate a report of unbalanced entries.
    
    Args:
        unbalanced_entries: List of dictionaries containing unbalanced entry details
        output_file: Path to the output report file
    """
    with open(output_file, 'w') as f:
        f.write("# Unbalanced Entries Report\n\n")
        f.write("| Voucher No | Vendor Code | Debit Total | Credit Total | Difference |\n")
        f.write("|------------|-------------|-------------|--------------|------------|\n")
        
        for entry in unbalanced_entries:
            f.write(f"| {entry['voucher_no']} | {entry['vendor_code']} | " 
                   f"{entry['debit_total']:.2f} | {entry['credit_total']:.2f} | " 
                   f"{entry['difference']:.2f} |\n")
        
        f.write(f"\n\nTotal unbalanced entries: {len(unbalanced_entries)}\n")
        f.write(f"\nNote: This report includes entries where the difference between debit and credit amounts exceeds the tolerance of 0.01.\n")


def generate_currency_modification_report(entries: List[Dict[str, Any]], output_file: str) -> List[Dict[str, Any]]:
    """
    Generate a report of all currency code modifications.
    
    Args:
        entries: List of journal entries
        output_file: Path to the output report file
    
    Returns:
        List[Dict[str, Any]]: List of modifications made
    """
    modifications = []
    
    for entry in entries:
        voucher_no = entry.get("voucher_no", "Unknown")
        
        # Check debit line
        debit_dept = entry.get("debit", {}).get("department", "")
        debit_company = debit_dept[:3] if debit_dept else ""
        debit_currency = entry.get("debit", {}).get("currency", "")
        
        if debit_company and debit_currency:
            transformed_debit = transform_currency_code(debit_company, debit_currency)
            if transformed_debit != debit_currency:
                modifications.append({
                    "voucher_no": voucher_no,
                    "line_type": "debit",
                    "company_code": debit_company,
                    "original_currency": debit_currency,
                    "transformed_currency": transformed_debit
                })
        
        # Check credit line
        credit_dept = entry.get("credit", {}).get("department", "")
        credit_company = credit_dept[:3] if credit_dept else ""
        credit_currency = entry.get("credit", {}).get("currency", "")
        
        if credit_company and credit_currency:
            transformed_credit = transform_currency_code(credit_company, credit_currency)
            if transformed_credit != credit_currency:
                modifications.append({
                    "voucher_no": voucher_no,
                    "line_type": "credit",
                    "company_code": credit_company,
                    "original_currency": credit_currency,
                    "transformed_currency": transformed_credit
                })
    
    # Write the report to a markdown file
    with open(output_file, 'w') as f:
        f.write("# Currency Modification Report\n\n")
        f.write("| Voucher No | Line Type | Company Code | Original Currency | Transformed Currency |\n")
        f.write("|------------|-----------|--------------|-------------------|---------------------|\n")
        
        for mod in modifications:
            f.write(f"| {mod['voucher_no']} | {mod['line_type']} | {mod['company_code']} | {mod['original_currency']} | {mod['transformed_currency']} |\n")
        
        f.write(f"\n\nTotal modifications: {len(modifications)}\n")
        f.write(f"\nNote: This report includes all currency code transformations for both debit and credit lines.\n")
    
    logger.info(f"Currency modification report generated: {output_file}")
    return modifications


def process_entries(entries: List[Dict[str, Any]], access_token: str, balance_tolerance: float = 0.01, 
                   skip_unbalanced: bool = False, unbalanced_report_file: str = "unbalanced_entries_report.md",
                   base_delay: float = 5.0, max_delay: float = 10.0, backoff_factor: float = 2.0, 
                   max_retries: int = 3) -> Tuple[int, int, int, int]:
    """
    Process all entries and post them to the ERP API with rate limiting.
    
    Args:
        entries: List of journal entries
        access_token: OAuth2 access token
        balance_tolerance: Acceptable difference between debit and credit amounts
        skip_unbalanced: If True, skip unbalanced entries instead of posting them
        unbalanced_report_file: Path to the output report file for unbalanced entries
        base_delay: Base delay in seconds between API calls
        max_delay: Maximum delay in seconds between API calls
        backoff_factor: Factor to increase delay on failures
        max_retries: Maximum number of retry attempts for failed API calls
    
    Returns:
        Tuple[int, int, int, int]: Count of successful, failed, balanced, and unbalanced entries
    """
    # Create a rate limiter
    rate_limiter = RateLimiter(base_delay, max_delay, backoff_factor)
    logger.info(f"Rate limiter initialized with base_delay={base_delay}s, max_delay={max_delay}s, backoff_factor={backoff_factor}")
    success_count = 0
    failure_count = 0
    balanced_count = 0
    unbalanced_count = 0
    unbalanced_entries = []
    
    # Group entries by voucher number and vendor code
    entry_groups = {}
    # Track entries that are already consolidated in the input data
    already_consolidated = set()
    
    for entry in entries:
        voucher_no = entry.get('voucher_no', 'Unknown')
        vendor_code = entry.get('credit', {}).get('vendor_code', '')
        
        # Check if this is a consolidated entry (empty debit and consolidated credit)
        if (not entry.get("debit", {}).get("account") and 
            entry.get("credit", {}).get("consolidated", False)):
            # Mark this voucher as already having a consolidated entry
            already_consolidated.add(voucher_no)
            
        if not vendor_code:
            # If no vendor code, just process as individual entry
            if voucher_no not in entry_groups:
                entry_groups[voucher_no] = {}
            if 'individual' not in entry_groups[voucher_no]:
                entry_groups[voucher_no]['individual'] = []
            entry_groups[voucher_no]['individual'].append(entry)
        else:
            # Group by vendor code
            if voucher_no not in entry_groups:
                entry_groups[voucher_no] = {}
            if vendor_code not in entry_groups[voucher_no]:
                entry_groups[voucher_no][vendor_code] = []
            entry_groups[voucher_no][vendor_code].append(entry)
    
    # Process each group
    for voucher_no, vendor_groups in entry_groups.items():
        # Check if this voucher is already consolidated in the input data
        is_already_consolidated = voucher_no in already_consolidated
        
        for vendor_code, group_entries in vendor_groups.items():
            # Find entries with valid debit information
            valid_entries = [e for e in group_entries if e["debit"] and e["debit"].get("amount")]
            
            # Find consolidated credit entries
            consolidated_entries = [e for e in group_entries if e["credit"].get("consolidated", False)]
            
            if not valid_entries:
                continue
                
            # If only one valid entry in the group or this voucher is already consolidated,
            # process each entry individually
            if len(valid_entries) == 1 or is_already_consolidated:
                # Process each valid entry individually
                for entry in valid_entries:
                    entry_voucher_no = entry.get('voucher_no', 'Unknown')
                    logger.info(f"Processing individual entry - Voucher: {entry_voucher_no}")
                
                    # Verify that debit and credit amounts balance after currency conversion
                    is_balanced, difference, debit_total, credit_total = verify_balanced_amounts(entry, balance_tolerance)
                    
                    if is_balanced:
                        logger.info(f"Entry balanced for voucher {entry_voucher_no}: " 
                                   f"Debit: {debit_total:.2f}, Credit: {credit_total:.2f}")
                        balanced_count += 1
                    else:
                        logger.warning(f"Unbalanced entry detected for voucher {entry_voucher_no}: " 
                                      f"Debit: {debit_total:.2f}, Credit: {credit_total:.2f}, " 
                                      f"Difference: {difference:.2f}")
                        unbalanced_count += 1
                        
                        # Store unbalanced entry details for reporting
                        unbalanced_entries.append({
                            "voucher_no": entry_voucher_no,
                            "vendor_code": entry.get('credit', {}).get('vendor_code', ''),
                            "debit_total": debit_total,
                            "credit_total": credit_total,
                            "difference": difference,
                            "entries": [entry]
                        })
                        
                        # Skip unbalanced entries if configured to do so
                        if skip_unbalanced:
                            logger.error(f"Skipping unbalanced entry for voucher {entry_voucher_no}")
                            continue
                        else:
                            logger.warning(f"Processing unbalanced entry for voucher {entry_voucher_no} despite imbalance")
                    
                    # Process debit line
                    debit_line = create_journal_line(entry, "debit")
                    # Ensure Document_No matches the voucher_no
                    debit_line["Document_No"] = entry_voucher_no
                    # Use the original External_Document_No without modification
                    logger.info(f"Posting debit line for voucher {entry_voucher_no} with Document_No: {debit_line['Document_No']}")
                    # Create a deep copy of the debit line to prevent any reference issues
                    debit_line_copy = json.loads(json.dumps(debit_line))
                    debit_success, debit_response = post_journal_line(debit_line_copy, access_token, rate_limiter, max_retries)
                    
                    if debit_success:
                        logger.info(f"Successfully posted debit line for voucher {entry_voucher_no}")
                        success_count += 1
                    else:
                        logger.error(f"Failed to post debit line for voucher {entry_voucher_no}")
                        failure_count += 1
                    
                    # If this voucher is already consolidated in the input data,
                    # only post the credit line for the entry with the consolidated credit
                    if not is_already_consolidated or not consolidated_entries:
                        # Process credit line
                        credit_line = create_journal_line(entry, "credit")
                        # Ensure Document_No matches the voucher_no
                        credit_line["Document_No"] = entry_voucher_no
                        # Use the original External_Document_No without modification
                        logger.info(f"Posting credit line for voucher {entry_voucher_no} with Document_No: {credit_line['Document_No']}")
                        # Create a deep copy of the credit line to prevent any reference issues
                        credit_line_copy = json.loads(json.dumps(credit_line))
                        credit_success, credit_response = post_journal_line(credit_line_copy, access_token, rate_limiter, max_retries)
                        
                        if credit_success:
                            logger.info(f"Successfully posted credit line for voucher {entry_voucher_no}")
                            success_count += 1
                        else:
                            logger.error(f"Failed to post credit line for voucher {entry_voucher_no}")
                            failure_count += 1
                
                # If this voucher is already consolidated and we have consolidated entries,
                # post the consolidated credit line once
                if is_already_consolidated and consolidated_entries:
                    # Use the first consolidated entry
                    consolidated_entry = consolidated_entries[0]
                    consolidated_voucher_no = consolidated_entry.get('voucher_no', voucher_no)
                    
                    # Process the consolidated credit line
                    credit_line = create_journal_line(consolidated_entry, "credit")
                    # Ensure Document_No matches the consolidated voucher_no
                    credit_line["Document_No"] = consolidated_voucher_no
                    # Use the original External_Document_No without modification
                    logger.info(f"Posting consolidated credit line for voucher {consolidated_voucher_no} with Document_No: {credit_line['Document_No']} - " +
                               f"Using existing consolidated entry")
                    
                    # Create a deep copy of the credit line to prevent any reference issues
                    credit_line_copy = json.loads(json.dumps(credit_line))
                    credit_success, credit_response = post_journal_line(credit_line_copy, access_token, rate_limiter, max_retries)
                    
                    if credit_success:
                        logger.info(f"Successfully posted consolidated credit line for voucher {consolidated_voucher_no}")
                        success_count += 1
                    else:
                        logger.error(f"Failed to post consolidated credit line for voucher {consolidated_voucher_no}")
                        failure_count += 1
            # Only process multiple entries with consolidated credit if this voucher is not already consolidated
            elif not is_already_consolidated:
                # Process multiple entries with consolidated credit
                logger.info(f"Processing {len(valid_entries)} entries with consolidated credit - Voucher: {voucher_no}")
                
                # Find the consolidated credit entry if it exists
                consolidated_entry = next((e for e in group_entries if e["credit"].get("consolidated", False)), None)
                
                if consolidated_entry:
                    # Use the existing consolidated credit entry
                    template_entry = consolidated_entry
                    consolidated_voucher_no = template_entry.get('voucher_no', voucher_no)
                else:
                    # Create a new consolidated credit entry from the first entry
                    # Sum up all debit amounts
                    total_amount = sum(e["debit"].get("amount", 0) for e in valid_entries)
                    
                    # Use the first entry as a template
                    template_entry = valid_entries[0].copy()
                    template_entry["credit"]["amount"] = total_amount
                    template_entry["credit"]["consolidated"] = True
                    template_entry["credit"]["original_entries_count"] = len(valid_entries)
                    template_entry["credit"]["consolidation_note"] = f"Consolidated from {len(valid_entries)} entries"
                    consolidated_voucher_no = template_entry.get('voucher_no', voucher_no)
                
                # Verify that the consolidated entries balance
                is_balanced, difference, debit_total, credit_total = verify_balanced_amounts(valid_entries, balance_tolerance)
                
                if is_balanced:
                    logger.info(f"Consolidated entries balanced for voucher group {voucher_no}: " 
                               f"Debit: {debit_total:.2f}, Credit: {credit_total:.2f}")
                    balanced_count += 1
                else:
                    logger.warning(f"Unbalanced consolidated entries detected for voucher group {voucher_no}: " 
                                  f"Debit: {debit_total:.2f}, Credit: {credit_total:.2f}, " 
                                  f"Difference: {difference:.2f}")
                    unbalanced_count += 1
                    
                    # Store unbalanced entry details for reporting
                    unbalanced_entries.append({
                        "voucher_no": voucher_no,
                        "vendor_code": vendor_code,
                        "debit_total": debit_total,
                        "credit_total": credit_total,
                        "difference": difference,
                        "entries": valid_entries
                    })
                    
                    # Skip unbalanced entries if configured to do so
                    if skip_unbalanced:
                        logger.error(f"Skipping unbalanced consolidated entries for voucher group {voucher_no}")
                        continue
                    else:
                        logger.warning(f"Processing unbalanced consolidated entries for voucher group {voucher_no} despite imbalance")
                
                # Process all debit lines
                for i, entry in enumerate(valid_entries):
                    debit_line = create_journal_line(entry, "debit")
                    # Ensure Document_No matches the entry's voucher_no
                    entry_voucher_no = entry.get('voucher_no', voucher_no)
                    debit_line["Document_No"] = entry_voucher_no
                    # Use the original External_Document_No without modification
                    logger.info(f"Posting debit line {i+1}/{len(valid_entries)} for voucher {entry_voucher_no} with Document_No: {debit_line['Document_No']}")
                    # Create a deep copy of the debit line to prevent any reference issues
                    debit_line_copy = json.loads(json.dumps(debit_line))
                    debit_success, debit_response = post_journal_line(debit_line_copy, access_token, rate_limiter, max_retries)
                    
                    if debit_success:
                        logger.info(f"Successfully posted debit line for voucher {entry_voucher_no}")
                        success_count += 1
                    else:
                        logger.error(f"Failed to post debit line for voucher {entry_voucher_no}")
                        failure_count += 1
                
                # Process the consolidated credit line
                credit_line = create_journal_line(template_entry, "credit")
                # Ensure Document_No matches the template entry's voucher_no
                credit_line["Document_No"] = consolidated_voucher_no
                # Use the original External_Document_No without modification
                logger.info(f"Posting consolidated credit line for voucher {consolidated_voucher_no} with Document_No: {credit_line['Document_No']} - " +
                           f"Consolidated from {len(valid_entries)} entries")
                
                # Create a deep copy of the credit line to prevent any reference issues
                credit_line_copy = json.loads(json.dumps(credit_line))
                credit_success, credit_response = post_journal_line(credit_line_copy, access_token, rate_limiter, max_retries)
                
                if credit_success:
                    logger.info(f"Successfully posted consolidated credit line for voucher {consolidated_voucher_no}")
                    success_count += 1
                else:
                    logger.error(f"Failed to post consolidated credit line for voucher {consolidated_voucher_no}")
                    failure_count += 1
    
    # Generate report of unbalanced entries if any were found
    if unbalanced_entries:
        generate_unbalanced_entries_report(unbalanced_entries, unbalanced_report_file)
        logger.info(f"Generated unbalanced entries report with {len(unbalanced_entries)} entries: {unbalanced_report_file}")
    
    return success_count, failure_count, balanced_count, unbalanced_count


def main():
    """Main function to process the input file and post to the ERP API."""
    parser = argparse.ArgumentParser(description='Process JSON file and post to ERP API')
    parser.add_argument('input_file', help='Input JSON file path')
    parser.add_argument('--report', help='Generate currency modification report to specified file path', default="currency_modification_report.md")
    parser.add_argument('--unbalanced-report', help='Generate unbalanced entries report to specified file path', default="unbalanced_entries_report.md")
    parser.add_argument('--balance-tolerance', type=float, default=0.01, help='Acceptable difference between debit and credit amounts')
    parser.add_argument('--skip-unbalanced', action='store_true', help='Skip unbalanced entries instead of posting them')
    parser.add_argument('--dry-run', action='store_true', help='Generate report only without posting to API')
    parser.add_argument('--sample-payload', help='Output a sample journal line payload to specified file path')
    parser.add_argument('--base-delay', type=float, default=5.0, help='Base delay between API calls in seconds (default: 5.0)')
    parser.add_argument('--max-delay', type=float, default=10.0, help='Maximum delay between API calls in seconds (default: 10.0)')
    parser.add_argument('--backoff-factor', type=float, default=2.0, help='Factor to increase delay on failures (default: 2.0)')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum number of retry attempts for failed API calls (default: 3)')
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Load input file
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        logger.info(f"Loaded {len(entries)} entries from {args.input_file}")
    except Exception as e:
        logger.error(f"Error loading input file: {str(e)}")
        sys.exit(1)
    
    # Generate currency modification report
    modifications = generate_currency_modification_report(entries, args.report)
    logger.info(f"Generated currency modification report with {len(modifications)} modifications")
    
    # If sample-payload is specified, generate a sample payload and exit
    if args.sample_payload:
        # Use the first entry to generate a sample payload
        if entries:
            entry = entries[0]
            debit_line = create_journal_line(entry, "debit")
            credit_line = create_journal_line(entry, "credit")
            
            sample = {
                "debit_line": debit_line,
                "credit_line": credit_line
            }
            
            with open(args.sample_payload, 'w', encoding='utf-8') as f:
                json.dump(sample, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Sample payload written to {args.sample_payload}")
            sys.exit(0)
    
    # If dry-run is specified, exit after generating the report
    if args.dry_run:
        logger.info("Dry run completed. Exiting without posting to API.")
        sys.exit(0)
    
    # Get access token
    try:
        access_token = get_access_token()
    except Exception as e:
        logger.error(f"Failed to get access token: {str(e)}")
        sys.exit(1)
    
    # Process entries
    success_count, failure_count, balanced_count, unbalanced_count = process_entries(
        entries, 
        access_token, 
        balance_tolerance=args.balance_tolerance,
        skip_unbalanced=args.skip_unbalanced,
        unbalanced_report_file=args.unbalanced_report,
        base_delay=args.base_delay,
        max_delay=args.max_delay,
        backoff_factor=args.backoff_factor,
        max_retries=args.max_retries
    )
    
    # Log summary
    total_lines = len(entries) * 2  # Each entry has debit and credit lines
    logger.info(f"Processing complete. Success: {success_count}/{total_lines}, Failure: {failure_count}/{total_lines}")
    logger.info(f"Balance check: Balanced: {balanced_count}, Unbalanced: {unbalanced_count}")


if __name__ == "__main__":
    main()
