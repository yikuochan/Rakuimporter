#!/usr/bin/env python3
"""
Test script to verify the duplicate billing fix for V-VC00048 entries.

This test ensures that V-VC00048 entries that are mapped to VCT vendor
do not also create VCT responsibility entries (which would cause duplicate billing).
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vct_responsibility_consolidation import collect_vct_responsibility_candidates

def test_duplicate_billing_prevention():
    """Test that V-VC00048 entries don't create duplicate billing."""
    
    # Sample entries that would previously cause duplicate billing
    test_entries = [
        {
            "voucher_no": "APA-0000552",
            "External_Document_No": "20250404",
            "Document_Date": "2025-04-22",
            "description": "ESCAR USA Ticket",
            "debit": {
                "amount": 500.0,
                "currency": "R-USD",
                "account": "75512-10",
                "gl_account": "G/L Account",
                "department": "VCA.1342G",
                "applicant_code": ""
            },
            "credit": {
                "amount": 500.0,
                "currency": "R-USD",
                "vendor_code": "V-VC00048",  # This would be mapped to VCT
                "gl_account": "Vendor",
                "department": "VCA.1342G",  # Non-VCT cost center
                "account_source": "vendor_code"
            }
        },
        {
            "voucher_no": "APA-0000553",
            "External_Document_No": "20250405",
            "Document_Date": "2025-04-23",
            "description": "Another expense",
            "debit": {
                "amount": 300.0,
                "currency": "NTD",
                "account": "75512-10",
                "gl_account": "G/L Account",
                "department": "VCT.1751G",
                "applicant_code": ""
            },
            "credit": {
                "amount": 300.0,
                "currency": "NTD",
                "vendor_code": "V-VC00048",  # VCT cost center - should not be skipped
                "gl_account": "Vendor",
                "department": "VCT.1751G",  # VCT cost center
                "account_source": "vendor_code"
            }
        }
    ]
    
    print("Testing duplicate billing prevention...")
    
    # Test the collection function
    candidates = collect_vct_responsibility_candidates(test_entries)
    
    print(f"Number of vouchers collected for VCT responsibility: {len(candidates)}")
    
    # Verify results
    if len(candidates) == 0:
        print("✅ SUCCESS: No VCT responsibility candidates collected (duplicate billing prevented)")
        print("   - V-VC00048 entries with non-VCT cost centers are correctly skipped")
        print("   - This prevents duplicate billing when intercompany transactions are already created")
    else:
        print("❌ FAILURE: VCT responsibility candidates were collected")
        print(f"   - Found candidates for vouchers: {list(candidates.keys())}")
        print("   - This could cause duplicate billing")
    
    # Additional verification
    for voucher_no, entries in candidates.items():
        print(f"\nVoucher {voucher_no}:")
        for entry in entries:
            cost_center = entry.get('credit', {}).get('department', '')[:3]
            print(f"  - Cost Center: {cost_center}, Amount: {entry.get('credit', {}).get('amount', 0)}")

if __name__ == "__main__":
    test_duplicate_billing_prevention()
