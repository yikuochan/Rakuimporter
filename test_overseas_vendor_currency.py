#!/usr/bin/env python3
"""
Test script for overseas vendor currency handling in process_japan_exports.py.

This script tests the special case where an overseas vendor (V-VC prefix) with NTD currency
in VCT company should have the currency code set to an empty string.
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
logger = logging.getLogger("test_overseas_vendor_currency")

def test_overseas_vendor_ntd_currency():
    """
    Test the special case where an overseas vendor (V-VC prefix) with NTD currency
    in VCT company should have the currency code set to an empty string.
    """
    # Create a test entry with an overseas vendor (V-VC prefix) with NTD currency in VCT company
    test_entry = {
        "voucher_no": "APA-0000373",
        "transaction_date": "2025/4/16",
        "application_date": "2025/4/16",
        "journal_generation_date": "2025/4/16",
        "description": "Gandi.net VicOne domain renewal",
        "External_Document_No": "2025/4/16",
        "Document_Date": "2025/4/16",
        "debit": {
            "gl_account": "G/L Account",
            "account": "75562-10",
            "amount": 24436.0,
            "currency": "NTD",
            "department": "VCT.1312G",
            "department_code": "VCT.1312G"
        },
        "credit": {
            "gl_account": "Vendor",
            "vendor_code": "V-VC00048",
            "account": "V-VC00048",
            "amount": 24436.0,
            "currency": "NTD",
            "department": "VCT.9999",
            "department_code": "VCT.9999",
            "Remarks": "- 2025/04/16 - 2028/04/16 Gandi.net VicOne domain renewal."
        }
    }

    # Test case 1: Overseas vendor with NTD currency in VCT company
    logger.info("Test case 1: Overseas vendor with NTD currency in VCT company")
    credit_line = create_journal_line(test_entry, "credit")
    logger.info(f"Credit line Currency_Code: '{credit_line['Currency_Code']}'")
    assert credit_line["Currency_Code"] == "", "Currency_Code should be empty for overseas vendor with NTD currency in VCT company"
    logger.info("Test case 1 passed: Currency_Code is empty for overseas vendor with NTD currency in VCT company")

    # Test case 2: Overseas vendor with USD currency in VCT company
    logger.info("Test case 2: Overseas vendor with USD currency in VCT company")
    test_entry["credit"]["currency"] = "USD"
    credit_line = create_journal_line(test_entry, "credit")
    logger.info(f"Credit line Currency_Code: '{credit_line['Currency_Code']}'")
    assert credit_line["Currency_Code"] == "R-USD", "Currency_Code should be R-USD for overseas vendor with USD currency in VCT company"
    logger.info("Test case 2 passed: Currency_Code is R-USD for overseas vendor with USD currency in VCT company")

    # Test case 3: Overseas vendor with NTD currency in VCA company
    logger.info("Test case 3: Overseas vendor with NTD currency in VCA company")
    test_entry["credit"]["currency"] = "NTD"
    test_entry["credit"]["department"] = "VCA.9999"
    test_entry["credit"]["department_code"] = "VCA.9999"
    credit_line = create_journal_line(test_entry, "credit")
    logger.info(f"Credit line Currency_Code: '{credit_line['Currency_Code']}'")
    assert credit_line["Currency_Code"] == "R-NTD", "Currency_Code should be R-NTD for overseas vendor with NTD currency in VCA company"
    logger.info("Test case 3 passed: Currency_Code is R-NTD for overseas vendor with NTD currency in VCA company")

    logger.info("All tests passed!")

if __name__ == "__main__":
    test_overseas_vendor_ntd_currency()
