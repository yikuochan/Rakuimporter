#!/usr/bin/env python3
"""
Debug VCA consolidation to see what entries are being created
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.csv_to_json_converter import consolidate_entries
import json

def debug_vca_consolidation():
    """Debug VCA consolidation to see what entries are being created"""
    
    print("Debugging VCA consolidation...")
    
    # Test data: VCA entries with V-VC00048
    test_entries = [
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
        }
    ]
    
    # Run consolidation
    consolidated_entries = consolidate_entries(test_entries)
    
    print(f"Input entries: {len(test_entries)}")
    print(f"Output entries: {len(consolidated_entries)}")
    
    # Analyze VCA entries
    vca_entries = [e for e in consolidated_entries if e.get('voucher_no') == 'APA-0000552']
    print(f"\nVCA entries (APA-0000552): {len(vca_entries)}")
    
    for i, entry in enumerate(vca_entries):
        print(f"\n--- Entry {i+1} ---")
        print(f"External_Document_No: {entry.get('External_Document_No')}")
        print(f"Description: {entry.get('description')}")
        
        # Check debit side
        debit = entry.get('debit', {})
        if debit.get('amount', 0) > 0:
            print(f"DEBIT: {debit.get('gl_account')} - {debit.get('account')} - Amount: {debit.get('amount')} {debit.get('currency')}")
            print(f"  Department: {debit.get('department')} / {debit.get('department_code')}")
            if debit.get('vct_responsibility'):
                print(f"  VCT Responsibility: True (Original: {debit.get('original_cost_center')})")
        
        # Check credit side
        credit = entry.get('credit', {})
        if credit.get('amount', 0) > 0:
            print(f"CREDIT: {credit.get('gl_account')} - {credit.get('account')} - Amount: {credit.get('amount')} {credit.get('currency')}")
            print(f"  Department: {credit.get('department')} / {credit.get('department_code')}")
            if credit.get('vct_responsibility'):
                print(f"  VCT Responsibility: True (Original: {credit.get('original_cost_center')})")
            if credit.get('consolidated'):
                print(f"  Consolidated: True (from {credit.get('original_entries_count')} entries)")
    
    # Check for VCT responsibility entries
    vct_responsibility_entries = [e for e in vca_entries if e.get('debit', {}).get('vct_responsibility', False) or e.get('credit', {}).get('vct_responsibility', False)]
    print(f"\nVCT responsibility entries: {len(vct_responsibility_entries)}")
    
    # Check for consolidated entries
    consolidated_entries_count = [e for e in vca_entries if e.get('credit', {}).get('consolidated', False)]
    print(f"Consolidated entries: {len(consolidated_entries_count)}")
    
    return vca_entries

if __name__ == "__main__":
    debug_vca_consolidation()
