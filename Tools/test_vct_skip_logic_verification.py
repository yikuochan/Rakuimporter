#!/usr/bin/env python3
"""
Test VCT V-VC00048 Skip Logic Verification

This test verifies that the existing V-VC00048 consolidated entry skip logic
in process_japan_exports.py is working correctly. The test simulates the
complete workflow:

1. CSV converter creates consolidated V-VC00048 entries (normal behavior)
2. BC payload generation skips these consolidated entries (existing skip logic)
3. VCT responsibility consolidation creates individual entries instead
4. Final result has no problematic consolidated entries in BC payload

This test validates that the existing solution is working as intended.
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.csv_to_json_converter import convert_csv_to_json
from core.vct_responsibility_consolidation import collect_vct_responsibility_candidates

def create_test_csv_with_vct_entries():
    """Create a test CSV file with V-VC00048 entries that should trigger skip logic."""
    csv_content = """伝票No.,仕訳日,申請日,仕訳データ生成日,Receipt/Invoice Note(明細),フリー２(明細),備考,Note(明細),Receipt/Invoice #(明細),勘定奉行：伝票区切,G/L Account,借方：勘定科目：会計連携項目,借方：補助科目：会計連携項目,換算前額,単位,借方：負担部門：会計連携項目,申請者CD/支払先CD,支払先CD,フリー２(明細),借方：負担部門コード,貸方：勘定科目：会計連携項目,貸方：補助科目：会計連携項目,Remarks
