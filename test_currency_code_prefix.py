#!/usr/bin/env python3
"""
Test script for verifying the currency code prefix handling in exchange_rate_query.py.
This test ensures that the R- prefix is correctly added to currency codes based on home currency.
"""

import sys
import logging
import unittest
from unittest.mock import patch, MagicMock
from exchange_rate_query import get_exchange_rate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_currency_code_prefix")

class TestCurrencyCodePrefix(unittest.TestCase):
    """Test cases for currency code prefix handling."""
    
    @patch('exchange_rate_query.api_client')
    @patch('exchange_rate_query.get_home_currency')
    def test_home_currency_no_prefix(self, mock_get_home_currency, mock_api_client):
        """Test that home currency doesn't get R- prefix."""
        # Setup
        mock_get_home_currency.return_value = "JPY"
        mock_api_client.get_exchange_rate.return_value = 1.0
        
        # Execute
        get_exchange_rate("JPY", "USD")
        
        # Verify
        mock_api_client.get_exchange_rate.assert_called_once()
        args, _ = mock_api_client.get_exchange_rate.call_args
        self.assertEqual(args[0], "JPY")  # First currency should not have R- prefix
        self.assertEqual(args[1], "R-USD")  # Second currency should have R- prefix
    
    @patch('exchange_rate_query.api_client')
    @patch('exchange_rate_query.get_home_currency')
    def test_non_home_currency_gets_prefix(self, mock_get_home_currency, mock_api_client):
        """Test that non-home currency gets R- prefix."""
        # Setup
        mock_get_home_currency.return_value = "JPY"
        mock_api_client.get_exchange_rate.return_value = 1.0
        
        # Execute
        get_exchange_rate("USD", "EUR")
        
        # Verify
        mock_api_client.get_exchange_rate.assert_called_once()
        args, _ = mock_api_client.get_exchange_rate.call_args
        self.assertEqual(args[0], "R-USD")  # First currency should have R- prefix
        self.assertEqual(args[1], "R-EUR")  # Second currency should have R- prefix
    
    @patch('exchange_rate_query.api_client')
    @patch('exchange_rate_query.get_home_currency')
    def test_already_prefixed_currency(self, mock_get_home_currency, mock_api_client):
        """Test that already prefixed currency doesn't get double prefix."""
        # Setup
        mock_get_home_currency.return_value = "JPY"
        mock_api_client.get_exchange_rate.return_value = 1.0
        
        # Execute
        get_exchange_rate("R-USD", "EUR")
        
        # Verify
        mock_api_client.get_exchange_rate.assert_called_once()
        args, _ = mock_api_client.get_exchange_rate.call_args
        self.assertEqual(args[0], "R-USD")  # First currency should keep its prefix
        self.assertEqual(args[1], "R-EUR")  # Second currency should have R- prefix
    
    @patch('exchange_rate_query.api_client')
    @patch('exchange_rate_query.get_home_currency')
    def test_same_currency_no_api_call(self, mock_get_home_currency, mock_api_client):
        """Test that same currency doesn't make API call."""
        # Setup
        mock_get_home_currency.return_value = "JPY"
        
        # Execute
        result = get_exchange_rate("USD", "USD")
        
        # Verify
        mock_api_client.get_exchange_rate.assert_not_called()
        self.assertEqual(result, 1.0)  # Should return 1.0 for same currency
    
    @patch('exchange_rate_query.api_client')
    @patch('exchange_rate_query.get_home_currency')
    def test_home_currency_conversion(self, mock_get_home_currency, mock_api_client):
        """Test conversion between home currency and foreign currency."""
        # Setup
        mock_get_home_currency.return_value = "JPY"
        mock_api_client.get_exchange_rate.return_value = 0.0092  # Example rate: 1 JPY = 0.0092 USD
        
        # Execute
        result = get_exchange_rate("JPY", "USD")
        
        # Verify
        mock_api_client.get_exchange_rate.assert_called_once()
        args, _ = mock_api_client.get_exchange_rate.call_args
        self.assertEqual(args[0], "JPY")  # Home currency should not have R- prefix
        self.assertEqual(args[1], "R-USD")  # Foreign currency should have R- prefix
        self.assertEqual(result, 0.0092)  # Should return the mocked rate

if __name__ == "__main__":
    unittest.main()
