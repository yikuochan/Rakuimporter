#!/usr/bin/env python3
"""
Test script to verify the currency transformation fix for the R-NTD issue.
This script tests the transform_currency_code function to ensure it correctly
handles home currencies without adding the R- prefix.
"""

import sys
import os

# Add the parent directory to the Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process_japan_exports import transform_currency_code

def test_currency_transformations():
    """Test various currency transformation scenarios."""
    
    print("=== Currency Transformation Fix Test ===\n")
    
    # Test cases: (company_code, currency_code, expected_result, description)
    test_cases = [
        # VCT company tests (home currency: NTD)
        ("VCT", "NTD", "", "VCT home currency NTD should become empty string"),
        ("VCT", "R-NTD", "", "VCT with R-NTD should become empty string (normalized)"),
        ("VCT", "USD", "R-USD", "VCT with foreign currency USD should get R- prefix"),
        ("VCT", "JPY", "R-JPY", "VCT with foreign currency JPY should get R- prefix"),
        ("VCT", "EUR", "R-EUR", "VCT with foreign currency EUR should get R- prefix"),
        
        # VCA company tests (home currency: USD)
        ("VCA", "USD", "", "VCA home currency USD should become empty string"),
        ("VCA", "R-USD", "", "VCA with R-USD should become empty string (normalized)"),
        ("VCA", "NTD", "R-NTD", "VCA with foreign currency NTD should get R- prefix"),
        ("VCA", "JPY", "R-JPY", "VCA with foreign currency JPY should get R- prefix"),
        
        # VCP company tests (home currency: PHP)
        ("VCP", "PHP", "", "VCP home currency PHP should become empty string"),
        ("VCP", "R-PHP", "", "VCP with R-PHP should become empty string (normalized)"),
        ("VCP", "USD", "R-USD", "VCP with foreign currency USD should get R- prefix"),
        
        # VCG company tests (home currency: EUR)
        ("VCG", "EUR", "", "VCG home currency EUR should become empty string"),
        ("VCG", "XEU", "R-EUR", "VCG with XEU should become R-EUR (special case)"),
        ("VCG", "USD", "R-USD", "VCG with foreign currency USD should get R- prefix"),
        
        # VCJ company tests (home currency: JPY)
        ("VCJ", "JPY", "", "VCJ home currency JPY should become empty string"),
        ("VCJ", "R-JPY", "", "VCJ with R-JPY should become empty string (normalized)"),
        ("VCJ", "USD", "R-USD", "VCJ with foreign currency USD should get R- prefix"),
        
        # Edge cases
        ("VCT", "", "", "Empty currency should remain empty"),
        ("UNKNOWN", "USD", "USD", "Unknown company should return original currency"),
    ]
    
    passed = 0
    failed = 0
    
    for company_code, currency_code, expected, description in test_cases:
        try:
            result = transform_currency_code(company_code, currency_code)
            
            if result == expected:
                print(f"✅ PASS: {description}")
                print(f"   Input: Company={company_code}, Currency={currency_code}")
                print(f"   Expected: '{expected}', Got: '{result}'\n")
                passed += 1
            else:
                print(f"❌ FAIL: {description}")
                print(f"   Input: Company={company_code}, Currency={currency_code}")
                print(f"   Expected: '{expected}', Got: '{result}'\n")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {description}")
            print(f"   Input: Company={company_code}, Currency={currency_code}")
            print(f"   Exception: {str(e)}\n")
            failed += 1
    
    print("=== Test Summary ===")
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! The currency transformation fix is working correctly.")
        print("The R-NTD issue should now be resolved.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the currency transformation logic.")
    
    return failed == 0

if __name__ == "__main__":
    success = test_currency_transformations()
    sys.exit(0 if success else 1)
