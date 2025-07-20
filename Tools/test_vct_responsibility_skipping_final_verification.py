#!/usr/bin/env python3
"""
Test to verify that VCT responsibility entries are properly skipped during processing.
This test confirms the final fix for V-VC00048 consolidation bug.
"""

import json
import sys
import os

# Add the parent directory to the path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process_japan_exports import process_entries
from unittest.mock import Mock, patch
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vct_responsibility_skipping():
    """Test that VCT responsibility entries are properly skipped during processing."""
    
    print("=" * 80)
    print("TESTING VCT RESPONSIBILITY ENTRY SKIPPING - FINAL VERIFICATION")
    print("=" * 80)
    
    # Test data with VCT responsibility entries that should be skipped
    test_entries = [
        # Regular entry that should be processed
        {
            "voucher_no": "APA-0000552",
            "transaction_date": "2025/04/22",
            "description": "Regular Entry",
            "External_Document_No": "20250404",
            "Document_Date": "2025/04/22",
            "debit": {
                "gl_account": "G/L Account",
                "account": "75512-10",
                "amount": 500.0,
                "currency": "USD",
                "department": "VCA.1342G",
                "applicant_code": "10126",
                "vendor_code": "V-VC00048"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "V-VC00048",
                "amount": 500.0,
                "currency": "R-USD",
                "department": "VCA.1342G",
                "vendor_code": "V-VC00048",
                "department_code": "VCA.9999"
            }
        },
        # VCT responsibility entry with top-level flag (should be skipped)
        {
            "voucher_no": "APA-0000552",
            "transaction_date": "2025/04/22",
            "description": "VCT Responsibility Entry - Top Level Flag",
            "External_Document_No": "20250404",
            "Document_Date": "2025/04/22",
            "vct_responsibility": True,  # This should cause the entry to be skipped
            "debit": {
                "gl_account": "G/L Account",
                "account": "18600-10",
                "amount": 1791.94,
                "currency": "R-USD",
                "department": "VCT.9999",
                "department_code": "VCT.9999"
            },
            "credit": {
                "gl_account": "",
                "account": "",
                "amount": 0,
                "currency": "",
                "department": "",
                "department_code": ""
            }
        },
        # VCT responsibility entry with debit flag (should be skipped)
        {
            "voucher_no": "APA-0000552",
            "transaction_date": "2025/04/22",
            "description": "VCT Responsibility Entry - Debit Flag",
            "External_Document_No": "20250404",
            "Document_Date": "2025/04/22",
            "debit": {
                "gl_account": "G/L Account",
                "account": "18600-10",
                "amount": 1791.94,
                "currency": "R-USD",
                "department": "VCT.9999",
                "department_code": "VCT.9999",
                "vct_responsibility": True  # This should cause the entry to be skipped
            },
            "credit": {
                "gl_account": "",
                "account": "",
                "amount": 0,
                "currency": "",
                "department": "",
                "department_code": ""
            }
        },
        # VCT responsibility entry with credit flag (should be skipped)
        {
            "voucher_no": "APA-0000552",
            "transaction_date": "2025/04/22",
            "description": "VCT Responsibility Entry - Credit Flag",
            "External_Document_No": "20250404",
            "Document_Date": "2025/04/22",
            "debit": {
                "gl_account": "",
                "account": "",
                "amount": 0,
                "currency": "",
                "department": "",
                "department_code": ""
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "V-VC00048",
                "amount": 1791.94,
                "currency": "R-USD",
                "department": "VCT.9999",
                "vendor_code": "V-VC00048",
                "department_code": "VCT.9999",
                "vct_responsibility": True  # This should cause the entry to be skipped
            }
        }
    ]
    
    print(f"\nTest data contains {len(test_entries)} entries:")
    print("1. Regular entry (should be processed)")
    print("2. VCT responsibility entry with top-level flag (should be skipped)")
    print("3. VCT responsibility entry with debit flag (should be skipped)")
    print("4. VCT responsibility entry with credit flag (should be skipped)")
    
    # Mock the API calls to track what gets processed
    processed_entries = []
    
    def mock_post_journal_line(journal_line, access_token, rate_limiter=None, max_retries=3):
        """Mock function to track processed journal lines."""
        processed_entries.append({
            'document_no': journal_line.get('Document_No'),
            'account_type': journal_line.get('Account_Type'),
            'account_no': journal_line.get('Account_No'),
            'description': journal_line.get('Description'),
            'amount': journal_line.get('Amount')
        })
        return True, {"success": True}
    
    # Mock the access token
    mock_access_token = "mock_token"
    
    # Mock the VCT responsibility consolidation functions to return empty results
    def mock_collect_vct_responsibility_candidates(entries):
        return {}
    
    def mock_create_consolidated_vct_responsibility_entries(*args):
        return 0, 0
    
    # Run the test with mocked functions
    with patch('core.process_japan_exports.post_journal_line', side_effect=mock_post_journal_line), \
         patch('core.process_japan_exports.collect_vct_responsibility_candidates', side_effect=mock_collect_vct_responsibility_candidates), \
         patch('core.process_japan_exports.create_consolidated_vct_responsibility_entries', side_effect=mock_create_consolidated_vct_responsibility_entries):
        
        print("\n" + "="*50)
        print("RUNNING PROCESS_ENTRIES WITH MOCKED API CALLS")
        print("="*50)
        
        success_count, failure_count, balanced_count, unbalanced_count = process_entries(
            test_entries,
            mock_access_token,
            balance_tolerance=0.01,
            skip_unbalanced=False
        )
    
    print(f"\n" + "="*50)
    print("PROCESSING RESULTS")
    print("="*50)
    print(f"Success count: {success_count}")
    print(f"Failure count: {failure_count}")
    print(f"Balanced count: {balanced_count}")
    print(f"Unbalanced count: {unbalanced_count}")
    print(f"Total processed journal lines: {len(processed_entries)}")
    
    print(f"\n" + "="*50)
    print("PROCESSED JOURNAL LINES DETAILS")
    print("="*50)
    for i, entry in enumerate(processed_entries, 1):
        print(f"{i}. Document: {entry['document_no']}")
        print(f"   Account Type: {entry['account_type']}")
        print(f"   Account No: {entry['account_no']}")
        print(f"   Description: {entry['description']}")
        print(f"   Amount: {entry['amount']}")
        print()
    
    # Verify results
    print("="*50)
    print("VERIFICATION RESULTS")
    print("="*50)
    
    # We should only have processed the regular entry (2 journal lines: debit + credit)
    expected_processed_lines = 2  # Only the regular entry should be processed
    actual_processed_lines = len(processed_entries)
    
    if actual_processed_lines == expected_processed_lines:
        print("✅ SUCCESS: VCT responsibility entries were properly skipped!")
        print(f"   Expected {expected_processed_lines} journal lines to be processed")
        print(f"   Actually processed {actual_processed_lines} journal lines")
        
        # Verify that only the regular entry was processed
        regular_entry_processed = any(
            'Regular Entry' in entry['description'] 
            for entry in processed_entries
        )
        
        vct_responsibility_processed = any(
            'VCT Responsibility' in entry['description'] 
            for entry in processed_entries
        )
        
        if regular_entry_processed and not vct_responsibility_processed:
            print("✅ CONFIRMED: Only regular entries were processed")
            print("✅ CONFIRMED: All VCT responsibility entries were skipped")
            return True
        else:
            print("❌ ERROR: VCT responsibility entries were not properly filtered")
            return False
    else:
        print("❌ FAILURE: VCT responsibility entries were not properly skipped!")
        print(f"   Expected {expected_processed_lines} journal lines to be processed")
        print(f"   Actually processed {actual_processed_lines} journal lines")
        print("   This indicates that VCT responsibility entries are still being processed")
        return False

def main():
    """Main function to run the test."""
    print("VCT Responsibility Entry Skipping - Final Verification Test")
    print("This test verifies that entries with vct_responsibility flags are properly skipped")
    
    try:
        success = test_vct_responsibility_skipping()
        
        if success:
            print("\n" + "="*80)
            print("🎉 ALL TESTS PASSED! VCT RESPONSIBILITY SKIPPING IS WORKING CORRECTLY!")
            print("="*80)
            print("The V-VC00048 consolidation bug fix is now complete and verified.")
            print("VCT responsibility entries will be properly skipped during processing.")
        else:
            print("\n" + "="*80)
            print("❌ TEST FAILED! VCT RESPONSIBILITY SKIPPING IS NOT WORKING!")
            print("="*80)
            print("The skip logic needs to be reviewed and fixed.")
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
