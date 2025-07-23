#!/usr/bin/env python3
"""
Test script to verify V-VC00048 ShortcutDimCode4 fix for company credit card transactions.

This script tests that:
1. V-VC00048 (company credit card) transactions have empty ShortcutDimCode4 for both debit and credit lines
2. Other vendor transactions follow existing business logic
3. The fix has highest priority after special travel accounts (72600-10, 72600-30)
4. Employee reimbursements still include employee IDs correctly

Usage:
    python Tools/test_v_vc00048_shortcut_dim_code4_fix.py
"""

import sys
import os
import json
import logging
from typing import Dict, List, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we want to test
from core.process_japan_exports import create_journal_line

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_v_vc00048_entry(cost_center: str, voucher_no: str = "TEST001", employee_id: str = "10036") -> Dict[str, Any]:
    """
    Create a test entry with V-VC00048 vendor (company credit card) for testing.
    
    Args:
        cost_center: The cost center code (e.g., "VCA", "VCP", "VCT")
        voucher_no: The voucher number
        employee_id: The employee ID for testing
        
    Returns:
        Dict[str, Any]: Test journal entry
    """
    return {
        "voucher_no": voucher_no,
        "External_Document_No": voucher_no,
        "Document_Date": "2025/01/15",
        "description": "Test V-VC00048 company credit card expense",
        "debit": {
            "account": "72600-20",  # Not special travel account
            "gl_account": "G/L Account",
            "amount": 1000.0,
            "currency": "USD",
            "department": f"{cost_center}.1234",
            "department_code": f"{cost_center}.1234",
            "applicant_code": employee_id
        },
        "credit": {
            "vendor_code": "V-VC00048",
            "gl_account": "Vendor",
            "amount": 1000.0,
            "currency": "USD",
            "department": f"{cost_center}.1234",
            "department_code": f"{cost_center}.1234",
            "applicant_code": employee_id,
            "account_source": "vendor_code",  # Company credit card payment
            "Remarks": "Company credit card expense"
        }
    }

def create_test_employee_reimbursement_entry(cost_center: str, voucher_no: str = "TEST002", employee_id: str = "10036") -> Dict[str, Any]:
    """
    Create a test entry for employee reimbursement (should include employee ID).
    
    Args:
        cost_center: The cost center code
        voucher_no: The voucher number
        employee_id: The employee ID
        
    Returns:
        Dict[str, Any]: Test journal entry
    """
    return {
        "voucher_no": voucher_no,
        "External_Document_No": voucher_no,
        "Document_Date": "2025/01/15",
        "description": "Test employee reimbursement",
        "debit": {
            "account": "72600-20",
            "gl_account": "G/L Account",
            "amount": 500.0,
            "currency": "USD",
            "department": f"{cost_center}.1234",
            "department_code": f"{cost_center}.1234",
            "applicant_code": employee_id
        },
        "credit": {
            "vendor_code": employee_id,  # Employee reimbursement
            "gl_account": "Vendor",
            "amount": 500.0,
            "currency": "USD",
            "department": f"{cost_center}.1234",
            "department_code": f"{cost_center}.1234",
            "applicant_code": employee_id,
            "account_source": "applicant_code",  # Employee payment
            "Remarks": "Employee reimbursement"
        }
    }

def create_test_travel_expense_entry(cost_center: str, voucher_no: str = "TEST003", employee_id: str = "10036") -> Dict[str, Any]:
    """
    Create a test entry for travel expense (should have N/A for ShortcutDimCode4).
    
    Args:
        cost_center: The cost center code
        voucher_no: The voucher number
        employee_id: The employee ID
        
    Returns:
        Dict[str, Any]: Test journal entry
    """
    return {
        "voucher_no": voucher_no,
        "External_Document_No": voucher_no,
        "Document_Date": "2025/01/15",
        "description": "Test travel expense",
        "debit": {
            "account": "72600-10",  # Special travel account
            "gl_account": "G/L Account",
            "amount": 800.0,
            "currency": "USD",
            "department": f"{cost_center}.1234",
            "department_code": f"{cost_center}.1234",
            "applicant_code": employee_id
        },
        "credit": {
            "vendor_code": "V-VC00048",
            "gl_account": "Vendor",
            "amount": 800.0,
            "currency": "USD",
            "department": f"{cost_center}.1234",
            "department_code": f"{cost_center}.1234",
            "applicant_code": employee_id,
            "account_source": "vendor_code",
            "Remarks": "Travel expense via company credit card"
        }
    }

