#!/usr/bin/env python3
"""
Test script for the currency prefix fix in process_japan_exports.py
Specifically tests the issue with OBA-0000028 where the currency code has an "R-" prefix
"""

import unittest
from process_japan_exports import transform_currency

class TestCurrencyPrefixFix(unittest.TestCase):
    def test_r_eur_to_usd_conversion(self):
        """Test that R-EUR to USD conversion works correctly"""
        # This simulates the OBA-0000028 case where R-EUR needs to be converted to USD
        company_code = "VCA"  # VCA's home currency is USD
        currency_code = "R-EUR"
        amount = 177.99
        
        # Call the transform_currency function
        transformed_currency, converted_amount = transform_currency(company_code, currency_code, amount)
        
        # The function should return empty string for currency (as it's converted to home currency)
        # and a converted amount (which will vary based on exchange rate)
        self.assertEqual(transformed_currency, "")
        self.assertGreater(converted_amount, 0)  # Just verify it's a positive number
        
        # Print the conversion result for manual verification
        print(f"Converted {amount} {currency_code} to {converted_amount:.2f} USD")
    
    def test_normalized_currency_used_for_conversion(self):
        """Test that the normalized currency (without R- prefix) is used for conversion"""
        # Mock the convert_amount function to verify it's called with the correct parameters
        import sys
        from unittest.mock import patch
        
        # Define a mock convert_amount function
        def mock_convert_amount(amount, from_currency, to_currency, **kwargs):
            # Verify that from_currency is normalized (without R- prefix)
            self.assertEqual(from_currency, "EUR")
            self.assertEqual(to_currency, "USD")
            # Return a fixed conversion rate for testing
            return amount * 1.137, True
        
        # Patch the convert_amount function in process_japan_exports module
        with patch('process_japan_exports.convert_amount', side_effect=mock_convert_amount):
            # Call transform_currency with R-EUR
            transformed_currency, converted_amount = transform_currency("VCA", "R-EUR", 177.99)
            
            # Verify the results
            self.assertEqual(transformed_currency, "")
            self.assertAlmostEqual(converted_amount, 202.37, places=2)

if __name__ == "__main__":
    unittest.main()