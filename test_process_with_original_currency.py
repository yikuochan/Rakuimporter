#!/usr/bin/env python3
"""
Test script to check how entries with original_currency are processed by process_japan_exports.py
"""

import json
import sys
from process_japan_exports import create_journal_line

def test_process_with_original_currency(json_file):
    """
    Test how entries with original_currency are processed by process_japan_exports.py
    
    Args:
        json_file (str): Path to the JSON file
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    
    print(f"Total entries: {len(entries)}")
    
    entries_with_original_currency = []
    for entry in entries:
        if "original_currency" in entry.get("debit", {}):
            entries_with_original_currency.append(entry)
    
    print(f"Entries with original_currency: {len(entries_with_original_currency)}")
    
    if entries_with_original_currency:
        print("\nProcessing sample entries with original_currency:")
        for i, entry in enumerate(entries_with_original_currency[:3]):  # Process first 3 entries
            print(f"\nEntry {i+1}:")
            print(f"  Voucher No: {entry.get('voucher_no', 'Unknown')}")
            print(f"  Description: {entry.get('description', 'Unknown')}")
            print(f"  Debit:")
            print(f"    Currency: {entry['debit'].get('currency', 'Unknown')}")
            print(f"    Amount: {entry['debit'].get('amount', 'Unknown')}")
            print(f"    Original Currency: {entry['debit'].get('original_currency', 'Unknown')}")
            print(f"    Original Amount: {entry['debit'].get('original_amount', 'Unknown')}")
            
            # Process the entry using create_journal_line
            debit_line = create_journal_line(entry, "debit")
            
            print(f"  Processed Debit Line:")
            print(f"    Currency_Code: {debit_line.get('Currency_Code', 'Unknown')}")
            print(f"    Amount: {debit_line.get('Amount', 'Unknown')}")
            
            # Process credit line for comparison
            credit_line = create_journal_line(entry, "credit")
            
            print(f"  Processed Credit Line:")
            print(f"    Currency_Code: {credit_line.get('Currency_Code', 'Unknown')}")
            print(f"    Amount: {credit_line.get('Amount', 'Unknown')}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_process_with_original_currency.py <json_file>")
        sys.exit(1)
    
    test_process_with_original_currency(sys.argv[1])
