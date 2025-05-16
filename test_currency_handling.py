#!/usr/bin/env python3
"""
Test script for currency handling in process_japan_exports.py
"""

import unittest
from process_japan_exports import create_journal_line, transform_currency_code

class TestCurrencyHandling(unittest.TestCase):
    def test_original_currency_and_amount_in_debit(self):
        """Test that original_currency and original_amount are used for debit lines"""
        # Create a test entry with original_currency and original_amount in debit
        test_entry = {
            "voucher_no": "TEST-001",
            "description": "Test Entry",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "72600-10",
                "sub_account": "72600-10",
                "amount": 9559.27,  # This is the converted amount in NTD
                "currency": "NTD",
                "department": "VCT.1342G",
                "applicant_code": "10055",
                "vendor_code": "",
                "free_field": "Test entry",
                "department_code": "VCT.1342G",
                "original_currency": "XEU",
                "original_amount": 260.0
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "10055",
                "sub_account": "32200-10",
                "amount": 260.0,
                "currency": "XEU",
                "department": "VCT.1342G",
                "applicant_code": "10055",
                "vendor_code": "10055",
                "free_field": "Test entry",
                "department_code": "VCT.9999"
            }
        }
        
        # Create journal line for debit
        debit_line = create_journal_line(test_entry, "debit")
        
        # Check that the original currency and amount are used
        self.assertEqual(debit_line["Currency_Code"], transform_currency_code("VCT", "XEU"))
        self.assertEqual(debit_line["Amount"], 260.0)
        
        # Create a test entry without original_currency and original_amount
        test_entry_without_original = {
            "voucher_no": "TEST-002",
            "description": "Test Entry Without Original",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "72600-10",
                "sub_account": "72600-10",
                "amount": 9559.27,
                "currency": "NTD",
                "department": "VCT.1342G",
                "applicant_code": "10055",
                "vendor_code": "",
                "free_field": "Test entry",
                "department_code": "VCT.1342G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "10055",
                "sub_account": "32200-10",
                "amount": 260.0,
                "currency": "XEU",
                "department": "VCT.1342G",
                "applicant_code": "10055",
                "vendor_code": "10055",
                "free_field": "Test entry",
                "department_code": "VCT.9999"
            }
        }
        
        # Create journal line for debit without original values
        debit_line_without_original = create_journal_line(test_entry_without_original, "debit")
        
        # Check that the regular currency transformation is applied
        self.assertEqual(debit_line_without_original["Currency_Code"], transform_currency_code("VCT", "NTD"))
        self.assertEqual(debit_line_without_original["Amount"], 9559.27)

    def test_transform_currency_code(self):
        """Test the transform_currency_code function"""
        # Test with matching company and currency
        self.assertEqual(transform_currency_code("VCT", "NTD"), "")
        self.assertEqual(transform_currency_code("VCP", "PHP"), "")
        
        # Test with non-matching company and currency
        self.assertEqual(transform_currency_code("VCT", "USD"), "USD")
        self.assertEqual(transform_currency_code("VCP", "EUR"), "EUR")
        
        # Test with R- prefix
        self.assertEqual(transform_currency_code("VCT", "R-NTD"), "")
        self.assertEqual(transform_currency_code("VCP", "R-PHP"), "")

if __name__ == "__main__":
    unittest.main()
