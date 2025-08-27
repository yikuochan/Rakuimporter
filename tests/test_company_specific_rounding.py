#!/usr/bin/env python3
"""
Comprehensive Test Suite for Company-Specific Rounding Implementation

This test suite validates the company-specific rounding functionality
across all modules: currency_rounding, company_rounding_config, and currency_converter.

Test Coverage:
1. Company-specific rounding rules validation
2. Currency converter integration testing
3. Backward compatibility testing
4. Edge case handling
5. Real-world scenario validation
"""

import sys
import os
import unittest
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

# Add the current directory to the Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.currency_rounding import (
        apply_company_rounding, 
        round_vca_amount, 
        round_vcp_amount, 
        round_vct_amount,
        validate_rounding_requirements,
        get_rounding_examples
    )
    from core.company_rounding_config import (
        get_company_rounding_config,
        get_company_home_currency,
        validate_company_config,
        RoundingMethod
    )
    from core.currency_converter import convert_amount, convert_through_intermediate
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running this test from the project root directory")
    sys.exit(1)

class TestCompanyRoundingConfig(unittest.TestCase):
    """Test the company rounding configuration module."""
    
    def test_vca_config(self):
        """Test VCA company configuration."""
        config = get_company_rounding_config("VCA")
        self.assertEqual(config["decimal_places"], 2)
        self.assertEqual(config["rounding_method"], RoundingMethod.ROUND_HALF_UP)
        self.assertEqual(config["home_currency"], "USD")
        
    def test_vcp_config(self):
        """Test VCP company configuration."""
        config = get_company_rounding_config("VCP")
        self.assertEqual(config["decimal_places"], 2)
        self.assertEqual(config["rounding_method"], RoundingMethod.ROUND_HALF_UP)
        self.assertEqual(config["home_currency"], "PHP")
        
    def test_vct_config(self):
        """Test VCT company configuration."""
        config = get_company_rounding_config("VCT")
        self.assertEqual(config["decimal_places"], 0)
        self.assertEqual(config["rounding_method"], RoundingMethod.ROUND_HALF_UP)
        self.assertEqual(config["home_currency"], "NTD")
        
    def test_vcg_config(self):
        """Test VCG company configuration (standard rounding)."""
        config = get_company_rounding_config("VCG")
        self.assertEqual(config["decimal_places"], 2)
        self.assertEqual(config["rounding_method"], RoundingMethod.ROUND_HALF_UP)
        self.assertEqual(config["home_currency"], "EUR")
        
    def test_unknown_company_config(self):
        """Test unknown company returns default configuration."""
        config = get_company_rounding_config("UNKNOWN")
        self.assertEqual(config["decimal_places"], 2)
        self.assertEqual(config["rounding_method"], RoundingMethod.ROUND_HALF_UP)
        self.assertIsNone(config["home_currency"])
        
    def test_company_validation(self):
        """Test company configuration validation."""
        is_valid, message = validate_company_config("VCA")
        self.assertTrue(is_valid)
        
        is_valid, message = validate_company_config("NONEXISTENT")
        self.assertFalse(is_valid)

