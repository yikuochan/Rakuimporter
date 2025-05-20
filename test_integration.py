#!/usr/bin/env python3
"""
Integration test for the currency code refactoring.
This test verifies that the entire flow works correctly, from CSV to JSON conversion
to exchange rate query with the R- prefix.
"""

import os
import sys
import json
import logging
from unittest.mock import patch, MagicMock

# Set required environment variables for testing
os.environ["ERP_CLIENT_ID"] = "test_client_id"
os.environ["ERP_CLIENT_SECRET"] = "test_client_secret"

# Import the modules we want to test
from csv_to_json_converter import normalize_currency
from exchange_rate_query import get_exchange_rate
from process_japan_exports import create_journal_line

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_integration")

def test_currency_normalization():
    """Test the currency normalization in csv_to_json_converter.py"""
    print("\n=== Testing Currency Normalization ===")
    
    # Test Japanese currency names
    assert normalize_currency("台湾ドル") == "NTD", "Failed to normalize 台湾ドル to NTD"
    print("✓ Successfully normalized 台湾ドル to NTD")
    
    assert normalize_currency("円") == "JPY", "Failed to normalize 円 to JPY"
    print("✓ Successfully normalized 円 to JPY")
    
    # Test other currencies (should remain unchanged)
    assert normalize_currency("USD") == "USD", "Failed to keep USD unchanged"
    print("✓ Successfully kept USD unchanged")

@patch('exchange_rate_query.api_client')
@patch('exchange_rate_query.get_home_currency')
def test_exchange_rate_query(mock_get_home_currency, mock_api_client):
    """Test the exchange rate query with R- prefix handling"""
    print("\n=== Testing Exchange Rate Query ===")
    
    # Setup mocks
    mock_get_home_currency.return_value = "JPY"
    mock_api_client.get_exchange_rate.return_value = 0.0092  # Example rate
    
    # Test home currency to foreign currency
    rate = get_exchange_rate("JPY", "USD")
    args, _ = mock_api_client.get_exchange_rate.call_args
    assert args[0] == "JPY", "Home currency should not have R- prefix"
    assert args[1] == "R-USD", "Foreign currency should have R- prefix"
    print(f"✓ Successfully added R- prefix to USD: {args[1]}")
    
    # Test foreign currency to foreign currency
    mock_api_client.get_exchange_rate.reset_mock()
    rate = get_exchange_rate("USD", "EUR")
    args, _ = mock_api_client.get_exchange_rate.call_args
    assert args[0] == "R-USD", "First foreign currency should have R- prefix"
    assert args[1] == "R-EUR", "Second foreign currency should have R- prefix"
    print(f"✓ Successfully added R- prefix to both USD and EUR: {args[0]}, {args[1]}")

def test_journal_line_creation():
    """Test the journal line creation with special currency cases"""
    print("\n=== Testing Journal Line Creation ===")
    
    # Load test data
    with open("test_sample_with_original_currency.json", 'r', encoding='utf-8') as f:
        entries = json.load(f)
    
    # Test USD entry
    usd_entry = entries[0]
    debit_line = create_journal_line(usd_entry, "debit")
    assert debit_line["Currency_Code"] == "USD", f"Expected USD, got {debit_line['Currency_Code']}"
    print(f"✓ Successfully processed USD entry: {debit_line['Currency_Code']}")
    
    # Test RMB entry
    rmb_entry = entries[1]
    debit_line = create_journal_line(rmb_entry, "debit")
    assert debit_line["Currency_Code"] == "R-RMB", f"Expected R-RMB, got {debit_line['Currency_Code']}"
    print(f"✓ Successfully processed RMB entry: {debit_line['Currency_Code']}")
    
    # Test XEU entry
    xeu_entry = entries[2]
    debit_line = create_journal_line(xeu_entry, "debit")
    assert debit_line["Currency_Code"] == "R-EUR", f"Expected R-EUR, got {debit_line['Currency_Code']}"
    print(f"✓ Successfully processed XEU entry: {debit_line['Currency_Code']}")

def main():
    """Run all tests"""
    try:
        test_currency_normalization()
        test_exchange_rate_query()
        test_journal_line_creation()
        print("\n=== All tests passed! ===")
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
