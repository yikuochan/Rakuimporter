#!/usr/bin/env python3
"""
Test script to verify that string length validation issues are fixed.
This script loads the JSON data and checks if any string values exceed 100 characters.
"""

import json
import sys

def check_string_lengths(data, max_length=100):
    """
    Check if any string values in the data exceed the maximum length.
    
    Args:
        data: The JSON data to check
        max_length: Maximum allowed string length
    
    Returns:
        list: List of validation errors
    """
    validation_errors = []
    
    for i, entry in enumerate(data):
        # Check voucher_no
        if len(entry.get("voucher_no", "")) > max_length:
            validation_errors.append(f"Entry {i}: voucher_no exceeds {max_length} characters: {entry['voucher_no']}")
        
        # Check description
        if len(entry.get("description", "")) > max_length:
            validation_errors.append(f"Entry {i}: description exceeds {max_length} characters: {entry['description']}")
        
        # Check debit section
        if "debit" in entry:
            debit = entry["debit"]
            # Check vendor_code
            if len(debit.get("vendor_code", "")) > max_length:
                validation_errors.append(f"Entry {i}: debit.vendor_code exceeds {max_length} characters: {debit['vendor_code']}")
            
            # Check applicant_code
            if len(debit.get("applicant_code", "")) > max_length:
                validation_errors.append(f"Entry {i}: debit.applicant_code exceeds {max_length} characters: {debit['applicant_code']}")
            
            # Check account
            if len(debit.get("account", "")) > max_length:
                validation_errors.append(f"Entry {i}: debit.account exceeds {max_length} characters: {debit['account']}")
        
        # Check credit section
        if "credit" in entry:
            credit = entry["credit"]
            # Check vendor_code
            if len(credit.get("vendor_code", "")) > max_length:
                validation_errors.append(f"Entry {i}: credit.vendor_code exceeds {max_length} characters: {credit['vendor_code']}")
            
            # Check applicant_code
            if len(credit.get("applicant_code", "")) > max_length:
                validation_errors.append(f"Entry {i}: credit.applicant_code exceeds {max_length} characters: {credit['applicant_code']}")
            
            # Check account
            if len(credit.get("account", "")) > max_length:
                validation_errors.append(f"Entry {i}: credit.account exceeds {max_length} characters: {credit['account']}")
    
    return validation_errors

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Check string lengths in JSON file')
    parser.add_argument('input_file', nargs='?', default="Test Raku export-all-noNTD.json", 
                        help='Input JSON file path (default: Test Raku export-all-noNTD.json)')
    args = parser.parse_args()
    
    input_file = args.input_file
    
    try:
        # Load the JSON data
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loaded {len(data)} entries from {input_file}")
        
        # Check string lengths
        validation_errors = check_string_lengths(data)
        
        if validation_errors:
            print(f"Found {len(validation_errors)} validation errors:")
            for error in validation_errors:
                print(f"- {error}")
        else:
            print("No string length validation errors found!")
        
        # Specifically check for the problematic voucher numbers mentioned in the error
        problematic_vouchers = ["VPA-0000095", "VPA-0000068"]
        for voucher in problematic_vouchers:
            for i, entry in enumerate(data):
                if entry.get("voucher_no") == voucher:
                    print(f"\nChecking entry with voucher_no {voucher}:")
                    print(f"- description: '{entry.get('description', '')}' (length: {len(entry.get('description', ''))})")
                    print(f"- debit.vendor_code: '{entry['debit'].get('vendor_code', '')}' (length: {len(entry['debit'].get('vendor_code', ''))})")
                    print(f"- debit.applicant_code: '{entry['debit'].get('applicant_code', '')}' (length: {len(entry['debit'].get('applicant_code', ''))})")
                    print(f"- credit.vendor_code: '{entry['credit'].get('vendor_code', '')}' (length: {len(entry['credit'].get('vendor_code', ''))})")
                    print(f"- credit.applicant_code: '{entry['credit'].get('applicant_code', '')}' (length: {len(entry['credit'].get('applicant_code', ''))})")
                    break
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
