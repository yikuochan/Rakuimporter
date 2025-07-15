#!/usr/bin/env python3
"""
Test External Document Number Uniqueness for VCT Responsibility Entries

This test verifies that the VCT responsibility consolidation properly integrates
with the global External Document Number uniqueness tracking system to prevent
duplicate External Document Numbers across the entire system.
"""

import sys
import os
import json
import logging
from unittest.mock import Mock, patch

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vct_responsibility_consolidation import (
    collect_vct_responsibility_candidates,
    create_consolidated_vct_responsibility_entries,
    generate_unique_external_doc_no
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_external_doc_no_uniqueness():
    """Test that External Document Numbers are made unique for VCT responsibility entries."""
    
    print("=" * 80)
    print("TESTING EXTERNAL DOCUMENT NUMBER UNIQUENESS FOR VCT RESPONSIBILITY ENTRIES")
    print("=" * 80)
    
    # Test data with duplicate External Document Numbers
    test_entries = [
        {
            "voucher_no": "APA-0000552",
            "External_Document_No": "APA-0000552",
            "Document_Date": "2024/05/27",
            "description": "Test expense 1",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCP.1000",
                "amount": 1000.0,
                "currency": "PHP"
            }
        },
        {
            "voucher_no": "APA-0000552",
            "External_Document_No": "APA-0000552",  # Same External Document Number
            "Document_Date": "2024/05/27",
            "description": "Test expense 2",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCP.2000",
                "amount": 2000.0,
                "currency": "PHP"
            }
        },
        {
            "voucher_no": "APA-0000552",
            "External_Document_No": "APA-0000552",  # Same External Document Number
            "Document_Date": "2024/05/27",
            "description": "Test expense 3",
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCP.3000",
                "amount": 3000.0,
                "currency": "PHP"
            }
        }
    ]
    
    print(f"\n1. Testing with {len(test_entries)} entries with duplicate External Document Numbers")
    
    # Test the unique External Document Number generation function
    external_doc_no_counter = {}
    
    print("\n2. Testing generate_unique_external_doc_no function:")
    
    # First occurrence should remain unchanged
    unique_1 = generate_unique_external_doc_no("APA-0000552", external_doc_no_counter)
    print(f"   First occurrence: APA-0000552 -> {unique_1}")
    assert unique_1 == "APA-0000552", f"Expected 'APA-0000552', got '{unique_1}'"
    
    # Second occurrence should get suffix -1
    unique_2 = generate_unique_external_doc_no("APA-0000552", external_doc_no_counter)
    print(f"   Second occurrence: APA-0000552 -> {unique_2}")
    assert unique_2 == "APA-0000552-1", f"Expected 'APA-0000552-1', got '{unique_2}'"
    
    # Third occurrence should get suffix -2
    unique_3 = generate_unique_external_doc_no("APA-0000552", external_doc_no_counter)
    print(f"   Third occurrence: APA-0000552 -> {unique_3}")
    assert unique_3 == "APA-0000552-2", f"Expected 'APA-0000552-2', got '{unique_3}'"
    
    print("   ✓ External Document Number uniqueness generation working correctly")
    
    # Test VCT responsibility candidate collection
    print("\n3. Testing VCT responsibility candidate collection:")
    vct_candidates = collect_vct_responsibility_candidates(test_entries)
    
    print(f"   Found {len(vct_candidates)} vouchers with VCT responsibility candidates")
    assert "APA-0000552" in vct_candidates, "Expected voucher APA-0000552 in candidates"
    assert len(vct_candidates["APA-0000552"]) == 3, f"Expected 3 entries, got {len(vct_candidates['APA-0000552'])}"
    
    print("   ✓ VCT responsibility candidate collection working correctly")
    
    # Test consolidated VCT responsibility entry creation with mocked API calls
    print("\n4. Testing consolidated VCT responsibility entry creation:")
    
    # Mock the post_journal_line function to avoid actual API calls
    posted_lines = []
    
    def mock_post_journal_line(journal_line, access_token, rate_limiter, max_retries):
        posted_lines.append(journal_line.copy())
        return True, {"success": True}
    
    # Mock the rate limiter
    mock_rate_limiter = Mock()
    
    # Reset external document number counter for this test
    external_doc_no_counter = {}
    used_doc_numbers = {}
    
    # Import the module first to ensure the import happens
    import core.vct_responsibility_consolidation
    
    with patch('core.process_japan_exports_fixed.post_journal_line', side_effect=mock_post_journal_line):
        success_count, failure_count = create_consolidated_vct_responsibility_entries(
            vct_candidates["APA-0000552"],
            "mock_access_token",
            mock_rate_limiter,
            used_doc_numbers,
            external_doc_no_counter
        )
    
    print(f"   Success count: {success_count}, Failure count: {failure_count}")
    assert success_count == 4, f"Expected 4 successful posts (3 debits + 1 credit), got {success_count}"
    assert failure_count == 0, f"Expected 0 failures, got {failure_count}"
    
    print(f"   Posted {len(posted_lines)} journal lines")
    
    # Verify External Document Number uniqueness in posted lines
    print("\n5. Verifying External Document Number uniqueness in posted lines:")
    
    external_doc_nos = [line["External_Document_No"] for line in posted_lines]
    print(f"   External Document Numbers: {external_doc_nos}")
    
    # Check that all External Document Numbers are unique
    unique_external_doc_nos = set(external_doc_nos)
    assert len(unique_external_doc_nos) == len(external_doc_nos), \
        f"Expected all External Document Numbers to be unique. Got duplicates: {external_doc_nos}"
    
    # Check the expected pattern
    expected_external_doc_nos = ["APA-0000552", "APA-0000552-1", "APA-0000552-2", "APA-0000552-3"]
    assert external_doc_nos == expected_external_doc_nos, \
        f"Expected {expected_external_doc_nos}, got {external_doc_nos}"
    
    print("   ✓ All External Document Numbers are unique")
    
    # Verify document number consistency
    print("\n6. Verifying document number consistency:")
    
    document_nos = [line["Document_No"] for line in posted_lines]
    print(f"   Document Numbers: {document_nos}")
    
    # All should use the same consolidated document number
    unique_document_nos = set(document_nos)
    assert len(unique_document_nos) == 1, \
        f"Expected all Document Numbers to be the same. Got: {document_nos}"
    
    expected_doc_no = "APA-0000552-1"  # First increment for VCT responsibility
    assert document_nos[0] == expected_doc_no, \
        f"Expected Document Number '{expected_doc_no}', got '{document_nos[0]}'"
    
    print(f"   ✓ All entries use the same consolidated Document Number: {document_nos[0]}")
    
    # Verify line types and amounts
    print("\n7. Verifying line types and amounts:")
    
    debit_lines = [line for line in posted_lines if line["Amount"] > 0]
    credit_lines = [line for line in posted_lines if line["Amount"] < 0]
    
    print(f"   Debit lines: {len(debit_lines)}")
    print(f"   Credit lines: {len(credit_lines)}")
    
    assert len(debit_lines) == 3, f"Expected 3 debit lines, got {len(debit_lines)}"
    assert len(credit_lines) == 1, f"Expected 1 credit line, got {len(credit_lines)}"
    
    # Check debit amounts
    debit_amounts = [line["Amount"] for line in debit_lines]
    expected_debit_amounts = [1000.0, 2000.0, 3000.0]
    assert debit_amounts == expected_debit_amounts, \
        f"Expected debit amounts {expected_debit_amounts}, got {debit_amounts}"
    
    # Check credit amount (should be negative sum)
    credit_amount = credit_lines[0]["Amount"]
    expected_credit_amount = -6000.0  # -(1000 + 2000 + 3000)
    assert credit_amount == expected_credit_amount, \
        f"Expected credit amount {expected_credit_amount}, got {credit_amount}"
    
    print("   ✓ Line types and amounts are correct")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - EXTERNAL DOCUMENT NUMBER UNIQUENESS IS WORKING CORRECTLY")
    print("=" * 80)
    
    return True

