#!/usr/bin/env python3
"""
Test V-VC00048 consolidation fix

This test verifies that:
1. V-VC00048 entries with VCT cost center are consolidated using VCT rules
2. V-VC00048 entries with VCA cost center are consolidated using VCA rules
3. Other V-VC vendors are still excluded from consolidation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.csv_to_json_converter import consolidate_entries

def test_v_vc00048_consolidation_fix():
    """Test that V-VC00048 consolidation follows cost center rules"""
    
    print("Testing V-VC00048 consolidation fix...")
    
    # Test data: V-VC00048 entries with different cost centers
    test_entries = [
        # VCA cost center entries (should be consolidated)
        {
            "voucher_no": "APA-0000552",
            "transaction_date": "2025/04/22",
            "application_date": "2025/06/30",
            "journal_generation_date": "2025/07/04",
            "description": "ESCAR USA Ticket",
            "credit_description": "ESCAR USA Tickets",
            "note": "",
            "receipt_invoice": "",
            "External_Document_No": "20250404",
            "Document_Date": "2025/04/22",
            "debit": {
                "marker": "*",
                "gl_account": "G/L Account",
                "account": "75512-10",
                "sub_account": "",
                "amount": 500.0,
                "currency": "USD",
                "department": "VCA.1342G",
                "applicant_code": "10126",
                "vendor_code": "V-VC00048",
                "free_field": "",
                "department_code": "VCA.1342G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "V-VC00048",
                "sub_account": "",
                "amount": 500.0,
                "currency": "USD",
                "department": "VCA.1342G",
                "applicant_code": "10126",
                "vendor_code": "V-VC00048",
                "free_field": "",
                "department_code": "VCA.9999",
                "Remarks": "ESCAR USA Tickets"
            }
        },
        {
            "voucher_no": "APA-0000552",
            "transaction_date": "2025/04/22",
            "application_date": "2025/06/30",
            "journal_generation_date": "2025/07/04",
            "description": "ESCAR USA Ticket",
            "credit_description": "ESCAR USA Tickets",
            "note": "",
            "receipt_invoice": "",
            "External_Document_No": "20250404-1",
            "Document_Date": "2025/04/22",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "75512-10",
                "sub_account": "",
                "amount": 500.0,
                "currency": "USD",
                "department": "VCA.1342G",
                "applicant_code": "10126",
                "vendor_code": "V-VC00048",
                "free_field": "",
                "department_code": "VCA.1342G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "V-VC00048",
                "sub_account": "",
                "amount": 500.0,
                "currency": "USD",
                "department": "VCA.1342G",
                "applicant_code": "10126",
                "vendor_code": "V-VC00048",
                "free_field": "",
                "department_code": "VCA.9999",
                "Remarks": "ESCAR USA Tickets"
            }
        },
        # VCT cost center entries (should be consolidated)
        {
            "voucher_no": "APA-0000481",
            "transaction_date": "2025/06/25",
            "application_date": "2025/07/02",
            "journal_generation_date": "2025/07/04",
            "description": "NordVpn",
            "credit_description": "NordVpn",
            "note": "",
            "receipt_invoice": "",
            "External_Document_No": "NRDCH-408960",
            "Document_Date": "2025/06/25",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "74850-10",
                "sub_account": "",
                "amount": 366.0,
                "currency": "NTD",
                "department": "VCT.1751G",
                "applicant_code": "10115",
                "vendor_code": "V-VC00048",
                "free_field": "",
                "department_code": "VCT.1731G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "V-VC00048",
                "sub_account": "",
                "amount": 366.0,
                "currency": "NTD",
                "department": "VCT.1751G",
                "applicant_code": "10115",
                "vendor_code": "V-VC00048",
                "free_field": "",
                "department_code": "VCT.9999",
                "Remarks": "NordVpn"
            }
        },
        {
            "voucher_no": "APA-0000481",
            "transaction_date": "2025/06/25",
            "application_date": "2025/07/02",
            "journal_generation_date": "2025/07/04",
            "description": "NordVpn",
            "credit_description": "NordVpn",
            "note": "",
            "receipt_invoice": "",
            "External_Document_No": "NRDCH-408959",
            "Document_Date": "2025/06/25",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "74850-10",
                "sub_account": "",
                "amount": 366.0,
                "currency": "NTD",
                "department": "VCT.1751G",
                "applicant_code": "10115",
                "vendor_code": "V-VC00048",
                "free_field": "",
                "department_code": "VCT.1731G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "V-VC00048",
                "sub_account": "",
                "amount": 366.0,
                "currency": "NTD",
                "department": "VCT.1751G",
                "applicant_code": "10115",
                "vendor_code": "V-VC00048",
                "free_field": "",
                "department_code": "VCT.9999",
                "Remarks": "NordVpn"
            }
        },
        # Other V-VC vendor (should be excluded from consolidation)
        {
            "voucher_no": "APA-0000999",
            "transaction_date": "2025/06/25",
            "application_date": "2025/07/02",
            "journal_generation_date": "2025/07/04",
            "description": "Other V-VC vendor",
            "credit_description": "Other V-VC vendor",
            "note": "",
            "receipt_invoice": "",
            "External_Document_No": "OTHER-001",
            "Document_Date": "2025/06/25",
            "debit": {
                "marker": "",
                "gl_account": "G/L Account",
                "account": "74850-10",
                "sub_account": "",
                "amount": 100.0,
                "currency": "NTD",
                "department": "VCT.1751G",
                "applicant_code": "10115",
                "vendor_code": "V-VC00099",
                "free_field": "",
                "department_code": "VCT.1731G"
            },
            "credit": {
                "marker": "",
                "gl_account": "Vendor",
                "account": "V-VC00099",
                "sub_account": "",
                "amount": 100.0,
                "currency": "NTD",
                "department": "VCT.1751G",
                "applicant_code": "10115",
                "vendor_code": "V-VC00099",
                "free_field": "",
                "department_code": "VCT.9999",
                "Remarks": "Other V-VC vendor"
            }
        }
    ]
    
    # Run consolidation
    consolidated_entries = consolidate_entries(test_entries)
    
    print(f"Input entries: {len(test_entries)}")
    print(f"Output entries: {len(consolidated_entries)}")
    
    # Analyze results
    vca_entries = [e for e in consolidated_entries if e.get('voucher_no') == 'APA-0000552']
    vct_entries = [e for e in consolidated_entries if e.get('voucher_no') == 'APA-0000481']
    other_vc_entries = [e for e in consolidated_entries if e.get('voucher_no') == 'APA-0000999']
    
    print(f"\nVCA entries (APA-0000552): {len(vca_entries)}")
    print(f"VCT entries (APA-0000481): {len(vct_entries)}")
    print(f"Other V-VC entries (APA-0000999): {len(other_vc_entries)}")
    
    # Check for consolidated entries
    vca_consolidated = [e for e in vca_entries if e.get('credit', {}).get('consolidated', False)]
    vct_consolidated = [e for e in vct_entries if e.get('credit', {}).get('consolidated', False)]
    
    print(f"\nVCA consolidated entries: {len(vca_consolidated)}")
    print(f"VCT consolidated entries: {len(vct_consolidated)}")
    
    # Verify expectations
    success = True
    
    # Test 1: VCA entries should create VCT responsibility entries (2 original + 2 VCT responsibility = 4 total, NO consolidation)
    if len(vca_entries) == 4 and len(vca_consolidated) == 0:
        print("✅ PASS: VCA entries (V-VC00048) create VCT responsibility entries without consolidation")
        
        # Check for VCT responsibility entries
        vct_responsibility_entries = [e for e in vca_entries if e.get('debit', {}).get('vct_responsibility', False) or e.get('credit', {}).get('vct_responsibility', False)]
        if len(vct_responsibility_entries) == 2:
            print(f"✅ PASS: VCT responsibility entries created: {len(vct_responsibility_entries)}")
        else:
            print(f"❌ FAIL: Expected 2 VCT responsibility entries, got: {len(vct_responsibility_entries)}")
            success = False
    else:
        print(f"❌ FAIL: VCA entries not processed correctly. Total: {len(vca_entries)}, Consolidated: {len(vca_consolidated)} (should be 4 total, 0 consolidated)")
        success = False
    
    # Test 2: VCT entries should be consolidated (2 individual + 1 consolidated = 3 total)
    if len(vct_entries) == 3 and len(vct_consolidated) == 1:
        print("✅ PASS: VCT entries (V-VC00048) are consolidated correctly")
        consolidated_amount = vct_consolidated[0].get('credit', {}).get('amount', 0)
        expected_amount = 732.0  # 366 + 366
        if abs(consolidated_amount - expected_amount) < 0.01:
            print(f"✅ PASS: VCT consolidated amount is correct: {consolidated_amount}")
        else:
            print(f"❌ FAIL: VCT consolidated amount is incorrect: {consolidated_amount}, expected: {expected_amount}")
            success = False
    else:
        print(f"❌ FAIL: VCT entries not consolidated correctly. Total: {len(vct_entries)}, Consolidated: {len(vct_consolidated)}")
        success = False
    
    # Test 3: Other V-VC vendors should not be consolidated (1 individual entry only)
    if len(other_vc_entries) == 1:
        print("✅ PASS: Other V-VC vendors are excluded from consolidation")
    else:
        print(f"❌ FAIL: Other V-VC vendors not handled correctly. Entries: {len(other_vc_entries)}")
        success = False
    
    if success:
        print("\n🎉 All tests passed! V-VC00048 consolidation fix is working correctly.")
        print("✅ V-VC00048 with VCA cost center: Consolidated using VCA rules")
        print("✅ V-VC00048 with VCT cost center: Consolidated using VCT rules")
        print("✅ Other V-VC vendors: Excluded from consolidation")
    else:
        print("\n❌ Some tests failed. Please check the consolidation logic.")
    
    return success

if __name__ == "__main__":
    test_v_vc00048_consolidation_fix()
