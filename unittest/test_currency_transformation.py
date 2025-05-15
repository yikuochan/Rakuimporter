#!/usr/bin/env python3
"""
Unit tests for currency transformation functionality.

This module tests the currency transformation rules for different company codes.
"""

import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process_japan_exports import transform_currency_code, transform_currency


class TestCurrencyTransformation(unittest.TestCase):
    """Test cases for currency transformation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock the exchange rates for testing
        # This is to avoid dependency on the actual exchange rate file
        self.original_get_exchange_rate = None
        
        try:
            import currency_converter
            import types
            
            # Store the original function
            self.original_get_exchange_rate = currency_converter.convert_amount
            
            # Replace with mock function
            def mock_convert_amount(amount, from_currency, to_currency, excel_path=None):
                # Define some fixed exchange rates for testing
                rates = {
                    ("USD", "NTD"): 31.0,
                    ("EUR", "NTD"): 33.5,
                    ("JPY", "NTD"): 0.21,
                    ("USD", "EUR"): 0.92,
                    ("USD", "PHP"): 56.0,
                    ("EUR", "USD"): 1.09,
                }
                
                # If currencies are the same, return the original amount
                if from_currency == to_currency:
                    return amount
                
                # Handle R- prefix
                from_curr = from_currency.replace('R-', '') if from_currency.startswith('R-') else from_currency
                to_curr = to_currency.replace('R-', '') if to_currency.startswith('R-') else to_currency
                
                # Get the rate or default to 1.0
                rate = rates.get((from_curr, to_curr), 1.0)
                
                return amount * rate
            
            # Apply the mock
            currency_converter.convert_amount = mock_convert_amount
            
        except ImportError:
            pass
    
    def tearDown(self):
        """Tear down test environment."""
        # Restore the original function if it was replaced
        if self.original_get_exchange_rate:
            import currency_converter
            currency_converter.convert_amount = self.original_get_exchange_rate

    def test_vct_currency_transformation(self):
        """Test currency transformation for VCT company."""
        # When currency is NTD for VCT, it should be transformed to empty string
        self.assertEqual(transform_currency_code("VCT", "NTD"), "")
        # Other currencies should remain unchanged
        self.assertEqual(transform_currency_code("VCT", "USD"), "USD")
        self.assertEqual(transform_currency_code("VCT", "EUR"), "EUR")

    def test_vcp_currency_transformation(self):
        """Test currency transformation for VCP company."""
        # When currency is R-PHP for VCP, it should be transformed to empty string
        self.assertEqual(transform_currency_code("VCP", "R-PHP"), "")
        # Other currencies should remain unchanged
        self.assertEqual(transform_currency_code("VCP", "USD"), "USD")
        self.assertEqual(transform_currency_code("VCP", "NTD"), "NTD")

    def test_vca_currency_transformation(self):
        """Test currency transformation for VCA company."""
        # When currency is R-USD for VCA, it should be transformed to empty string
        self.assertEqual(transform_currency_code("VCA", "R-USD"), "")
        # Other currencies should remain unchanged
        self.assertEqual(transform_currency_code("VCA", "EUR"), "EUR")
        self.assertEqual(transform_currency_code("VCA", "NTD"), "NTD")

    def test_vcg_currency_transformation(self):
        """Test currency transformation for VCG company."""
        # When currency is R-EUR for VCG, it should be transformed to empty string
        self.assertEqual(transform_currency_code("VCG", "R-EUR"), "")
        # Other currencies should remain unchanged
        self.assertEqual(transform_currency_code("VCG", "USD"), "USD")
        self.assertEqual(transform_currency_code("VCG", "NTD"), "NTD")

    def test_vcj_currency_transformation(self):
        """Test currency transformation for VCJ company."""
        # When currency is JPY for VCJ, it should be transformed to empty string
        self.assertEqual(transform_currency_code("VCJ", "JPY"), "")
        # Other currencies should remain unchanged
        self.assertEqual(transform_currency_code("VCJ", "USD"), "USD")
        self.assertEqual(transform_currency_code("VCJ", "NTD"), "NTD")

    def test_unknown_company_code(self):
        """Test currency transformation for unknown company code."""
        # For unknown company codes, currency should remain unchanged
        self.assertEqual(transform_currency_code("XYZ", "NTD"), "NTD")
        self.assertEqual(transform_currency_code("XYZ", "USD"), "USD")


    def test_currency_conversion(self):
        """Test currency conversion functionality."""
        # Test conversion from USD to NTD for VCT
        currency, amount = transform_currency("VCT", "USD", 100)
        self.assertEqual(currency, "")  # Currency code should be empty for home currency
        self.assertAlmostEqual(amount, 3232.88, delta=100)  # 100 USD ≈ 3232.88 NTD (based on actual rate)
        
        # Test conversion from USD to USD for VCA
        currency, amount = transform_currency("VCA", "R-USD", 100)
        self.assertEqual(currency, "")  # Home currency
        self.assertEqual(amount, 100)  # No conversion needed
        
        # Test with unknown company code
        currency, amount = transform_currency("XYZ", "USD", 100)
        self.assertEqual(currency, "USD")  # Currency code should remain unchanged
        self.assertEqual(amount, 100)  # Amount should remain unchanged
        
        # Test with same currency
        currency, amount = transform_currency("VCT", "NTD", 100)
        self.assertEqual(currency, "")  # Home currency
        self.assertEqual(amount, 100)  # No conversion needed

if __name__ == "__main__":
    unittest.main()
