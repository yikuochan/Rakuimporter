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

from process_japan_exports import transform_currency_code


class TestCurrencyTransformation(unittest.TestCase):
    """Test cases for currency transformation functionality."""

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


if __name__ == "__main__":
    unittest.main()