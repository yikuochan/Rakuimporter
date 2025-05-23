#!/usr/bin/env python3
"""
Test script for the OBA-0000028 case with real data
"""

import json
import logging
from process_japan_exports import create_journal_line, transform_currency

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_oba_0000028():
    """Test the OBA-0000028 case with real data"""
    # Create a test entry that simulates OBA-0000028
    test_entry = {
        "voucher_no": "OBA-0000028",
        "description": "Test Entry for OBA-0000028",
        "debit": {
            "marker": "",
            "gl_account": "G/L Account",
            "account": "72600-10",
            "sub_account": "72600-10",
            "amount": 202.37,  # This is the converted amount in USD
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
            "amount": 177.99,
            "currency": "R-EUR",  # This is the currency that was causing the issue
            "department": "VCA.1342G",
            "applicant_code": "10055",
            "vendor_code": "10055",
            "free_field": "Test entry",
            "department_code": "VCA.9999"
        }
    }
    
    # Process the credit line (which was causing the issue)
    try:
        credit_line = create_journal_line(test_entry, "credit")
        logger.info(f"Successfully created credit line for OBA-0000028")
        logger.info(f"Credit line: {json.dumps(credit_line, indent=2)}")
        
        # Verify that the currency code is empty (converted to home currency)
        assert credit_line["Currency_Code"] == "", "Currency_Code should be empty after conversion to home currency"
        
        # Verify that the amount is converted correctly (approximately)
        # The exact conversion rate may vary, so we just check that it's close to the expected value
        expected_amount = -202.37  # Negative because it's a credit line
        assert abs(credit_line["Amount"] - expected_amount) < 5.0, f"Amount {credit_line['Amount']} is not close to expected {expected_amount}"
        
        logger.info(f"All assertions passed for OBA-0000028 credit line")
        return True
    except Exception as e:
        logger.error(f"Error processing OBA-0000028: {str(e)}")
        return False

def test_direct_transform_currency():
    """Test the transform_currency function directly with OBA-0000028 data"""
    company_code = "VCA"  # VCA's home currency is USD
    currency_code = "R-EUR"
    amount = 177.99
    
    try:
        transformed_currency, converted_amount = transform_currency(company_code, currency_code, amount)
        logger.info(f"Direct transform_currency test: {amount} {currency_code} -> {converted_amount:.2f} {transformed_currency or 'USD'}")
        
        # Verify that the currency code is empty (converted to home currency)
        assert transformed_currency == "", "Currency_Code should be empty after conversion to home currency"
        
        # Verify that the amount is converted correctly (approximately)
        expected_amount = 202.37
        assert abs(converted_amount - expected_amount) < 5.0, f"Amount {converted_amount} is not close to expected {expected_amount}"
        
        logger.info(f"All assertions passed for direct transform_currency test")
        return True
    except Exception as e:
        logger.error(f"Error in direct transform_currency test: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting OBA-0000028 test")
    
    # Test the OBA-0000028 case
    success1 = test_oba_0000028()
    
    # Test the transform_currency function directly
    success2 = test_direct_transform_currency()
    
    # Print overall result
    if success1 and success2:
        logger.info("All tests passed successfully!")
        print("SUCCESS: All tests passed!")
    else:
        logger.error("Some tests failed!")
        print("FAILURE: Some tests failed!")