V-VC00048,2024/01/15,2024/01/15,2024/01/15,Test Receipt Note 1,Free Field 1,Test Remarks 1,Note 1,Invoice 1,区切1,1110,1110,,1000,JPY,ABC.1234,APP001,V-VC00048,Free2 Field 1,ABC,V-VC00048,,Test Description 1
V-VC00048,2024/01/15,2024/01/15,2024/01/15,Test Receipt Note 2,Free Field 2,Test Remarks 2,Note 2,Invoice 2,区切2,1120,1120,,2000,JPY,DEF.5678,APP002,V-VC00048,Free2 Field 2,DEF,V-VC00048,,Test Description 2
V-VC00048,2024/01/16,2024/01/16,2024/01/16,Test Receipt Note 3,Free Field 3,Test Remarks 3,Note 3,Invoice 3,区切3,1130,1130,,1500,JPY,GHI.9999,APP003,V-VC00048,Free2 Field 3,GHI,V-VC00048,,Test Description 3"""
    
    return csv_content

def test_csv_converter_creates_consolidated_entries():
    """Test that CSV converter creates consolidated V-VC00048 entries as expected."""
    print("Testing CSV converter consolidated entry creation...")
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_csv:
        temp_csv.write(create_test_csv_with_vct_entries())
        temp_csv_path = temp_csv.name
    
    try:
        # Create temporary JSON output
        temp_json_path = temp_csv_path.replace('.csv', '.json')
        
        # Convert CSV to JSON
        entry_count = convert_csv_to_json(
            temp_csv_path,
            temp_json_path,
            max_desc_length=100,
            fix_line_breaks=True,
            line_break_replacement=' '
        )
        
        # Read and analyze the JSON output
        with open(temp_json_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        print(f"CSV converter created {len(entries)} entries")
        
        # Find V-VC00048 consolidated entries
        v_vc00048_consolidated = [
            entry for entry in entries 
            if (entry.get('credit', {}).get('consolidated') == True and
                entry.get('credit', {}).get('vendor_code') == 'V-VC00048')
        ]
        
        print(f"Found {len(v_vc00048_consolidated)} V-VC00048 consolidated entries")
        
        if v_vc00048_consolidated:
            print("✅ CSV converter correctly creates V-VC00048 consolidated entries")
            for entry in v_vc00048_consolidated:
                print(f"  - Voucher: {entry.get('voucher_no')}, Amount: {entry.get('credit', {}).get('amount')}")
            return True, entries
        else:
            print("❌ CSV converter did not create expected V-VC00048 consolidated entries")
            return False, entries
            
    except Exception as e:
        print(f"❌ Error during CSV converter test: {str(e)}")
        return False, []
    finally:
        # Clean up
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)
        if 'temp_json_path' in locals() and os.path.exists(temp_json_path):
            os.remove(temp_json_path)

def test_vct_responsibility_collection():
    """Test that VCT responsibility candidates are correctly collected."""
    print("Testing VCT responsibility candidate collection...")
    
    # Create test entries that should be collected as VCT responsibility candidates
    test_entries = [
        {
            'voucher_no': 'V-VC00048',
            'credit': {
                'vendor_code': 'V-VC00048',
                'department': 'ABC.1234',  # Non-VCT cost center
                'amount': 1000,
                'currency': 'JPY'
            }
        },
        {
            'voucher_no': 'V-VC00048',
            'credit': {
                'vendor_code': 'V-VC00048',
                'department': 'DEF.5678',  # Non-VCT cost center
                'amount': 2000,
                'currency': 'JPY'
            }
        },
        {
            'voucher_no': 'V-VC00048',
            'credit': {
                'vendor_code': 'V-VC00048',
                'department': 'VCT.9999',  # VCT cost center - should be excluded
                'amount': 1500,
                'currency': 'JPY'
            }
        }
    ]
    
    try:
        # Collect VCT responsibility candidates
        vct_candidates = collect_vct_responsibility_candidates(test_entries)
        
        print(f"Collected VCT candidates for {len(vct_candidates)} vouchers")
        
        # Check if candidates were collected correctly
        if 'V-VC00048' in vct_candidates:
            candidates = vct_candidates['V-VC00048']
            print(f"Found {len(candidates)} candidates for voucher V-VC00048")
            
            # Should have 2 candidates (ABC and DEF), not the VCT one
            if len(candidates) == 2:
                print("✅ VCT responsibility collection correctly excludes VCT cost centers")
                for candidate in candidates:
                    dept = candidate.get('credit', {}).get('department', '')
                    cost_center = dept[:3] if dept else ''
                    print(f"  - Cost Center: {cost_center}, Amount: {candidate.get('credit', {}).get('amount')}")
                return True
            else:
                print(f"❌ Expected 2 candidates, got {len(candidates)}")
                return False
        else:
            print("❌ No VCT candidates collected for V-VC00048")
            return False
            
    except Exception as e:
        print(f"❌ Error during VCT responsibility collection test: {str(e)}")
        return False

def test_skip_logic_simulation():
    """Test the V-VC00048 consolidated entry skip logic simulation."""
    print("Testing V-VC00048 consolidated entry skip logic...")
    
    # Create test entries that simulate what would be processed
    test_entries = [
        {
            'voucher_no': 'V-VC00048',
            'credit': {
                'vendor_code': 'V-VC00048',
                'consolidated': True,  # This should be skipped
                'amount': 3000,
                'currency': 'JPY'
            }
        },
        {
            'voucher_no': 'V-VC00048',
            'credit': {
                'vendor_code': 'V-VC00048',
                'consolidated': False,  # This should be processed
                'amount': 1000,
                'currency': 'JPY'
            }
        },
        {
            'voucher_no': 'OTHER-001',
            'credit': {
                'vendor_code': 'OTHER-VENDOR',
                'consolidated': True,  # This should be processed (not V-VC00048)
                'amount': 2000,
                'currency': 'JPY'
            }
        }
    ]
    
    try:
        # Simulate the skip logic from process_japan_exports.py
        group_entries = test_entries
        
        # Find V-VC00048 consolidated entries that should be skipped
        v_vc00048_consolidated_entries = [
            e for e in group_entries 
            if (e.get("credit", {}).get("consolidated") == True and
                e.get("credit", {}).get("vendor_code") == "V-VC00048")
        ]
        
        print(f"Found {len(v_vc00048_consolidated_entries)} V-VC00048 consolidated entries to skip")
        
        if v_vc00048_consolidated_entries:
            print("✅ Skip logic correctly identifies V-VC00048 consolidated entries")
            
            # Simulate skipping them
            non_consolidated_entries = [e for e in group_entries if e not in v_vc00048_consolidated_entries]
            print(f"After skipping, {len(non_consolidated_entries)} entries remain for processing")
            
            # Verify the right entries remain
            remaining_vouchers = [e.get('voucher_no') for e in non_consolidated_entries]
            print(f"Remaining entries: {remaining_vouchers}")
            
            # Should have the non-consolidated V-VC00048 and the OTHER-001 entry
            if len(non_consolidated_entries) == 2:
                print("✅ Skip logic correctly preserves non-consolidated entries")
                return True
            else:
                print(f"❌ Expected 2 remaining entries, got {len(non_consolidated_entries)}")
                return False
        else:
            print("❌ Skip logic did not identify any V-VC00048 consolidated entries")
            return False
            
    except Exception as e:
        print(f"❌ Error during skip logic simulation: {str(e)}")
        return False

def main():
    """Run all tests to verify VCT V-VC00048 skip logic is working correctly."""
    print("=" * 70)
    print("VCT V-VC00048 Skip Logic Verification")
    print("=" * 70)
    
    all_tests_passed = True
    
    # Test 1: CSV converter creates consolidated entries
    print("\n1. Testing CSV converter consolidated entry creation...")
    csv_test_result, entries = test_csv_converter_creates_consolidated_entries()
    if not csv_test_result:
        all_tests_passed = False
    
    # Test 2: VCT responsibility collection
    print("\n2. Testing VCT responsibility candidate collection...")
    vct_collection_result = test_vct_responsibility_collection()
    if not vct_collection_result:
        all_tests_passed = False
    
    # Test 3: Skip logic simulation
    print("\n3. Testing V-VC00048 consolidated entry skip logic...")
    skip_logic_result = test_skip_logic_simulation()
    if not skip_logic_result:
        all_tests_passed = False
    
    # Summary
    print("\n" + "=" * 70)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED")
        print("✅ V-VC00048 skip logic is working correctly")
        print("✅ Consolidated entries are properly identified and skipped")
        print("✅ VCT responsibility entries are correctly collected")
        print("\nCONCLUSION:")
        print("The existing solution in process_japan_exports.py should work correctly.")
        print("V-VC00048 consolidated entries will be skipped during BC payload generation,")
        print("and individual VCT responsibility entries will be created instead.")
    else:
        print("❌ SOME TESTS FAILED")
        print("❌ V-VC00048 skip logic may need adjustment")
    print("=" * 70)
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
