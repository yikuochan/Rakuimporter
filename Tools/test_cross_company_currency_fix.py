#!/usr/bin/env python3
"""
Test Cross-Company Currency Conversion Fix

This test verifies that currency conversion works correctly across different companies,
specifically testing the issue where VCP company with NTD transactions should query
exchange rates using "NTD" (not "R-NTD") but post to Business Central using "R-NTD".

The test validates the original design intent:
1. Exchange rate queries use original currency codes (NTD, USD, JPY, PHP, EUR)
2. R- prefix is only added during Business Central API posting
3. Cross-company scenarios work correctly (e.g., VCP + NTD, VCT + USD)
"""

import sys
import os
import unittest
import logging
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules we need to test
from core.exchange_rate_query import get_exchange_rate
from core.process_japan_exports import transform_currency_code, create_journal_line
from company_currency_mapping import COMPANY_HOME_CURRENCY

class TestCrossCompanyCurrencyFix(unittest.TestCase):
    """Test cross-company currency conversion scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging to capture debug information
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Test data for different company scenarios
        self.test_scenarios = [
            {
                "name": "VCP_with_NTD",
                "company": "VCP",
                "home_currency": "PHP",
                "foreign_currency": "NTD",
                "expected_exchange_query_from": "PHP",
                "expected_exchange_query_to": "NTD",  # Should NOT be "R-NTD"
                "expected_bc_posting_currency": "R-NTD"  # Should be "R-NTD" for BC posting
            },
            {
                "name": "VCT_with_USD",
                "company": "VCT",
                "home_currency": "NTD",
                "foreign_currency": "USD",
                "expected_exchange_query_from": "NTD",
                "expected_exchange_query_to": "USD",  # Should NOT be "R-USD"
                "expected_bc_posting_currency": "R-USD"  # Should be "R-USD" for BC posting
            },
            {
                "name": "VCA_with_JPY",
                "company": "VCA",
                "home_currency": "USD",
                "foreign_currency": "JPY",
                "expected_exchange_query_from": "USD",
                "expected_exchange_query_to": "JPY",  # Should NOT be "R-JPY"
                "expected_bc_posting_currency": "R-JPY"  # Should be "R-JPY" for BC posting
            },
            {
                "name": "VCG_with_NTD",
                "company": "VCG",
                "home_currency": "EUR",
                "foreign_currency": "NTD",
                "expected_exchange_query_from": "EUR",
                "expected_exchange_query_to": "NTD",  # Should NOT be "R-NTD"
                "expected_bc_posting_currency": "R-NTD"  # Should be "R-NTD" for BC posting
            },
            {
                "name": "VCJ_with_PHP",
                "company": "VCJ",
                "home_currency": "JPY",
                "foreign_currency": "PHP",
                "expected_exchange_query_from": "JPY",
                "expected_exchange_query_to": "PHP",  # Should NOT be "R-PHP"
                "expected_bc_posting_currency": "R-PHP"  # Should be "R-PHP" for BC posting
            }
        ]
    
    def test_company_currency_mapping(self):
        """Test that company currency mapping is correct."""
        expected_mappings = {
            "VCT": "NTD",
            "VCP": "PHP",
            "VCA": "USD",
            "VCG": "EUR",
            "VCJ": "JPY"
        }
        
        for company, expected_currency in expected_mappings.items():
            actual_currency = COMPANY_HOME_CURRENCY.get(company)
            self.assertEqual(actual_currency, expected_currency, 
                           f"Company {company} should have home currency {expected_currency}, got {actual_currency}")
    
    @patch('core.exchange_rate_api.ExchangeRateAPI')
    def test_exchange_rate_query_currency_codes(self, mock_api_class):
        """Test that exchange rate queries use original currency codes without R- prefix."""
        # Mock the API client
        mock_api_instance = MagicMock()
        mock_api_class.return_value = mock_api_instance
        mock_api_instance.get_exchange_rate.return_value = 32.5  # Mock exchange rate
        
        for scenario in self.test_scenarios:
            with self.subTest(scenario=scenario["name"]):
                self.logger.info(f"Testing exchange rate query for scenario: {scenario['name']}")
                
                # Call get_exchange_rate
                try:
                    rate = get_exchange_rate(
                        from_currency=scenario["expected_exchange_query_from"],
                        to_currency=scenario["expected_exchange_query_to"],
                        company_name=scenario["company"]
                    )
                    
                    # Verify the API was called with the correct currency codes
                    mock_api_instance.get_exchange_rate.assert_called()
                    call_args = mock_api_instance.get_exchange_rate.call_args
                    
                    # Extract the actual currency codes passed to the API
                    actual_from_currency = call_args[0][0]  # First positional argument
                    actual_to_currency = call_args[0][1]    # Second positional argument
                    
                    self.logger.info(f"API called with: from={actual_from_currency}, to={actual_to_currency}")
                    
                    # Verify that NO R- prefix was added during exchange rate query
                    self.assertEqual(actual_from_currency, scenario["expected_exchange_query_from"],
                                   f"Exchange rate query should use {scenario['expected_exchange_query_from']}, not {actual_from_currency}")
                    self.assertEqual(actual_to_currency, scenario["expected_exchange_query_to"],
                                   f"Exchange rate query should use {scenario['expected_exchange_query_to']}, not {actual_to_currency}")
                    
                    # Verify that the rate was returned
                    self.assertEqual(rate, 32.5)
                    
                except Exception as e:
                    self.fail(f"Exchange rate query failed for {scenario['name']}: {str(e)}")
                
                # Reset the mock for the next iteration
                mock_api_instance.reset_mock()
    
    def test_business_central_posting_currency_transformation(self):
        """Test that Business Central posting correctly transforms currency codes with R- prefix."""
        for scenario in self.test_scenarios:
            with self.subTest(scenario=scenario["name"]):
                self.logger.info(f"Testing BC posting currency transformation for scenario: {scenario['name']}")
                
                # Test transform_currency_code function
                transformed_currency = transform_currency_code(
                    company_code=scenario["company"],
                    currency_code=scenario["foreign_currency"]
                )
                
                self.assertEqual(transformed_currency, scenario["expected_bc_posting_currency"],
                               f"BC posting should transform {scenario['foreign_currency']} to {scenario['expected_bc_posting_currency']}, got {transformed_currency}")
    
    def test_home_currency_handling(self):
        """Test that home currencies are handled correctly (empty string for BC posting)."""
        for scenario in self.test_scenarios:
            with self.subTest(scenario=scenario["name"]):
                self.logger.info(f"Testing home currency handling for scenario: {scenario['name']}")
                
                # Test that home currency becomes empty string for BC posting
                transformed_currency = transform_currency_code(
                    company_code=scenario["company"],
                    currency_code=scenario["home_currency"]
                )
                
                self.assertEqual(transformed_currency, "",
                               f"Home currency {scenario['home_currency']} for company {scenario['company']} should become empty string, got '{transformed_currency}'")
    
    def test_journal_line_creation_currency_consistency(self):
        """Test that journal line creation applies currency transformation consistently."""
        # Create a test entry for VCP company with NTD currency
        test_entry = {
            "voucher_no": "VPA-TEST-001",
            "Document_Date": "2025-01-21",
            "description": "Test cross-company currency",
            "debit": {
                "amount": 1000.0,
                "currency": "NTD",
                "department": "VCP.1234",
                "account": "12345-10",
                "gl_account": "G/L Account",
                "applicant_code": "TEST001"
            },
            "credit": {
                "amount": 1000.0,
                "currency": "NTD",
                "department": "VCP.1234",
                "vendor_code": "V-TEST001",
                "gl_account": "Vendor",
                "Remarks": "Test credit entry"
            }
        }
        
        # Test debit line creation
        debit_line = create_journal_line(test_entry, "debit")
        self.assertEqual(debit_line["Currency_Code"], "R-NTD",
                        f"Debit line should have Currency_Code 'R-NTD' for VCP company with NTD, got '{debit_line['Currency_Code']}'")
        
        # Test credit line creation
        credit_line = create_journal_line(test_entry, "credit")
        self.assertEqual(credit_line["Currency_Code"], "R-NTD",
                        f"Credit line should have Currency_Code 'R-NTD' for VCP company with NTD, got '{credit_line['Currency_Code']}'")
        
        self.logger.info(f"Journal line currency codes - Debit: '{debit_line['Currency_Code']}', Credit: '{credit_line['Currency_Code']}'")
    
    def test_vct_home_currency_special_case(self):
        """Test VCT company with NTD (home currency) becomes empty string."""
        # Create a test entry for VCT company with NTD currency (home currency)
        test_entry = {
            "voucher_no": "VCT-TEST-001",
            "Document_Date": "2025-01-21",
            "description": "Test VCT home currency",
            "debit": {
                "amount": 1000.0,
                "currency": "NTD",
                "department": "VCT.1234",
                "account": "12345-10",
                "gl_account": "G/L Account",
                "applicant_code": "TEST001"
            },
            "credit": {
                "amount": 1000.0,
                "currency": "NTD",
                "department": "VCT.1234",
                "vendor_code": "V-TEST001",
                "gl_account": "Vendor",
                "Remarks": "Test credit entry"
            }
        }
        
        # Test debit line creation
        debit_line = create_journal_line(test_entry, "debit")
        self.assertEqual(debit_line["Currency_Code"], "",
                        f"VCT debit line should have empty Currency_Code for NTD (home currency), got '{debit_line['Currency_Code']}'")
        
        # Test credit line creation
        credit_line = create_journal_line(test_entry, "credit")
        self.assertEqual(credit_line["Currency_Code"], "",
                        f"VCT credit line should have empty Currency_Code for NTD (home currency), got '{credit_line['Currency_Code']}'")
        
        self.logger.info(f"VCT home currency test - Debit: '{debit_line['Currency_Code']}', Credit: '{credit_line['Currency_Code']}'")
    
    def test_r_prefix_not_duplicated(self):
        """Test that R- prefix is not duplicated if currency already has it."""
        # Test with currency that already has R- prefix
        transformed_currency = transform_currency_code("VCP", "R-NTD")
        self.assertEqual(transformed_currency, "R-NTD",
                        f"Currency with existing R- prefix should not be duplicated, got '{transformed_currency}'")
        
        # Test with various R- prefixed currencies
        test_cases = [
            ("VCP", "R-USD", "R-USD"),
            ("VCT", "R-JPY", "R-JPY"),
            ("VCA", "R-EUR", "R-EUR"),
        ]
        
        for company, input_currency, expected_output in test_cases:
            with self.subTest(company=company, currency=input_currency):
                result = transform_currency_code(company, input_currency)
                self.assertEqual(result, expected_output,
                               f"R- prefix should not be duplicated for {company} with {input_currency}")

def run_cross_company_currency_tests():
    """Run the cross-company currency conversion tests."""
    print("=" * 80)
    print("CROSS-COMPANY CURRENCY CONVERSION FIX TESTS")
    print("=" * 80)
    print()
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCrossCompanyCurrencyFix)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_cross_company_currency_tests()
    sys.exit(0 if success else 1)