def test_v_vc00048_shortcut_dim_code4_empty():
    """
    Test that V-VC00048 (company credit card) transactions have empty ShortcutDimCode4.
    """
    logger.info("=== Testing V-VC00048 ShortcutDimCode4 Empty ===")
    
    test_cases = [
        {
            "name": "V-VC00048 VCA cost center - debit line",
            "entry": create_test_v_vc00048_entry("VCA", "TEST001", "10036"),
            "line_type": "debit",
            "expected_shortcut_dim_code4": ""
        },
        {
            "name": "V-VC00048 VCA cost center - credit line",
            "entry": create_test_v_vc00048_entry("VCA", "TEST001", "10036"),
            "line_type": "credit",
            "expected_shortcut_dim_code4": ""
        },
        {
            "name": "V-VC00048 VCP cost center - debit line",
            "entry": create_test_v_vc00048_entry("VCP", "TEST002", "10036"),
            "line_type": "debit",
            "expected_shortcut_dim_code4": ""
        },
        {
            "name": "V-VC00048 VCP cost center - credit line",
            "entry": create_test_v_vc00048_entry("VCP", "TEST002", "10036"),
            "line_type": "credit",
            "expected_shortcut_dim_code4": ""
        },
        {
            "name": "V-VC00048 VCT cost center - debit line",
            "entry": create_test_v_vc00048_entry("VCT", "TEST003", "10036"),
            "line_type": "debit",
            "expected_shortcut_dim_code4": ""
        },
        {
            "name": "V-VC00048 VCT cost center - credit line",
            "entry": create_test_v_vc00048_entry("VCT", "TEST003", "10036"),
            "line_type": "credit",
            "expected_shortcut_dim_code4": ""
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        logger.info(f"Testing: {test_case['name']}")
        
        # Create journal line
        journal_line = create_journal_line(test_case["entry"], test_case["line_type"])
        
        actual_shortcut_dim_code4 = journal_line.get("ShortcutDimCode4", "")
        expected_shortcut_dim_code4 = test_case["expected_shortcut_dim_code4"]
        
        if actual_shortcut_dim_code4 == expected_shortcut_dim_code4:
            logger.info(f"  ✅ PASS: ShortcutDimCode4 is empty for V-VC00048 company credit card")
        else:
            logger.error(f"  ❌ FAIL: Expected '{expected_shortcut_dim_code4}', got '{actual_shortcut_dim_code4}'")
            all_passed = False
    
    return all_passed

def test_employee_reimbursement_includes_employee_id():
    """
    Test that employee reimbursements still include employee ID in ShortcutDimCode4.
    """
    logger.info("=== Testing Employee Reimbursement Includes Employee ID ===")
    
    test_cases = [
        {
            "name": "Employee reimbursement VCA - debit line",
            "entry": create_test_employee_reimbursement_entry("VCA", "TEST004", "10036"),
            "line_type": "debit",
            "expected_shortcut_dim_code4": "10036"
        },
        {
            "name": "Employee reimbursement VCA - credit line",
            "entry": create_test_employee_reimbursement_entry("VCA", "TEST004", "10036"),
            "line_type": "credit",
            "expected_shortcut_dim_code4": "10036"
        },
        {
            "name": "Employee reimbursement VCP - debit line",
            "entry": create_test_employee_reimbursement_entry("VCP", "TEST005", "10037"),
            "line_type": "debit",
            "expected_shortcut_dim_code4": "10037"
        },
        {
            "name": "Employee reimbursement VCP - credit line",
            "entry": create_test_employee_reimbursement_entry("VCP", "TEST005", "10037"),
            "line_type": "credit",
            "expected_shortcut_dim_code4": "10037"
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        logger.info(f"Testing: {test_case['name']}")
        
        # Create journal line
        journal_line = create_journal_line(test_case["entry"], test_case["line_type"])
        
        actual_shortcut_dim_code4 = journal_line.get("ShortcutDimCode4", "")
        expected_shortcut_dim_code4 = test_case["expected_shortcut_dim_code4"]
        
        if actual_shortcut_dim_code4 == expected_shortcut_dim_code4:
            logger.info(f"  ✅ PASS: ShortcutDimCode4 includes employee ID '{actual_shortcut_dim_code4}'")
        else:
            logger.error(f"  ❌ FAIL: Expected '{expected_shortcut_dim_code4}', got '{actual_shortcut_dim_code4}'")
            all_passed = False
    
    return all_passed

def test_travel_expense_priority_over_v_vc00048():
    """
    Test that travel expense accounts (72600-10, 72600-30) have higher priority than V-VC00048.
    """
    logger.info("=== Testing Travel Expense Priority Over V-VC00048 ===")
    
    test_cases = [
        {
            "name": "Travel expense 72600-10 with V-VC00048 - debit line",
            "entry": create_test_travel_expense_entry("VCA", "TEST006", "10036"),
            "line_type": "debit",
            "expected_shortcut_dim_code4": "N/A"
        },
        {
            "name": "Travel expense 72600-10 with V-VC00048 - credit line",
            "entry": create_test_travel_expense_entry("VCA", "TEST006", "10036"),
            "line_type": "credit",
            "expected_shortcut_dim_code4": ""  # V-VC00048 rule applies to credit line
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        logger.info(f"Testing: {test_case['name']}")
        
        # Create journal line
        journal_line = create_journal_line(test_case["entry"], test_case["line_type"])
        
        actual_shortcut_dim_code4 = journal_line.get("ShortcutDimCode4", "")
        expected_shortcut_dim_code4 = test_case["expected_shortcut_dim_code4"]
        
        if actual_shortcut_dim_code4 == expected_shortcut_dim_code4:
            logger.info(f"  ✅ PASS: ShortcutDimCode4 is '{actual_shortcut_dim_code4}' (correct priority)")
        else:
            logger.error(f"  ❌ FAIL: Expected '{expected_shortcut_dim_code4}', got '{actual_shortcut_dim_code4}'")
            all_passed = False
    
    return all_passed

def test_v_vc00048_account_no_mapping():
    """
    Test that V-VC00048 Account_No mapping still works correctly with the ShortcutDimCode4 fix.
    """
    logger.info("=== Testing V-VC00048 Account_No Mapping ===")
    
    test_cases = [
        {
            "name": "V-VC00048 VCA cost center - should map to VCT",
            "entry": create_test_v_vc00048_entry("VCA", "TEST007", "10036"),
            "line_type": "credit",
            "expected_account_no": "VCT"
        },
        {
            "name": "V-VC00048 VCP cost center - should map to VCT",
            "entry": create_test_v_vc00048_entry("VCP", "TEST008", "10036"),
            "line_type": "credit",
            "expected_account_no": "VCT"
        },
        {
            "name": "V-VC00048 VCT cost center - should remain V-VC00048",
            "entry": create_test_v_vc00048_entry("VCT", "TEST009", "10036"),
            "line_type": "credit",
            "expected_account_no": "V-VC00048"
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        logger.info(f"Testing: {test_case['name']}")
        
        # Create journal line
        journal_line = create_journal_line(test_case["entry"], test_case["line_type"])
        
        actual_account_no = journal_line.get("Account_No", "")
        expected_account_no = test_case["expected_account_no"]
        
        if actual_account_no == expected_account_no:
            logger.info(f"  ✅ PASS: Account_No is '{actual_account_no}' (correct mapping)")
        else:
            logger.error(f"  ❌ FAIL: Expected '{expected_account_no}', got '{actual_account_no}'")
            all_passed = False
    
    return all_passed

def main():
    """
    Run all V-VC00048 ShortcutDimCode4 tests.
    """
    logger.info("Starting V-VC00048 ShortcutDimCode4 Fix Tests")
    logger.info("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: V-VC00048 ShortcutDimCode4 should be empty
    test1_passed = test_v_vc00048_shortcut_dim_code4_empty()
    all_tests_passed = all_tests_passed and test1_passed
    
    logger.info("")
    
    # Test 2: Employee reimbursements should include employee ID
    test2_passed = test_employee_reimbursement_includes_employee_id()
    all_tests_passed = all_tests_passed and test2_passed
    
    logger.info("")
    
    # Test 3: Travel expense priority over V-VC00048
    test3_passed = test_travel_expense_priority_over_v_vc00048()
    all_tests_passed = all_tests_passed and test3_passed
    
    logger.info("")
    
    # Test 4: V-VC00048 Account_No mapping still works
    test4_passed = test_v_vc00048_account_no_mapping()
    all_tests_passed = all_tests_passed and test4_passed
    
    logger.info("")
    logger.info("=" * 60)
    
    if all_tests_passed:
        logger.info("🎉 ALL TESTS PASSED! V-VC00048 ShortcutDimCode4 fix is working correctly.")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED! Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
