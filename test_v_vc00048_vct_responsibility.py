#!/usr/bin/env python3
"""
Test script for V-VC00048 mapping to VCT for non-VCT cost centers with additional VCT responsibility entries.

This script tests the implementation of Issue #78 extended requirement, which adds additional
debit and credit lines in VCT to record the responsibility of expense.
"""

import json
import logging
import sys
from process_japan_exports import create_journal_line, create_vct_responsibility_entries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_v_vc00048_vct_responsibility")

class MockRateLimiter:
    """Mock rate limiter for testing"""
    def wait_before_request(self):
        pass
    
    def record_success(self):
        pass
    
    def record_failure(self):
        pass

def mock_post_journal_line(journal_line, access_token, rate_limiter, max_retries):
    """Mock function to simulate posting a journal line"""
    logger.info(f"Mock posting journal line: {json.dumps(journal_line, indent=2)}")
    return True, {"status": "success"}

def test_vct_responsibility_entries():
    """
    Test the creation of additional VCT responsibility entries for V-VC00048 vendor.
    """
    # Create a test entry with V-VC00048 vendor code and non-VCT cost center
    test_entry = {
        "voucher_no": "TEST-001",
        "External_Document_No": "EXT-001",
        "Document_Date": "2025/05/15",
        "description": "Test Entry",
        "debit": {
            "gl_account": "G/L Account",
            "account": "75510-10",
            "amount": 1000.0,
            "currency": "USD",
            "department": "VCA.1342G",
            "applicant_code": "10126",
            "vendor_code": "V-VC00048"
        },
        "credit": {
            "gl_account": "Vendor",
            "account": "V-VC00048",
            "amount": 1000.0,
            "currency": "R-USD",
            "department": "VCA.1342G",
            "applicant_code": "10126",
            "vendor_code": "V-VC00048",
            "department_code": "VCA.9999",
            "Remarks": "Test Expense"
        }
    }
    
    # Create a mock access token
    mock_access_token = "mock_token"
    
    # Create a mock rate limiter
    mock_rate_limiter = MockRateLimiter()
    
    # Patch the post_journal_line function in the module
    import process_japan_exports
    original_post_journal_line = process_japan_exports.post_journal_line
    process_japan_exports.post_journal_line = mock_post_journal_line
    
    try:
        # Call the function to create VCT responsibility entries
        logger.info("Testing create_vct_responsibility_entries function")
        success_count, failure_count = create_vct_responsibility_entries(
            test_entry, mock_access_token, mock_rate_limiter
        )
        
        # Verify the results
        assert success_count == 2, f"Expected 2 successful entries, got {success_count}"
        assert failure_count == 0, f"Expected 0 failed entries, got {failure_count}"
        
        logger.info("✅ Test passed: create_vct_responsibility_entries function works correctly")
        
        # Test with a consolidated entry
        consolidated_entry = test_entry.copy()
        consolidated_entry["credit"]["consolidated"] = True
        consolidated_entry["credit"]["original_entries_count"] = 2
        
        logger.info("Testing create_vct_responsibility_entries function with consolidated entry")
        success_count, failure_count = create_vct_responsibility_entries(
            consolidated_entry, mock_access_token, mock_rate_limiter
        )
        
        # Verify the results
        assert success_count == 2, f"Expected 2 successful entries for consolidated entry, got {success_count}"
        assert failure_count == 0, f"Expected 0 failed entries for consolidated entry, got {failure_count}"
        
        logger.info("✅ Test passed: create_vct_responsibility_entries function works correctly with consolidated entry")
        
    finally:
        # Restore the original function
        process_japan_exports.post_journal_line = original_post_journal_line

