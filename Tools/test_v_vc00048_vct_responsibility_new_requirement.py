#!/usr/bin/env python3
"""
Test script for V-VC00048 VCT Responsibility New Requirement

This script tests the updated implementation where V-VC00048 entries with non-VCT cost centers
now create VCT responsibility entries to record expense responsibility in VCT company.

Expected behavior:
1. V-VC00048 + non-VCT cost center (e.g., VCA) → Creates VCT responsibility entries
2. V-VC00048 + VCT cost center → NO VCT responsibility entries (prevent duplicates)
3. Other vendors → No change to existing logic
"""

import sys
import os
import json
from typing import Dict, List, Any

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vct_responsibility_consolidation import collect_vct_responsibility_candidates

def test_vct_responsibility_inclusion():
    """Test that V-VC00048 entries with non-VCT cost centers are included for VCT responsibility"""
    print("\n=== Testing VCT Responsibility Inclusion for V-VC00048 ===")
    
    # Test data with V-VC00048 entries
    test_entries = [
        # V-VC00048 with VCA cost center - SHOULD be included
        {
            "voucher_no": "APA-0000401",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCA.1342G",
                "amount": 1000.0
            }
        },
        # V-VC00048 with VCP cost center - SHOULD be included
        {
            "voucher_no": "APA-0000402",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCP.1234",
                "amount": 2000.0
            }
        },
        # V-VC00048 with VCT cost center - SHOULD be excluded
        {
            "voucher_no": "APA-0000403",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCT.1692G",
                "amount": 3000.0
            }
        },
        # Non-V-VC00048 vendor - SHOULD be excluded
        {
            "voucher_no": "APA-0000404",
            "credit": {
                "vendor_code": "OTHER-VENDOR",
                "department": "VCA.5678",
                "amount": 4000.0
            }
        }
    ]
    
    # Collect VCT responsibility candidates
    candidates = collect_vct_responsibility_candidates(test_entries)
    
    # Check results
    print(f"\nTotal vouchers with VCT responsibility candidates: {len(candidates)}")
    
    # Expected: APA-0000401 and APA-0000402 should be included
    expected_vouchers = ["APA-0000401", "APA-0000402"]
    
    success = True
    for voucher in expected_vouchers:
        if voucher in candidates:
            print(f"✓ {voucher}: Correctly included for VCT responsibility (V-VC00048 with non-VCT cost center)")
        else:
            print(f"✗ {voucher}: ERROR - Should be included for VCT responsibility")
            success = False
    
    # Check that VCT cost center entry is excluded
    if "APA-0000403" not in candidates:
        print(f"✓ APA-0000403: Correctly excluded (V-VC00048 with VCT cost center)")
    else:
        print(f"✗ APA-0000403: ERROR - Should be excluded from VCT responsibility")
        success = False
    
    # Check that non-V-VC00048 vendor is excluded
    if "APA-0000404" not in candidates:
        print(f"✓ APA-0000404: Correctly excluded (non-V-VC00048 vendor)")
    else:
        print(f"✗ APA-0000404: ERROR - Should be excluded from VCT responsibility")
        success = False
    
    return success

