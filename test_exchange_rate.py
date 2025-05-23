"""
Unit tests for the exchange rate functionality.

This module tests the API-based exchange rate functions.
"""

import unittest
from unittest.mock import patch, MagicMock
import datetime
from exchange_rate_query import get_exchange_rate
from exchange_rate_api import ExchangeRateAPI

class TestExchangeRate(unittest.TestCase):
    
    @patch('exchange_rate_api.OAuthTokenHelper.acquire_token')
    @patch('exchange_rate_api.requests.get')
    def test_api_exchange_rate_direct(self, mock_get, mock_acquire_token):
        """Test direct conversion from foreign currency to home currency"""
        # Mock the token response
        mock_acquire_token.return_value = {
            "access_token": "fake_token",
            "expires_in": 3600
        }
        
        # Mock the exchange rate response for VCJ (JPY is home currency)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "Currency_Code": "USD",
                    "Exchange_Rate_Amount": 1,
                    "Relational_Exch_Rate_Amount": 149.53,
                    "Starting_Date": "2025-04-01"
                }
            ]
        }
        mock_get.return_value = mock_response
        mock_response.raise_for_status = MagicMock()
        
        # Test USD to JPY conversion
        api_client = ExchangeRateAPI()
        rate = api_client.get_exchange_rate("USD", "JPY", "VCJ")
        self.assertAlmostEqual(rate, 149.53, places=2)
        
    @patch('exchange_rate_api.OAuthTokenHelper.acquire_token')
    @patch('exchange_rate_api.requests.get')
    def test_api_exchange_rate_inverse(self, mock_get, mock_acquire_token):
        """Test conversion from home currency to foreign currency"""
        # Mock the token response
        mock_acquire_token.return_value = {
            "access_token": "fake_token",
            "expires_in": 3600
        }
        
        # Mock the exchange rate response for VCJ (JPY is home currency)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "Currency_Code": "USD",
                    "Exchange_Rate_Amount": 1,
                    "Relational_Exch_Rate_Amount": 149.53,
                    "Starting_Date": "2025-04-01"
                }
            ]
        }
        mock_get.return_value = mock_response
        mock_response.raise_for_status = MagicMock()
        
        # Test JPY to USD conversion (inverse of USD to JPY)
        api_client = ExchangeRateAPI()
        rate = api_client.get_exchange_rate("JPY", "USD", "VCJ")
        self.assertAlmostEqual(rate, 1/149.53, places=5)
        
    @patch('exchange_rate_api.OAuthTokenHelper.acquire_token')
    @patch('exchange_rate_api.requests.get')
    def test_api_exchange_rate_cross(self, mock_get, mock_acquire_token):
        """Test cross-conversion between two foreign currencies"""
        # Mock the token response
        mock_acquire_token.return_value = {
            "access_token": "fake_token",
            "expires_in": 3600
        }
        
        # Mock the exchange rate response for VCJ (JPY is home currency)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "Currency_Code": "USD",
                    "Exchange_Rate_Amount": 1,
                    "Relational_Exch_Rate_Amount": 149.53,
                    "Starting_Date": "2025-04-01"
                },
                {
                    "Currency_Code": "EUR",
                    "Exchange_Rate_Amount": 1,
                    "Relational_Exch_Rate_Amount": 162.03,
                    "Starting_Date": "2025-04-01"
                }
            ]
        }
        mock_get.return_value = mock_response
        mock_response.raise_for_status = MagicMock()
        
        # Test USD to EUR conversion (cross-rate)
        api_client = ExchangeRateAPI()
        rate = api_client.get_exchange_rate("USD", "EUR", "VCJ")
        # USD/EUR = (USD/JPY) / (EUR/JPY) = 149.53 / 162.03
        expected_rate = 149.53 / 162.03
        self.assertAlmostEqual(rate, expected_rate, places=5)
        
    @patch('exchange_rate_api.OAuthTokenHelper.acquire_token')
    @patch('exchange_rate_api.requests.get')
    def test_api_exchange_rate_with_prefix(self, mock_get, mock_acquire_token):
        """Test handling of currency code prefixes"""
        # Mock the token response
        mock_acquire_token.return_value = {
            "access_token": "fake_token",
            "expires_in": 3600
        }
        
        # Mock the exchange rate response for VCT (NTD is home currency)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "Currency_Code": "R-USD",
                    "Exchange_Rate_Amount": 100,
                    "Relational_Exch_Rate_Amount": 3233,
                    "Starting_Date": "2025-04-01"
                }
            ]
        }
        mock_get.return_value = mock_response
        mock_response.raise_for_status = MagicMock()
        
        # Test R-USD to NTD conversion
        api_client = ExchangeRateAPI()
        rate = api_client.get_exchange_rate("R-USD", "NTD", "VCT")
        # 100 USD = 3233 NTD, so 1 USD = 32.33 NTD
        self.assertAlmostEqual(rate, 32.33, places=2)
        
        # Test USD to NTD conversion (should normalize the currency code)
        rate = api_client.get_exchange_rate("USD", "NTD", "VCT")
        self.assertAlmostEqual(rate, 32.33, places=2)
        
    def test_same_currency(self):
        """Test that conversion between the same currency returns 1.0"""
        rate = get_exchange_rate("USD", "USD")
        self.assertEqual(rate, 1.0)
        
    @patch('exchange_rate_api.OAuthTokenHelper.acquire_token')
    @patch('exchange_rate_api.requests.get')
    def test_use_month_start(self, mock_get, mock_acquire_token):
        """Test that use_month_start parameter sets the date to the first day of the month"""
        # Mock the token response
        mock_acquire_token.return_value = {
            "access_token": "fake_token",
            "expires_in": 3600
        }
        
        # Mock the exchange rate response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "value": [
                {
                    "Currency_Code": "USD",
                    "Exchange_Rate_Amount": 1,
                    "Relational_Exch_Rate_Amount": 149.53,
                    "Starting_Date": "2025-05-01"
                }
            ]
        }
        mock_get.return_value = mock_response
        mock_response.raise_for_status = MagicMock()
        
        # Test with use_month_start=True
        api_client = ExchangeRateAPI()
        
        # Use a specific date (e.g., May 15, 2025)
        test_date = "2025-05-15"
        api_client.get_exchange_rate("USD", "JPY", "VCJ", date=test_date, use_month_start=True)
        
        # Check that the API was called with the first day of the month
        # Extract the URL from the call arguments
        call_args = mock_get.call_args[0][0]
        
        # Verify that the URL contains the first day of the month
        self.assertIn("Starting_Date le 2025-05-01", call_args)

if __name__ == '__main__':
    unittest.main()
