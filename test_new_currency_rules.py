#!/usr/bin/env python3
"""
Test script for the new currency code conversion rules in process_japan_exports.py
"""

import unittest
from process_japan_exports import transform_currency_code, transform_currency

class TestNewCurrencyRules(unittest.TestCase):
    def test_transform_currency_code_usd(self):
        """Test the transform_currency_code function with USD"""
        # Test USD with matching company
        self.assertEqual(transform_currency_code("VCA", "USD"), "R-USD")
        self.assertEqual(transform_currency_code("VCA", "R-USD"), "R-USD")
        
        # Test USD with non-matching company
        self.assertEqual(transform_currency_code("VCT", "USD"), "USD")
        self.assertEqual(transform_currency_code("VCP", "USD"), "USD")
    
    def test_transform_currency_code_rmb(self):
        """Test the transform_currency_code function with RMB"""
        # There's no company with RMB as home currency in the current mapping
        # So it should return RMB unchanged
        self.assertEqual(transform_currency_code("VCT", "RMB"), "RMB")
        
        # We can't easily test the R-RMB case without modifying the company_currency_map
        # in the actual function, so we'll skip that part of the test
    
    def test_transform_currency_code_xeu(self):
        """Test the transform_currency_code function with XEU"""
        # Test XEU with matching company (VCG uses EUR)
        self.assertEqual(transform_currency_code("VCG", "XEU"), "R-EUR")
        self.assertEqual(transform_currency_code("VCG", "R-XEU"), "R-EUR")
        
        # Test XEU with non-matching company
        self.assertEqual(transform_currency_code("VCT", "XEU"), "XEU")
        self.assertEqual(transform_currency_code("VCP", "XEU"), "XEU")
    
    def test_transform_currency_function(self):
        """Test the transform_currency function with the new rules"""
        # Test USD with matching company
        currency, amount = transform_currency("VCA", "USD", 100.0)
        self.assertEqual(currency, "R-USD")
        self.assertEqual(amount, 100.0)
        
        # Test RMB with VCT (will be converted to NTD)
        # Since RMB is not a home currency for VCT, it will be converted to NTD
        # and the currency code will be empty (as NTD is the home currency for VCT)
        currency, amount = transform_currency("VCT", "RMB", 100.0)
        self.assertEqual(currency, "")  # Empty string because it's converted to home currency
        self.assertNotEqual(amount, 100.0)  # Amount should be converted
        
        # Test XEU with matching company (VCG uses EUR)
        currency, amount = transform_currency("VCG", "XEU", 100.0)
        self.assertEqual(currency, "R-EUR")
        self.assertEqual(amount, 100.0)

if __name__ == "__main__":
    unittest.main()
