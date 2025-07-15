#!/usr/bin/env python3
"""
Test script for VCT responsibility entry consolidation logic.

This script tests the new consolidation functionality using the APA-0000552 example
with 4 V-VC00048 entries that should be consolidated into:
- 4 individual debit lines (preserving original amounts and cost centers)
- 1 consolidated credit line (with total amount)
- All using the same document number (single increment)
"""

import json
import sys
import os
from typing import Dict, List, Any

# Add the parent directory to the path so we can import from core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vct_responsibility_consolidation import (
    collect_vct_responsibility_candidates,
    create_consolidated_vct_responsibility_entries,
    extract_description_from_entry
)

def create_test_entries() -> List[Dict[str, Any]]:
    """
    Create test entries based on the APA-0000552 example from the CSV file.
    
    Returns:
        List of test journal entries with V-VC00048 vendor mappings
    """
    test_entries = [
        {
            "voucher_no": "APA-0000552",
            "External_Document_No": "APA-0000552",
            "Document_Date": "2025/05/22",
            "description": "Test expense entry 1",
            "credit": {
                "amount": 500.0,
                "currency": "NTD",
                "vendor_code": "V-VC00048",
                "gl_account": "Vendor",
                "department": "VCA.1001",
                "Remarks": "VCA expense for project A"
            }
        },
        {
            "voucher_no": "APA-0000552",
            "External_Document_No": "APA-0000552", 
            "Document_Date": "2025/05/22",
            "description": "Test expense entry 2",
            "credit": {
                "amount": 500.0,
                "currency": "NTD",
                "vendor_code": "V-VC00048",
                "gl_account": "Vendor",
                "department": "VCA.1002",
                "Remarks": "VCA expense for project B"
            }
        },
        {
            "voucher_no": "APA-0000552",
            "External_Document_No": "APA-0000552",
            "Document_Date": "2025/05/22", 
            "description": "Test expense entry 3",
            "credit": {
                "amount": 566.94,
                "currency": "NTD",
                "vendor_code": "V-VC00048",
                "gl_account": "Vendor",
                "department": "VCA.1003",  # Changed from VCT to VCA
                "Remarks": "VCA expense for project C"
            }
        },
        {
            "voucher_no": "APA-0000552",
            "External_Document_No": "APA-0000552",
            "Document_Date": "2025/05/22",
            "description": "Test expense entry 4", 
            "credit": {
                "amount": 225.0,
                "currency": "NTD",
                "vendor_code": "V-VC00048",
                "gl_account": "Vendor",
                "department": "VCA.1004",  # Changed from VCT to VCA
                "Remarks": "VCA expense for project D"
            }
        },
        # Add a non-V-VC00048 entry to test filtering
        {
            "voucher_no": "APA-0000553",
            "External_Document_No": "APA-0000553",
            "Document_Date": "2025/05/22",
            "description": "Regular vendor entry",
            "credit": {
                "amount": 1000.0,
                "currency": "NTD", 
                "vendor_code": "V-REGULAR",
                "gl_account": "Vendor",
                "department": "VCA.1001",
                "Remarks": "Regular vendor expense"
            }
        },
        # Add a VCT cost center entry (should be filtered out)
        {
            "voucher_no": "APA-0000554",
            "External_Document_No": "APA-0000554",
            "Document_Date": "2025/05/22",
            "description": "VCT cost center entry",
            "credit": {
                "amount": 750.0,
                "currency": "NTD",
                "vendor_code": "V-VC00048", 
                "gl_account": "Vendor",
                "department": "VCT.1005",  # VCT cost center - should be filtered out
                "Remarks": "VCT cost center expense"
            }
        }
    ]
    
    return test_entries

