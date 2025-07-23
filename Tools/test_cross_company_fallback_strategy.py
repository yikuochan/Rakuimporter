#!/usr/bin/env python3
"""
Test script for cross-company exchange rate fallback strategy.

This test verifies that the enhanced exchange rate query logic can handle
cross-company scenarios where the primary company doesn't have the required
exchange rates, and falls back to other companies intelligently.
"""

import sys
import os
import logging
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the modules to test
from core.exchange_rate_query import (
    get_exchange_rate, 
    get_exchange_rate_with_fallback, 
    get_company_for_home_currency
)
from utils.company_currency_mapping import COMPANY_HOME_CURRENCY

class TestCrossCompanyFallbackStrategy(unittest.TestCase):
    """Test cases for cross-company exchange rate fallback strategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = logging.getLogger(__name__)
        
    def test_get_company_for_home_currency(self):
        """Test that we can find companies by their home currency."""
        self.logger.info("Testing get_company_for_home_currency function...")
        
        # Test known mappings
        test_cases = [
            ("NTD", "VCT"),
            ("USD", "VCA"),
            ("PHP", "VCP"),
            ("EUR", "VCG"),
            ("JPY", "VCJ"),
            ("UNKNOWN", None)
        ]
        
        for currency, expected_company in test_cases:
            with self.subTest(currency=currency):
                result = get_company_for_home_currency(currency)
                self.assertEqual(result, expected_company)
                self.logger.info(f"✅ {currency} -> {result} (expected: {expected_company})")
    
    @patch('core.exchange_rate_query.api_client')
    def test_fallback_strategy_order(self, mock_api_client):
        """Test that the fallback strategy tries companies in the correct order."""
        self.logger.info("Testing fallback strategy company order...")
        
        # Mock API client to fail for first few companies, succeed for last
        def mock_get_exchange_rate(from_curr, to_curr, company, **kwargs):
            if company == "VCJ":  # Succeed only for VCJ (master company)
                return 1.75
            else:
                raise Exception(f"No rates in company {company}")
        
        mock_api_client.get_exchange_rate.side_effect = mock_get_exchange_rate
        
        # Test VCP (PHP) trying to get NTD to PHP rate
        # Expected order: VCP -> VCT (NTD home) -> VCP (PHP home, duplicate) -> VCJ
        rate = get_exchange_rate_with_fallback("NTD", "PHP", "VCP")
        
        # Should succeed with rate from VCJ
        self.assertEqual(rate, 1.75)
        
        # Verify the calls were made in correct order
        calls = mock_api_client.get_exchange_rate.call_args_list
        companies_tried = [call[0][2] for call in calls]  # Third positional argument is company
        
        # Should try: VCP, VCT (NTD home), VCJ (master)
        expected_companies = ["VCP", "VCT", "VCJ"]
        actual_companies = companies_tried[:len(expected_companies)]
        
        self.logger.info(f"Companies tried: {actual_companies}")
        self.logger.info(f"Expected order: {expected_companies}")
        
        # Verify VCP was tried first
        self.assertEqual(actual_companies[0], "VCP")
        # Verify VCT (NTD home) was tried
        self.assertIn("VCT", actual_companies)
        # Verify VCJ (master) was tried last and succeeded
        self.assertEqual(actual_companies[-1], "VCJ")
        
        self.logger.info("✅ Fallback strategy order is correct")
    
    @patch('core.exchange_rate_query.api_client')
    def test_successful_primary_company(self, mock_api_client):
        """Test that primary company is used when it has the rates."""
        self.logger.info("Testing successful primary company lookup...")
        
        # Mock API client to succeed for primary company
        mock_api_client.get_exchange_rate.return_value = 32.5
        
        rate = get_exchange_rate_with_fallback("USD", "NTD", "VCT")
        
        # Should succeed with primary company
        self.assertEqual(rate, 32.5)
        
        # Verify only one call was made to primary company
        mock_api_client.get_exchange_rate.assert_called_once_with(
            "USD", "NTD", "VCT", use_month_start=False
        )
        
        self.logger.info("✅ Primary company lookup successful")
    
    @patch('core.exchange_rate_query.api_client')
    def test_home_currency_fallback(self, mock_api_client):
        """Test fallback to companies where currencies are home currencies."""
        self.logger.info("Testing home currency fallback...")
        
        # Mock API client to fail for primary, succeed for home currency company
        def mock_get_exchange_rate(from_curr, to_curr, company, **kwargs):
            if company == "VCT":  # VCT is home for NTD
                return 0.57  # NTD to PHP rate
            else:
                raise Exception(f"No rates in company {company}")
        
        mock_api_client.get_exchange_rate.side_effect = mock_get_exchange_rate
        
        # VCP trying to get NTD to PHP, should fallback to VCT (NTD home)
        rate = get_exchange_rate_with_fallback("NTD", "PHP", "VCP")
        
        self.assertEqual(rate, 0.57)
        
        # Verify VCT was called (NTD home company)
        calls = mock_api_client.get_exchange_rate.call_args_list
        companies_tried = [call[0][2] for call in calls]  # Third positional argument is company
        self.assertIn("VCT", companies_tried)
        
        self.logger.info("✅ Home currency fallback successful")
    
    @patch('core.exchange_rate_query.api_client')
    def test_all_companies_fail(self, mock_api_client):
        """Test behavior when all companies fail to provide exchange rates."""
        self.logger.info("Testing all companies fail scenario...")
        
        # Mock API client to always fail
        mock_api_client.get_exchange_rate.side_effect = Exception("No rates available")
        
        # Should raise exception when all companies fail
        with self.assertRaises(Exception) as context:
            get_exchange_rate_with_fallback("NTD", "PHP", "VCP")
        
        error_message = str(context.exception)
        self.assertIn("No exchange rate found", error_message)
        self.assertIn("NTD to PHP", error_message)
        
        self.logger.info("✅ All companies fail scenario handled correctly")
    
    @patch('core.exchange_rate_query.api_client')
    def test_main_get_exchange_rate_with_fallback(self, mock_api_client):
        """Test the main get_exchange_rate function with fallback integration."""
        self.logger.info("Testing main get_exchange_rate function with fallback...")
        
        # Mock API client to fail for primary, succeed for fallback
        def mock_get_exchange_rate(from_curr, to_curr, company, **kwargs):
            if company == "VCJ":  # Master company succeeds
                return 29.5
            else:
                raise Exception(f"No rates in company {company}")
        
        mock_api_client.get_exchange_rate.side_effect = mock_get_exchange_rate
        
        # Test with VCP company (should fallback to VCJ)
        rate = get_exchange_rate("NTD", "PHP", "VCP")
        
        self.assertEqual(rate, 29.5)
        
        self.logger.info("✅ Main function with fallback integration successful")
    
    @patch('core.exchange_rate_query.api_client')
    def test_last_resort_1_to_1_conversion(self, mock_api_client):
        """Test 1:1 conversion as last resort when all fallbacks fail."""
        self.logger.info("Testing 1:1 conversion as last resort...")
        
        # Mock API client to always fail
        mock_api_client.get_exchange_rate.side_effect = Exception("No rates available")
        
        # Should return 1.0 as last resort
        rate = get_exchange_rate("NTD", "PHP", "VCP")
        
        self.assertEqual(rate, 1.0)
        
        self.logger.info("✅ 1:1 conversion last resort working correctly")
    
    def test_same_currency_optimization(self):
        """Test that same currency returns 1.0 immediately."""
        self.logger.info("Testing same currency optimization...")
        
        rate = get_exchange_rate("USD", "USD", "VCA")
        self.assertEqual(rate, 1.0)
        
        self.logger.info("✅ Same currency optimization working")


def run_cross_company_fallback_tests():
    """Run all cross-company fallback strategy tests."""
    print("=" * 80)
    print("CROSS-COMPANY EXCHANGE RATE FALLBACK STRATEGY TESTS")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCrossCompanyFallbackStrategy)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
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
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED - Cross-company fallback strategy is working correctly!")
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} test(s) failed")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_cross_company_fallback_tests()
    sys.exit(0 if success else 1)
