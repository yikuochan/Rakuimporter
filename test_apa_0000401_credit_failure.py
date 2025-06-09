#!/usr/bin/env python3
"""
Test script to diagnose credit line posting failure for voucher APA-0000401.

This script extracts and processes only the APA-0000401 voucher from a JSON file
with enhanced logging to diagnose the failure.

Usage:
    python test_apa_0000401_credit_failure.py <input_json_file>

Example:
    python test_apa_0000401_credit_failure.py 0604-Raku\ export-\ VCT\ credit\ card\ 1.utf8.json
"""

import argparse
import json
import logging
import os
import sys
from process_japan_exports import (
    get_access_token, 
    post_journal_line, 
    create_journal_line, 
    RateLimiter,
    DecimalEncoder,
    analyze_error_response
)

# Set up logging with both file and console handlers
def setup_logging():
    # Create logger
    logger = logging.getLogger("apa_0000401_diagnosis")
    logger.setLevel(logging.DEBUG)  # Set to DEBUG for maximum verbosity
    logger.handlers = []  # Remove any existing handlers
    
    # Create handlers
    try:
        file_handler = logging.FileHandler("apa_0000401_diagnosis.log")
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        # Add file handler to logger
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Error setting up log file: {str(e)}")
    
    # Always add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    return logger

# Set up logging
logger = setup_logging()

def extract_voucher(entries, voucher_no="APA-0000401"):
    """
    Extract entries with the specified voucher number.
    
    Args:
        entries: List of journal entries
        voucher_no: Voucher number to extract
        
    Returns:
        List of entries with the specified voucher number
    """
    extracted = [entry for entry in entries if entry.get('voucher_no') == voucher_no]
    logger.info(f"Found {len(extracted)} entries with voucher number {voucher_no}")
    return extracted

def process_voucher(entry, access_token):
    """
    Process a single voucher entry with detailed logging.
    
    Args:
        entry: The journal entry to process
        access_token: OAuth2 access token
        
    Returns:
        Tuple[bool, bool]: Success status for debit and credit lines
    """
    # Create a rate limiter with longer delays for testing
    rate_limiter = RateLimiter(base_delay=2.0, max_delay=10.0, backoff_factor=2.0)
    max_retries = 3
    
    entry_voucher_no = entry.get('voucher_no', 'Unknown')
    logger.info(f"Processing entry - Voucher: {entry_voucher_no}")
    logger.info(f"Full entry data: {json.dumps(entry, indent=2, cls=DecimalEncoder)}")
    
    # Process debit line
    debit_line = create_journal_line(entry, "debit")
    # Ensure Document_No matches the voucher_no
    debit_line["Document_No"] = entry_voucher_no
    logger.info(f"Posting debit line for voucher {entry_voucher_no}")
    logger.info(f"Debit line payload: {json.dumps(debit_line, indent=2, cls=DecimalEncoder)}")
    
    # Create a deep copy of the debit line to prevent any reference issues
    debit_line_copy = json.loads(json.dumps(debit_line, cls=DecimalEncoder))
    debit_success, debit_response = post_journal_line(debit_line_copy, access_token, rate_limiter, max_retries)
    
    if debit_success:
        logger.info(f"Successfully posted debit line for voucher {entry_voucher_no}")
        logger.info(f"Debit response: {json.dumps(debit_response, indent=2, cls=DecimalEncoder)}")
    else:
        logger.error(f"Failed to post debit line for voucher {entry_voucher_no}")
        logger.error(f"Debit failure details: {json.dumps(debit_response, indent=2, cls=DecimalEncoder)}")
        
        # Analyze the error response
        if isinstance(debit_response, dict) and "error" in debit_response:
            error_analysis = analyze_error_response(debit_response)
            logger.error(f"Debit line error analysis: {error_analysis}")
    
    # Process credit line
    credit_line = create_journal_line(entry, "credit")
    # Ensure Document_No matches the voucher_no
    credit_line["Document_No"] = entry_voucher_no
    logger.info(f"Posting credit line for voucher {entry_voucher_no}")
    logger.info(f"Credit line payload: {json.dumps(credit_line, indent=2, cls=DecimalEncoder)}")
    
    # Log detailed information about the credit line before posting
    logger.info(f"Credit line details for voucher {entry_voucher_no}:")
    logger.info(f"Account Type: {credit_line.get('Account_Type')}")
    logger.info(f"Account No: {credit_line.get('Account_No')}")
    logger.info(f"Currency Code: {credit_line.get('Currency_Code')}")
    logger.info(f"Amount: {credit_line.get('Amount')}")
    logger.info(f"Dimensions: {credit_line.get('Shortcut_Dimension_1_Code')}, {credit_line.get('Shortcut_Dimension_2_Code')}")
    
    # Create a deep copy of the credit line to prevent any reference issues
    credit_line_copy = json.loads(json.dumps(credit_line, cls=DecimalEncoder))
    credit_success, credit_response = post_journal_line(credit_line_copy, access_token, rate_limiter, max_retries)
    
    if credit_success:
        logger.info(f"Successfully posted credit line for voucher {entry_voucher_no}")
        logger.info(f"Credit response: {json.dumps(credit_response, indent=2, cls=DecimalEncoder)}")
    else:
        logger.error(f"Failed to post credit line for voucher {entry_voucher_no}")
        logger.error(f"Credit line failure details: {json.dumps(credit_response, indent=2, cls=DecimalEncoder)}")
        logger.error(f"Original entry data: {json.dumps(entry.get('credit', {}), indent=2, cls=DecimalEncoder)}")
        
        # Analyze the error response
        if isinstance(credit_response, dict) and "error" in credit_response:
            error_analysis = analyze_error_response(credit_response)
            logger.error(f"Credit line error analysis: {error_analysis}")
    
    return debit_success, credit_success

def main():
    """Main function to process the input file and diagnose the issue."""
    parser = argparse.ArgumentParser(description='Diagnose credit line posting failure for voucher APA-0000401')
    parser.add_argument('input_file', help='Input JSON file path')
    parser.add_argument('--voucher', default="APA-0000401", help='Voucher number to extract (default: APA-0000401)')
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
    
    # Extract voucher entries
    voucher_entries = extract_voucher(entries, args.voucher)
    
    if not voucher_entries:
        logger.error(f"No entries found with voucher number {args.voucher}")
        sys.exit(1)
    
    # Get access token
    try:
        access_token = get_access_token()
    except Exception as e:
        logger.error(f"Failed to get access token: {str(e)}")
        sys.exit(1)
    
    # Process each voucher entry
    success_count = 0
    failure_count = 0
    
    for entry in voucher_entries:
        debit_success, credit_success = process_voucher(entry, access_token)
        
        if debit_success:
            success_count += 1
        else:
            failure_count += 1
            
        if credit_success:
            success_count += 1
        else:
            failure_count += 1
    
    # Log summary
    logger.info(f"Processing complete. Success: {success_count}, Failure: {failure_count}")

if __name__ == "__main__":
    main()
