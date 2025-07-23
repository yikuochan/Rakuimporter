#!/usr/bin/env python3
"""
Test to verify that VCT responsibility entries are properly skipped during processing.
This test ensures that entries with "vct_responsibility": True are not processed by the regular logic.
"""

import json
import sys
import os

# Add the parent directory to the path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process_japan_exports import process_entries
from unittest.mock import Mock, patch
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vct_responsibility_skipping():
    """Test that VCT responsibility entries are properly skipped during processing."""
    
    # Create test data with VCT responsibility entries
    test_entries = [
        # Regular entry (should be processed)
        {
            "voucher_no": "APA-0000481",
            "transaction_date": "2025/06/25",
            "description": "NordVpn",
            "External_Document_No": "NRDCH-408960",
            "Document_Date": "2025/06/25",
            "debit": {
                "gl_account": "G/L Account",
                "account": "74850-10",
                "amount": 366.0,
                "currency": "NTD",
                "department": "VCT.1751G",
                "applicant_code": "10115",
                "vendor_code": "V-VC00048",
                "department_code": "VCT.1731G"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "V-VC00048",
                "sub_account": "31200-10",
                "amount": 366.0,
                "currency": "NTD",
                "department": "VCT.1751G",
                "applicant_code": "10115",
                "vendor_code": "V-VC00048",
                "department_code": "VCT.9999",
                "Remarks": "NordVpn, credit card No.:4865951001070770",
                "account_source": "vendor_code"
            }
        },
        # VCT responsibility entry (should be skipped)
        {
            "voucher_no": "APA-0000552",
            "transaction_date": "2025/04/22",
            "description": "VCA.1342G ESCAR USA Ticket",
            "credit_description": "ESCAR USA Tickets, Freight Fraud Symposium Ticket, AUTO ISAC Europe Ticket, COVESA TV setup and Tear",
            "External_Document_No": "20250404",
            "Document_Date": "2025/04/22",
            "debit": {
                "gl_account": "G/L Account",
                "account": "18600-10",
                "amount": 1791.94,
                "currency": "R-USD",
                "department": "VCT.9999",
                "department_code": "VCT.9999",
                "vct_responsibility": True,
                "original_cost_center": "VCA"
            },
            "credit": {
                "gl_account": "",
                "account": "",
                "amount": 0,
                "currency": "",
                "department": "",
                "department_code": "",
                "Remarks": ""
            },
            "vct_responsibility": True
        },
        # Another VCT responsibility entry (should be skipped)
        {
            "voucher_no": "APA-0000552",
            "transaction_date": "2025/04/22",
            "description": "ESCAR USA Ticket",
            "credit_description": "ESCAR USA Tickets, Freight Fraud Symposium Ticket, AUTO ISAC Europe Ticket, COVESA TV setup and Tear",
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
                "Remarks": "ESCAR USA Ticket",
                "vct_responsibility": True,
                "original_cost_center": "VCA"
            },
            "vct_responsibility": True
        }
    ]
    
    # Mock the access token and API calls
    mock_access_token = "mock_token"
    
    # Track which entries were processed
    processed_entries = []
    
    def mock_post_journal_line(journal_line, access_token, rate_limiter, max_retries):
        """Mock function to track which journal lines are posted."""
        processed_entries.append({
            "document_no": journal_line.get("Document_No"),
            "account_type": journal_line.get("Account_Type"),
            "account_no": journal_line.get("Account_No"),
            "amount": journal_line.get("Amount"),
            "description": journal_line.get("Description")
        })
        return True, {"success": True}
    
    # Mock the VCT responsibility consolidation functions to prevent them from running
    def mock_collect_vct_responsibility_candidates(entries):
        return {}
    
    def mock_create_consolidated_vct_responsibility_entries(*args):
        return 0, 0
    
    # Patch the functions
    with patch('core.process_japan_exports.post_journal_line', side_effect=mock_post_journal_line), \
         patch('core.process_japan_exports.collect_vct_responsibility_candidates', side_effect=mock_collect_vct_responsibility_candidates), \
         patch('core.process_japan_exports.create_consolidated_vct_responsibility_entries', side_effect=mock_create_consolidated_vct_responsibility_entries):
        
        # Process the entries
        success_count, failure_count, balanced_count, unbalanced_count = process_entries(
            test_entries,
            mock_access_token,
            balance_tolerance=0.01,
            skip_unbalanced=False,
            base_delay=0.1,  # Fast for testing
            max_delay=0.2,
            max_retries=1
        )
    
    # Analyze results
    logger.info(f"Processing results: Success: {success_count}, Failure: {failure_count}")
    logger.info(f"Balance results: Balanced: {balanced_count}, Unbalanced: {unbalanced_count}")
    logger.info(f"Total processed journal lines: {len(processed_entries)}")
    
    # Check that only the regular entry was processed (2 lines: debit + credit)
    expected_processed_lines = 2  # Only the regular entry should be processed
    actual_processed_lines = len(processed_entries)
    
    logger.info(f"Expected processed lines: {expected_processed_lines}")
    logger.info(f"Actual processed lines: {actual_processed_lines}")
    
    # Log details of processed entries
    for i, entry in enumerate(processed_entries):
        logger.info(f"Processed entry {i+1}: Document_No={entry['document_no']}, "
                   f"Account_Type={entry['account_type']}, Account_No={entry['account_no']}, "
                   f"Amount={entry['amount']}, Description={entry['description']}")
    
    # Verify results
    if actual_processed_lines == expected_processed_lines:
        logger.info("✅ SUCCESS: VCT responsibility entries were properly skipped!")
        logger.info("✅ Only regular entries were processed as expected")
        
        # Verify that the processed entries are from the regular entry
        regular_entry_found = False
        for entry in processed_entries:
            if entry['document_no'] == 'APA-0000481':
                regular_entry_found = True
                break
        
        if regular_entry_found:
            logger.info("✅ SUCCESS: Regular entry (APA-0000481) was processed correctly")
        else:
            logger.error("❌ FAILURE: Regular entry was not found in processed entries")
            return False
        
        # Verify that no VCT responsibility entries were processed
        vct_responsibility_found = False
        for entry in processed_entries:
            if entry['document_no'] == 'APA-0000552':
                vct_responsibility_found = True
                break
        
        if not vct_responsibility_found:
            logger.info("✅ SUCCESS: VCT responsibility entries (APA-0000552) were properly skipped")
        else:
            logger.error("❌ FAILURE: VCT responsibility entries were incorrectly processed")
            return False
        
        return True
    else:
        logger.error(f"❌ FAILURE: Expected {expected_processed_lines} processed lines, but got {actual_processed_lines}")
        logger.error("❌ VCT responsibility entries may not have been properly skipped")
        return False

def main():
    """Run the VCT responsibility skipping verification test."""
    logger.info("=" * 80)
    logger.info("VCT RESPONSIBILITY ENTRY SKIPPING VERIFICATION TEST")
    logger.info("=" * 80)
    logger.info("Testing that entries with 'vct_responsibility': True are properly skipped during processing")
    logger.info("")
    
    try:
        success = test_vct_responsibility_skipping()
        
        logger.info("")
        logger.info("=" * 80)
        if success:
            logger.info("🎉 ALL TESTS PASSED! VCT responsibility entry skipping is working correctly.")
            logger.info("✅ VCT responsibility entries are properly excluded from regular processing")
            logger.info("✅ Regular entries continue to be processed normally")
        else:
            logger.error("❌ TEST FAILED! VCT responsibility entry skipping is not working correctly.")
            logger.error("❌ Please check the implementation in process_japan_exports.py")
        logger.info("=" * 80)
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