def test_vct_responsibility_entries_format():
    """
    Test the format of the VCT responsibility entries.
    """
    # Create a test entry with V-VC00048 vendor code and non-VCT cost center
    test_entry = {
        "voucher_no": "TEST-001",
        "External_Document_No": "EXT-001",
        "Document_Date": "2025/05/15",
        "description": "Test Entry",
        "debit": {
            "gl_account": "G/L Account",
            "account": "75510-10",
            "amount": 1000.0,
            "currency": "USD",
            "department": "VCA.1342G",
            "applicant_code": "10126",
            "vendor_code": "V-VC00048"
        },
        "credit": {
            "gl_account": "Vendor",
            "account": "V-VC00048",
            "amount": 1000.0,
            "currency": "R-USD",
            "department": "VCA.1342G",
            "applicant_code": "10126",
            "vendor_code": "V-VC00048",
            "department_code": "VCA.9999",
            "Remarks": "Test Expense"
        }
    }
    
    # Create a mock access token
    mock_access_token = "mock_token"
    
    # Create a mock rate limiter
    mock_rate_limiter = MockRateLimiter()
    
    # Store the journal lines that would be posted
    posted_journal_lines = []
    
    # Patch the post_journal_line function to capture the journal lines
    def capture_journal_line(journal_line, access_token, rate_limiter, max_retries):
        posted_journal_lines.append(journal_line.copy())
        return True, {"status": "success"}
    
    # Patch the post_journal_line function in the module
    import process_japan_exports
    original_post_journal_line = process_japan_exports.post_journal_line
    process_japan_exports.post_journal_line = capture_journal_line
    
    try:
        # Call the function to create VCT responsibility entries
        create_vct_responsibility_entries(test_entry, mock_access_token, mock_rate_limiter)
        
        # Verify that two journal lines were posted
        assert len(posted_journal_lines) == 2, f"Expected 2 journal lines, got {len(posted_journal_lines)}"
        
        # Get the debit and credit lines
        debit_line = posted_journal_lines[0]
        credit_line = posted_journal_lines[1]
        
        # Verify the debit line
        assert debit_line["Account_Type"] == "G/L Account", f"Expected Account_Type 'G/L Account', got '{debit_line['Account_Type']}'"
        assert debit_line["Account_No"] == "18600-10", f"Expected Account_No '18600-10', got '{debit_line['Account_No']}'"
        assert debit_line["Description"] == "VCA Test Expense", f"Expected Description 'VCA Test Expense', got '{debit_line['Description']}'"
        assert debit_line["External_Document_No"] == "EXT-001", f"Expected External_Document_No 'EXT-001', got '{debit_line['External_Document_No']}'"
        assert debit_line["Document_No"] == "TEST-001", f"Expected Document_No 'TEST-001', got '{debit_line['Document_No']}'"
        assert debit_line["Shortcut_Dimension_1_Code"] == "VCT", f"Expected Shortcut_Dimension_1_Code 'VCT', got '{debit_line['Shortcut_Dimension_1_Code']}'"
        assert debit_line["Shortcut_Dimension_2_Code"] == "VCT.9999", f"Expected Shortcut_Dimension_2_Code 'VCT.9999', got '{debit_line['Shortcut_Dimension_2_Code']}'"
        assert debit_line["Currency_Code"] == "R-USD", f"Expected Currency_Code 'R-USD', got '{debit_line['Currency_Code']}'"
        assert debit_line["Amount"] == 1000.0, f"Expected Amount 1000.0, got {debit_line['Amount']}"
        
        # Verify the credit line
        assert credit_line["Account_Type"] == "Vendor", f"Expected Account_Type 'Vendor', got '{credit_line['Account_Type']}'"
        assert credit_line["Account_No"] == "V-VC00048", f"Expected Account_No 'V-VC00048', got '{credit_line['Account_No']}'"
        assert credit_line["Description"] == "VCA Test Expense", f"Expected Description 'VCA Test Expense', got '{credit_line['Description']}'"
        assert credit_line["External_Document_No"] == "EXT-001", f"Expected External_Document_No 'EXT-001', got '{credit_line['External_Document_No']}'"
        assert credit_line["Document_No"] == "TEST-001", f"Expected Document_No 'TEST-001', got '{credit_line['Document_No']}'"
        assert credit_line["Shortcut_Dimension_1_Code"] == "VCT", f"Expected Shortcut_Dimension_1_Code 'VCT', got '{credit_line['Shortcut_Dimension_1_Code']}'"
        assert credit_line["Shortcut_Dimension_2_Code"] == "VCT.9999", f"Expected Shortcut_Dimension_2_Code 'VCT.9999', got '{credit_line['Shortcut_Dimension_2_Code']}'"
        assert credit_line["Currency_Code"] == "R-USD", f"Expected Currency_Code 'R-USD', got '{credit_line['Currency_Code']}'"
        assert credit_line["Amount"] == -1000.0, f"Expected Amount -1000.0, got {credit_line['Amount']}"
        
        logger.info("✅ Test passed: VCT responsibility entries have the correct format")
        
    finally:
        # Restore the original function
        process_japan_exports.post_journal_line = original_post_journal_line

if __name__ == "__main__":
    test_vct_responsibility_entries()
    test_vct_responsibility_entries_format()
    logger.info("All tests passed!")
