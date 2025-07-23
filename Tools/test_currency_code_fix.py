#!/usr/bin/env python3
"""
Test script to verify the currency code fix for all companies.

This script tests the transform_currency_code function to ensure:
1. Home currencies return empty string
2. Foreign currencies get R- prefix
3. All companies are handled correctly
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process_japan_exports import transform_currency_code

def test_currency_code_transformation():
    """Test currency code transformation for all companies."""
    
    print("Testing Currency Code Transformation Fix")
    print("=" * 50)
    
    # Test cases: (company_code, currency_code, expected_result, description)
    test_cases = [
        # VCT Company (Taiwan - NTD home currency)
        ("VCT", "NTD", "", "VCT + NTD (home currency) → empty"),
        ("VCT", "R-NTD", "", "VCT + R-NTD (home currency with prefix) → empty"),
        ("VCT", "USD", "R-USD", "VCT + USD (foreign currency) → R-USD"),
        ("VCT", "JPY", "R-JPY", "VCT + JPY (foreign currency) → R-JPY"),
        ("VCT", "R-USD", "R-USD", "VCT + R-USD (already prefixed) → R-USD"),
        
        # VCA Company (America - USD home currency)
        ("VCA", "USD", "", "VCA + USD (home currency) → empty"),
        ("VCA", "R-USD", "", "VCA + R-USD (home currency with prefix) → empty"),
        ("VCA", "NTD", "R-NTD", "VCA + NTD (foreign currency) → R-NTD"),
        ("VCA", "PHP", "R-PHP", "VCA + PHP (foreign currency) → R-PHP"),
        ("VCA", "R-NTD", "R-NTD", "VCA + R-NTD (already prefixed) → R-NTD"),
        
        # VCP Company (Philippines - PHP home currency)
        ("VCP", "PHP", "", "VCP + PHP (home currency) → empty"),
        ("VCP", "R-PHP", "", "VCP + R-PHP (home currency with prefix) → empty"),
        ("VCP", "USD", "R-USD", "VCP + USD (foreign currency) → R-USD"),
        ("VCP", "NTD", "R-NTD", "VCP + NTD (foreign currency) → R-NTD"),
        ("VCP", "R-USD", "R-USD", "VCP + R-USD (already prefixed) → R-USD"),
        
        # VCG Company (Germany - EUR home currency)
        ("VCG", "EUR", "", "VCG + EUR (home currency) → empty"),
        ("VCG", "R-EUR", "", "VCG + R-EUR (home currency with prefix) → empty"),
        ("VCG", "USD", "R-USD", "VCG + USD (foreign currency) → R-USD"),
        ("VCG", "NTD", "R-NTD", "VCG + NTD (foreign currency) → R-NTD"),
        ("VCG", "XEU", "R-EUR", "VCG + XEU (special case) → R-EUR"),
        
        # VCJ Company (Japan - JPY home currency)
        ("VCJ", "JPY", "", "VCJ + JPY (home currency) → empty"),
        ("VCJ", "R-JPY", "", "VCJ + R-JPY (home currency with prefix) → empty"),
        ("VCJ", "USD", "R-USD", "VCJ + USD (foreign currency) → R-USD"),
        ("VCJ", "NTD", "R-NTD", "VCJ + NTD (foreign currency) → R-NTD"),
        ("VCJ", "R-USD", "R-USD", "VCJ + R-USD (already prefixed) → R-USD"),
        
        # Unknown company (should return original)
        ("XXX", "USD", "USD", "XXX + USD (unknown company) → USD"),
        ("XXX", "NTD", "NTD", "XXX + NTD (unknown company) → NTD"),
    ]
    
    passed = 0
    failed = 0
    
    for company_code, currency_code, expected, description in test_cases:
        try:
            result = transform_currency_code(company_code, currency_code)
            
            if result == expected:
                print(f"✅ PASS: {description}")
                print(f"   Input: {company_code} + {currency_code} → Output: '{result}'")
                passed += 1
            else:
                print(f"❌ FAIL: {description}")
                print(f"   Input: {company_code} + {currency_code}")
                print(f"   Expected: '{expected}', Got: '{result}'")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {description}")
            print(f"   Exception: {str(e)}")
            failed += 1
        
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Currency code fix is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

def test_original_issue():
    """Test the specific issue from the error log."""
    
    print("\nTesting Original Issue (VCT + NTD)")
    print("=" * 40)
    
    # The original issue: VCT company with NTD currency was getting "R-NTD"
    # This should now return empty string
    result = transform_currency_code("VCT", "NTD")
    
    if result == "":
        print("✅ ORIGINAL ISSUE FIXED!")
        print("   VCT + NTD → '' (empty string)")
        print("   This will prevent the 'R-NTD currency not found' error")
        return True
    else:
        print("❌ ORIGINAL ISSUE NOT FIXED!")
        print(f"   VCT + NTD → '{result}' (should be empty string)")
        return False

if __name__ == "__main__":
    print("Currency Code Fix Verification Test")
    print("=" * 60)
    
    # Test the transformation function
    transformation_ok = test_currency_code_transformation()
    
    # Test the original issue specifically
    original_issue_ok = test_original_issue()
    
    print("\n" + "=" * 60)
    if transformation_ok and original_issue_ok:
        print("🎉 ALL TESTS PASSED! The currency code fix is working correctly.")
        print("\nThe fix will resolve the 'R-NTD currency not found' error by:")
        print("1. Returning empty string for home currencies (VCT + NTD → '')")
        print("2. Adding R- prefix only for foreign currencies")
        print("3. Working consistently across all companies")
        sys.exit(0)
    else:
        print("⚠️  SOME TESTS FAILED! Please review the implementation.")
        sys.exit(1)
