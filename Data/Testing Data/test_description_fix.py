#!/usr/bin/env python3
"""
Test script to verify the description field population in journal lines.
"""

import json
import sys
from process_japan_exports import create_journal_line

def test_description_population():
    """Test that the description field is properly populated in journal lines."""
    # Load the JSON data for VPA-0000093
    try:
        with open('0526-Raku export- VCT GE.utf8.json', 'r', encoding='utf-8') as f:
            entries = json.load(f)
    except Exception as e:
        print(f"Error loading input file: {str(e)}")
        sys.exit(1)
    
    # Find the entry for VPA-0000093
    vpa_0000093_entry = None
    for entry in entries:
        if entry.get('voucher_no') == 'VPA-0000093':
            vpa_0000093_entry = entry
            break
    
    if not vpa_0000093_entry:
        print("Entry for VPA-0000093 not found in the JSON file.")
        sys.exit(1)
    
    # Print the entry data to verify the description fields
    print("Entry data for VPA-0000093:")
    print(f"Main description: '{vpa_0000093_entry.get('description', '')}'")
    print(f"Debit free_field: '{vpa_0000093_entry.get('debit', {}).get('free_field', '')}'")
    print(f"Credit free_field: '{vpa_0000093_entry.get('credit', {}).get('free_field', '')}'")
    
    # Create journal lines for debit and credit
    debit_line = create_journal_line(vpa_0000093_entry, "debit")
    credit_line = create_journal_line(vpa_0000093_entry, "credit")
    
    # Print the description fields from the journal lines
    print("\nJournal line descriptions:")
    print(f"Debit line description: '{debit_line['Description']}'")
    print(f"Credit line description: '{credit_line['Description']}'")
    
    # Check if the descriptions are properly populated
    if not debit_line['Description']:
        print("\nISSUE DETECTED: Debit line description is empty!")
        print("This could be because:")
        print("1. The main description field is empty")
        print("2. The debit free_field is empty")
        print("3. The debit_description field is empty (if it exists)")
    else:
        print("\nDebit line description is properly populated.")
    
    if not credit_line['Description'] or credit_line['Description'] == "Consolidated from 1 entries":
        print("\nISSUE DETECTED: Credit line description is empty or only contains consolidation note!")
        print("This could be because:")
        print("1. The main description field is empty")
        print("2. The credit free_field is empty")
        print("3. The credit_description field is empty (if it exists)")
    else:
        print("\nCredit line description is properly populated.")

if __name__ == "__main__":
    test_description_population()