class TestCompanyRounding(unittest.TestCase):
    """Test the company-specific rounding logic."""
    
    def test_vca_rounding_requirements(self):
        """Test VCA rounding: standard rounding to 2 decimals."""
        # Test cases with standard rounding to 2 decimal places
        test_cases = [
            (10.118, 10.12),  # Round up
            (10.119, 10.12),  # Round up
            (10.115, 10.12),  # Round up (half-up)
            (10.111, 10.11),  # Round down
            (5.678, 5.68),    # Round up
            (5.679, 5.68)     # Round down
        ]
        
        for input_amount, expected in test_cases:
            with self.subTest(amount=input_amount):
                result = apply_company_rounding(input_amount, "VCA")
                self.assertEqual(float(result), expected, 
                    f"VCA rounding failed: {input_amount} → {float(result)}, expected {expected}")
                
    def test_vcp_rounding_requirements(self):
        """Test VCP rounding: standard rounding to 2 decimals (same as VCA)."""
        test_cases = [
            (10.118, 10.12),  # Round up
            (10.119, 10.12),  # Round up
            (5.678, 5.68),    # Round up
            (5.679, 5.68)     # Round down
        ]
        
        for input_amount, expected in test_cases:
            with self.subTest(amount=input_amount):
                result = apply_company_rounding(input_amount, "VCP")
                self.assertEqual(float(result), expected,
                    f"VCP rounding failed: {input_amount} → {float(result)}, expected {expected}")
                
    def test_vct_rounding_requirements(self):
        """Test VCT rounding: round to nearest integer."""
        # Test cases with proper rounding to nearest integer
        test_cases = [
            (99.9, 100),  # Round up
            (99.1, 99),   # Round down
            (100.9, 101), # Round up  
            (99.0, 99),   # No change
            (50.5, 51),   # Round up (half-up)
            (50.4, 50),   # Round down
            (50.6, 51)    # Round up
        ]
        
        for input_amount, expected in test_cases:
            with self.subTest(amount=input_amount):
                result = apply_company_rounding(input_amount, "VCT")
                self.assertEqual(float(result), expected,
                    f"VCT rounding failed: {input_amount} → {float(result)}, expected {expected}")
                
    def test_convenience_functions(self):
        """Test convenience rounding functions."""
        # Test VCA convenience function
        result = round_vca_amount(10.118)
        self.assertEqual(float(result), 10.12)
        
        # Test VCP convenience function
        result = round_vcp_amount(5.678)
        self.assertEqual(float(result), 5.68)
        
        # Test VCT convenience function
        result = round_vct_amount(99.9)
        self.assertEqual(float(result), 100)
        
    def test_decimal_input_handling(self):
        """Test that Decimal inputs are handled correctly."""
        # Test with Decimal input
        decimal_input = Decimal("10.118")
        result = apply_company_rounding(decimal_input, "VCA")
        self.assertEqual(result, Decimal("10.12"))
        
    def test_override_parameters(self):
        """Test override parameters for precision and method."""
        # Test precision override
        result = apply_company_rounding(10.118, "VCA", override_precision=3)
        self.assertEqual(float(result), 10.118)  # 3 decimals, still rounds down
        
        # Test method override
        result = apply_company_rounding(10.115, "VCA", override_method=RoundingMethod.ROUND_HALF_UP)
        self.assertEqual(float(result), 10.12)  # Standard rounding instead of round down

class TestCurrencyConverterIntegration(unittest.TestCase):
    """Test currency converter integration with company-specific rounding."""
    
    def test_same_currency_company_rounding(self):
        """Test same currency conversion with company-specific rounding."""
        # VCA: should round to 2 decimals using standard rounding
        result, success = convert_amount(10.118, "USD", "USD", company_code="VCA")
        self.assertTrue(success)
        self.assertEqual(float(result), 10.12)
        
        # VCT: should round to nearest integer  
        result, success = convert_amount(99.9, "NTD", "NTD", company_code="VCT")
        self.assertTrue(success)
        self.assertEqual(float(result), 100)
        
    def test_fallback_to_standard_rounding(self):
        """Test fallback to standard rounding when company code is not provided."""
        # Without company code, should use decimal_precision parameter
        result, success = convert_amount(10.118, "USD", "USD", decimal_precision=2)
        self.assertTrue(success)
        self.assertEqual(float(result), 10.12)  # Standard rounding
        
    def test_unknown_company_fallback(self):
        """Test fallback behavior for unknown company codes."""
        # Unknown company should use default rounding (ROUND_HALF_UP)
        result, success = convert_amount(10.115, "USD", "USD", company_code="UNKNOWN")
        self.assertTrue(success)
        self.assertEqual(float(result), 10.12)  # Standard rounding

