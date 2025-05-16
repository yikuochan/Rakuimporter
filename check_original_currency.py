#!/usr/bin/env python3
"""
Script to check entries with original_currency in a JSON file
"""

import json
import sys

def check_original_currency(json_file):
    """
    Check entries with original_currency in a JSON file
    
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
        print("\nSample entries with original_currency:")
        for i, entry in enumerate(entries_with_original_currency[:3]):  # Print first 3 entries
            print(f"\nEntry {i+1}:")
            print(f"  Voucher No: {entry.get('voucher_no', 'Unknown')}")
            print(f"  Description: {entry.get('description', 'Unknown')}")
            print(f"  Debit:")
            print(f"    Currency: {entry['debit'].get('currency', 'Unknown')}")
            print(f"    Amount: {entry['debit'].get('amount', 'Unknown')}")
            print(f"    Original Currency: {entry['debit'].get('original_currency', 'Unknown')}")
            print(f"    Original Amount: {entry['debit'].get('original_amount', 'Unknown')}")
            print(f"  Credit:")
            print(f"    Currency: {entry['credit'].get('currency', 'Unknown')}")
            print(f"    Amount: {entry['credit'].get('amount', 'Unknown')}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_original_currency.py <json_file>")
        sys.exit(1)
    
    check_original_currency(sys.argv[1])
