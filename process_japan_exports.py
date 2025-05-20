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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("erp_api_integration.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("erp_api_integration")

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
    if company_code == "VCG" and (normalized_currency == "XEU" or normalized_currency == "EUR"):
        logger.info(f"Transforming currency code for company {company_code}: {currency_code} -> 'R-EUR'")
        return "R-EUR", amount
    
    # If the company code exists in our mapping
    if company_code in company_currency_map:
        target_currency = company_currency_map[company_code]
        
        # If the currency already matches the target
        if normalized_currency == target_currency:
            logger.info(f"Transforming currency code for company {company_code}: {currency_code} -> ''")
            
            # New requirement: Add R- prefix for specific currencies
            if normalized_currency == "USD":
                logger.info(f"Adding R- prefix to USD: '' -> 'R-USD'")
                return "R-USD", amount
            elif normalized_currency == "RMB":
                logger.info(f"Adding R- prefix to RMB: '' -> 'R-RMB'")
                return "R-RMB", amount
            elif normalized_currency == "XEU":
                logger.info(f"Adding R- prefix to XEU: '' -> 'R-EUR'")
                return "R-EUR", amount
            
            # For other currencies, return empty string as before
            return "", amount
        
        # If we have a different currency, convert the amount to the target currency
        elif normalized_currency:
            try:
                # Convert amount to target currency
                converted_amount = convert_amount(amount, normalized_currency, target_currency)
                logger.info(f"Converted {amount} {currency_code} to {converted_amount:.2f} {target_currency} for company {company_code}")
                
                # Apply the same currency code transformation rules after conversion
                if target_currency == "USD":
                    logger.info(f"Adding R- prefix to USD after conversion: '' -> 'R-USD'")
                    return "R-USD", converted_amount
                elif target_currency == "RMB":
                    logger.info(f"Adding R- prefix to RMB after conversion: '' -> 'R-RMB'")
                    return "R-RMB", converted_amount
                elif target_currency == "XEU" or target_currency == "EUR":
                    logger.info(f"Adding R- prefix to EUR after conversion: '' -> 'R-EUR'")
                    return "R-EUR", converted_amount
                
                # Return empty string for currency code (as it's the home currency) and the converted amount
                return "", converted_amount
            except Exception as e:
                logger.warning(f"Failed to convert {amount} from {currency_code} to {target_currency}: {str(e)}")
                # Return original currency code and amount if conversion fails
                return currency_code, amount
    
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
    if company_code == "VCG" and (normalized_currency == "XEU" or normalized_currency == "EUR"):
        logger.info(f"Transforming currency code for company {company_code}: {currency_code} -> 'R-EUR'")
        return "R-EUR"
    
    # If the company code exists in our mapping and the currency matches
    if company_code in company_currency_map and normalized_currency == company_currency_map[company_code]:
        logger.info(f"Transforming currency code for company {company_code}: {currency_code} -> ''")
        
        # New requirement: Add R- prefix for specific currencies
        if normalized_currency == "USD":
            logger.info(f"Adding R- prefix to USD: '' -> 'R-USD'")
            return "R-USD"
        elif normalized_currency == "RMB":
            logger.info(f"Adding R- prefix to RMB: '' -> 'R-RMB'")
            return "R-RMB"
        elif normalized_currency == "XEU" or normalized_currency == "EUR":
            logger.info(f"Adding R- prefix to {normalized_currency}: '' -> 'R-EUR'")
            return "R-EUR"
        
        # For other currencies, return empty string as before
        return ""
    
    return currency_code


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
    
    # Add a note for consolidated entries
    description = entry.get("description", "")
    if entry_type == "credit" and entry_data.get("consolidated", False):
        consolidation_note = entry_data.get("consolidation_note", f"Consolidated from {entry_data.get('original_entries_count', 1)} entries")
        if description and len(description) + len(consolidation_note) + 3 <= 100:  # +3 for " - "
            description = f"{description} - {consolidation_note}"
        elif len(consolidation_note) <= 100:
            description = consolidation_note
        logger.info(f"Added consolidation note to description: {description}")
    
    # Determine ShortcutDimCode4 (empty if vendor_code present, otherwise use applicant_code)
    shortcut_dim_code4 = "" if entry_data.get("vendor_code") else entry_data.get("applicant_code", "")
    
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
    
    # Get voucher_no and ensure it's not too long
    voucher_no = entry.get("voucher_no", "")
    if len(voucher_no) > 100:
        voucher_no = voucher_no[:100]
        logger.warning(f"Truncated External_Document_No to 100 characters: {voucher_no}")
    
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
        
        # Special case for XEU (treat XEU as EUR)
        if currency_to_use == "XEU":
            if company_code == "VCG":
                transformed_currency = "R-EUR"
                logger.info(
                    f"Special case: Transforming XEU to R-EUR for company VCG - Voucher: {entry.get('voucher_no', 'Unknown')}, "
                    f"Original Currency: {currency_to_use}, Transformed Currency: {transformed_currency}"
                )
            else:
                transformed_currency = "R-EUR"
                logger.info(
                    f"Special case: Transforming XEU to R-EUR - Voucher: {entry.get('voucher_no', 'Unknown')}, "
                    f"Original Currency: {currency_to_use}, Transformed Currency: {transformed_currency}"
                )
        # Special case for RMB (always transform to R-RMB)
        elif currency_to_use == "RMB":
            transformed_currency = "R-RMB"
            logger.info(
                f"Special case: Transforming RMB to R-RMB - Voucher: {entry.get('voucher_no', 'Unknown')}, "
                f"Original Currency: {currency_to_use}, Transformed Currency: {transformed_currency}"
            )
        # Special case for USD with VCA
        elif company_code == "VCA" and currency_to_use == "USD":
            transformed_currency = "R-USD"
            logger.info(
                f"Special case: Transforming USD to R-USD for company VCA - Voucher: {entry.get('voucher_no', 'Unknown')}, "
                f"Original Currency: {currency_to_use}, Transformed Currency: {transformed_currency}"
            )
        else:
            # Apply transform_currency_code to the original currency
            transformed_currency = transform_currency_code(company_code, currency_to_use)
        
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
        "External_Document_No": voucher_no,
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


def post_journal_line(journal_line: Dict[str, Any], access_token: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Post a journal line to the ERP API.
    
    Args:
        journal_line: The journal line payload
        access_token: OAuth2 access token
    
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
            base_url = "https://api.businesscentral.dynamics.com/v2.0/6b83c27c-aa6d-475a-9933-5c34bb008d73/Staging/ODataV4/Company"
            api_url = f"{base_url}('{company_code}')/PurchaseJournals"
            logger.info(f"Using company-specific API URL for {company_code}: {api_url}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
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
        response.raise_for_status()
        response_data = response.json()
        # Log the response data
        logger.info(f"API response body: {json.dumps(response_data, indent=2)}")
        return True, response_data
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {str(e)}")
        try:
            error_data = response.json()
            logger.error(f"API error response: {json.dumps(error_data, indent=2)}")
            return False, error_data
        except:
            return False, {"error": str(e)}
    except Exception as e:
        logger.error(f"Error posting journal line: {str(e)}")
        return False, {"error": str(e)}


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


def process_entries(entries: List[Dict[str, Any]], access_token: str) -> Tuple[int, int]:
    """
    Process all entries and post them to the ERP API.
    
    Args:
        entries: List of journal entries
        access_token: OAuth2 access token
    
    Returns:
        Tuple[int, int]: Count of successful and failed entries
    """
    success_count = 0
    failure_count = 0
    
    # Group entries by voucher number and vendor code
    entry_groups = {}
    for entry in entries:
        voucher_no = entry.get('voucher_no', 'Unknown')
        vendor_code = entry.get('credit', {}).get('vendor_code', '')
        
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
        for vendor_code, group_entries in vendor_groups.items():
            # Skip entries that are marked as consolidated but have empty debit
            # These are the consolidated credit entries we'll generate ourselves
            valid_entries = [e for e in group_entries if e["debit"] and e["debit"].get("amount")]
            
            if not valid_entries:
                continue
                
            # If only one valid entry in the group, process it normally
            if len(valid_entries) == 1 and not valid_entries[0]["credit"].get("consolidated", False):
                entry = valid_entries[0]
                logger.info(f"Processing single entry - Voucher: {entry.get('voucher_no', 'Unknown')}")
                
                # Process debit line
                debit_line = create_journal_line(entry, "debit")
                logger.info(f"Posting debit line for voucher {entry.get('voucher_no', 'Unknown')}")
                debit_success, debit_response = post_journal_line(debit_line, access_token)
                
                if debit_success:
                    logger.info(f"Successfully posted debit line for voucher {entry.get('voucher_no', 'Unknown')}")
                    success_count += 1
                else:
                    logger.error(f"Failed to post debit line for voucher {entry.get('voucher_no', 'Unknown')}")
                    failure_count += 1
                
                # Small delay between requests to avoid rate limiting
                time.sleep(0.5)
                
                # Process credit line
                credit_line = create_journal_line(entry, "credit")
                logger.info(f"Posting credit line for voucher {entry.get('voucher_no', 'Unknown')}")
                credit_success, credit_response = post_journal_line(credit_line, access_token)
                
                if credit_success:
                    logger.info(f"Successfully posted credit line for voucher {entry.get('voucher_no', 'Unknown')}")
                    success_count += 1
                else:
                    logger.error(f"Failed to post credit line for voucher {entry.get('voucher_no', 'Unknown')}")
                    failure_count += 1
                
                # Small delay between entries
                time.sleep(0.5)
            else:
                # Process multiple entries with consolidated credit
                logger.info(f"Processing {len(valid_entries)} entries with consolidated credit - Voucher: {voucher_no}")
                
                # Process all debit lines
                for i, entry in enumerate(valid_entries):
                    debit_line = create_journal_line(entry, "debit")
                    logger.info(f"Posting debit line {i+1}/{len(valid_entries)} for voucher {voucher_no}")
                    debit_success, debit_response = post_journal_line(debit_line, access_token)
                    
                    if debit_success:
                        logger.info(f"Successfully posted debit line for voucher {voucher_no}")
                        success_count += 1
                    else:
                        logger.error(f"Failed to post debit line for voucher {voucher_no}")
                        failure_count += 1
                    
                    # Small delay between requests to avoid rate limiting
                    time.sleep(0.5)
                
                # Find the consolidated credit entry if it exists
                consolidated_entry = next((e for e in group_entries if e["credit"].get("consolidated", False)), None)
                
                if consolidated_entry:
                    # Use the existing consolidated credit entry
                    credit_line = create_journal_line(consolidated_entry, "credit")
                    logger.info(f"Posting consolidated credit line for voucher {voucher_no} - " +
                               f"Consolidated from {consolidated_entry['credit'].get('original_entries_count', len(valid_entries))} entries")
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
                    
                    credit_line = create_journal_line(template_entry, "credit")
                    logger.info(f"Posting new consolidated credit line for voucher {voucher_no} - " +
                               f"Consolidated from {len(valid_entries)} entries")
                
                credit_success, credit_response = post_journal_line(credit_line, access_token)
                
                if credit_success:
                    logger.info(f"Successfully posted consolidated credit line for voucher {voucher_no}")
                    success_count += 1
                else:
                    logger.error(f"Failed to post consolidated credit line for voucher {voucher_no}")
                    failure_count += 1
                
                # Small delay between entries
                time.sleep(0.5)
    
    return success_count, failure_count


def main():
    """Main function to process the input file and post to the ERP API."""
    parser = argparse.ArgumentParser(description='Process JSON file and post to ERP API')
    parser.add_argument('input_file', help='Input JSON file path')
    parser.add_argument('--report', help='Generate currency modification report to specified file path', default="currency_modification_report.md")
    parser.add_argument('--dry-run', action='store_true', help='Generate report only without posting to API')
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
    success_count, failure_count = process_entries(entries, access_token)
    
    # Log summary
    total_lines = len(entries) * 2  # Each entry has debit and credit lines
    logger.info(f"Processing complete. Success: {success_count}/{total_lines}, Failure: {failure_count}/{total_lines}")


if __name__ == "__main__":
    main()
