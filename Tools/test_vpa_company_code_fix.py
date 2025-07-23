#!/usr/bin/env python3
"""
Test script to verify VPA company code assignment fix.

This test verifies that VPA vouchers are no longer hardcoded to VCP company
and instead use proper company determination logic.
"""

import sys
import os
import json
import logging

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process_japan_exports import create_journal_line

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vpa_company_code_assignment():
    """Test that VPA vouchers get correct company assignment based on department field."""
    
    print("=" * 60)
    print("Testing VPA Company Code Assignment Fix")
    print("=" * 60)
    
    # Test Case 1: VPA voucher with VCT department should go to VCT
    test_entry_vct = {
        "voucher_no": "VPA-0000242",
        "description": "Mobile fee",
        "Document_Date": "2025/06/25",
        "External_Document_No": "0625",
        "debit": {
            "department": "VCT.1234G",  # Should determine company as VCT
            "account": "74510-10",
            "gl_account": "G/L Account",
            "amount": 599.0,
            "currency": "NTD",
            "applicant_code": "10001"
        },
        "credit": {
            "department": "VCT.1234G",  # Should determine company as VCT
            "gl_account": "Vendor",
            "vendor_code": "V-TW00001",
            "amount": 599.0,
            "currency": "NTD",
            "applicant_code": "10001"
        }
    }
    
    # Test Case 2: VPA voucher with VCP department should go to VCP
    test_entry_vcp = {
        "voucher_no": "VPA-0000243",
        "description": "Office supplies",
        "Document_Date": "2025/06/25",
        "External_Document_No": "0626",
        "debit": {
            "department": "VCP.5678G",  # Should determine company as VCP
            "account": "74510-10",
            "gl_account": "G/L Account",
            "amount": 1000.0,
            "currency": "PHP",
            "applicant_code": "10002"
        },
        "credit": {
            "department": "VCP.5678G",  # Should determine company as VCP
            "gl_account": "Vendor",
            "vendor_code": "V-PH00001",
            "amount": 1000.0,
            "currency": "PHP",
            "applicant_code": "10002"
        }
    }
    
    # Test Case 3: VPA voucher with no department should default to VCT
    test_entry_no_dept = {
        "voucher_no": "VPA-0000244",
        "description": "Travel expense",
        "Document_Date": "2025/06/25",
        "External_Document_No": "0627",
        "debit": {
            "department": "",  # Empty department
            "account": "74510-10",
            "gl_account": "G/L Account",
            "amount": 500.0,
            "currency": "USD",
            "applicant_code": "10003"
        },
        "credit": {
            "department": "",  # Empty department
            "gl_account": "Vendor",
            "vendor_code": "V-US00001",
            "amount": 500.0,
            "currency": "USD",
            "applicant_code": "10003"
        }
    }
    
    # Test Case 4: OBA voucher with VCT department should go to VCT (not VCJ)
    test_entry_oba = {
        "voucher_no": "OBA-0000036",
        "description": "Equipment purchase",
        "Document_Date": "2025/06/25",
        "External_Document_No": "0628",
        "debit": {
            "department": "VCT.9999G",  # Should determine company as VCT
            "account": "74510-10",
            "gl_account": "G/L Account",
            "amount": 2000.0,
            "currency": "NTD",
            "applicant_code": "10004"
        },
        "credit": {
            "department": "VCT.9999G",  # Should determine company as VCT
            "gl_account": "Vendor",
            "vendor_code": "V-TW00002",
            "amount": 2000.0,
            "currency": "NTD",
            "applicant_code": "10004"
        }
    }
    
    test_cases = [
        ("VPA with VCT department", test_entry_vct, "VCT"),
        ("VPA with VCP department", test_entry_vcp, "VCP"),
        ("VPA with no department", test_entry_no_dept, "VCT"),
        ("OBA with VCT department", test_entry_oba, "VCT")
    ]
    
    all_passed = True
    
    for test_name, entry, expected_company in test_cases:
        print(f"\nTest: {test_name}")
        print(f"Voucher: {entry['voucher_no']}")
        print(f"Department: '{entry['debit']['department']}'")
        print(f"Expected Company: {expected_company}")
        
        try:
            # Create debit line to test company determination
            debit_line = create_journal_line(entry, "debit")
            actual_company = debit_line.get("Shortcut_Dimension_1_Code", "")
            
            print(f"Actual Company: {actual_company}")
            
            if actual_company == expected_company:
                print("✅ PASSED")
            else:
                print("❌ FAILED")
                all_passed = False
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("VPA company code assignment fix is working correctly.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("VPA company code assignment fix needs further investigation.")
    print("=" * 60)
    
    return all_passed

def test_oba_company_code_assignment():
    """Test that OBA vouchers get correct company assignment (not hardcoded to VCJ)."""
    
    print("\n" + "=" * 60)
    print("Testing OBA Company Code Assignment Fix")
    print("=" * 60)
    
    # Test Case: OBA voucher should not be hardcoded to VCJ
    test_entry = {
        "voucher_no": "OBA-0000036",
        "description": "Equipment purchase",
        "Document_Date": "2025/06/25",
        "External_Document_No": "0628",
        "debit": {
            "department": "VCT.9999G",  # Should determine company as VCT, not VCJ
            "account": "74510-10",
            "gl_account": "G/L Account",
            "amount": 2000.0,
            "currency": "NTD",
            "applicant_code": "10004"
        },
        "credit": {
            "department": "VCT.9999G",  # Should determine company as VCT, not VCJ
            "gl_account": "Vendor",
            "vendor_code": "V-TW00002",
            "amount": 2000.0,
            "currency": "NTD",
            "applicant_code": "10004"
        }
    }
    
    print(f"Voucher: {test_entry['voucher_no']}")
    print(f"Department: '{test_entry['debit']['department']}'")
    print("Expected: Should NOT be hardcoded to VCJ")
    
    try:
        # Create debit line to test company determination
        debit_line = create_journal_line(test_entry, "debit")
        actual_company = debit_line.get("Shortcut_Dimension_1_Code", "")
        
        print(f"Actual Company: {actual_company}")
        
        if actual_company == "VCT":
            print("✅ PASSED - OBA voucher correctly assigned to VCT based on department")
            return True
        elif actual_company == "VCJ":
            print("❌ FAILED - OBA voucher still hardcoded to VCJ!")
            return False
        else:
            print(f"⚠️  UNEXPECTED - OBA voucher assigned to {actual_company}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("VPA/OBA Company Code Assignment Fix Test")
    print("This test verifies that voucher prefixes are no longer hardcoded to specific companies")
    
    # Run VPA tests
    vpa_passed = test_vpa_company_code_assignment()
    
    # Run OBA tests
    oba_passed = test_oba_company_code_assignment()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    if vpa_passed and oba_passed:
        print("🎉 ALL TESTS PASSED!")
        print("Company code assignment fix is working correctly.")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED!")
        print("Company code assignment fix needs further investigation.")
        sys.exit(1)
