#!/usr/bin/env python3
"""
Test script to verify the currency transformation fix for home currencies.
This script tests the transform_currency_code function to ensure it correctly
identifies home currencies and returns empty strings instead of R- prefixed codes.
"""

import sys
import os

# Add the parent directory to the Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process_japan_exports import transform_currency_code

def test_currency_transformation():
    """Test the currency transformation logic for all companies and currencies."""
    
    print("Testing Currency Transformation Fix")
    print("=" * 50)
    
    # Test cases: (company_code, currency_code, expected_result, description)
    test_cases = [
        # VCT company tests (home currency: NTD)
        ("VCT", "NTD", "", "VCT home currency NTD should return empty string"),
        ("VCT", "R-NTD", "", "VCT home currency R-NTD should return empty string"),
        ("VCT", "USD", "R-USD", "VCT foreign currency USD should get R- prefix"),
        ("VCT", "JPY", "R-JPY", "VCT foreign currency JPY should get R- prefix"),
        
        # VCA company tests (home currency: USD)
        ("VCA", "USD", "", "VCA home currency USD should return empty string"),
        ("VCA", "R-USD", "", "VCA home currency R-USD should return empty string"),
        ("VCA", "NTD", "R-NTD", "VCA foreign currency NTD should get R- prefix"),
        ("VCA", "EUR", "R-EUR", "VCA foreign currency EUR should get R- prefix"),
        
        # VCP company tests (home currency: PHP)
        ("VCP", "PHP", "", "VCP home currency PHP should return empty string"),
        ("VCP", "R-PHP", "", "VCP home currency R-PHP should return empty string"),
        ("VCP", "USD", "R-USD", "VCP foreign currency USD should get R- prefix"),
        ("VCP", "NTD", "R-NTD", "VCP foreign currency NTD should get R- prefix"),
        
        # VCG company tests (home currency: EUR)
        ("VCG", "EUR", "", "VCG home currency EUR should return empty string"),
        ("VCG", "R-EUR", "", "VCG home currency R-EUR should return empty string"),
        ("VCG", "XEU", "R-EUR", "VCG special case XEU should become R-EUR"),
        ("VCG", "USD", "R-USD", "VCG foreign currency USD should get R- prefix"),
        
        # VCJ company tests (home currency: JPY)
        ("VCJ", "JPY", "", "VCJ home currency JPY should return empty string"),
        ("VCJ", "R-JPY", "", "VCJ home currency R-JPY should return empty string"),
        ("VCJ", "USD", "R-USD", "VCJ foreign currency USD should get R- prefix"),
        ("VCJ", "NTD", "R-NTD", "VCJ foreign currency NTD should get R- prefix"),
        
        # Edge cases
        ("UNKNOWN", "USD", "USD", "Unknown company should return original currency"),
        ("VCT", "", "", "Empty currency should return empty string"),
    ]
    
    passed = 0
    failed = 0
    
    for company_code, currency_code, expected, description in test_cases:
        try:
            result = transform_currency_code(company_code, currency_code)
            
            if result == expected:
                print(f"✅ PASS: {description}")
                print(f"   Input: company='{company_code}', currency='{currency_code}'")
                print(f"   Expected: '{expected}', Got: '{result}'")
                passed += 1
            else:
                print(f"❌ FAIL: {description}")
                print(f"   Input: company='{company_code}', currency='{currency_code}'")
                print(f"   Expected: '{expected}', Got: '{result}'")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {description}")
            print(f"   Input: company='{company_code}', currency='{currency_code}'")
            print(f"   Exception: {str(e)}")
            failed += 1
        
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The currency transformation fix is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

def test_specific_vct_ntd_case():
    """Test the specific case that was failing: VCT company with NTD currency."""
    
    print("\nTesting Specific VCT + NTD Case")
    print("=" * 30)
    
    # This is the exact case that was failing in the logs
    company_code = "VCT"
    currency_code = "NTD"
    
    print(f"Testing: company_code='{company_code}', currency_code='{currency_code}'")
    
    try:
        result = transform_currency_code(company_code, currency_code)
        
        if result == "":
            print(f"✅ SUCCESS: VCT + NTD correctly returns empty string")
            print(f"   Result: '{result}'")
            return True
        else:
            print(f"❌ FAILURE: VCT + NTD should return empty string, got '{result}'")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    print("Currency Transformation Fix Test")
    print("This test verifies that home currencies return empty strings")
    print("instead of R- prefixed codes, which was causing API errors.\n")
    
    # Test the specific failing case first
    specific_test_passed = test_specific_vct_ntd_case()
    
    # Run comprehensive tests
    all_tests_passed = test_currency_transformation()
    
    if specific_test_passed and all_tests_passed:
        print("\n🎉 All tests passed! The fix should resolve the R-NTD API error.")
        sys.exit(0)
    else:
        print("\n❌ Tests failed. The fix needs more work.")
        sys.exit(1)