def test_vct_responsibility_entry_structure():
    """Test the structure of VCT responsibility entries"""
    print("\n=== Testing VCT Responsibility Entry Structure ===")
    
    # Import the function to create entries
    from core.vct_responsibility_consolidation import create_consolidated_vct_responsibility_entries
    
    # Test entry with V-VC00048 and VCA cost center
    test_entries = [{
        "voucher_no": "APA-0000401",
        "External_Document_No": "20250502",
        "Document_Date": "2025/05/02",
        "description": "AUTO IQ AUTOMOTIVE CYBERSECURITY SUMMIT",
        "credit": {
            "vendor_code": "V-VC00048",
            "department": "VCA.1342G",
            "amount": 6534.55,
            "currency": "R-USD",
            "Remarks": "Events"
        }
    }]
    
    # Mock the post_journal_line function to capture the payloads
    posted_lines = []
    
    def mock_post_journal_line(journal_line, access_token, rate_limiter, max_retries):
        posted_lines.append(journal_line.copy())
        return True, {"success": True}
    
    # Replace the import in the module
    import core.vct_responsibility_consolidation
    original_post = core.vct_responsibility_consolidation.post_journal_line
    core.vct_responsibility_consolidation.post_journal_line = mock_post_journal_line
    
    try:
        # Create VCT responsibility entries
        success, failure = create_consolidated_vct_responsibility_entries(
            test_entries, 
            "mock_token", 
            None,  # rate_limiter
            {},    # used_doc_numbers
            {}     # external_doc_no_counter
        )
        
        # Check that we got 2 entries (1 debit + 1 credit)
        if len(posted_lines) == 2:
            print(f"✓ Created correct number of entries: {len(posted_lines)}")
        else:
            print(f"✗ ERROR - Expected 2 entries, got {len(posted_lines)}")
            return False
        
        # Check debit line structure
        debit_line = posted_lines[0]
        print("\nDebit Line Structure:")
        print(f"  Account Type: {debit_line.get('Account_Type')} (expected: G/L Account)")
        print(f"  Account No: {debit_line.get('Account_No')} (expected: 18600-10)")
        print(f"  Description: {debit_line.get('Description')}")
        print(f"  Department Code: {debit_line.get('Shortcut_Dimension_2_Code')} (expected: VCT.9999)")
        print(f"  Intercompany Code: {debit_line.get('ShortcutDimCode3')} (expected: VCA)")
        print(f"  Amount: {debit_line.get('Amount')} (expected: 6534.55)")
        print(f"  Currency: {debit_line.get('Currency_Code')} (expected: R-USD)")
        
        # Verify debit line
        debit_correct = (
            debit_line.get('Account_Type') == 'G/L Account' and
            debit_line.get('Account_No') == '18600-10' and
            debit_line.get('Shortcut_Dimension_2_Code') == 'VCT.9999' and
            debit_line.get('ShortcutDimCode3') == 'VCA' and
            debit_line.get('Amount') == 6534.55 and
            debit_line.get('Currency_Code') == 'R-USD' and
            'VCA.1342G' in debit_line.get('Description', '')
        )
        
        if debit_correct:
            print("✓ Debit line structure is correct")
        else:
            print("✗ ERROR - Debit line structure is incorrect")
            return False
        
        # Check credit line structure
        credit_line = posted_lines[1]
        print("\nCredit Line Structure:")
        print(f"  Account Type: {credit_line.get('Account_Type')} (expected: Vendor)")
        print(f"  Account No: {credit_line.get('Account_No')} (expected: V-VC00048)")
        print(f"  Description: {credit_line.get('Description')}")
        print(f"  Department Code: {credit_line.get('Shortcut_Dimension_2_Code')} (expected: VCT.9999)")
        print(f"  Intercompany Code: {credit_line.get('ShortcutDimCode3')} (expected: empty)")
        print(f"  Amount: {credit_line.get('Amount')} (expected: -6534.55)")
        print(f"  Currency: {credit_line.get('Currency_Code')} (expected: R-USD)")
        
        # Verify credit line
        credit_correct = (
            credit_line.get('Account_Type') == 'Vendor' and
            credit_line.get('Account_No') == 'V-VC00048' and
            credit_line.get('Shortcut_Dimension_2_Code') == 'VCT.9999' and
            credit_line.get('ShortcutDimCode3') == '' and
            credit_line.get('Amount') == -6534.55 and
            credit_line.get('Currency_Code') == 'R-USD'
        )
        
        if credit_correct:
            print("✓ Credit line structure is correct")
        else:
            print("✗ ERROR - Credit line structure is incorrect")
            return False
        
        return True
        
    finally:
        # Restore original function
        core.vct_responsibility_consolidation.post_journal_line = original_post

def test_consolidation_logic():
    """Test that multiple V-VC00048 entries for same voucher are consolidated"""
    print("\n=== Testing Consolidation Logic ===")
    
    # Test data with multiple V-VC00048 entries for same voucher
    test_entries = [
        {
            "voucher_no": "APA-0000401",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCA.1342G",
                "amount": 6534.55
            }
        },
        {
            "voucher_no": "APA-0000401",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCA.1342G",
                "amount": 750.00
            }
        }
    ]
    
    # Collect VCT responsibility candidates
    candidates = collect_vct_responsibility_candidates(test_entries)
    
    # Check that both entries are collected for the same voucher
    if "APA-0000401" in candidates:
        entries_count = len(candidates["APA-0000401"])
        print(f"✓ Voucher APA-0000401 has {entries_count} entries for consolidation")
        
        if entries_count == 2:
            print("✓ Both V-VC00048 entries collected for consolidation")
            return True
        else:
            print(f"✗ ERROR - Expected 2 entries, got {entries_count}")
            return False
    else:
        print("✗ ERROR - Voucher APA-0000401 not found in candidates")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("V-VC00048 VCT Responsibility New Requirement Test")
    print("=" * 60)
    
    tests = [
        ("VCT Responsibility Inclusion", test_vct_responsibility_inclusion),
        ("VCT Responsibility Entry Structure", test_vct_responsibility_entry_structure),
        ("Consolidation Logic", test_consolidation_logic)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ ERROR in {test_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! V-VC00048 VCT responsibility new requirement is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