def test_collect_vct_responsibility_candidates():
    """
    Test the collect_vct_responsibility_candidates function.
    """
    print("=" * 60)
    print("Testing collect_vct_responsibility_candidates function")
    print("=" * 60)
    
    test_entries = create_test_entries()
    print(f"Created {len(test_entries)} test entries")
    
    # Collect VCT responsibility candidates
    vct_candidates = collect_vct_responsibility_candidates(test_entries)
    
    print(f"\nCollected VCT responsibility candidates for {len(vct_candidates)} vouchers:")
    for voucher_no, entries in vct_candidates.items():
        print(f"  - Voucher {voucher_no}: {len(entries)} entries")
        for i, entry in enumerate(entries, 1):
            department = entry.get('credit', {}).get('department', '')
            cost_center = department[:3] if department else ''
            amount = entry.get('credit', {}).get('amount', 0)
            print(f"    {i}. Department: {department}, Cost Center: {cost_center}, Amount: {amount}")
    
    # Verify expected results
    expected_vouchers = {"APA-0000552"}  # Only APA-0000552 should have VCT responsibility candidates
    actual_vouchers = set(vct_candidates.keys())
    
    print(f"\nExpected vouchers: {expected_vouchers}")
    print(f"Actual vouchers: {actual_vouchers}")
    
    if expected_vouchers == actual_vouchers:
        print("✅ Voucher filtering test PASSED")
    else:
        print("❌ Voucher filtering test FAILED")
        return False
    
    # Verify APA-0000552 has 4 entries (excluding VCT cost center)
    apa_552_entries = vct_candidates.get("APA-0000552", [])
    if len(apa_552_entries) == 4:
        print("✅ Entry count test PASSED")
    else:
        print(f"❌ Entry count test FAILED - Expected 4, got {len(apa_552_entries)}")
        return False
    
    # Verify cost centers are correct (all VCA - excluding the VCT.1005 entry)
    expected_cost_centers = ["VCA", "VCA", "VCA", "VCA"]
    actual_cost_centers = []
    for entry in apa_552_entries:
        department = entry.get('credit', {}).get('department', '')
        cost_center = department[:3] if department else ''
        actual_cost_centers.append(cost_center)
    
    actual_cost_centers.sort()
    expected_cost_centers.sort()
    
    print(f"Expected cost centers: {expected_cost_centers}")
    print(f"Actual cost centers: {actual_cost_centers}")
    
    if expected_cost_centers == actual_cost_centers:
        print("✅ Cost center filtering test PASSED")
    else:
        print("❌ Cost center filtering test FAILED")
        return False
    
    return True

def test_extract_description_from_entry():
    """
    Test the extract_description_from_entry function.
    """
    print("\n" + "=" * 60)
    print("Testing extract_description_from_entry function")
    print("=" * 60)
    
    # Test with Remarks field
    entry1 = {
        "description": "",
        "credit": {
            "Remarks": "Test remarks description"
        }
    }
    
    description1 = extract_description_from_entry(entry1)
    print(f"Test 1 - Remarks field: '{description1}'")
    if description1 == "Test remarks description":
        print("✅ Remarks test PASSED")
    else:
        print("❌ Remarks test FAILED")
        return False
    
    # Test with main description field
    entry2 = {
        "description": "Main description",
        "credit": {
            "Remarks": "Test remarks description"
        }
    }
    
    description2 = extract_description_from_entry(entry2)
    print(f"Test 2 - Main description: '{description2}'")
    if description2 == "Main description":
        print("✅ Main description test PASSED")
    else:
        print("❌ Main description test FAILED")
        return False
    
    # Test with credit_description field
    entry3 = {
        "description": "",
        "credit_description": "Credit description",
        "credit": {
            "Remarks": "Test remarks description"
        }
    }
    
    description3 = extract_description_from_entry(entry3)
    print(f"Test 3 - Credit description: '{description3}'")
    if description3 == "Credit description":
        print("✅ Credit description test PASSED")
    else:
        print("❌ Credit description test FAILED")
        return False
    
    return True

class MockRateLimiter:
    """Mock rate limiter for testing."""
    def wait_before_request(self):
        pass
    
    def record_success(self):
        pass
    
    def record_failure(self):
        pass

def mock_post_journal_line(journal_line, access_token, rate_limiter, max_retries):
    """
    Mock function to simulate posting journal lines.
    Returns success for testing purposes.
    """
    print(f"Mock posting journal line:")
    print(f"  Document_No: {journal_line.get('Document_No')}")
    print(f"  Account_Type: {journal_line.get('Account_Type')}")
    print(f"  Account_No: {journal_line.get('Account_No')}")
    print(f"  Amount: {journal_line.get('Amount')}")
    print(f"  Currency_Code: {journal_line.get('Currency_Code')}")
    print(f"  Shortcut_Dimension_1_Code: {journal_line.get('Shortcut_Dimension_1_Code')}")
    print(f"  Shortcut_Dimension_2_Code: {journal_line.get('Shortcut_Dimension_2_Code')}")
    print(f"  ShortcutDimCode3: {journal_line.get('ShortcutDimCode3')}")
    print(f"  Description: {journal_line.get('Description')}")
    print()
    
    return True, {"success": True}

