#!/usr/bin/env python3
"""
Test script for V-VC00048 mapping to VCT for non-VCT cost centers.

This script tests the implementation of Issue #78:
For non-VCT cost centers, if vendor V-VC00048 is selected, the vendor code VCT should be used instead.
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
logger = logging.getLogger("test_v_vc00048_mapping")

def test_v_vc00048_mapping():
    """
    Test the mapping of vendor code V-VC00048 to VCT for non-VCT cost centers.
    """
    # Test case 1: V-VC00048 with non-VCT cost center (should map to VCT)
    test_entry_1 = {
        "voucher_no": "APA-0000401",
        "transaction_date": "2025/05/02",
        "application_date": "2025/05/23",
        "journal_generation_date": "2025/06/02",
        "description": "VicOne Corporate Credit Card Marketing Expense",
        "External_Document_No": "20250502",
        "Document_Date": "2025/05/02",
        "debit": {
            "gl_account": "G/L Account",
            "account": "75510-10",
            "amount": 6534.55,
            "currency": "R-USD",
            "department": "VCA.1342G",
            "department_code": "VCA.1342G"
        },
        "credit": {
            "gl_account": "Vendor",
            "vendor_code": "V-VC00048",
            "account": "V-VC00048",
            "amount": 6534.55,
            "currency": "R-USD",
            "department": "VCA.1342G",
            "department_code": "VCA.1342G",
            "Remarks": "Events"
        }
    }

    # Test case 2: V-VC00048 with VCT cost center (should remain V-VC00048)
    test_entry_2 = {
        "voucher_no": "APA-0000451",
        "transaction_date": "2025/03/31",
        "application_date": "2025/05/26",
        "journal_generation_date": "2025/06/02",
        "description": "VicOne Corporate Credit Card Saas Subscription",
        "External_Document_No": "5224028806",
        "Document_Date": "2025/03/31",
        "debit": {
            "gl_account": "G/L Account",
            "account": "76900-10",
            "amount": 15917.00,
            "currency": "NTD",
            "department": "VCT.1692G",
            "department_code": "VCT.1692G"
        },
        "credit": {
            "gl_account": "Vendor",
            "vendor_code": "V-VC00048",
            "account": "V-VC00048",
            "amount": 15917.00,
            "currency": "NTD",
            "department": "VCT.1692G",
            "department_code": "VCT.1692G",
            "Remarks": "Google Cloud Billing"
        }
    }

    # Test case 3: Different vendor code (should remain unchanged)
    test_entry_3 = {
        "voucher_no": "APA-0000500",
        "transaction_date": "2025/05/15",
        "application_date": "2025/05/30",
        "journal_generation_date": "2025/06/02",
        "description": "Office Supplies",
        "External_Document_No": "INV12345",
        "Document_Date": "2025/05/15",
        "debit": {
            "gl_account": "G/L Account",
            "account": "76100-10",
            "amount": 5000.00,
            "currency": "NTD",
            "department": "VCT.1234G",
            "department_code": "VCT.1234G"
        },
        "credit": {
            "gl_account": "Vendor",
            "vendor_code": "VENDOR123",
            "account": "VENDOR123",
            "amount": 5000.00,
            "currency": "NTD",
            "department": "VCT.1234G",
            "department_code": "VCT.1234G",
            "Remarks": "Office supplies"
        }
    }

    # Test case 4: Consolidated entry with V-VC00048 and non-VCT cost center
    test_entry_4 = {
        "voucher_no": "APA-0000600",
        "transaction_date": "2025/05/20",
        "application_date": "2025/05/30",
        "journal_generation_date": "2025/06/02",
        "description": "Consolidated Credit Card Expenses",
        "External_Document_No": "CONS12345",
        "Document_Date": "2025/05/20",
        "debit": {
            "gl_account": "G/L Account",
            "account": "75510-10",
            "amount": 10000.00,
            "currency": "R-USD",
            "department": "VCA.1342G",
            "department_code": "VCA.1342G"
        },
        "credit": {
            "gl_account": "Vendor",
            "vendor_code": "V-VC00048",
            "account": "V-VC00048",
            "amount": 10000.00,
            "currency": "R-USD",
            "department": "VCA.1342G",
            "department_code": "VCA.1342G",
            "Remarks": "Consolidated expenses",
            "consolidated": True,
            "original_entries_count": 3,
            "consolidation_note": "Consolidated from 3 entries"
        }
    }

    # Run test case 1: V-VC00048 with non-VCT cost center (should map to VCT)
    logger.info("Test case 1: V-VC00048 with non-VCT cost center (VCA)")
    credit_line_1 = create_journal_line(test_entry_1, "credit")
    logger.info(f"Credit line Account_No: '{credit_line_1['Account_No']}'")
    assert credit_line_1["Account_No"] == "VCT", "Account_No should be mapped to VCT for V-VC00048 with non-VCT cost center"
    logger.info("Test case 1 passed: Account_No is mapped to VCT for V-VC00048 with non-VCT cost center")

    # Run test case 2: V-VC00048 with VCT cost center (should remain V-VC00048)
    logger.info("Test case 2: V-VC00048 with VCT cost center")
    credit_line_2 = create_journal_line(test_entry_2, "credit")
    logger.info(f"Credit line Account_No: '{credit_line_2['Account_No']}'")
    assert credit_line_2["Account_No"] == "V-VC00048", "Account_No should remain V-VC00048 for VCT cost center"
    logger.info("Test case 2 passed: Account_No remains V-VC00048 for VCT cost center")

    # Run test case 3: Different vendor code (should remain unchanged)
    logger.info("Test case 3: Different vendor code")
    credit_line_3 = create_journal_line(test_entry_3, "credit")
    logger.info(f"Credit line Account_No: '{credit_line_3['Account_No']}'")
    assert credit_line_3["Account_No"] == "VENDOR123", "Account_No should remain unchanged for different vendor codes"
    logger.info("Test case 3 passed: Account_No remains unchanged for different vendor codes")

    # Run test case 4: Consolidated entry with V-VC00048 and non-VCT cost center
    logger.info("Test case 4: Consolidated entry with V-VC00048 and non-VCT cost center")
    credit_line_4 = create_journal_line(test_entry_4, "credit")
    logger.info(f"Credit line Account_No: '{credit_line_4['Account_No']}'")
    assert credit_line_4["Account_No"] == "VCT", "Account_No should be mapped to VCT for consolidated entry with V-VC00048 and non-VCT cost center"
    logger.info("Test case 4 passed: Account_No is mapped to VCT for consolidated entry with V-VC00048 and non-VCT cost center")

    logger.info("All tests passed!")

if __name__ == "__main__":
    test_v_vc00048_mapping()
