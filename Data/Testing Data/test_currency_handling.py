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
        # XEU is now always transformed to R-EUR
        self.assertEqual(debit_line["Currency_Code"], "R-EUR")
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
        self.assertEqual(transform_currency_code("VCT", "USD"), "R-USD")
        self.assertEqual(transform_currency_code("VCP", "EUR"), "R-EUR")
        
        # Test with R- prefix
        self.assertEqual(transform_currency_code("VCT", "R-NTD"), "")
        self.assertEqual(transform_currency_code("VCP", "R-PHP"), "")
        
        # Test new currency code conversion rules
        self.assertEqual(transform_currency_code("VCA", "USD"), "")  # USD is home currency for VCA
        self.assertEqual(transform_currency_code("VCG", "USD"), "R-USD")  # USD is not home currency for VCG
        self.assertEqual(transform_currency_code("VCT", "RMB"), "R-RMB")  # Not a home currency for VCT
        
        # Test EUR with VCG - should return empty string since EUR is home currency for VCG
        self.assertEqual(transform_currency_code("VCG", "EUR"), "")
        # Test EUR with VCT - should return R-EUR since EUR is not home currency for VCT
        self.assertEqual(transform_currency_code("VCT", "EUR"), "R-EUR")
        
        # Test with R- prefix for home currencies - should still return empty string
        self.assertEqual(transform_currency_code("VCA", "R-USD"), "")  # R-USD for VCA is normalized to USD, which is home currency
        self.assertEqual(transform_currency_code("VCT", "R-NTD"), "")  # R-NTD for VCT is normalized to NTD, which is home currency
        
        # Test new requirements for NTD, JPY, and PHP as non-home currencies
        self.assertEqual(transform_currency_code("VCA", "NTD"), "R-NTD")  # NTD is not home currency for VCA
        self.assertEqual(transform_currency_code("VCT", "JPY"), "R-JPY")  # JPY is not home currency for VCT
        self.assertEqual(transform_currency_code("VCJ", "PHP"), "R-PHP")  # PHP is not home currency for VCJ
        
    def test_shortcut_dim_code4_logic(self):
        """Test that ShortcutDimCode4 always uses applicant_code for both debit and credit lines"""
        from process_japan_exports import create_journal_line
        
        # Test case 1: Entry with applicant_code present
        test_entry_with_applicant = {
            "voucher_no": "TEST-001",
            "description": "Test Entry",
            "debit": {
                "gl_account": "G/L Account",
                "account": "72600-10",
                "amount": 1000,
                "currency": "NTD",
                "department": "VCT.1342G",
                "applicant_code": "APP123",
                "vendor_code": "VEND456"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "10055",
                "amount": 1000,
                "currency": "NTD",
                "department": "VCT.1342G",
                "applicant_code": "APP789",
                "vendor_code": "VEND456"
            }
        }
        
        # Create journal lines
        debit_line = create_journal_line(test_entry_with_applicant, "debit")
        credit_line = create_journal_line(test_entry_with_applicant, "credit")
        
        # Check that applicant_code is used for ShortcutDimCode4 in both lines
        self.assertEqual(debit_line["ShortcutDimCode4"], "APP123")
        self.assertEqual(credit_line["ShortcutDimCode4"], "APP789")
        
        # Test case 2: Entry with empty applicant_code
        test_entry_without_applicant = {
            "voucher_no": "TEST-002",
            "description": "Test Entry",
            "debit": {
                "gl_account": "G/L Account",
                "account": "72600-10",
                "amount": 1000,
                "currency": "NTD",
                "department": "VCT.1342G",
                "applicant_code": "",
                "vendor_code": "VEND456"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "10055",
                "amount": 1000,
                "currency": "NTD",
                "department": "VCT.1342G",
                "applicant_code": "",
                "vendor_code": "VEND456"
            }
        }
        
        # Create journal lines
        debit_line_empty = create_journal_line(test_entry_without_applicant, "debit")
        credit_line_empty = create_journal_line(test_entry_without_applicant, "credit")
        
        # Check that ShortcutDimCode4 is empty when applicant_code is empty
        self.assertEqual(debit_line_empty["ShortcutDimCode4"], "")
        self.assertEqual(credit_line_empty["ShortcutDimCode4"], "")

if __name__ == "__main__":
    unittest.main()
