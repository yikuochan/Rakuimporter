#!/usr/bin/env python3
"""
Currency Value Modifier for JSON Files

This script modifies currency values in JSON files based on specific rules:
1. For department codes under VCT: Change currency value from NTD to empty
2. For department codes under VCJ: If currency is JPY, change currency value to empty

Usage:
    python modify_currency.py -i INPUT_JSON_FILE [-o OUTPUT_JSON_FILE]

Arguments:
    -i, --input    Input JSON file path (required)
    -o, --output   Output JSON file path (optional, defaults to input_filename-modified.json)

Example:
    python modify_currency.py -i "data.json" -o "modified_data.json"
"""

import json
import os
import argparse
import sys

def modify_currency_values(data):
    """
    Modify currency values based on the rules:
    1. For department codes under VCT: Change currency value from NTD to empty
    2. For department codes under VCJ: If currency is JPY, change currency value to empty
    """
    modified_count = 0
    
    for entry in data:
        # Process debit section
        if "debit" in entry and "department_code" in entry["debit"]:
            dept_code = entry["debit"]["department_code"]
            currency = entry["debit"].get("currency", "")
            
            # Rule 1: VCT department with NTD currency
            if dept_code.startswith("VCT") and currency == "NTD":
                entry["debit"]["currency"] = ""
                modified_count += 1
            
            # Rule 2: VCJ department with JPY currency
            elif dept_code.startswith("VCJ") and currency == "JPY":
                entry["debit"]["currency"] = ""
                modified_count += 1
        
        # Process credit section
        if "credit" in entry and "department_code" in entry["credit"]:
            dept_code = entry["credit"]["department_code"]
            currency = entry["credit"].get("currency", "")
            
            # Rule 1: VCT department with NTD currency
            if dept_code.startswith("VCT") and currency == "NTD":
                entry["credit"]["currency"] = ""
                modified_count += 1
            
            # Rule 2: VCJ department with JPY currency
            elif dept_code.startswith("VCJ") and currency == "JPY":
                entry["credit"]["currency"] = ""
                modified_count += 1
    
    return data, modified_count

def main():
    parser = argparse.ArgumentParser(
        description='Modify currency values in JSON files based on specific rules.',
        epilog='Example: python modify_currency.py -i "data.json" -o "modified_data.json"'
    )
    parser.add_argument('-i', '--input', required=True, help='Input JSON file path (required)')
    parser.add_argument('-o', '--output', help='Output JSON file path (default: input_filename-modified.json)')
    
    args = parser.parse_args()
    
    # If output file is not specified, derive it from the input filename
    if not args.output:
        input_base = args.input.rsplit('.', 1)[0]  # Remove extension
        args.output = f"{input_base}-modified.json"
    
    try:
        # Check if input file exists
        if not os.path.exists(args.input):
            print(f"Error: Input file '{args.input}' not found.")
            sys.exit(1)
        
        print(f"Reading input file: {args.input}")
        # Read the input file
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Found {len(data)} entries in the input file.")
        
        # Modify the currency values
        modified_data, count = modify_currency_values(data)
        
        # Write the modified data to the output file
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(modified_data, f, ensure_ascii=False, indent=2)
        
        print(f"Modified {count} currency values.")
        print(f"Modified data saved to {args.output}")
        
        # Verify the output file was created
        if os.path.exists(args.output):
            print(f"Output file '{args.output}' successfully created.")
            print(f"File size: {os.path.getsize(args.output)} bytes")
        else:
            print(f"Error: Failed to create output file '{args.output}'.")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
