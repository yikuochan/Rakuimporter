#!/usr/bin/env python3
"""
Test for ShortcutDimCode4 logic in process_japan_exports.py

This test verifies that the ShortcutDimCode4 field is correctly set based on the source of account_no:
1. When account type is vendor and account_no comes from column O (支払先CD), ShortcutDimCode4 should be empty
2. When account type is vendor and account_no comes from column N (申請者CD/支払先CD), ShortcutDimCode4 should use the applicant_code value
"""

import unittest
import json
import os
import sys
from process_japan_exports import create_journal_line

class TestShortcutDimCode4Logic(unittest.TestCase):
    """Test cases for ShortcutDimCode4 logic in process_japan_exports.py"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a sample entry with vendor account type
        self.vendor_entry_pay_to_vendor = {
            "voucher_no": "TEST-001",
            "description": "Test Entry",
            "debit": {
                "gl_account": "Vendor",
                "account": "VENDOR123",  # Same as vendor_code (from column O)
                "vendor_code": "VENDOR123",  # From column O (支払先CD)
                "applicant_code": "EMPLOYEE456",  # From column N (申請者CD/支払先CD)
                "amount": 1000,
                "currency": "JPY",
                "department": "VCJ.1000"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "VENDOR123",  # Same as vendor_code (from column O)
                "vendor_code": "VENDOR123",  # From column O (支払先CD)
                "applicant_code": "EMPLOYEE456",  # From column N (申請者CD/支払先CD)
                "amount": 1000,
                "currency": "JPY",
                "department": "VCJ.1000"
            }
        }

        # Create a sample entry with vendor account type but account_no from applicant_code
        self.vendor_entry_pay_to_employee = {
            "voucher_no": "TEST-002",
            "description": "Test Entry",
            "debit": {
                "gl_account": "Vendor",
                "account": "EMPLOYEE456",  # Same as applicant_code (from column N)
                "vendor_code": "",  # Empty vendor_code
                "applicant_code": "EMPLOYEE456",  # From column N (申請者CD/支払先CD)
                "amount": 1000,
                "currency": "JPY",
                "department": "VCJ.1000"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "EMPLOYEE456",  # Same as applicant_code (from column N)
                "vendor_code": "",  # Empty vendor_code
                "applicant_code": "EMPLOYEE456",  # From column N (申請者CD/支払先CD)
                "amount": 1000,
                "currency": "JPY",
                "department": "VCJ.1000"
            }
        }

        # Create a sample entry with non-vendor account type
        self.non_vendor_entry = {
            "voucher_no": "TEST-003",
            "description": "Test Entry",
            "debit": {
                "gl_account": "G/L Account",
                "account": "ACCOUNT789",
                "vendor_code": "VENDOR123",
                "applicant_code": "EMPLOYEE456",
                "amount": 1000,
                "currency": "JPY",
                "department": "VCJ.1000"
            },
            "credit": {
                "gl_account": "G/L Account",
                "account": "ACCOUNT789",
                "vendor_code": "VENDOR123",
                "applicant_code": "EMPLOYEE456",
                "amount": 1000,
                "currency": "JPY",
                "department": "VCJ.1000"
            }
        }

    def test_shortcut_dim_code4_pay_to_vendor(self):
        """Test ShortcutDimCode4 is empty when account_no comes from vendor_code (column O)"""
        # Test debit line
        debit_line = create_journal_line(self.vendor_entry_pay_to_vendor, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "", 
                         "ShortcutDimCode4 should be empty for vendor payment (from column O)")

        # Test credit line
        credit_line = create_journal_line(self.vendor_entry_pay_to_vendor, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "", 
                         "ShortcutDimCode4 should be empty for vendor payment (from column O)")

    def test_shortcut_dim_code4_pay_to_employee(self):
        """Test ShortcutDimCode4 uses applicant_code when account_no comes from applicant_code (column N)"""
        # Test debit line
        debit_line = create_journal_line(self.vendor_entry_pay_to_employee, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "EMPLOYEE456", 
                         "ShortcutDimCode4 should use applicant_code for employee payment (from column N)")

        # Test credit line
        credit_line = create_journal_line(self.vendor_entry_pay_to_employee, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "EMPLOYEE456", 
                         "ShortcutDimCode4 should use applicant_code for employee payment (from column N)")

    def test_shortcut_dim_code4_non_vendor(self):
        """Test ShortcutDimCode4 uses applicant_code for non-vendor account types"""
        # Test debit line
        debit_line = create_journal_line(self.non_vendor_entry, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "EMPLOYEE456", 
                         "ShortcutDimCode4 should use applicant_code for non-vendor account types")

        # Test credit line
        credit_line = create_journal_line(self.non_vendor_entry, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "EMPLOYEE456", 
                         "ShortcutDimCode4 should use applicant_code for non-vendor account types")

if __name__ == "__main__":
    unittest.main()
