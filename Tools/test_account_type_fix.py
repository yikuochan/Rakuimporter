#!/usr/bin/env python3
"""
Test script to verify the Account_Type fix for empty gl_account fields.

This script tests the fix for the Business Central API error:
"'' is not an option. The existing options are: G/L Account,Customer,Vendor,Bank Account,Fixed Asset,IC Partner,Employee,Allocation Account"

The fix implements robust fallback logic similar to the cost center handling pattern.
"""

import sys
import os
import json
import logging

# Add the parent directory to the path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process_japan_exports import create_journal_line, setup_logging

# Set up logging
logger = setup_logging()

def test_account_type_inference():
    """Test that Account_Type is properly inferred when gl_account is empty."""
    
    print("=" * 60)
    print("Testing Account_Type Inference Fix")
    print("=" * 60)
    
    # Test Case 1: Empty gl_account with vendor_code should infer "Vendor"
    test_entry_1 = {
        "voucher_no": "VPA-0000251",
        "External_Document_No": "LK44675907",
        "Document_Date": "2025-03-16",
        "description": "Purchase office keyboard when onboarding",
        "debit": {
            "gl_account": "",  # Empty - this was causing the issue
            "account": "",
            "vendor_code": "V-SUPPLIER001",  # Has vendor code
            "amount": 1000,
            "currency": "NTD",
            "department": "VCT.9999",
            "department_code": "VCT.9999"
        },
        "credit": {
            "gl_account": "",
            "account": "",
            "vendor_code": "",
            "amount": 0,
            "currency": "",
            "department": "",
            "department_code": "",
            "Remarks": ""
        }
    }
    
    print("\nTest Case 1: Empty gl_account with vendor_code")
    print(f"Input: gl_account='{test_entry_1['debit']['gl_account']}', vendor_code='{test_entry_1['debit']['vendor_code']}'")
    
    try:
        journal_line = create_journal_line(test_entry_1, "debit")
        account_type = journal_line.get("Account_Type", "")
        account_no = journal_line.get("Account_No", "")
        
        print(f"Result: Account_Type='{account_type}', Account_No='{account_no}'")
        
        if account_type == "Vendor":
            print("✅ PASS: Account_Type correctly inferred as 'Vendor'")
        else:
            print(f"❌ FAIL: Expected 'Vendor', got '{account_type}'")
            return False
            
        if account_no == "V-SUPPLIER001":
            print("✅ PASS: Account_No correctly set from vendor_code")
        else:
            print(f"❌ FAIL: Expected 'V-SUPPLIER001', got '{account_no}'")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False
    
    # Test Case 2: Empty gl_account with account field should infer "G/L Account"
    test_entry_2 = {
        "voucher_no": "VPA-0000252",
        "External_Document_No": "LK44675908",
        "Document_Date": "2025-03-16",
        "description": "General ledger transaction",
        "debit": {
            "gl_account": "",  # Empty
            "account": "72600-10",  # Has account
            "vendor_code": "",  # No vendor code
            "amount": 1500,
            "currency": "NTD",
            "department": "VCT.9999",
            "department_code": "VCT.9999"
        },
        "credit": {
            "gl_account": "",
            "account": "",
            "vendor_code": "",
            "amount": 0,
            "currency": "",
            "department": "",
            "department_code": "",
            "Remarks": ""
        }
    }
    
    print("\nTest Case 2: Empty gl_account with account field")
    print(f"Input: gl_account='{test_entry_2['debit']['gl_account']}', account='{test_entry_2['debit']['account']}', vendor_code='{test_entry_2['debit']['vendor_code']}'")
    
    try:
        journal_line = create_journal_line(test_entry_2, "debit")
        account_type = journal_line.get("Account_Type", "")
        account_no = journal_line.get("Account_No", "")
        
        print(f"Result: Account_Type='{account_type}', Account_No='{account_no}'")
        
        if account_type == "G/L Account":
            print("✅ PASS: Account_Type correctly inferred as 'G/L Account'")
        else:
            print(f"❌ FAIL: Expected 'G/L Account', got '{account_type}'")
            return False
            
        if account_no == "72600-10":
            print("✅ PASS: Account_No correctly set from account field")
        else:
            print(f"❌ FAIL: Expected '72600-10', got '{account_no}'")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False
    
    # Test Case 3: Empty gl_account with no indicators should default to "G/L Account"
    test_entry_3 = {
        "voucher_no": "VPA-0000253",
        "External_Document_No": "LK44675909",
        "Document_Date": "2025-03-16",
        "description": "Default case transaction",
        "debit": {
            "gl_account": "",  # Empty
            "account": "",     # Empty
            "vendor_code": "", # Empty
            "amount": 2000,
            "currency": "NTD",
            "department": "VCT.9999",
            "department_code": "VCT.9999"
        },
        "credit": {
            "gl_account": "",
            "account": "",
            "vendor_code": "",
            "amount": 0,
            "currency": "",
            "department": "",
            "department_code": "",
            "Remarks": ""
        }
    }
    
    print("\nTest Case 3: Empty gl_account with no indicators (default case)")
    print(f"Input: gl_account='{test_entry_3['debit']['gl_account']}', account='{test_entry_3['debit']['account']}', vendor_code='{test_entry_3['debit']['vendor_code']}'")
    
    try:
        journal_line = create_journal_line(test_entry_3, "debit")
        account_type = journal_line.get("Account_Type", "")
        account_no = journal_line.get("Account_No", "")
        
        print(f"Result: Account_Type='{account_type}', Account_No='{account_no}'")
        
        if account_type == "G/L Account":
            print("✅ PASS: Account_Type correctly defaulted to 'G/L Account'")
        else:
            print(f"❌ FAIL: Expected 'G/L Account', got '{account_type}'")
            return False
            
        if account_no == "":
            print("✅ PASS: Account_No correctly empty for default case")
        else:
            print(f"❌ FAIL: Expected empty string, got '{account_no}'")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False
    
    # Test Case 4: Existing gl_account should be preserved
    test_entry_4 = {
        "voucher_no": "VPA-0000254",
        "External_Document_No": "LK44675910",
        "Document_Date": "2025-03-16",
        "description": "Existing gl_account transaction",
        "debit": {
            "gl_account": "Vendor",  # Already set
            "account": "",
            "vendor_code": "V-SUPPLIER002",
            "amount": 3000,
            "currency": "NTD",
            "department": "VCT.9999",
            "department_code": "VCT.9999"
        },
        "credit": {
            "gl_account": "",
            "account": "",
            "vendor_code": "",
            "amount": 0,
            "currency": "",
            "department": "",
            "department_code": "",
            "Remarks": ""
        }
    }
    
    print("\nTest Case 4: Existing gl_account should be preserved")
    print(f"Input: gl_account='{test_entry_4['debit']['gl_account']}', vendor_code='{test_entry_4['debit']['vendor_code']}'")
    
    try:
        journal_line = create_journal_line(test_entry_4, "debit")
        account_type = journal_line.get("Account_Type", "")
        account_no = journal_line.get("Account_No", "")
        
        print(f"Result: Account_Type='{account_type}', Account_No='{account_no}'")
        
        if account_type == "Vendor":
            print("✅ PASS: Account_Type correctly preserved as 'Vendor'")
        else:
            print(f"❌ FAIL: Expected 'Vendor', got '{account_type}'")
            return False
            
        if account_no == "V-SUPPLIER002":
            print("✅ PASS: Account_No correctly set from vendor_code")
        else:
            print(f"❌ FAIL: Expected 'V-SUPPLIER002', got '{account_no}'")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False
    
    return True