def test_integration_with_existing_counter():
    """Test that VCT responsibility entries integrate with existing external document number counter."""
    
    print("\n" + "=" * 80)
    print("TESTING INTEGRATION WITH EXISTING EXTERNAL DOCUMENT NUMBER COUNTER")
    print("=" * 80)
    
    # Simulate existing external document numbers from regular entries
    external_doc_no_counter = {
        "APA-0000552": 2,  # Already used APA-0000552, APA-0000552-1, APA-0000552-2
        "OTHER-DOC": 0     # Another document with one occurrence
    }
    
    print(f"Starting with existing counter: {external_doc_no_counter}")
    
    # Test generating unique External Document Numbers
    print("\n1. Testing with existing counter state:")
    
    # Should get APA-0000552-3 (next available)
    unique_1 = generate_unique_external_doc_no("APA-0000552", external_doc_no_counter)
    print(f"   APA-0000552 -> {unique_1}")
    assert unique_1 == "APA-0000552-3", f"Expected 'APA-0000552-3', got '{unique_1}'"
    
    # Should get APA-0000552-4 (next available)
    unique_2 = generate_unique_external_doc_no("APA-0000552", external_doc_no_counter)
    print(f"   APA-0000552 -> {unique_2}")
    assert unique_2 == "APA-0000552-4", f"Expected 'APA-0000552-4', got '{unique_2}'"
    
    # Should get OTHER-DOC-1 (first duplicate)
    unique_3 = generate_unique_external_doc_no("OTHER-DOC", external_doc_no_counter)
    print(f"   OTHER-DOC -> {unique_3}")
    assert unique_3 == "OTHER-DOC-1", f"Expected 'OTHER-DOC-1', got '{unique_3}'"
    
    print("   ✓ Integration with existing counter working correctly")
    
    print(f"Final counter state: {external_doc_no_counter}")
    
    print("\n✅ INTEGRATION TEST PASSED")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        # Run the tests
        test_external_doc_no_uniqueness()
        test_integration_with_existing_counter()
        
        print("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("The External Document Number uniqueness fix is working correctly.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