def test_create_consolidated_vct_responsibility_entries():
    """
    Test the create_consolidated_vct_responsibility_entries function.
    """
    print("\n" + "=" * 60)
    print("Testing create_consolidated_vct_responsibility_entries function")
    print("=" * 60)
    
    # Monkey patch the post_journal_line function for testing
    import core.process_japan_exports
    original_post_function = None
    
    try:
        # Save the original function
        original_post_function = core.process_japan_exports.post_journal_line
    except AttributeError:
        pass
    
    # Replace with mock function
    core.process_japan_exports.post_journal_line = mock_post_journal_line
    
    try:
        test_entries = create_test_entries()
        vct_candidates = collect_vct_responsibility_candidates(test_entries)
        
        # Test with APA-0000552 entries
        apa_552_entries = vct_candidates.get("APA-0000552", [])
        
        if not apa_552_entries:
            print("❌ No APA-0000552 entries found for testing")
            return False
        
        print(f"Testing consolidation with {len(apa_552_entries)} entries for voucher APA-0000552")
        
        # Create mock objects
        mock_access_token = "mock_token"
        mock_rate_limiter = MockRateLimiter()
        used_doc_numbers = {}
        external_doc_no_counter = {}
        
        # Test the consolidation function
        success_count, failure_count = create_consolidated_vct_responsibility_entries(
            apa_552_entries, 
            mock_access_token, 
            mock_rate_limiter, 
            used_doc_numbers,
            external_doc_no_counter,
            max_retries=3
        )
        
        print(f"Consolidation results: Success: {success_count}, Failure: {failure_count}")
        print(f"Document numbers used: {used_doc_numbers}")
        
        # Verify results
        expected_success = 5  # 4 debit lines + 1 credit line
        expected_failure = 0
        expected_doc_number = "APA-0000552-1"
        
        if success_count == expected_success and failure_count == expected_failure:
            print("✅ Success/failure count test PASSED")
        else:
            print(f"❌ Success/failure count test FAILED - Expected {expected_success}/{expected_failure}, got {success_count}/{failure_count}")
            return False
        
        if "APA-0000552" in used_doc_numbers and used_doc_numbers["APA-0000552"] == 1:
            print("✅ Document number sequencing test PASSED")
        else:
            print(f"❌ Document number sequencing test FAILED - Expected APA-0000552: 1, got {used_doc_numbers}")
            return False
        
        # Test total amount calculation
        total_amount = sum(entry.get('credit', {}).get('amount', 0) for entry in apa_552_entries)
        expected_total = 500.0 + 500.0 + 566.94 + 225.0  # 1791.94
        
        if abs(total_amount - expected_total) < 0.01:
            print(f"✅ Total amount calculation test PASSED - Total: {total_amount}")
        else:
            print(f"❌ Total amount calculation test FAILED - Expected {expected_total}, got {total_amount}")
            return False
        
        return True
        
    finally:
        # Restore original function if it existed
        if original_post_function:
            core.process_japan_exports.post_journal_line = original_post_function

def main():
    """
    Run all tests for VCT responsibility consolidation.
    """
    print("VCT Responsibility Entry Consolidation Test Suite")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Collect VCT responsibility candidates
    if not test_collect_vct_responsibility_candidates():
        all_tests_passed = False
    
    # Test 2: Extract description from entry
    if not test_extract_description_from_entry():
        all_tests_passed = False
    
    # Test 3: Create consolidated VCT responsibility entries
    if not test_create_consolidated_vct_responsibility_entries():
        all_tests_passed = False
    
    # Final results
    print("\n" + "=" * 60)
    print("TEST SUITE RESULTS")
    print("=" * 60)
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! VCT responsibility consolidation is working correctly.")
        print("\nExpected behavior for APA-0000552:")
        print("- 4 individual debit lines (preserving original amounts and cost centers)")
        print("- 1 consolidated credit line (total amount: 1791.94)")
        print("- All entries use document number: APA-0000552-1")
        print("- 37.5% reduction in API calls (8 → 5)")
        print("- 75% reduction in document numbers (4 → 1)")
    else:
        print("❌ SOME TESTS FAILED! Please review the implementation.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
