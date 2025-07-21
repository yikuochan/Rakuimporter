#!/usr/bin/env python3
"""
Test script for date format validation and correction fix.

This script tests the enhanced convert_date_format function to ensure it properly
handles various date formats and corrects common corruption issues.
"""

import sys
import os
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the function to test
from core.process_japan_exports import convert_date_format, setup_logging

def test_date_format_conversion():
    """Test the convert_date_format function with various inputs."""
    
    # Set up logging
    logger = setup_logging()
    
    print("Testing Date Format Conversion Function")
    print("=" * 50)
    
    # Test cases: (input, expected_output, description)
    test_cases = [
        # Normal cases
        ("2025/06/25", "2025-06-25", "Normal date format"),
        ("2025/6/25", "2025-06-25", "Single digit month"),
        ("2025/06/5", "2025-06-05", "Single digit day"),
        ("2025/6/5", "2025-06-05", "Single digit month and day"),
        
        # Different separators
        ("2025-06-25", "2025-06-25", "Already hyphenated"),
        ("2025.06.25", "2025-06-25", "Dot separator"),
        
        # Corrupted year cases (the main issue)
        ("1114/06/25", "2025-06-25", "Corrupted year 1114 -> 2025"),
        ("1114-06-25", "2025-06-25", "Corrupted year 1114 with hyphens"),
        ("1114.06.25", "2025-06-25", "Corrupted year 1114 with dots"),
        
        # Other year correction cases
        ("25/06/25", "2025-06-25", "Two-digit year"),
        ("125/06/25", "2025-06-25", "Three-digit year"),
        ("1800/06/25", "2025-06-25", "Suspicious old year"),
        ("3000/06/25", "2025-06-25", "Future year beyond range"),
        
        # Edge cases
        ("", "", "Empty string"),
        ("2025", "2025", "Invalid format - not 3 parts"),
        ("2025/13/25", "2025/13/25", "Invalid month"),
        ("2025/06/32", "2025/06/32", "Invalid day"),
        ("abc/06/25", "abc/06/25", "Invalid year"),
        ("2025/abc/25", "2025/abc/25", "Invalid month"),
        ("2025/06/abc", "2025/06/abc", "Invalid day"),
        
        # Real-world test case from the error
        ("1114/06/25", "2025-06-25", "Actual failing case from error log"),
    ]
    
    passed = 0
    failed = 0
    
    for input_date, expected, description in test_cases:
        try:
            result = convert_date_format(input_date)
            if result == expected:
                print(f"✓ PASS: {description}")
                print(f"  Input: '{input_date}' -> Output: '{result}'")
                passed += 1
            else:
                print(f"✗ FAIL: {description}")
                print(f"  Input: '{input_date}' -> Expected: '{expected}' -> Got: '{result}'")
                failed += 1
        except Exception as e:
            print(f"✗ ERROR: {description}")
            print(f"  Input: '{input_date}' -> Exception: {str(e)}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

def test_specific_error_case():
    """Test the specific error case from the log."""
    
    print("\nTesting Specific Error Case")
    print("=" * 30)
    
    # This is the exact case that was failing
    corrupted_date = "1114/06/25"
    expected_result = "2025-06-25"
    
    print(f"Testing corrupted date: '{corrupted_date}'")
    result = convert_date_format(corrupted_date)
    print(f"Result: '{result}'")
    print(f"Expected: '{expected_result}'")
    
    if result == expected_result:
        print("✓ SUCCESS: Corrupted date fixed correctly!")
        return True
    else:
        print("✗ FAILURE: Corrupted date not fixed properly!")
        return False

def simulate_journal_line_creation():
    """Simulate creating a journal line with the fixed date."""
    
    print("\nSimulating Journal Line Creation")
    print("=" * 35)
    
    # Simulate entry data with corrupted date
    mock_entry = {
        "voucher_no": "VPA-0000251",
        "Document_Date": "1114/06/25",  # Corrupted date
        "debit": {
            "amount": 799.00,
            "currency": "NTD",
            "department": "VCT.1751G",
            "gl_account": "G/L Account",
            "account": "75410-10",
            "applicant_code": "10119"
        },
        "credit": {
            "amount": 799.00,
            "currency": "NTD",
            "department": "VCT.1751G",
            "gl_account": "Vendor",
            "vendor_code": "32200-10",
            "applicant_code": "10119"
        }
    }
    
    print(f"Original Document_Date: '{mock_entry['Document_Date']}'")
    
    # Test the date conversion
    formatted_date = convert_date_format(mock_entry["Document_Date"])
    print(f"Formatted Document_Date: '{formatted_date}'")
    
    # Check if it's in the correct format for Business Central
    if formatted_date == "2025-06-25":
        print("✓ SUCCESS: Date is now in correct format for Business Central API!")
        return True
    else:
        print("✗ FAILURE: Date is still not in correct format!")
        return False

if __name__ == "__main__":
    print("Date Format Fix Test Suite")
    print("=" * 60)
    
    # Run all tests
    test1_passed = test_date_format_conversion()
    test2_passed = test_specific_error_case()
    test3_passed = simulate_journal_line_creation()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"Date Format Conversion Tests: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Specific Error Case Test: {'PASSED' if test2_passed else 'FAILED'}")
    print(f"Journal Line Simulation: {'PASSED' if test3_passed else 'FAILED'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n🎉 ALL TESTS PASSED! The date format fix is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED! Please review the implementation.")
        sys.exit(1)