class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing functionality."""
    
    def test_currency_converter_without_company_code(self):
        """Test that currency converter works without company_code (legacy behavior)."""
        # Should work exactly as before when no company_code is provided
        result, success = convert_amount(10.118, "USD", "USD", decimal_precision=2)
        self.assertTrue(success)
        self.assertEqual(float(result), 10.12)  # Standard rounding
        
        # Zero decimal precision
        result, success = convert_amount(10.118, "USD", "USD", decimal_precision=0)
        self.assertTrue(success)
        self.assertEqual(float(result), 10)  # Rounded to whole number
        
    def test_intermediate_conversion_backward_compatibility(self):
        """Test intermediate conversion without company code."""
        # This should work as before, though actual conversion will depend on exchange rates
        result, success = convert_through_intermediate(
            100, "USD", "EUR", "USD", decimal_precision=2
        )
        # We can't test the exact result without exchange rate data,
        # but we can test that it doesn't crash and returns valid types
        self.assertIsInstance(result, Decimal)
        self.assertIsInstance(success, bool)

class TestRealWorldScenarios(unittest.TestCase):
    """Test real-world scenarios based on business requirements."""
    
    def test_vca_expense_scenario(self):
        """Test VCA expense processing scenario."""
        # Simulate VCA expense of 1,250.678 USD
        expense_amount = 1250.678
        result = apply_company_rounding(expense_amount, "VCA")
        expected = 1250.68  # Standard rounding to 2 decimals
        self.assertEqual(float(result), expected)
        
    def test_vcp_expense_scenario(self):
        """Test VCP expense processing scenario.""" 
        # Simulate VCP expense of 15,432.999 PHP
        expense_amount = 15432.999
        result = apply_company_rounding(expense_amount, "VCP")
        expected = 15433.00  # Standard rounding to 2 decimals
        self.assertEqual(float(result), expected)
        
    def test_vct_expense_scenario(self):
        """Test VCT expense processing scenario."""
        # Simulate VCT expense of 50,000.75 NTD
        expense_amount = 50000.75
        result = apply_company_rounding(expense_amount, "VCT")
        expected = 50001  # Round to nearest integer
        self.assertEqual(float(result), expected)
        
    def test_mixed_company_processing(self):
        """Test processing expenses for multiple companies."""
        expenses = [
            ("VCA", 1234.567, 1234.57),  # Standard rounding
            ("VCP", 9876.543, 9876.54),  # Standard rounding
            ("VCT", 5555.9, 5556),       # Round to nearest integer
            ("VCG", 777.775, 777.78),    # Standard rounding for VCG
        ]
        
        for company, amount, expected in expenses:
            with self.subTest(company=company, amount=amount):
                result = apply_company_rounding(amount, company)
                self.assertEqual(float(result), expected,
                    f"{company} rounding failed: {amount} → {float(result)}, expected {expected}")

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_zero_amounts(self):
        """Test rounding of zero amounts."""
        for company in ["VCA", "VCP", "VCT"]:
            with self.subTest(company=company):
                result = apply_company_rounding(0, company)
                self.assertEqual(float(result), 0)
                
    def test_negative_amounts(self):
        """Test rounding of negative amounts."""
        # VCA: -10.118 should become -10.12 (standard rounding)
        result = apply_company_rounding(-10.118, "VCA")
        self.assertEqual(float(result), -10.12)
        
        # VCT: -99.9 should become -100 (round to nearest)
        result = apply_company_rounding(-99.9, "VCT")
        self.assertEqual(float(result), -100)
        
    def test_very_small_amounts(self):
        """Test rounding of very small amounts."""
        # VCA: 0.001 should become 0.00 (standard rounding)
        result = apply_company_rounding(0.001, "VCA")
        self.assertEqual(float(result), 0.00)
        
        # VCT: 0.9 should become 1 (round to nearest)
        result = apply_company_rounding(0.9, "VCT")
        self.assertEqual(float(result), 1)
        
    def test_very_large_amounts(self):
        """Test rounding of very large amounts."""
        large_amount = 999999999.999
        
        # VCA: should use standard rounding to 2 decimals
        result = apply_company_rounding(large_amount, "VCA")
        self.assertEqual(float(result), 1000000000.00)
        
        # VCT: should round to nearest integer
        result = apply_company_rounding(large_amount, "VCT")
        self.assertEqual(float(result), 1000000000)

class TestRequirementsValidation(unittest.TestCase):
    """Test validation against the original business requirements."""
    
    def test_requirements_validation(self):
        """Test the built-in requirements validation function."""
        is_valid, report = validate_rounding_requirements()
        self.assertTrue(is_valid, f"Requirements validation failed:\n" + "\n".join(report))
        
    def test_specific_requirement_examples(self):
        """Test the specific examples mentioned in requirements."""
        # VCA, VCP: 10.118 to 10.12 (standard rounding)
        vca_result = apply_company_rounding(10.118, "VCA")
        self.assertEqual(float(vca_result), 10.12)
        
        vcp_result = apply_company_rounding(10.118, "VCP")
        self.assertEqual(float(vcp_result), 10.12)
        
        # VCT: 99.9 to 100 (round to nearest integer)
        vct_result = apply_company_rounding(99.9, "VCT")
        self.assertEqual(float(vct_result), 100)

def run_comprehensive_test():
    """Run all tests and provide a comprehensive report."""
    print("Running Company-Specific Rounding Test Suite")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestCompanyRoundingConfig,
        TestCompanyRounding,
        TestCurrencyConverterIntegration,
        TestBackwardCompatibility,
        TestRealWorldScenarios,
        TestEdgeCases,
        TestRequirementsValidation
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    
    return success

if __name__ == "__main__":
    # Run the comprehensive test
    success = run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)