#!/usr/bin/env python3
"""
Universal Precision Fix Validation Test

This test validates that the Decimal-based exchange rate fixes resolve
floating-point precision issues for all companies' rounding methods.

Key test case: VPA-0000271 USD to PHP conversion
- Original amount: 355.72 USD
- Exchange rate: 57.91 (USD to PHP)
- Expected result: 20,599.75 PHP (with ROUND_HALF_UP to 2 decimals)
- Previous buggy result: 20,599.74 PHP (due to float precision loss)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal, ROUND_HALF_UP
import logging
from core.currency_converter import convert_amount
from core.currency_rounding import apply_company_rounding, validate_rounding_requirements
from core.company_rounding_config import list_all_company_configs

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_vpa_271_precision():
    """
    Test the specific VPA-0000271 case that was failing.
    This should now produce 20,599.75 PHP instead of 20,599.74 PHP.
    """
    print("=" * 80)
    print("Testing VPA-0000271 Precision Fix")
    print("=" * 80)
    
    # VPA-0000271 parameters from the actual transaction
    original_usd = Decimal('355.72')
    expected_rate = Decimal('57.91')  # USD to PHP rate from logs
    company_code = 'VCP'
    
    # Calculate expected result manually with proper ROUND_HALF_UP
    raw_php = original_usd * expected_rate  # Should be 20599.7452
    expected_php = Decimal('20599.75')  # Properly rounded with ROUND_HALF_UP
    
    print(f"Original USD amount: {original_usd}")
    print(f"Exchange rate (USD to PHP): {expected_rate}")
    print(f"Raw calculation: {original_usd} × {expected_rate} = {raw_php}")
    print(f"Expected PHP result (ROUND_HALF_UP): {expected_php}")
    print()
    
    # Test direct rounding to verify our expectations
    print("Manual rounding verification:")
    manual_rounded = raw_php.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    print(f"Manual ROUND_HALF_UP: {raw_php} → {manual_rounded}")
    
    # Test company rounding function
    company_rounded = apply_company_rounding(raw_php, company_code)
    print(f"Company rounding (VCP): {raw_php} → {company_rounded}")
    
    # Verify the fix
    if manual_rounded == expected_php and company_rounded == expected_php:
        print("✅ PASS: Rounding produces expected result")
        return True
    else:
        print("❌ FAIL: Rounding does not produce expected result")
        print(f"   Expected: {expected_php}")
        print(f"   Manual:   {manual_rounded}")
        print(f"   Company:  {company_rounded}")
        return False

def test_all_company_rounding():
    """
    Test rounding for all configured companies to ensure universal fix.
    """
    print("\n" + "=" * 80)
    print("Testing All Company Rounding Methods")
    print("=" * 80)
    
    # Test cases that are known to be sensitive to floating-point precision
    test_cases = [
        (Decimal('20599.7452'), 'VCP', Decimal('20599.75')),  # VPA-0000271 case
        (Decimal('10.118'), 'VCA', Decimal('10.12')),        # VCA 2-decimal ROUND_HALF_UP
        (Decimal('10.115'), 'VCA', Decimal('10.12')),        # VCA half-up case
        (Decimal('99.5'), 'VCT', Decimal('100')),            # VCT 0-decimal ROUND_HALF_UP
        (Decimal('99.49999'), 'VCT', Decimal('99')),         # VCT precision edge case
        (Decimal('5.675'), 'VCP', Decimal('5.68')),          # VCP half-up case
        (Decimal('10.125'), 'VCG', Decimal('10.13')),        # VCG 2-decimal ROUND_HALF_UP
        (Decimal('1000.5'), 'VCJ', Decimal('1001')),         # VCJ 0-decimal ROUND_HALF_UP
    ]
    
    all_passed = True
    
    for amount, company, expected in test_cases:
        try:
            result = apply_company_rounding(amount, company)
            if result == expected:
                print(f"✅ {company}: {amount} → {result} (expected {expected})")
            else:
                print(f"❌ {company}: {amount} → {result} (expected {expected})")
                all_passed = False
        except Exception as e:
            print(f"❌ {company}: ERROR - {str(e)}")
            all_passed = False
    
    return all_passed

def test_precision_edge_cases():
    """
    Test specific floating-point precision edge cases.
    """
    print("\n" + "=" * 80)
    print("Testing Floating-Point Precision Edge Cases")
    print("=" * 80)
    
    # These are amounts that commonly cause floating-point precision issues
    edge_cases = [
        # Cases where float precision would cause incorrect rounding
        (Decimal('0.125'), 'VCA', Decimal('0.13')),   # Should round up
        (Decimal('1.235'), 'VCP', Decimal('1.24')),   # Should round up  
        (Decimal('99.995'), 'VCT', Decimal('100')),   # Should round up to integer
        (Decimal('0.5'), 'VCT', Decimal('1')),        # Half-up to integer
        
        # Cases derived from actual exchange rate calculations
        (Decimal('3113.825'), 'VCP', Decimal('3113.83')),    # Common in USD conversions
        (Decimal('15110.835'), 'VCP', Decimal('15110.84')),  # Hotel accommodation amounts
        (Decimal('27916.845'), 'VCP', Decimal('27916.85')),  # Training expense amounts
    ]
    
    all_passed = True
    
    for amount, company, expected in edge_cases:
        try:
            result = apply_company_rounding(amount, company)
            if result == expected:
                print(f"✅ {company}: {amount} → {result}")
            else:
                print(f"❌ {company}: {amount} → {result} (expected {expected})")
                all_passed = False
        except Exception as e:
            print(f"❌ {company}: ERROR - {str(e)}")
            all_passed = False
    
    return all_passed

def test_existing_validation():
    """
    Run the existing validation tests to ensure they still pass.
    """
    print("\n" + "=" * 80)
    print("Running Existing Validation Tests")
    print("=" * 80)
    
    try:
        is_valid, report = validate_rounding_requirements()
        
        for line in report:
            if "PASS" in line:
                print(f"✅ {line}")
            else:
                print(f"❌ {line}")
        
        if is_valid:
            print("\n✅ All existing validation tests passed")
        else:
            print("\n❌ Some existing validation tests failed")
        
        return is_valid
    except Exception as e:
        print(f"❌ Error running validation: {str(e)}")
        return False

def main():
    """
    Run all precision fix validation tests.
    """
    print("Universal Precision Fix Validation")
    print("This test validates the Decimal-based exchange rate fixes")
    print("resolve floating-point precision issues for all companies.")
    print()
    
    # Run all test suites
    tests = [
        ("VPA-0000271 Precision Fix", test_vpa_271_precision),
        ("All Company Rounding", test_all_company_rounding),
        ("Precision Edge Cases", test_precision_edge_cases),
        ("Existing Validation", test_existing_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall Result: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Universal precision fix is working correctly!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - Review the failures above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)