def test_original_error_scenario():
    """Test the exact scenario from the original error log."""
    
    print("\n" + "=" * 60)
    print("Testing Original Error Scenario")
    print("=" * 60)
    
    # Recreate the exact scenario from the error log
    error_entry = {
        "voucher_no": "VPA-0000251",
        "External_Document_No": "LK44675907",
        "Document_Date": "2025-03-16",
        "description": "Purchase office keyboard when onboarding",
        "debit": {
            "gl_account": "",  # This was empty, causing the error
            "account": "",     # This was empty
            "vendor_code": "", # This was empty
            "amount": 0,       # This was 0
            "currency": "",    # This was empty
            "department": "VCT",
            "department_code": ""
        },
        "credit": {
            "gl_account": "",
            "account": "",
            "vendor_code": "",
            "amount": 0,
            "currency": "",
            "department": "",
            "department_code": "",
            "Remarks": ""
        }
    }
    
    print("Original Error Scenario:")
    print(f"- gl_account: '{error_entry['debit']['gl_account']}'")
    print(f"- account: '{error_entry['debit']['account']}'")
    print(f"- vendor_code: '{error_entry['debit']['vendor_code']}'")
    print(f"- amount: {error_entry['debit']['amount']}")
    print(f"- currency: '{error_entry['debit']['currency']}'")
    
    try:
        journal_line = create_journal_line(error_entry, "debit")
        account_type = journal_line.get("Account_Type", "")
        account_no = journal_line.get("Account_No", "")
        
        print(f"\nAfter Fix:")
        print(f"- Account_Type: '{account_type}'")
        print(f"- Account_No: '{account_no}'")
        
        # The fix should default to "G/L Account" since no indicators are present
        if account_type == "G/L Account":
            print("✅ PASS: Account_Type no longer empty - defaulted to 'G/L Account'")
        else:
            print(f"❌ FAIL: Expected 'G/L Account', got '{account_type}'")
            return False
        
        # Account_No should be empty since no account field is provided
        if account_no == "":
            print("✅ PASS: Account_No correctly empty for default case")
        else:
            print(f"❌ FAIL: Expected empty string, got '{account_no}'")
            return False
        
        print("✅ SUCCESS: Original error scenario now handled correctly!")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("Account_Type Fix Verification Test")
    print("This test verifies the fix for empty Account_Type fields that caused Business Central API errors.")
    
    # Run inference tests
    inference_passed = test_account_type_inference()
    
    # Run original error scenario test
    original_error_passed = test_original_error_scenario()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if inference_passed and original_error_passed:
        print("✅ ALL TESTS PASSED")
        print("\nThe Account_Type fix is working correctly:")
        print("- Empty gl_account with vendor_code → infers 'Vendor'")
        print("- Empty gl_account with account field → infers 'G/L Account'")
        print("- Empty gl_account with no indicators → defaults to 'G/L Account'")
        print("- Existing gl_account values → preserved unchanged")
        print("- Original error scenario → now handled correctly")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        if not inference_passed:
            print("- Account_Type inference tests failed")
        if not original_error_passed:
            print("- Original error scenario test failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
