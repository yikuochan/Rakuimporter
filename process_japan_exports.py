#!/usr/bin/env python3
"""
VicOne ERP API Integration Script

This script processes JSON files containing journal entries and posts them to the VicOne ERP API.
For each entry in the input file, it generates two journal lines (debit and credit) and posts them
to the ERP API endpoint.

Usage:
    python process_japan_exports.py <input_json_file>

Example:
    python process_japan_exports.py jp-test-Evelyn\ Raku\ export_journal_data.json
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, List, Any, Optional, Tuple

import requests

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
        response = requests.post(TOKEN_URL, data=data)
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


def create_journal_line(entry: Dict[str, Any], entry_type: str) -> Dict[str, Any]:
    """
    Create a journal line payload for the API from an entry.
    
    Args:
        entry: The journal entry data
        entry_type: Either 'debit' or 'credit'
    
    Returns:
        Dict[str, Any]: The journal line payload
    """
    # Get the entry data based on type
    entry_data = entry[entry_type]
    
    # Determine amount (positive for debit, negative for credit)
    amount = entry_data["amount"] if entry_type == "debit" else -entry_data["amount"]
    
    # Determine ShortcutDimCode4 (vendor_code if present, otherwise applicant_code)
    shortcut_dim_code4 = entry_data.get("vendor_code", "") or entry_data.get("applicant_code", "")
    
    # Create the journal line payload
    journal_line = {
        "Journal_Template_Name": JOURNAL_TEMPLATE_NAME,
        "Journal_Batch_Name": JOURNAL_BATCH_NAME,
        "Document_Type": DOCUMENT_TYPE,
        "External_Document_No": entry.get("voucher_no", ""),
        "Account_Type": entry_data.get("gl_account", ""),
        "Account_No": entry_data.get("account", ""),
        "Description": entry.get("description", ""),
        "Currency_Code": entry_data.get("currency", ""),
        "Amount": amount,
        "Shortcut_Dimension_1_Code": entry_data.get("department", "")[:3] if entry_data.get("department") else "",
        "Shortcut_Dimension_2_Code": entry_data.get("department", ""),
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
    
    return journal_line


def post_journal_line(journal_line: Dict[str, Any], access_token: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Post a journal line to the ERP API.
    
    Args:
        journal_line: The journal line payload
        access_token: OAuth2 access token
    
    Returns:
        Tuple[bool, Dict[str, Any]]: Success status and response data
    """
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
        response = requests.post(API_URL, json=journal_line, headers=headers)
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
    
    for i, entry in enumerate(entries):
        logger.info(f"Processing entry {i+1}/{len(entries)} - Voucher: {entry.get('voucher_no', 'Unknown')}")
        
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
    
    return success_count, failure_count


def main():
    """Main function to process the input file and post to the ERP API."""
    parser = argparse.ArgumentParser(description='Process JSON file and post to ERP API')
    parser.add_argument('input_file', help='Input JSON file path')
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
