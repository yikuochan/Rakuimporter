#!/usr/bin/env python3
"""
Detailed analysis of OBA-0000027 voucher balance issue.
This tool will examine the specific entries for this voucher to understand
why it has a 420.00 NTD difference between debit and credit.
"""

import sys
import os
import json
import tempfile
from decimal import Decimal

# Add the parent directory to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.csv_to_json_converter import convert_csv_to_json as original_convert
from core.csv_to_json_converter_enhanced import convert_csv_to_json as enhanced_convert

def analyze_oba_0000027():
    """Analyze OBA-0000027 voucher in detail."""
    
    print("=" * 80)
    print("DETAILED ANALYSIS OF OBA-0000027 VOUCHER")
    print("=" * 80)
    
    # Test file path
    test_csv = "Data/Testing Data/0523-Raku export-VCT PR-1.utf8.csv"
    
    if not os.path.exists(test_csv):
        print(f"❌ Test file not found: {test_csv}")
        return
    
    print(f"📁 Using test file: {test_csv}")
    
    # Convert with enhanced converter
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_file:
        temp_json_path = temp_file.name
    
    try:
        print("\n📝 Converting with enhanced converter...")
        entry_count = enhanced_convert(test_csv, temp_json_path)
        print(f"✅ Generated {entry_count} entries")
        
        # Load the results
        with open(temp_json_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        # Filter OBA-0000027 entries
        oba_entries = [entry for entry in entries if entry.get('voucher_no') == 'OBA-0000027']
        
        print(f"\n🔍 Found {len(oba_entries)} entries for OBA-0000027:")
        print("-" * 60)
        
        total_debit = Decimal('0')
        total_credit = Decimal('0')
        
        for i, entry in enumerate(oba_entries, 1):
            debit_amount = Decimal(str(entry['debit']['amount'])) if entry['debit']['amount'] else Decimal('0')
            credit_amount = Decimal(str(entry['credit']['amount'])) if entry['credit']['amount'] else Decimal('0')
            
            total_debit += debit_amount
            total_credit += credit_amount
            
            print(f"Entry {i}:")
            print(f"  External_Document_No: {entry.get('External_Document_No', 'N/A')}")
            print(f"  Description: {entry.get('description', 'N/A')}")
            
            if debit_amount > 0:
                print(f"  DEBIT:  {debit_amount:>12} {entry['debit']['currency']}")
                print(f"    Account: {entry['debit']['account']}")
                print(f"    Department: {entry['debit']['department']}")
                print(f"    GL Account: {entry['debit']['gl_account']}")
            else:
                print(f"  DEBIT:  {0:>12} (empty)")
            
            if credit_amount > 0:
                print(f"  CREDIT: {credit_amount:>12} {entry['credit']['currency']}")
                print(f"    Account: {entry['credit']['account']}")
                print(f"    Department: {entry['credit']['department']}")
                print(f"    GL Account: {entry['credit']['gl_account']}")
                print(f"    Vendor Code: {entry['credit']['vendor_code']}")
                if entry['credit'].get('consolidated'):
                    print(f"    ⚡ CONSOLIDATED from {entry['credit'].get('original_entries_count', 'N/A')} entries")
                    print(f"    Raw total before rounding: {entry['credit'].get('raw_total_before_rounding', 'N/A')}")
            else:
                print(f"  CREDIT: {0:>12} (empty)")
            
            print()
        
        print("=" * 60)
        print("SUMMARY:")
        print(f"Total DEBIT:  {total_debit:>12} NTD")
        print(f"Total CREDIT: {total_credit:>12} NTD")
        difference = total_credit - total_debit
        print(f"Difference:   {difference:>12} NTD")
        
        if difference == 0:
            print("✅ BALANCED!")
        else:
            print(f"❌ UNBALANCED by {abs(difference)} NTD")
            
            # Analyze the difference
            print(f"\n🔍 ANALYZING THE {abs(difference)} NTD DIFFERENCE:")
            
            # Check if it's a rounding issue
            for entry in oba_entries:
                if entry['credit'].get('consolidated') and entry['credit'].get('raw_total_before_rounding'):
                    raw_total = Decimal(str(entry['credit']['raw_total_before_rounding']))
                    rounded_total = Decimal(str(entry['credit']['amount']))
                    rounding_diff = rounded_total - raw_total
                    if rounding_diff != 0:
                        print(f"  Rounding difference in consolidated entry: {rounding_diff}")
            
            # Check for special handling
            print(f"  Looking for special handling in code...")
            
            # Check if there's a hardcoded amount
            for entry in oba_entries:
                if entry['credit'].get('consolidated') and entry['credit']['amount'] == 83868:
                    print(f"  ⚠️  Found hardcoded amount 83868 in consolidated entry!")
                    print(f"      This suggests special handling for OBA-0000027")
        
        print("\n🔍 DETAILED ENTRY BREAKDOWN:")
        debit_entries = [e for e in oba_entries if e['debit']['amount'] > 0]
        credit_entries = [e for e in oba_entries if e['credit']['amount'] > 0]
        
        print(f"\nDEBIT ENTRIES ({len(debit_entries)}):")
        for entry in debit_entries:
            print(f"  {entry['debit']['amount']:>10} {entry['debit']['currency']} - {entry['debit']['account']} - {entry.get('description', 'N/A')}")
        
        print(f"\nCREDIT ENTRIES ({len(credit_entries)}):")
        for entry in credit_entries:
            consolidated_note = " (CONSOLIDATED)" if entry['credit'].get('consolidated') else ""
            print(f"  {entry['credit']['amount']:>10} {entry['credit']['currency']} - {entry['credit']['account']}{consolidated_note}")
            if entry['credit'].get('consolidated'):
                print(f"    └─ From {entry['credit'].get('original_entries_count', 'N/A')} original entries")
    
    finally:
        # Clean up
        try:
            os.remove(temp_json_path)
        except:
            pass

if __name__ == "__main__":
    analyze_oba_0000027()
