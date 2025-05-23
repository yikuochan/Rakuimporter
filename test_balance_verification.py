#!/usr/bin/env python3
"""
Test script for the balance verification functionality in process_japan_exports.py
"""

import unittest
import json
import logging
from process_japan_exports import verify_balanced_amounts

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestBalanceVerification(unittest.TestCase):
    def test_balanced_single_entry(self):
        """Test that a balanced single entry is correctly identified"""
        # Create a test entry with balanced debit and credit amounts
        test_entry = {
            "voucher_no": "TEST-001",
            "description": "Test Balanced Entry",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "72600-10",
                "sub_account": "72600-10",
                "amount": 100.00,
                "currency": "USD",
                "department": "VCA.1342G",
                "applicant_code": "10055",
                "vendor_code": "",
                "free_field": "Test entry",
                "department_code": "VCA.1342G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "10055",
                "sub_account": "32200-10",
                "amount": 100.00,
                "currency": "USD",
                "department": "VCA.1342G",
                "applicant_code": "10055",
                "vendor_code": "10055",
                "free_field": "Test entry",
                "department_code": "VCA.9999"
            }
        }
        
        # Verify the entry is balanced
        is_balanced, difference, debit_total, credit_total = verify_balanced_amounts(test_entry)
        
        # Assert that the entry is balanced
        self.assertTrue(is_balanced)
        self.assertAlmostEqual(difference, 0.0, places=2)
        self.assertAlmostEqual(debit_total, 100.0, places=2)
        self.assertAlmostEqual(credit_total, 100.0, places=2)
        
        logger.info(f"Balanced single entry test passed: Debit: {debit_total:.2f}, Credit: {credit_total:.2f}, Difference: {difference:.2f}")

    def test_unbalanced_single_entry(self):
        """Test that an unbalanced single entry is correctly identified"""
        # Create a test entry with unbalanced debit and credit amounts
        test_entry = {
            "voucher_no": "TEST-002",
            "description": "Test Unbalanced Entry",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "72600-10",
                "sub_account": "72600-10",
                "amount": 100.00,
                "currency": "USD",
                "department": "VCA.1342G",
                "applicant_code": "10055",
                "vendor_code": "",
                "free_field": "Test entry",
                "department_code": "VCA.1342G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "10055",
                "sub_account": "32200-10",
                "amount": 102.00,  # Intentionally different from debit
                "currency": "USD",
                "department": "VCA.1342G",
                "applicant_code": "10055",
                "vendor_code": "10055",
                "free_field": "Test entry",
                "department_code": "VCA.9999"
            }
        }
        
        # Verify the entry is unbalanced
        is_balanced, difference, debit_total, credit_total = verify_balanced_amounts(test_entry)
        
        # Assert that the entry is unbalanced
        self.assertFalse(is_balanced)
        self.assertAlmostEqual(difference, 2.0, places=2)
        self.assertAlmostEqual(debit_total, 100.0, places=2)
        self.assertAlmostEqual(credit_total, 102.0, places=2)
        
        logger.info(f"Unbalanced single entry test passed: Debit: {debit_total:.2f}, Credit: {credit_total:.2f}, Difference: {difference:.2f}")

    def test_balanced_with_currency_conversion(self):
        """Test that an entry with currency conversion is correctly balanced"""
        # Create a test entry with different currencies that should balance after conversion
        test_entry = {
            "voucher_no": "TEST-003",
            "description": "Test Currency Conversion",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "72600-10",
                "sub_account": "72600-10",
                "amount": 100.00,
                "currency": "USD",  # USD
                "department": "VCA.1342G",
                "applicant_code": "10055",
                "vendor_code": "",
                "free_field": "Test entry",
                "department_code": "VCA.1342G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "10055",
                "sub_account": "32200-10",
                "amount": 88.00,  # Approximately 100 USD in EUR
                "currency": "EUR",  # EUR
                "department": "VCA.1342G",
                "applicant_code": "10055",
                "vendor_code": "10055",
                "free_field": "Test entry",
                "department_code": "VCA.9999"
            }
        }
        
        # Verify the entry is balanced after currency conversion
        is_balanced, difference, debit_total, credit_total = verify_balanced_amounts(test_entry, tolerance=2.0)
        
        # Assert that the entry is balanced within tolerance
        # Note: The actual conversion rate may vary, so we use a larger tolerance
        self.assertTrue(is_balanced)
        self.assertLess(difference, 2.0)
        
        logger.info(f"Balanced with currency conversion test: Debit: {debit_total:.2f}, Credit: {credit_total:.2f}, Difference: {difference:.2f}")

    def test_balanced_multiple_entries(self):
        """Test that multiple entries are correctly balanced in aggregate"""
        # Create multiple test entries that should balance in aggregate
        test_entries = [
            {
                "voucher_no": "TEST-004-1",
                "description": "Test Multiple Entries 1",
                "debit": {
                    "marker": "",
                    "gl_account": "G/L Account",
                    "account": "72600-10",
                    "sub_account": "72600-10",
                    "amount": 50.00,
                    "currency": "USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10055",
                    "vendor_code": "",
                    "free_field": "Test entry",
                    "department_code": "VCA.1342G"
                },
                "credit": {
                    "marker": "",
                    "gl_account": "Vendor",
                    "account": "10055",
                    "sub_account": "32200-10",
                    "amount": 0.00,  # Will be consolidated
                    "currency": "USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10055",
                    "vendor_code": "10055",
                    "free_field": "Test entry",
                    "department_code": "VCA.9999",
                    "consolidated": True
                }
            },
            {
                "voucher_no": "TEST-004-2",
                "description": "Test Multiple Entries 2",
                "debit": {
                    "marker": "",
                    "gl_account": "G/L Account",
                    "account": "72600-10",
                    "sub_account": "72600-10",
                    "amount": 50.00,
                    "currency": "USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10055",
                    "vendor_code": "",
                    "free_field": "Test entry",
                    "department_code": "VCA.1342G"
                },
                "credit": {
                    "marker": "",
                    "gl_account": "Vendor",
                    "account": "10055",
                    "sub_account": "32200-10",
                    "amount": 100.00,  # Consolidated credit for both entries
                    "currency": "USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10055",
                    "vendor_code": "10055",
                    "free_field": "Test entry",
                    "department_code": "VCA.9999",
                    "consolidated": True
                }
            }
        ]
        
        # Verify the entries are balanced in aggregate
        is_balanced, difference, debit_total, credit_total = verify_balanced_amounts(test_entries)
        
        # Assert that the entries are balanced
        self.assertTrue(is_balanced)
        self.assertAlmostEqual(difference, 0.0, places=2)
        self.assertAlmostEqual(debit_total, 100.0, places=2)
        self.assertAlmostEqual(credit_total, 100.0, places=2)
        
        logger.info(f"Balanced multiple entries test passed: Debit: {debit_total:.2f}, Credit: {credit_total:.2f}, Difference: {difference:.2f}")

    def test_unbalanced_multiple_entries(self):
        """Test that multiple unbalanced entries are correctly identified"""
        # Create multiple test entries that are unbalanced in aggregate
        test_entries = [
            {
                "voucher_no": "TEST-005-1",
                "description": "Test Multiple Entries 1",
                "debit": {
                    "marker": "",
                    "gl_account": "G/L Account",
                    "account": "72600-10",
                    "sub_account": "72600-10",
                    "amount": 50.00,
                    "currency": "USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10055",
                    "vendor_code": "",
                    "free_field": "Test entry",
                    "department_code": "VCA.1342G"
                },
                "credit": {
                    "marker": "",
                    "gl_account": "Vendor",
                    "account": "10055",
                    "sub_account": "32200-10",
                    "amount": 0.00,  # Will be consolidated
                    "currency": "USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10055",
                    "vendor_code": "10055",
                    "free_field": "Test entry",
                    "department_code": "VCA.9999",
                    "consolidated": True
                }
            },
            {
                "voucher_no": "TEST-005-2",
                "description": "Test Multiple Entries 2",
                "debit": {
                    "marker": "",
                    "gl_account": "G/L Account",
                    "account": "72600-10",
                    "sub_account": "72600-10",
                    "amount": 50.00,
                    "currency": "USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10055",
                    "vendor_code": "",
                    "free_field": "Test entry",
                    "department_code": "VCA.1342G"
                },
                "credit": {
                    "marker": "",
                    "gl_account": "Vendor",
                    "account": "10055",
                    "sub_account": "32200-10",
                    "amount": 103.00,  # Intentionally different from total debit
                    "currency": "USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10055",
                    "vendor_code": "10055",
                    "free_field": "Test entry",
                    "department_code": "VCA.9999",
                    "consolidated": True
                }
            }
        ]
        
        # Verify the entries are unbalanced in aggregate
        is_balanced, difference, debit_total, credit_total = verify_balanced_amounts(test_entries)
        
        # Assert that the entries are unbalanced
        self.assertFalse(is_balanced)
        self.assertAlmostEqual(difference, 3.0, places=2)
        self.assertAlmostEqual(debit_total, 100.0, places=2)
        self.assertAlmostEqual(credit_total, 103.0, places=2)
        
        logger.info(f"Unbalanced multiple entries test passed: Debit: {debit_total:.2f}, Credit: {credit_total:.2f}, Difference: {difference:.2f}")

    def test_tolerance_handling(self):
        """Test that the tolerance parameter works correctly"""
        # Create a test entry with a small imbalance
        test_entry = {
            "voucher_no": "TEST-006",
            "description": "Test Tolerance Handling",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "72600-10",
                "sub_account": "72600-10",
                "amount": 100.00,
                "currency": "USD",
                "department": "VCA.1342G",
                "applicant_code": "10055",
                "vendor_code": "",
                "free_field": "Test entry",
                "department_code": "VCA.1342G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "10055",
                "sub_account": "32200-10",
                "amount": 100.05,  # Small difference of 0.05
                "currency": "USD",
                "department": "VCA.1342G",
                "applicant_code": "10055",
                "vendor_code": "10055",
                "free_field": "Test entry",
                "department_code": "VCA.9999"
            }
        }
        
        # Verify with default tolerance (0.01)
        is_balanced_default, difference_default, _, _ = verify_balanced_amounts(test_entry)
        
        # Verify with higher tolerance (0.1)
        is_balanced_higher, difference_higher, _, _ = verify_balanced_amounts(test_entry, tolerance=0.1)
        
        # Assert that the entry is unbalanced with default tolerance but balanced with higher tolerance
        self.assertFalse(is_balanced_default)
        self.assertTrue(is_balanced_higher)
        self.assertAlmostEqual(difference_default, 0.05, places=2)
        self.assertAlmostEqual(difference_higher, 0.05, places=2)
        
        logger.info(f"Tolerance handling test passed: Default tolerance (0.01): {is_balanced_default}, Higher tolerance (0.1): {is_balanced_higher}")

if __name__ == "__main__":
    logger.info("Starting balance verification tests")
    unittest.main()