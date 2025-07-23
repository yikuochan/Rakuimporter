#!/usr/bin/env python3
"""
Debug VCT consolidation to understand the correct pattern
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.csv_to_json_converter import consolidate_entries

def debug_vct_consolidation():
    """Debug VCT consolidation to understand the correct pattern"""
    
    # VCT test data (from the test file)
    test_entries = [
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
        }
    ]
    
    print("=== DEBUG VCT CONSOLIDATION ===")
    print(f"Input entries: {len(test_entries)}")
    
    # Run consolidation
    result = consolidate_entries(test_entries)
    
    print(f"Output entries: {len(result)}")
    
    # Analyze results
    for i, entry in enumerate(result):
        print(f"\nEntry {i+1}:")
        print(f"  Voucher: {entry['voucher_no']}")
        print(f"  External_Doc_No: {entry['External_Document_No']}")
        print(f"  Debit amount: {entry['debit']['amount']}")
        print(f"  Credit amount: {entry['credit']['amount']}")
        print(f"  Credit consolidated: {entry['credit'].get('consolidated', False)}")
        print(f"  Credit vendor: {entry['credit']['vendor_code']}")
        print(f"  Credit department: {entry['credit']['department']}")
    
    print(f"\n=== ANALYSIS ===")
    individual_entries = [e for e in result if not e['credit'].get('consolidated', False)]
    consolidated_entries = [e for e in result if e['credit'].get('consolidated', False)]
    
    print(f"Individual entries: {len(individual_entries)}")
    print(f"Consolidated entries: {len(consolidated_entries)}")
    
    print(f"\nVCT Pattern: {len(result)} total entries ({len(individual_entries)} individual + {len(consolidated_entries)} consolidated)")

if __name__ == "__main__":
    debug_vct_consolidation()
