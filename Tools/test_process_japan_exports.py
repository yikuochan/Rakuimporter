#!/usr/bin/env python3
"""
Test script to run process_japan_exports.py with the truncated-modified file.
This script will create journal lines from the truncated-modified file and check for string length validation errors.
"""

import json
import sys
from process_japan_exports import create_journal_line

def test_journal_lines(input_file):
    """
    Test creating journal lines from the input file and check for string length validation errors.
    
    Args:
        input_file: Path to the input JSON file
    """
    try:
        # Load the JSON data
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loaded {len(data)} entries from {input_file}")
        
        # Process each entry
        validation_errors = []
        for i, entry in enumerate(data):
            try:
                # Create debit journal line
                debit_line = create_journal_line(entry, "debit")
                
                # Check string lengths in debit line
                for key, value in debit_line.items():
                    if isinstance(value, str) and len(value) > 100:
                        validation_errors.append(f"Entry {i} (debit): {key} exceeds 100 characters: {value}")
                
                # Create credit journal line
                credit_line = create_journal_line(entry, "credit")
                
                # Check string lengths in credit line
                for key, value in credit_line.items():
                    if isinstance(value, str) and len(value) > 100:
                        validation_errors.append(f"Entry {i} (credit): {key} exceeds 100 characters: {value}")
                
            except Exception as e:
                validation_errors.append(f"Error processing entry {i}: {str(e)}")
        
        # Report results
        if validation_errors:
            print(f"Found {len(validation_errors)} validation errors:")
            for error in validation_errors:
                print(f"- {error}")
        else:
            print("No string length validation errors found in journal lines!")
        
        # Specifically check for the problematic voucher numbers mentioned in the error
        problematic_vouchers = ["VPA-0000095", "VPA-0000068"]
        for voucher in problematic_vouchers:
            for i, entry in enumerate(data):
                if entry.get("voucher_no") == voucher:
                    print(f"\nChecking journal lines for entry with voucher_no {voucher}:")
                    
                    # Create journal lines
                    debit_line = create_journal_line(entry, "debit")
                    credit_line = create_journal_line(entry, "credit")
                    
                    # Check debit line
                    print("Debit line:")
                    for key, value in debit_line.items():
                        if isinstance(value, str):
                            print(f"- {key}: '{value}' (length: {len(value)})")
                    
                    # Check credit line
                    print("\nCredit line:")
                    for key, value in credit_line.items():
                        if isinstance(value, str):
                            print(f"- {key}: '{value}' (length: {len(value)})")
                    
                    break
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    input_file = "Test Raku export-all-noNTD-truncated-modified.json"
    test_journal_lines(input_file)
