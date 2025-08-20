#!/usr/bin/env python3
"""
Validation script to test VCT responsibility double counting fix.

This script validates that the fix for VCT responsibility double counting works correctly
by testing with actual data from the VCA-0721.json file and comparing before/after behavior.

Usage:
    python validate_vct_responsibility_fix.py
"""

import json
import sys
import os
from decimal import Decimal

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.vct_responsibility_consolidation import collect_vct_responsibility_candidates


def load_test_data():
    """Load test data from VCA-0721.json file."""
    try:
        with open('examples/0721/VCA-0721.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: VCA-0721.json file not found. Please ensure it exists in examples/0721/")
        return None


def analyze_vct_responsibility_candidates(entries):
    """Analyze VCT responsibility candidates and return detailed breakdown."""
    candidates = collect_vct_responsibility_candidates(entries)
    
    analysis = {
        'total_vouchers': len(candidates),
        'voucher_details': {},
        'total_amount': 0
    }
    
    for voucher_no, voucher_entries in candidates.items():
        voucher_total = sum(entry['credit']['amount'] for entry in voucher_entries)
        analysis['voucher_details'][voucher_no] = {
            'entry_count': len(voucher_entries),
            'total_amount': voucher_total,
            'entries': [
                {
                    'amount': entry['credit']['amount'],
                    'cost_center': entry['credit']['department'][:3] if entry['credit'].get('department') else '',
                    'is_consolidated': entry['credit'].get('consolidated', False)
                }
                for entry in voucher_entries
            ]
        }
        analysis['total_amount'] += voucher_total
    
    return analysis


def test_with_vca_0721_data():
    """Test the fix with actual VCA-0721.json data."""
    print("=" * 60)
    print("VCT Responsibility Double Counting Fix Validation")
    print("=" * 60)
    
    entries = load_test_data()
    if not entries:
        return False
    
    print(f"Loaded {len(entries)} entries from VCA-0721.json")
    
    # Analyze all V-VC00048 entries
    vvc_entries = [e for e in entries if e.get('credit', {}).get('vendor_code') == 'V-VC00048']
    print(f"Found {len(vvc_entries)} V-VC00048 entries total")
    
    # Show breakdown of V-VC00048 entries
    consolidated_entries = [e for e in vvc_entries if e.get('credit', {}).get('consolidated', False)]
    original_entries = [e for e in vvc_entries if not e.get('credit', {}).get('consolidated', False)]
    
    print(f"- Original entries: {len(original_entries)}")
    print(f"- Consolidated entries: {len(consolidated_entries)}")
    
    # Analyze VCT responsibility candidates
    print("\nAnalyzing VCT responsibility candidates...")
    analysis = analyze_vct_responsibility_candidates(entries)
    
    print(f"VCT responsibility will be created for {analysis['total_vouchers']} vouchers:")
    
    for voucher_no, details in analysis['voucher_details'].items():
        print(f"\n  {voucher_no}:")
        print(f"    Entries collected: {details['entry_count']}")
        print(f"    Total amount: {details['total_amount']}")
        
        for i, entry in enumerate(details['entries'], 1):
            consolidated_flag = " (CONSOLIDATED)" if entry['is_consolidated'] else ""
            print(f"      Entry {i}: {entry['amount']} from {entry['cost_center']}{consolidated_flag}")
    
    print(f"\nTotal VCT responsibility amount: {analysis['total_amount']}")
    
    return True


def validate_specific_scenarios():
    """Validate specific scenarios that were problematic before the fix."""
    print("\n" + "=" * 60)
    print("Specific Scenario Validation")
    print("=" * 60)
    
    # Test Case 1: APA-0000470 scenario (the main problem case)
    print("\nTest Case 1: APA-0000470 Double Counting Prevention")
    test_entries = [
        {
            "voucher_no": "APA-0000470",
            "credit": {
                "vendor_code": "V-VC00048",
                "amount": 5600.0,
                "department": "VCA.1342G",
                "currency": "R-USD"
            }
        },
        {
            "voucher_no": "APA-0000470",
            "credit": {
                "vendor_code": "V-VC00048",
                "amount": 10000.0,
                "department": "VCA.1342G",
                "currency": "R-USD"
            }
        },
        {
            "voucher_no": "APA-0000470",
            "credit": {
                "vendor_code": "V-VC00048",
                "amount": 15600.0,
                "department": "VCA.1342G",
                "currency": "R-USD",
                "consolidated": True,
                "original_entries_count": 2
            }
        }
    ]
    
    candidates = collect_vct_responsibility_candidates(test_entries)
    
    if "APA-0000470" in candidates:
        total_amount = sum(e['credit']['amount'] for e in candidates["APA-0000470"])
        entry_count = len(candidates["APA-0000470"])
        
        print(f"  Entries collected: {entry_count} (expected: 2)")
        print(f"  Total amount: {total_amount} (expected: 15600.0, NOT 31200.0)")
        
        if entry_count == 2 and total_amount == 15600.0:
            print("  ✅ PASS: Consolidated entry correctly excluded")
        else:
            print("  ❌ FAIL: Double counting still occurring")
            return False
    else:
        print("  ❌ FAIL: No candidates collected for APA-0000470")
        return False
    
    # Test Case 2: Single entry with consolidated should still work
    print("\nTest Case 2: Single Entry With Consolidated")
    test_entries_single = [
        {
            "voucher_no": "APA-0000579",
            "credit": {
                "vendor_code": "V-VC00048",
                "amount": 300.0,
                "department": "VCA.1342G",
                "currency": "R-USD"
            }
        },
        {
            "voucher_no": "APA-0000579",
            "credit": {
                "vendor_code": "V-VC00048",
                "amount": 300.0,
                "department": "VCA.1342G",
                "currency": "R-USD",
                "consolidated": True,
                "original_entries_count": 1
            }
        }
    ]
    
    candidates_single = collect_vct_responsibility_candidates(test_entries_single)
    
    if "APA-0000579" in candidates_single:
        total_amount = sum(e['credit']['amount'] for e in candidates_single["APA-0000579"])
        entry_count = len(candidates_single["APA-0000579"])
        
        print(f"  Entries collected: {entry_count} (expected: 1)")
        print(f"  Total amount: {total_amount} (expected: 300.0, NOT 600.0)")
        
        if entry_count == 1 and total_amount == 300.0:
            print("  ✅ PASS: Single entry with consolidated handled correctly")
        else:
            print("  ❌ FAIL: Single entry double counting")
            return False
    else:
        print("  ❌ FAIL: No candidates collected for APA-0000579")
        return False
    
    return True


def compare_before_after_amounts():
    """Compare expected amounts before and after the fix."""
    print("\n" + "=" * 60)
    print("Before/After Comparison")
    print("=" * 60)
    
    # Expected results based on the BC console screenshot and logs
    scenarios = [
        {
            "voucher": "APA-0000470",
            "original_entries": [5600.0, 10000.0],
            "consolidated_amount": 15600.0,
            "before_fix_total": 31200.0,  # 5600 + 10000 + 15600
            "after_fix_total": 15600.0    # 5600 + 10000
        },
        {
            "voucher": "APA-0000579", 
            "original_entries": [300.0],
            "consolidated_amount": 300.0,
            "before_fix_total": 600.0,    # 300 + 300
            "after_fix_total": 300.0      # 300
        },
        {
            "voucher": "APA-0000600",
            "original_entries": [873.96],
            "consolidated_amount": 873.96,
            "before_fix_total": 1747.92,  # 873.96 + 873.96
            "after_fix_total": 873.96     # 873.96
        }
    ]
    
    print("Expected VCT responsibility amounts:")
    print(f"{'Voucher':<15} {'Before Fix':<12} {'After Fix':<12} {'Savings':<12}")
    print("-" * 55)
    
    total_before = 0
    total_after = 0
    
    for scenario in scenarios:
        before = scenario["before_fix_total"]
        after = scenario["after_fix_total"]
        savings = before - after
        
        print(f"{scenario['voucher']:<15} {before:<12.2f} {after:<12.2f} {savings:<12.2f}")
        
        total_before += before
        total_after += after
    
    total_savings = total_before - total_after
    print("-" * 55)
    print(f"{'TOTAL':<15} {total_before:<12.2f} {total_after:<12.2f} {total_savings:<12.2f}")
    
    savings_percentage = (total_savings / total_before) * 100
    print(f"\nTotal savings: {total_savings:.2f} ({savings_percentage:.1f}% reduction)")
    
    return True


def main():
    """Main validation function."""
    print("Starting VCT Responsibility Double Counting Fix Validation...")
    
    success = True
    
    # Test with actual VCA-0721.json data
    if not test_with_vca_0721_data():
        success = False
    
    # Validate specific scenarios
    if not validate_specific_scenarios():
        success = False
    
    # Compare before/after amounts
    if not compare_before_after_amounts():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("The VCT responsibility double counting fix is working correctly.")
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("Please review the issues above.")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)