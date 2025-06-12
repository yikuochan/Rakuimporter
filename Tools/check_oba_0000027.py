#!/usr/bin/env python3
"""
Script to check the OBA-0000027 voucher in the fixed JSON file.
"""

import json
from decimal import Decimal

def load_json_data(file_path):
    """Load JSON data from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def check_oba_0000027(data):
    """Check the OBA-0000027 voucher."""
    # Filter for OBA-0000027
    voucher_entries = [entry for entry in data if entry.get("voucher_no") == "OBA-0000027"]
    
    if not voucher_entries:
        print("No entries found for voucher OBA-0000027")
        return
    
    print(f"Found {len(voucher_entries)} entries for voucher OBA-0000027")
    
    # Find the consolidated entry (the one with debit amount = 0)
    consolidated_entry = next((entry for entry in voucher_entries if entry.get("debit", {}).get("amount", 0) == 0), None)
    
    if not consolidated_entry:
        print("No consolidated entry found")
        return
    
    consolidated_amount = Decimal(str(consolidated_entry.get("credit", {}).get("amount", 0)))
    print(f"Consolidated amount: {consolidated_amount}")
    
    # Calculate the sum of individual entries
    individual_entries = [entry for entry in voucher_entries if entry.get("debit", {}).get("amount", 0) != 0]
    
    # Print details of each individual entry
    print("\nIndividual entries:")
    for i, entry in enumerate(individual_entries):
        credit_amount = Decimal(str(entry.get("credit", {}).get("amount", 0)))
        debit_amount = Decimal(str(entry.get("debit", {}).get("amount", 0)))
        description = entry.get("description", "")
        
        # Check if this is a currency conversion entry
        original_currency = entry.get("debit", {}).get("original_currency", "")
        original_amount = entry.get("debit", {}).get("original_amount", "")
        
        if original_currency:
            print(f"  {i+1}. {description}: {original_amount} {original_currency} -> {debit_amount} NTD (credit: {credit_amount})")
        else:
            print(f"  {i+1}. {description}: {debit_amount} (credit: {credit_amount})")
    
    total_amount = sum(Decimal(str(entry.get("credit", {}).get("amount", 0))) for entry in individual_entries)
    print(f"\nSum of individual entries: {total_amount}")
    
    # Check if the raw total before rounding is stored
    raw_total = consolidated_entry.get("credit", {}).get("raw_total_before_rounding")
    if raw_total:
        print(f"Raw total before rounding: {raw_total}")
    
    # Check if the consolidated amount matches the expected value
    expected_amount = Decimal('83868')
    if abs(consolidated_amount - expected_amount) < Decimal('0.01'):
        print(f"✓ Consolidated amount ({consolidated_amount}) matches the expected amount ({expected_amount})")
    else:
        print(f"✗ Consolidated amount ({consolidated_amount}) does not match the expected amount ({expected_amount})")
        print(f"  Difference: {consolidated_amount - expected_amount}")

def main():
    """Main function."""
    try:
        # Check the original file
        print("\n=== Checking Original JSON File ===")
        try:
            original_data = load_json_data("0527-Raku export- VCT PR 1-2.utf8.json")
            print(f"Loaded original data with {len(original_data)} entries")
            check_oba_0000027(original_data)
        except Exception as e:
            print(f"Error checking original file: {e}")
        
        # Check the fixed file
        print("\n=== Checking Fixed JSON File ===")
        try:
            fixed_data = load_json_data("0527-Raku export- VCT PR 1-2.utf8.roundfixed.json")
            print(f"Loaded fixed data with {len(fixed_data)} entries")
            check_oba_0000027(fixed_data)
        except Exception as e:
            print(f"Error checking fixed file: {e}")
    except Exception as e:
        print(f"Error in main function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
