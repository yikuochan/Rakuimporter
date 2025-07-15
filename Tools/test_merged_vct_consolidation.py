#!/usr/bin/env python3
"""
Test script to verify the merged VCT responsibility consolidation functionality
in the main process_japan_exports.py file.
"""

import sys
import os
import json
from decimal import Decimal

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vct_responsibility_consolidation import collect_vct_responsibility_candidates

def test_vct_candidate_collection():
    """Test VCT responsibility candidate collection with sample data."""
    print("Testing VCT responsibility candidate collection...")
    
    # Sample entries with V-VC00048 vendor code
    test_entries = [
        {
            "voucher_no": "APA-0000552",
            "debit": {
                "amount": 1000.0,
                "department": "VCA.1234",
                "account": "62100-10"
            },
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCA.1234",
                "amount": 1000.0,
                "gl_account": "Vendor"
            }
        },
        {
            "voucher_no": "APA-0000552",
            "debit": {
                "amount": 2000.0,
                "department": "VCA.5678",
                "account": "62200-10"
            },
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCA.5678",
                "amount": 2000.0,
                "gl_account": "Vendor"
            }
        },
        {
            "voucher_no": "APA-0000553",
            "debit": {
                "amount": 500.0,
                "department": "VCP.9999",
                "account": "61100-10"
            },
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCP.9999",
                "amount": 500.0,
                "gl_account": "Vendor"
            }
        },
        {
            "voucher_no": "APA-0000554",
            "debit": {
                "amount": 750.0,
                "department": "VCT.1111",
                "account": "63100-10"
            },
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCT.1111",
                "amount": 750.0,
                "gl_account": "Vendor"
            }
        }
    ]
    
    # Test candidate collection
    candidates = collect_vct_responsibility_candidates(test_entries)
    
    print(f"Found {len(candidates)} vouchers with VCT responsibility candidates:")
    for voucher_no, entries in candidates.items():
        print(f"  Voucher {voucher_no}: {len(entries)} entries")
        for entry in entries:
            dept = entry.get('credit', {}).get('department', '')
            cost_center = dept[:3] if dept else ''
            amount = entry.get('credit', {}).get('amount', 0)
            print(f"    - Department: {dept}, Cost Center: {cost_center}, Amount: {amount}")
    
    # Verify expected results
    expected_vouchers = {"APA-0000552", "APA-0000553"}  # VCT entries should be excluded
    actual_vouchers = set(candidates.keys())
    
    if actual_vouchers == expected_vouchers:
        print("✅ VCT candidate collection test PASSED")
        print(f"   Expected vouchers: {expected_vouchers}")
        print(f"   Actual vouchers: {actual_vouchers}")
        return True
    else:
        print("❌ VCT candidate collection test FAILED")
        print(f"   Expected vouchers: {expected_vouchers}")
        print(f"   Actual vouchers: {actual_vouchers}")
        return False

def test_import_functionality():
    """Test that the imports work correctly in the main file."""
    print("\nTesting import functionality...")
    
    try:
        # Test importing the main processing function
        from core.process_japan_exports import process_entries
        print("✅ Successfully imported process_entries from core.process_japan_exports")
        
        # Test importing the consolidation functions
        from core.vct_responsibility_consolidation import (
            collect_vct_responsibility_candidates,
            create_consolidated_vct_responsibility_entries
        )
        print("✅ Successfully imported VCT consolidation functions")
        
        return True
    except ImportError as e:
        print(f"❌ Import test FAILED: {e}")
        return False

def test_function_signatures():
    """Test that function signatures are correct."""
    print("\nTesting function signatures...")
    
    try:
        from core.process_japan_exports import process_entries
        from core.vct_responsibility_consolidation import (
            collect_vct_responsibility_candidates,
            create_consolidated_vct_responsibility_entries
        )
        
        # Test collect_vct_responsibility_candidates signature
        test_entries = []
        result = collect_vct_responsibility_candidates(test_entries)
        if isinstance(result, dict):
            print("✅ collect_vct_responsibility_candidates signature correct")
        else:
            print("❌ collect_vct_responsibility_candidates returned unexpected type")
            return False
        
        print("✅ Function signature tests PASSED")
        return True
    except Exception as e:
        print(f"❌ Function signature test FAILED: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Merged VCT Responsibility Consolidation")
    print("=" * 60)
    
    tests = [
        test_import_functionality,
        test_function_signatures,
        test_vct_candidate_collection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! The merged implementation is working correctly.")
        return 0
    else:
        print("⚠️  Some tests FAILED. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
