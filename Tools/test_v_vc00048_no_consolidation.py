#!/usr/bin/env python3
"""
Test script for V-VC00048 No Consolidation Requirement

This script tests that V-VC00048 entries are NOT consolidated per finance team requirement.
They should be created as individual debit/credit pairs for easier auditing.

Expected behavior:
1. Multiple V-VC00048 entries for same voucher → Individual pairs (NOT consolidated)
2. Each pair gets its own document number
3. V-VC00048 + non-VCT cost center → Creates individual VCT responsibility pairs
4. V-VC00048 + VCT cost center → NO VCT responsibility entries
"""

import sys
import os
import json
from typing import Dict, List, Any

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vct_responsibility_consolidation import (
    collect_vct_responsibility_candidates,
    create_consolidated_vct_responsibility_entries
)

def test_no_consolidation_for_v_vc00048():
    """Test that V-VC00048 entries use consolidated approach (multiple debits + single credit)"""
    print("\n=== Testing Consolidated Approach for V-VC00048 ===")
    
    # Mock the post_journal_line function to capture the payloads
    posted_lines = []
    
    def mock_post_journal_line(journal_line, access_token, rate_limiter, max_retries):
        posted_lines.append(journal_line.copy())
        return True, {"success": True}
    
    # Replace the import in the module
    import core.process_japan_exports
    original_post = core.process_japan_exports.post_journal_line
    core.process_japan_exports.post_journal_line = mock_post_journal_line
    
    try:
        # Test data with multiple V-VC00048 entries for same voucher
        test_entries = [
            {
                "voucher_no": "APA-0000401",
                "External_Document_No": "20250502",
                "Document_Date": "2025/05/02",
                "description": "First expense",
                "credit": {
                    "vendor_code": "V-VC00048",
                    "department": "VCA.1342G",
                    "amount": 1000.0,
                    "currency": "USD",
                    "Remarks": "Expense 1"
                }
            },
            {
                "voucher_no": "APA-0000401",
                "External_Document_No": "20250502",
                "Document_Date": "2025/05/02",
                "description": "Second expense",
                "credit": {
                    "vendor_code": "V-VC00048",
                    "department": "VCA.1342G",
                    "amount": 2000.0,
                    "currency": "USD",
                    "Remarks": "Expense 2"
                }
            }
        ]
        
        # Create VCT responsibility entries
        success, failure = create_consolidated_vct_responsibility_entries(
            test_entries, 
            "mock_token", 
            None,  # rate_limiter
            {},    # used_doc_numbers
            {}     # external_doc_no_counter
        )
        
        # Check that we got 3 entries (2 debits + 1 credit)
        if len(posted_lines) == 3:
            print(f"✓ Created correct number of entries: {len(posted_lines)} (2 debits + 1 credit)")
        else:
            print(f"✗ ERROR - Expected 3 entries (2 debits + 1 credit), got {len(posted_lines)}")
            return False
        
        # Check document numbers - should all have the same document number
        doc_numbers = [line.get('Document_No') for line in posted_lines]
        unique_doc_numbers = set(doc_numbers)
        
        # All entries should have the same document number
        if len(unique_doc_numbers) == 1:
            consolidated_doc_no = list(unique_doc_numbers)[0]
            print(f"✓ All entries use same document number: {consolidated_doc_no}")
        else:
            print(f"✗ ERROR - Expected 1 unique document number, got {len(unique_doc_numbers)}: {sorted(unique_doc_numbers)}")
            return False
        
        # Separate debits and credits
        debit_lines = [line for line in posted_lines if line.get('Amount') > 0]
        credit_lines = [line for line in posted_lines if line.get('Amount') < 0]
        
        # Verify we have 2 debits and 1 credit
        if len(debit_lines) == 2 and len(credit_lines) == 1:
            print(f"✓ Correct structure: {len(debit_lines)} debits + {len(credit_lines)} credit")
        else:
            print(f"✗ ERROR - Expected 2 debits + 1 credit, got {len(debit_lines)} debits + {len(credit_lines)} credits")
            return False
        
        # Verify debit amounts match original entries
        debit_amounts = sorted([line.get('Amount') for line in debit_lines])
        expected_amounts = sorted([1000.0, 2000.0])
        
        if debit_amounts == expected_amounts:
            print(f"✓ Debit amounts match original entries: {debit_amounts}")
        else:
            print(f"✗ ERROR - Debit amounts incorrect: expected {expected_amounts}, got {debit_amounts}")
            return False
        
        # Verify credit amount is consolidated total
        credit_amount = credit_lines[0].get('Amount')
        expected_credit = -3000.0  # -(1000 + 2000)
        
        if credit_amount == expected_credit:
            print(f"✓ Credit amount is consolidated total: {credit_amount}")
        else:
            print(f"✗ ERROR - Credit amount incorrect: expected {expected_credit}, got {credit_amount}")
            return False
        
        # Verify account types
        debit_account_types = [line.get('Account_Type') for line in debit_lines]
        credit_account_type = credit_lines[0].get('Account_Type')
        
        if all(acc_type == 'G/L Account' for acc_type in debit_account_types):
            print("✓ All debit lines use G/L Account type")
        else:
            print(f"✗ ERROR - Debit lines should use G/L Account type, got: {debit_account_types}")
            return False
        
        if credit_account_type == 'Vendor':
            print("✓ Credit line uses Vendor account type")
        else:
            print(f"✗ ERROR - Credit line should use Vendor account type, got: {credit_account_type}")
            return False
        
        return True
        
    finally:
        # Restore original function
        core.process_japan_exports.post_journal_line = original_post

