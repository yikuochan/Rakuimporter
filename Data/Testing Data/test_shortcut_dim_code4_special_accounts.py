#!/usr/bin/env python3
"""
Test for ShortcutDimCode4 special accounts logic in process_japan_exports.py

This test verifies that the ShortcutDimCode4 field is correctly set to "N/A" for specific debit accounts:
- When debit account is "72600-10", ShortcutDimCode4 should be "N/A"
- When debit account is "72600-30", ShortcutDimCode4 should be "N/A"
- This rule takes precedence over all other ShortcutDimCode4 logic
"""

import unittest
import json
import os
import sys

# Add the parent directory to the path to import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.process_japan_exports import create_journal_line

class TestShortcutDimCode4SpecialAccounts(unittest.TestCase):
    """Test cases for ShortcutDimCode4 special accounts logic in process_japan_exports.py"""

    def setUp(self):
        """Set up test fixtures"""
        # Test entry with debit account 72600-10 (from SD4 test data)
        self.entry_72600_10 = {
            "voucher_no": "APA-0000447",
            "transaction_date": "2025/05/22",
            "application_date": "2025/05/23",
            "journal_generation_date": "2025/06/22",
            "description": "Peter Yang改票費用 May 15 Berlin-Vienna",
            "note": "",
            "receipt_invoice": "",
            "External_Document_No": "T400755571",
            "Document_Date": "2025/05/22",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "72600-10",
                "sub_account": "",
                "amount": 33700.0,
                "currency": "NTD",
                "department": "VCT.1692G",
                "applicant_code": "Z00006",
                "vendor_code": "V04315397",
                "free_field": "",
                "department_code": "VCT.1692G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "V04315397",
                "sub_account": "31200-10",
                "amount": 33700.0,
                "currency": "NTD",
                "department": "VCT.1692G",
                "applicant_code": "Z00006",
                "vendor_code": "V04315397",
                "free_field": "",
                "department_code": "VCT.9999",
                "Remarks": "Peter Yang改票費用 May 15 Berlin-Vienna",
                "account_source": "vendor_code"
            }
        }

        # Test entry with debit account 72600-30 (from SD4 test data)
        self.entry_72600_30 = {
            "voucher_no": "APA-0000515",
            "transaction_date": "2025/05/06",
            "application_date": "2025/06/16",
            "journal_generation_date": "2025/06/22",
            "description": "桃園機場差旅接送｜東輝租車 202502〜202504",
            "note": "",
            "receipt_invoice": "",
            "External_Document_No": "PD30826076",
            "Document_Date": "2025/05/06",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "72600-30",
                "sub_account": "72600-30",
                "amount": 37590.0,
                "currency": "NTD",
                "department": "VCT.1751G",
                "applicant_code": "10129",
                "vendor_code": "V22665986",
                "free_field": "",
                "department_code": "VCT.1751G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "V22665986",
                "sub_account": "31200-10",
                "amount": 37590.0,
                "currency": "NTD",
                "department": "VCT.1751G",
                "applicant_code": "10129",
                "vendor_code": "V22665986",
                "free_field": "",
                "department_code": "VCT.9999",
                "Remarks": "桃園機場差旅接送｜東輝租車 202502〜202504",
                "account_source": "vendor_code"
            }
        }

        # Test entry with different debit account (should follow existing logic)
        self.entry_other_account = {
            "voucher_no": "TEST-001",
            "transaction_date": "2025/05/22",
            "application_date": "2025/05/23",
            "journal_generation_date": "2025/06/22",
            "description": "Test Entry",
            "note": "",
            "receipt_invoice": "",
            "External_Document_No": "TEST001",
            "Document_Date": "2025/05/22",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "50000-10",  # Different account
                "sub_account": "",
                "amount": 1000.0,
                "currency": "NTD",
                "department": "VCT.1000G",
                "applicant_code": "TEST123",
                "vendor_code": "VENDOR123",
                "free_field": "",
                "department_code": "VCT.1000G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "VENDOR123",
                "sub_account": "31200-10",
                "amount": 1000.0,
                "currency": "NTD",
                "department": "VCT.1000G",
                "applicant_code": "TEST123",
                "vendor_code": "VENDOR123",
                "free_field": "",
                "department_code": "VCT.9999",
                "Remarks": "Test Entry",
                "account_source": "vendor_code"
            }
        }

        # Test entry with vendor account type and special debit account (to test precedence)
        self.entry_vendor_with_special_account = {
            "voucher_no": "TEST-002",
            "transaction_date": "2025/05/22",
            "application_date": "2025/05/23",
            "journal_generation_date": "2025/06/22",
            "description": "Test Vendor Entry",
            "note": "",
            "receipt_invoice": "",
            "External_Document_No": "TEST002",
            "Document_Date": "2025/05/22",
            "debit": {
                "marker": "",
                "gl_account": "Vendor",  # Vendor account type
                "account": "72600-10",  # Special account
                "sub_account": "",
                "amount": 1000.0,
                "currency": "NTD",
                "department": "VCT.1000G",
                "applicant_code": "TEST456",
                "vendor_code": "VENDOR456",
                "free_field": "",
                "department_code": "VCT.1000G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "VENDOR456",
                "sub_account": "31200-10",
                "amount": 1000.0,
                "currency": "NTD",
                "department": "VCT.1000G",
                "applicant_code": "TEST456",
                "vendor_code": "VENDOR456",
                "free_field": "",
                "department_code": "VCT.9999",
                "Remarks": "Test Vendor Entry",
                "account_source": "applicant_code"
            }
        }

    def test_debit_account_72600_10(self):
        """Test ShortcutDimCode4 is 'N/A' when debit account is 72600-10"""
        # Test debit line
        debit_line = create_journal_line(self.entry_72600_10, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "N/A", 
                         "ShortcutDimCode4 should be 'N/A' for debit account 72600-10")

        # Test credit line (should follow existing logic, not affected by special rule)
        credit_line = create_journal_line(self.entry_72600_10, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "", 
                         "ShortcutDimCode4 should follow existing logic for credit line")

    def test_debit_account_72600_30(self):
        """Test ShortcutDimCode4 is 'N/A' when debit account is 72600-30"""
        # Test debit line
        debit_line = create_journal_line(self.entry_72600_30, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "N/A", 
                         "ShortcutDimCode4 should be 'N/A' for debit account 72600-30")

        # Test credit line (should follow existing logic, not affected by special rule)
        credit_line = create_journal_line(self.entry_72600_30, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "", 
                         "ShortcutDimCode4 should follow existing logic for credit line")

    def test_other_debit_account(self):
        """Test ShortcutDimCode4 follows existing logic for other debit accounts"""
        # Test debit line with different account
        # Based on the test data, this is a vendor payment scenario (credit has vendor_code account_source)
        # So the debit line should have empty ShortcutDimCode4
        debit_line = create_journal_line(self.entry_other_account, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "", 
                         "ShortcutDimCode4 should be empty for debit line of vendor payment")

        # Test credit line
        credit_line = create_journal_line(self.entry_other_account, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "", 
                         "ShortcutDimCode4 should be empty for vendor payment from vendor_code")

    def test_precedence_over_vendor_logic(self):
        """Test that special account rule takes precedence over vendor account logic"""
        # Test debit line with vendor account type but special account number
        debit_line = create_journal_line(self.entry_vendor_with_special_account, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "N/A", 
                         "ShortcutDimCode4 should be 'N/A' even for vendor account type with special account number")

        # Test credit line (should follow existing vendor logic)
        credit_line = create_journal_line(self.entry_vendor_with_special_account, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "TEST456", 
                         "ShortcutDimCode4 should use applicant_code for vendor credit from applicant_code")

    def test_credit_lines_not_affected(self):
        """Test that credit lines with special accounts are not affected by the special rule"""
        # Create a test entry where credit account is one of the special accounts
        entry_credit_special = {
            "voucher_no": "TEST-003",
            "transaction_date": "2025/05/22",
            "application_date": "2025/05/23",
            "journal_generation_date": "2025/06/22",
            "description": "Test Credit Special",
            "note": "",
            "receipt_invoice": "",
            "External_Document_No": "TEST003",
            "Document_Date": "2025/05/22",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "50000-10",
                "sub_account": "",
                "amount": 1000.0,
                "currency": "NTD",
                "department": "VCT.1000G",
                "applicant_code": "TEST789",
                "vendor_code": "VENDOR789",
                "free_field": "",
                "department_code": "VCT.1000G"
            },
            "credit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "72600-10",  # Special account in credit
                "sub_account": "",
                "amount": 1000.0,
                "currency": "NTD",
                "department": "VCT.1000G",
                "applicant_code": "TEST789",
                "vendor_code": "VENDOR789",
                "free_field": "",
                "department_code": "VCT.1000G",
                "Remarks": "Test Credit Special"
            }
        }

        # Test debit line (should follow existing logic)
        debit_line = create_journal_line(entry_credit_special, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "TEST789", 
                         "ShortcutDimCode4 should use applicant_code for regular debit account")

        # Test credit line (should follow existing logic, not special rule)
        credit_line = create_journal_line(entry_credit_special, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "TEST789", 
                         "ShortcutDimCode4 should use applicant_code for credit line, not special rule")

    def test_case_sensitivity(self):
        """Test that account matching is case-sensitive"""
        # Create entry with mixed case account number (since numbers don't change with .lower())
        import copy
        entry_mixed_case = copy.deepcopy(self.entry_72600_10)
        entry_mixed_case["debit"]["account"] = "72600-1O"  # Using capital O instead of zero

        debit_line = create_journal_line(entry_mixed_case, "debit")
        # Should follow existing logic, not special rule
        # Since this is still a vendor payment scenario, it should be empty string
        self.assertEqual(debit_line["ShortcutDimCode4"], "", 
                        "ShortcutDimCode4 should follow existing vendor logic for different account")

    def test_partial_match_not_triggered(self):
        """Test that partial matches don't trigger the special rule"""
        # Create entry with similar but different account number
        entry_similar = self.entry_72600_10.copy()
        entry_similar["debit"]["account"] = "72600-101"  # Similar but different

        debit_line = create_journal_line(entry_similar, "debit")
        # Should follow existing logic, not special rule
        self.assertNotEqual(debit_line["ShortcutDimCode4"], "N/A", 
                           "ShortcutDimCode4 should not use special rule for similar account")

if __name__ == "__main__":
    unittest.main()
