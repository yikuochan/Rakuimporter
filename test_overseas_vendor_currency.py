#!/usr/bin/env python3
"""
Test script for overseas vendor currency handling

This script tests the special handling of overseas vendors (V-VC prefix) in the process_japan_exports.py module.
It verifies that:
1. For V-VC vendors, the original currency and amount are preserved
2. For non-V-VC vendors, the existing currency transformation logic is applied

Usage:
    python test_overseas_vendor_currency.py
"""

import json
import logging
import sys
from process_japan_exports import create_journal_line

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_overseas_vendor")

def create_test_entry(vendor_code, currency="R-USD", amount=375.59):
    """Create a test entry with the specified vendor code and currency"""
    return {
        "voucher_no": "APA-0000404",
        "transaction_date": "2025/4/7",
        "application_date": "2025/5/6",
        "journal_generation_date": "2025/5/23",
        "description": "Test Entry",
        "note": "",
        "receipt_invoice": "",
        "External_Document_No": "TEST-123",
        "Document_Date": "2025/4/7",
        "debit": {
            "marker": "",
            "gl_account": "G/L Account",
            "account": "74850-10",
            "sub_account": "",
            "amount": amount,
            "currency": currency,
            "department": "VCT.1692G",
            "applicant_code": "10036",
            "vendor_code": vendor_code,
            "free_field": "",
            "department_code": "VCT.1692G",
            "original_currency": currency,
            "original_amount": amount
        },
        "credit": {
            "marker": "",
            "gl_account": "Vendor",
            "account": vendor_code,
            "sub_account": "31200-10",
            "amount": amount,
            "currency": currency,
            "department": "VCT.1692G",
            "applicant_code": "10036",
            "vendor_code": vendor_code,
            "free_field": "",
            "department_code": "VCT.9999",
            "Remarks": "Test Remarks",
            "account_source": "vendor_code"
        }
    }

def test_overseas_vendor():
    """Test handling of overseas vendor (V-VC prefix)"""
    # Create a test entry with V-VC vendor code
    entry = create_test_entry("V-VC00048", "R-USD", 375.59)
    
    # Generate credit journal line
    credit_line = create_journal_line(entry, "credit")
    
    # Verify that the original currency and amount are preserved
    assert credit_line["Currency_Code"] == "R-USD", f"Expected Currency_Code to be 'R-USD', got '{credit_line['Currency_Code']}'"
    assert credit_line["Amount"] == -375.59, f"Expected Amount to be -375.59, got {credit_line['Amount']}"
    
    logger.info("✅ Overseas vendor test passed: Original currency (R-USD) and amount (375.59) preserved")
    return credit_line

def test_regular_vendor():
    """Test handling of regular vendor (non-V-VC prefix)"""
    # Create a test entry with non-V-VC vendor code
    entry = create_test_entry("V53530703", "R-USD", 375.59)
    
    # Generate credit journal line
    credit_line = create_journal_line(entry, "credit")
    
    # Verify that the currency is transformed to empty string (home currency)
    # and amount is converted to NTD
    assert credit_line["Currency_Code"] == "", f"Expected Currency_Code to be '' (empty), got '{credit_line['Currency_Code']}'"
    assert credit_line["Amount"] < -10000, f"Expected Amount to be converted to NTD (around -12143), got {credit_line['Amount']}"
    
    logger.info(f"✅ Regular vendor test passed: Currency transformed to '' and amount converted to {credit_line['Amount']}")
    return credit_line

def main():
    """Run all tests"""
    logger.info("Starting overseas vendor currency handling tests")
    
    # Test overseas vendor
    overseas_result = test_overseas_vendor()
    logger.info(f"Overseas vendor journal line: {json.dumps(overseas_result, indent=2)}")
    
    # Test regular vendor
    regular_result = test_regular_vendor()
    logger.info(f"Regular vendor journal line: {json.dumps(regular_result, indent=2)}")
    
    logger.info("All tests passed!")

if __name__ == "__main__":
    main()
