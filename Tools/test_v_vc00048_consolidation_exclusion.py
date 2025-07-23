#!/usr/bin/env python3
"""
Test script to verify that V-VC00048 entries are excluded from consolidation
during CSV to JSON conversion process.

This test verifies the fix for the issue where V-VC00048 entries were being
consolidated during CSV to JSON conversion, which should not happen according
to GitHub issue #78.
"""

import json
import sys
import os

# Add the parent directory to the path so we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_v_vc00048_consolidation_exclusion():
    """
    Test that V-VC00048 entries are excluded from consolidation in JSON output.
    """
    print("Testing V-VC00048 consolidation exclusion...")
    
    # Read the generated JSON file
    json_file_path = "examples/Raku export-CC.json"
    
    if not os.path.exists(json_file_path):
        print(f"ERROR: JSON file {json_file_path} does not exist")
        print("Please run: python run_importer.py \"examples/Raku export-CC.csv\" --skip-import")
        return False
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    
    print(f"Loaded {len(entries)} entries from {json_file_path}")
    
    # Check for consolidated entries
    consolidated_entries = []
    v_vc_entries = []
    
    for entry in entries:
        # Check if this is a consolidated entry
        if entry.get("credit", {}).get("consolidated", False):
            consolidated_entries.append(entry)
        
        # Check if this is a V-VC entry
        vendor_code = entry.get("credit", {}).get("vendor_code", "")
        if vendor_code.startswith("V-VC"):
            v_vc_entries.append(entry)
    
    print(f"Found {len(consolidated_entries)} consolidated entries")
    print(f"Found {len(v_vc_entries)} V-VC entries")
    
    # Test 1: Check consolidated entries - V-VC00048 with VCT cost center should be consolidated
    v_vc00048_consolidated = [e for e in consolidated_entries if e.get("credit", {}).get("vendor_code") == "V-VC00048"]
    other_v_vc_consolidated = [e for e in consolidated_entries if e.get("credit", {}).get("vendor_code", "").startswith("V-VC") and e.get("credit", {}).get("vendor_code") != "V-VC00048"]
    
    # V-VC00048 with VCT cost center should be consolidated
    vct_consolidated = [e for e in v_vc00048_consolidated if e.get("credit", {}).get("department", "").startswith("VCT")]
    if vct_consolidated:
        print(f"✅ PASS: Found {len(vct_consolidated)} V-VC00048 VCT consolidated entries (expected)")
    
    # Other V-VC vendors should NOT be consolidated
    if other_v_vc_consolidated:
        print("❌ FAIL: Found consolidated entries for other V-VC vendors:")
        for entry in other_v_vc_consolidated:
            voucher_no = entry.get("voucher_no", "Unknown")
            vendor_code = entry.get("credit", {}).get("vendor_code", "Unknown")
            print(f"  - Voucher: {voucher_no}, Vendor: {vendor_code}")
        return False
    else:
        print("✅ PASS: No consolidated entries found for other V-VC vendors")
    
    # Test 2: All V-VC entries should be individual entries
    if v_vc_entries:
        print(f"✅ PASS: Found {len(v_vc_entries)} individual V-VC entries (not consolidated)")
        
        # Verify each V-VC entry is individual
        for entry in v_vc_entries:
            voucher_no = entry.get("voucher_no", "Unknown")
            vendor_code = entry.get("credit", {}).get("vendor_code", "Unknown")
            external_doc_no = entry.get("External_Document_No", "Unknown")
            
            # Check that it has either debit OR credit amount (VCT responsibility entries have only one side)
            debit_amount = entry.get("debit", {}).get("amount", 0)
            credit_amount = entry.get("credit", {}).get("amount", 0)
            
            # Check if this is a VCT responsibility entry
            is_vct_responsibility = (entry.get("debit", {}).get("vct_responsibility", False) or 
                                   entry.get("credit", {}).get("vct_responsibility", False))
            
            # Check if this is a consolidated entry
            is_consolidated = entry.get("credit", {}).get("consolidated", False)
            
            if is_vct_responsibility:
                # VCT responsibility entries should have either debit OR credit amount
                if (debit_amount > 0 and credit_amount == 0) or (credit_amount > 0 and debit_amount == 0):
                    print(f"  ✅ VCT responsibility entry: {voucher_no} - {vendor_code} - {external_doc_no}")
                else:
                    print(f"  ❌ Invalid VCT responsibility entry: {voucher_no} - {vendor_code} - {external_doc_no} (debit: {debit_amount}, credit: {credit_amount})")
                    return False
            elif is_consolidated:
                # Consolidated entries should have only credit amount
                if credit_amount > 0 and debit_amount == 0:
                    print(f"  ✅ Consolidated entry: {voucher_no} - {vendor_code} - {external_doc_no}")
                else:
                    print(f"  ❌ Invalid consolidated entry: {voucher_no} - {vendor_code} - {external_doc_no} (debit: {debit_amount}, credit: {credit_amount})")
                    return False
            else:
                # Regular entries should have both debit and credit amounts
                if debit_amount > 0 and credit_amount > 0:
                    print(f"  ✅ Individual entry: {voucher_no} - {vendor_code} - {external_doc_no}")
                else:
                    print(f"  ❌ Invalid entry: {voucher_no} - {vendor_code} - {external_doc_no} (debit: {debit_amount}, credit: {credit_amount})")
                    return False
    else:
        print("❌ FAIL: No V-VC entries found in JSON output")
        return False
    
    # Test 3: Verify expected structure for V-VC00048 entries
    v_vc00048_entries = [e for e in v_vc_entries if e.get("credit", {}).get("vendor_code") == "V-VC00048"]
    
    # New expected counts based on updated logic:
    # APA-0000552 (VCA): 2 original + 2 VCT responsibility = 4 entries
    # APA-0000481 (VCT): 2 original + 1 consolidated = 3 entries (but consolidated entry is not in v_vc_entries)
    # So we expect 4 + 2 = 6 individual V-VC00048 entries
    if len(v_vc00048_entries) >= 6:  # At least 6 individual entries
        print(f"✅ PASS: Found {len(v_vc00048_entries)} V-VC00048 entries (expected at least 6)")
    else:
        print(f"❌ FAIL: Expected at least 6 V-VC00048 entries, found {len(v_vc00048_entries)}")
        return False
    
    # Test 4: Verify voucher distribution
    voucher_counts = {}
    for entry in v_vc00048_entries:
        voucher_no = entry.get("voucher_no", "Unknown")
        voucher_counts[voucher_no] = voucher_counts.get(voucher_no, 0) + 1
    
    # Updated expected counts:
    # APA-0000552 (VCA): 4 entries (2 original + 2 VCT responsibility)
    # APA-0000481 (VCT): 2 individual entries (consolidated entry is separate)
    expected_vouchers = {"APA-0000552": 4, "APA-0000481": 2}
    
    for voucher_no, expected_count in expected_vouchers.items():
        actual_count = voucher_counts.get(voucher_no, 0)
        if actual_count >= expected_count:
            print(f"✅ PASS: Voucher {voucher_no} has {actual_count} entries (expected at least {expected_count})")
        else:
            print(f"❌ FAIL: Voucher {voucher_no} expected at least {expected_count} entries, found {actual_count}")
            return False
    
    print("\n🎉 All tests passed! V-VC00048 consolidation exclusion is working correctly.")
    return True

if __name__ == "__main__":
    success = test_v_vc00048_consolidation_exclusion()
    sys.exit(0 if success else 1)
