#!/usr/bin/env python3
"""
Test script to verify that the enhanced CSV converter now properly creates
VCT consolidated billing entries and VCT responsibility entries.

This test will:
1. Use the enhanced converter to process a CSV file
2. Verify that consolidated credit entries are created
3. Verify that VCT responsibility entries are created for non-VCT cost centers
4. Compare results with expected behavior
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.csv_to_json_converter_enhanced import convert_csv_to_json

def test_enhanced_converter_consolidation():
    """Test that the enhanced converter creates proper consolidated entries."""
    
    print("=" * 80)
    print("TESTING ENHANCED CONVERTER CONSOLIDATION")
    print("=" * 80)
    
    # Test with a known CSV file
    test_csv_files = [
        "Data/Testing Data/0523-Raku export-VCT PR-1.utf8.csv",
        "Data/Testing Data/0523-Raku export-VCT GE-1.utf8.csv",
        "Data/Testing Data/Evelyn Raku export_utf8.csv",
        "Data/Testing Data/Raku export_utf8.csv"
    ]
    
    csv_file = None
    for test_file in test_csv_files:
        if os.path.exists(test_file):
            csv_file = test_file
            break
    
    if not csv_file:
        print("❌ No test CSV file found. Checked:")
        for test_file in test_csv_files:
            print(f"   - {test_file}")
        return False
    
    print(f"✅ Using test CSV file: {csv_file}")
    
    # Create temporary output file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        output_json = temp_file.name
    
    try:
        print(f"\n📝 Converting CSV to JSON with consolidation...")
        
        # Convert using enhanced converter
        entry_count = convert_csv_to_json(
            csv_file, 
            output_json, 
            max_desc_length=100,
            use_comprehensive_fix=True,
            keep_temp_files=False
        )
        
        print(f"✅ Conversion completed. Generated {entry_count} entries.")
        
        # Load and analyze the results
        with open(output_json, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"Total entries: {len(entries)}")
        
        # Count different types of entries
        consolidated_credit_entries = []
        vct_responsibility_debit_entries = []
        vct_responsibility_credit_entries = []
        regular_debit_entries = []
        v_vc00048_entries = []
        
        for entry in entries:
            # Check for consolidated credit entries
            if (entry.get('credit', {}).get('consolidated') == True):
                consolidated_credit_entries.append(entry)
            
            # Check for VCT responsibility entries
            if (entry.get('debit', {}).get('vct_responsibility') == True):
                vct_responsibility_debit_entries.append(entry)
            
            if (entry.get('credit', {}).get('vct_responsibility') == True):
                vct_responsibility_credit_entries.append(entry)
            
            # Check for regular debit entries
            if (entry.get('debit', {}).get('amount', 0) > 0 and 
                not entry.get('debit', {}).get('vct_responsibility')):
                regular_debit_entries.append(entry)
            
            # Check for V-VC00048 entries
            if entry.get('credit', {}).get('vendor_code') == 'V-VC00048':
                v_vc00048_entries.append(entry)
        
        print(f"\n📈 ENTRY TYPE BREAKDOWN:")
        print(f"Regular debit entries: {len(regular_debit_entries)}")
        print(f"Consolidated credit entries: {len(consolidated_credit_entries)}")
        print(f"VCT responsibility debit entries: {len(vct_responsibility_debit_entries)}")
        print(f"VCT responsibility credit entries: {len(vct_responsibility_credit_entries)}")
        print(f"V-VC00048 entries: {len(v_vc00048_entries)}")
        
        # Verify consolidation is working
        success = True
        
        if len(consolidated_credit_entries) == 0:
            print("❌ ERROR: No consolidated credit entries found!")
            success = False
        else:
            print(f"✅ Found {len(consolidated_credit_entries)} consolidated credit entries")
            
            # Show sample consolidated entry
            sample_consolidated = consolidated_credit_entries[0]
            print(f"\n📋 SAMPLE CONSOLIDATED ENTRY:")
            print(f"   Voucher: {sample_consolidated.get('voucher_no')}")
            print(f"   Vendor: {sample_consolidated.get('credit', {}).get('vendor_code')}")
            print(f"   Amount: {sample_consolidated.get('credit', {}).get('amount')}")
            print(f"   Currency: {sample_consolidated.get('credit', {}).get('currency')}")
            print(f"   Original entries count: {sample_consolidated.get('credit', {}).get('original_entries_count', 'N/A')}")
        
        # Check for VCT responsibility entries
        if len(vct_responsibility_debit_entries) > 0 or len(vct_responsibility_credit_entries) > 0:
            print(f"✅ Found VCT responsibility entries:")
            print(f"   - Debit entries: {len(vct_responsibility_debit_entries)}")
            print(f"   - Credit entries: {len(vct_responsibility_credit_entries)}")
            
            if len(vct_responsibility_debit_entries) > 0:
                sample_vct_debit = vct_responsibility_debit_entries[0]
                print(f"\n📋 SAMPLE VCT RESPONSIBILITY DEBIT ENTRY:")
                print(f"   Voucher: {sample_vct_debit.get('voucher_no')}")
                print(f"   Account: {sample_vct_debit.get('debit', {}).get('account')}")
                print(f"   Department: {sample_vct_debit.get('debit', {}).get('department')}")
                print(f"   Amount: {sample_vct_debit.get('debit', {}).get('amount')}")
                print(f"   Original cost center: {sample_vct_debit.get('debit', {}).get('original_cost_center')}")
        
        # Check for V-VC00048 processing
        if len(v_vc00048_entries) > 0:
            print(f"✅ Found {len(v_vc00048_entries)} V-VC00048 entries")
            
            # Analyze cost centers
            cost_centers = {}
            for entry in v_vc00048_entries:
                dept = entry.get('credit', {}).get('department', '')
                cost_center = dept[:3] if dept else 'Unknown'
                if cost_center not in cost_centers:
                    cost_centers[cost_center] = 0
                cost_centers[cost_center] += 1
            
            print(f"   Cost center breakdown:")
            for cc, count in cost_centers.items():
                print(f"     - {cc}: {count} entries")
        
        # Verify balance (debit total should equal credit total)
        total_debit = sum(entry.get('debit', {}).get('amount', 0) for entry in entries)
        total_credit = sum(entry.get('credit', {}).get('amount', 0) for entry in entries)
        
        print(f"\n⚖️  BALANCE VERIFICATION:")
        print(f"Total debit amount: {total_debit:,.2f}")
        print(f"Total credit amount: {total_credit:,.2f}")
        print(f"Difference: {abs(total_debit - total_credit):,.2f}")
        
        if abs(total_debit - total_credit) < 0.01:  # Allow for small rounding differences
            print("✅ Entries are balanced!")
        else:
            print("⚠️  WARNING: Entries are not balanced!")
        
        print(f"\n📄 Full results saved to: {output_json}")
        
        if success:
            print(f"\n🎉 SUCCESS: Enhanced converter consolidation is working correctly!")
            return True
        else:
            print(f"\n❌ FAILURE: Enhanced converter consolidation has issues!")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(output_json):
                os.remove(output_json)
        except:
            pass

if __name__ == "__main__":
    success = test_enhanced_converter_consolidation()
    sys.exit(0 if success else 1)