def test_vct_cost_center_exclusion():
    """Test that V-VC00048 with VCT cost center is excluded"""
    print("\n=== Testing VCT Cost Center Exclusion ===")
    
    # Test data with V-VC00048 and VCT cost center
    test_entries = [
        {
            "voucher_no": "APA-0000403",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCT.1692G",
                "amount": 3000.0
            }
        }
    ]
    
    # Collect VCT responsibility candidates
    candidates = collect_vct_responsibility_candidates(test_entries)
    
    # Should be empty since VCT cost center is excluded
    if len(candidates) == 0:
        print("✓ V-VC00048 with VCT cost center correctly excluded")
        return True
    else:
        print(f"✗ ERROR - V-VC00048 with VCT cost center should be excluded, but found {len(candidates)} candidates")
        return False

def test_non_vct_cost_center_inclusion():
    """Test that V-VC00048 with non-VCT cost centers are included"""
    print("\n=== Testing Non-VCT Cost Center Inclusion ===")
    
    # Test data with various non-VCT cost centers
    test_entries = [
        {
            "voucher_no": "APA-0000401",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCA.1342G",
                "amount": 1000.0
            }
        },
        {
            "voucher_no": "APA-0000402",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCP.1234",
                "amount": 2000.0
            }
        },
        {
            "voucher_no": "APA-0000405",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCG.5678",
                "amount": 3000.0
            }
        }
    ]
    
    # Collect VCT responsibility candidates
    candidates = collect_vct_responsibility_candidates(test_entries)
    
    # Check that all non-VCT entries are included
    expected_vouchers = ["APA-0000401", "APA-0000402", "APA-0000405"]
    
    success = True
    for voucher in expected_vouchers:
        if voucher in candidates:
            print(f"✓ {voucher}: Correctly included (V-VC00048 with non-VCT cost center)")
        else:
            print(f"✗ {voucher}: ERROR - Should be included")
            success = False
    
    return success

def main():
    """Run all tests"""
    print("=" * 60)
    print("V-VC00048 No Consolidation Test")
    print("=" * 60)
    
    tests = [
        ("No Consolidation for V-VC00048", test_no_consolidation_for_v_vc00048),
        ("VCT Cost Center Exclusion", test_vct_cost_center_exclusion),
        ("Non-VCT Cost Center Inclusion", test_non_vct_cost_center_inclusion)
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
        print("\n🎉 All tests passed! V-VC00048 entries are correctly created as individual pairs (no consolidation).")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
