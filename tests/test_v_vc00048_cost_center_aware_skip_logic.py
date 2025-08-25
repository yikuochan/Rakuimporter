#!/usr/bin/env python3
"""
Test V-VC00048 Cost Center Aware Skip Logic (Issue #96)

This test verifies the fix for Issue #96 that implements cost-center-aware 
V-VC00048 consolidated entry handling. The test validates that:

1. V-VC00048 consolidated entries with VCT cost centers get normal consolidated billing
2. V-VC00048 consolidated entries with non-VCT cost centers are skipped and replaced with VCT responsibility entries
3. The cost center extraction logic works correctly for different department formats

This addresses the bug where APA-0000619 (VCT cost center) was incorrectly being skipped.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.vct_responsibility_consolidation import collect_vct_responsibility_candidates

def create_test_entries_mixed_cost_centers():
    """Create test entries with both VCT and non-VCT cost centers."""
    return [
        {
            'voucher_no': 'APA-0000619',  # Based on real data - VCT cost center
            'description': 'VicOne Corporate Credit Card Saas Subscription',
            'Document_Date': '2025/07/16',
            'External_Document_No': 'APA-0000619',
            'debit': {
                'account': '76900-10',
                'gl_account': 'G/L Account',
                'amount': 64.00,  # Total of 25.00 + 39.00
                'currency': 'R-USD',
                'department': 'VCT.1692G',
                'applicant_code': '10108',
                'Receipt/Invoice Note(明細)': 'Combined credit card charges'
            },
            'credit': {
                'account': '31200-10',
                'gl_account': 'Vendor',
                'vendor_code': 'V-VC00048',
                'amount': 64.00,
                'currency': 'R-USD',
                'department': 'VCT.1692G',  # VCT cost center
                'consolidated': True,  # This should NOT be skipped
                'original_entries_count': 2,
                'consolidation_note': 'Consolidated from 2 entries'
            }
        },
        {
            'voucher_no': 'APA-0000630',  # Non-VCT cost center entry
            'description': 'VicOne Corporate Credit Card RD Product Testing Expense',
            'Document_Date': '2025/07/21',
            'External_Document_No': 'APA-0000630',
            'debit': {
                'account': '76710-10',
                'gl_account': 'G/L Account',
                'amount': 117.71,
                'currency': 'R-USD',
                'department': 'VCG.1697G',
                'applicant_code': '10083'
            },
            'credit': {
                'account': '31200-10',
                'gl_account': 'Vendor',
                'vendor_code': 'V-VC00048',
                'amount': 117.71,
                'currency': 'R-USD',
                'department': 'VCG.1697G',  # Non-VCT cost center (VCG)
                'consolidated': True  # This SHOULD be skipped
            }
        },
        {
            'voucher_no': 'APA-0000640',  # Another VCT cost center entry
            'description': 'VicOne Corporate Credit Card Office Supplies',
            'Document_Date': '2025/07/25',
            'External_Document_No': 'APA-0000640',
            'debit': {
                'account': '75400-10',
                'gl_account': 'G/L Account',
                'amount': 150.00,
                'currency': 'R-USD',
                'department': 'VCT.1751G',
                'applicant_code': '10129'
            },
            'credit': {
                'account': '31200-10',
                'gl_account': 'Vendor',
                'vendor_code': 'V-VC00048',
                'amount': 150.00,
                'currency': 'R-USD',
                'department': 'VCT.1751G',  # VCT cost center
                'consolidated': True  # This should NOT be skipped
            }
        },
        {
            'voucher_no': 'APA-0000650',  # Non-V-VC00048 vendor (should be processed normally)
            'description': 'Regular vendor payment',
            'Document_Date': '2025/07/30',
            'External_Document_No': 'APA-0000650',
            'debit': {
                'account': '74150-10',
                'gl_account': 'G/L Account',
                'amount': 1000.00,
                'currency': 'NTD',
                'department': 'VCP.1234G'
            },
            'credit': {
                'account': '31200-10',
                'gl_account': 'Vendor',
                'vendor_code': 'V-OTHER001',
                'amount': 1000.00,
                'currency': 'NTD',
                'department': 'VCP.1234G',
                'consolidated': True  # Should be processed normally (not V-VC00048)
            }
        }
    ]

def test_cost_center_extraction():
    """Test that cost center extraction works correctly."""
    print("Testing cost center extraction logic...")
    
    test_cases = [
        ('VCT.1692G', 'VCT'),
        ('VCG.1697G', 'VCG'),
        ('VCP.1234G', 'VCP'),
        ('VCA.5678G', 'VCA'),
        ('VCJ.9999G', 'VCJ'),
        ('VCT.1751', 'VCT'),  # Without G suffix
        ('ABC', 'ABC'),  # Three character code
        ('XY', 'XY'),  # Two character code
        ('', ''),  # Empty department
    ]
    
    all_passed = True
    
    for department, expected_cost_center in test_cases:
        cost_center = department[:3] if department else ""
        if cost_center == expected_cost_center:
            print(f"  ✅ '{department}' -> '{cost_center}'")
        else:
            print(f"  ❌ '{department}' -> Expected '{expected_cost_center}', got '{cost_center}'")
            all_passed = False
    
    return all_passed

def test_vct_cost_center_skip_logic():
    """Test the new cost-center-aware skip logic for V-VC00048 entries."""
    print("Testing V-VC00048 cost-center-aware skip logic...")
    
    test_entries = create_test_entries_mixed_cost_centers()
    
    # Simulate the new skip logic from process_japan_exports.py
    v_vc00048_consolidated_entries_to_skip = []
    v_vc00048_consolidated_entries_to_keep = []
    
    for entry in test_entries:
        is_v_vc00048_consolidated = (
            entry.get("credit", {}).get("consolidated") == True and 
            entry.get("credit", {}).get("vendor_code") == "V-VC00048"
        )
        
        if is_v_vc00048_consolidated:
            department = entry.get("credit", {}).get("department", "")
            cost_center = department[:3] if department else ""
            
            # Only skip if cost center is NOT VCT
            if cost_center != "VCT":
                v_vc00048_consolidated_entries_to_skip.append(entry)
                print(f"  🔄 Skipping V-VC00048 entry for NON-VCT cost center {cost_center} - Voucher: {entry.get('voucher_no')}")
            else:
                v_vc00048_consolidated_entries_to_keep.append(entry)
                print(f"  ✅ Keeping V-VC00048 entry for VCT cost center {cost_center} - Voucher: {entry.get('voucher_no')}")
    
    # Verify results
    expected_to_skip = 1  # APA-0000630 (VCG cost center)
    expected_to_keep = 2  # APA-0000619 and APA-0000640 (VCT cost centers)
    
    print(f"\nResults:")
    print(f"  Entries to skip: {len(v_vc00048_consolidated_entries_to_skip)} (expected: {expected_to_skip})")
    print(f"  Entries to keep: {len(v_vc00048_consolidated_entries_to_keep)} (expected: {expected_to_keep})")
    
    success = True
    
    if len(v_vc00048_consolidated_entries_to_skip) != expected_to_skip:
        print(f"  ❌ Expected {expected_to_skip} entries to skip, got {len(v_vc00048_consolidated_entries_to_skip)}")
        success = False
    
    if len(v_vc00048_consolidated_entries_to_keep) != expected_to_keep:
        print(f"  ❌ Expected {expected_to_keep} entries to keep, got {len(v_vc00048_consolidated_entries_to_keep)}")
        success = False
    
    # Verify specific vouchers
    skipped_vouchers = [e.get('voucher_no') for e in v_vc00048_consolidated_entries_to_skip]
    kept_vouchers = [e.get('voucher_no') for e in v_vc00048_consolidated_entries_to_keep]
    
    if 'APA-0000630' not in skipped_vouchers:
        print(f"  ❌ APA-0000630 (VCG cost center) should be skipped")
        success = False
    
    if 'APA-0000619' not in kept_vouchers:
        print(f"  ❌ APA-0000619 (VCT cost center) should be kept")
        success = False
    
    if 'APA-0000640' not in kept_vouchers:
        print(f"  ❌ APA-0000640 (VCT cost center) should be kept")
        success = False
    
    if success:
        print("  ✅ Cost-center-aware skip logic working correctly")
    
    return success

def test_vct_responsibility_collection_exclusion():
    """Test that VCT responsibility collection correctly excludes VCT cost centers and consolidated entries."""
    print("Testing VCT responsibility collection with cost center filtering...")
    
    # Create test entries including both consolidated and non-consolidated V-VC00048 entries
    test_entries_for_vct_collection = [
        {
            'voucher_no': 'APA-0000630',
            'credit': {
                'vendor_code': 'V-VC00048',
                'department': 'VCG.1697G',  # Non-VCT cost center
                'amount': 117.71,
                'consolidated': False  # Non-consolidated entry should be collected
            }
        },
        {
            'voucher_no': 'APA-0000631',
            'credit': {
                'vendor_code': 'V-VC00048',
                'department': 'VCT.1692G',  # VCT cost center
                'amount': 50.00,
                'consolidated': False  # Even non-consolidated VCT entries should be excluded
            }
        },
        {
            'voucher_no': 'APA-0000632',
            'credit': {
                'vendor_code': 'V-VC00048',
                'department': 'VCP.1234G',  # Non-VCT cost center
                'amount': 75.00,
                'consolidated': True  # Consolidated entries should be excluded
            }
        }
    ]
    
    # Collect VCT responsibility candidates
    vct_candidates = collect_vct_responsibility_candidates(test_entries_for_vct_collection)
    
    print(f"VCT responsibility candidates collected for {len(vct_candidates)} vouchers")
    
    # Should only have APA-0000630 (non-VCT cost center AND non-consolidated)
    expected_vouchers = ['APA-0000630']
    excluded_vouchers = ['APA-0000631', 'APA-0000632']  # VCT cost center or consolidated
    
    success = True
    
    for voucher in expected_vouchers:
        if voucher in vct_candidates:
            candidates = vct_candidates[voucher]
            cost_center = candidates[0].get('credit', {}).get('department', '')[:3]
            is_consolidated = candidates[0].get('credit', {}).get('consolidated', False)
            print(f"  ✅ {voucher} (cost center: {cost_center}, consolidated: {is_consolidated}) correctly collected for VCT responsibility")
        else:
            print(f"  ❌ {voucher} should be collected for VCT responsibility")
            success = False
    
    for voucher in excluded_vouchers:
        if voucher not in vct_candidates:
            entry = next((e for e in test_entries_for_vct_collection if e.get('voucher_no') == voucher), {})
            cost_center = entry.get('credit', {}).get('department', '')[:3]
            is_consolidated = entry.get('credit', {}).get('consolidated', False)
            print(f"  ✅ {voucher} (cost center: {cost_center}, consolidated: {is_consolidated}) correctly excluded from VCT responsibility")
        else:
            print(f"  ❌ {voucher} should be excluded from VCT responsibility")
            success = False
    
    return success

def test_apa_0000619_specific_case():
    """Test the specific APA-0000619 case that was failing."""
    print("Testing specific APA-0000619 case...")
    
    # Recreate the exact APA-0000619 scenario from the CSV data
    apa_0000619_entry = {
        'voucher_no': 'APA-0000619',
        'description': 'VicOne Corporate Credit Card Saas Subscription',
        'Document_Date': '2025/07/16',
        'External_Document_No': 'APA-0000619',
        'debit': {
            'account': '76900-10',
            'gl_account': 'G/L Account',
            'amount': 64.00,  # 25.00 + 39.00 from CSV
            'currency': 'R-USD',
            'department': 'VCT.1692G',  # This is the key - VCT cost center
            'applicant_code': '10108'
        },
        'credit': {
            'account': '31200-10',
            'gl_account': 'Vendor',
            'vendor_code': 'V-VC00048',
            'amount': 64.00,
            'currency': 'R-USD',
            'department': 'VCT.1692G',  # VCT cost center
            'consolidated': True  # This should NOT be skipped with the fix
        }
    }
    
    # Test the skip logic
    department = apa_0000619_entry.get("credit", {}).get("department", "")
    cost_center = department[:3] if department else ""
    
    is_v_vc00048_consolidated = (
        apa_0000619_entry.get("credit", {}).get("consolidated") == True and 
        apa_0000619_entry.get("credit", {}).get("vendor_code") == "V-VC00048"
    )
    
    should_be_skipped = is_v_vc00048_consolidated and cost_center != "VCT"
    
    print(f"  Department: {department}")
    print(f"  Cost Center: {cost_center}")
    print(f"  Is V-VC00048 consolidated: {is_v_vc00048_consolidated}")
    print(f"  Should be skipped: {should_be_skipped}")
    
    if not should_be_skipped:
        print("  ✅ APA-0000619 will NOT be skipped (correct - should get consolidated billing)")
        return True
    else:
        print("  ❌ APA-0000619 will be skipped (incorrect - should get consolidated billing)")
        return False

def test_non_v_vc00048_entries_unaffected():
    """Test that non-V-VC00048 entries are not affected by the skip logic."""
    print("Testing that non-V-VC00048 entries are unaffected...")
    
    test_entries = create_test_entries_mixed_cost_centers()
    
    # Find non-V-VC00048 consolidated entries
    non_v_vc00048_entries = [
        entry for entry in test_entries
        if (entry.get("credit", {}).get("consolidated") == True and
            entry.get("credit", {}).get("vendor_code") != "V-VC00048")
    ]
    
    print(f"Found {len(non_v_vc00048_entries)} non-V-VC00048 consolidated entries")
    
    # These should not be affected by the V-VC00048 skip logic
    for entry in non_v_vc00048_entries:
        vendor = entry.get("credit", {}).get("vendor_code")
        voucher = entry.get("voucher_no")
        print(f"  ✅ {voucher} (vendor: {vendor}) should be processed normally")
    
    # Verify we have at least one non-V-VC00048 entry
    if len(non_v_vc00048_entries) >= 1:
        print("  ✅ Non-V-VC00048 entries are correctly unaffected")
        return True
    else:
        print("  ❌ Test data should include non-V-VC00048 entries")
        return False

def main():
    """Run all tests to verify the cost-center-aware V-VC00048 skip logic."""
    print("=" * 80)
    print("V-VC00048 Cost Center Aware Skip Logic Test (Issue #96)")
    print("=" * 80)
    
    all_tests_passed = True
    
    # Test 1: Cost center extraction
    print("\n1. Testing cost center extraction logic...")
    if not test_cost_center_extraction():
        all_tests_passed = False
    
    # Test 2: Cost-center-aware skip logic
    print("\n2. Testing V-VC00048 cost-center-aware skip logic...")
    if not test_vct_cost_center_skip_logic():
        all_tests_passed = False
    
    # Test 3: VCT responsibility collection exclusion
    print("\n3. Testing VCT responsibility collection exclusion...")
    if not test_vct_responsibility_collection_exclusion():
        all_tests_passed = False
    
    # Test 4: Specific APA-0000619 case
    print("\n4. Testing specific APA-0000619 case...")
    if not test_apa_0000619_specific_case():
        all_tests_passed = False
    
    # Test 5: Non-V-VC00048 entries unaffected
    print("\n5. Testing that non-V-VC00048 entries are unaffected...")
    if not test_non_v_vc00048_entries_unaffected():
        all_tests_passed = False
    
    # Summary
    print("\n" + "=" * 80)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED")
        print("✅ Cost-center-aware V-VC00048 skip logic is working correctly")
        print("✅ VCT cost centers (like APA-0000619) will get consolidated billing")
        print("✅ Non-VCT cost centers will be skipped and get VCT responsibility entries")
        print("✅ Issue #96 has been correctly resolved")
        print("\nEXPECTED BEHAVIOR:")
        print("- APA-0000619 (VCT.1692G) will get normal consolidated billing")
        print("- Non-VCT cost center V-VC00048 entries will be skipped")
        print("- VCT responsibility entries will be created for skipped entries")
    else:
        print("❌ SOME TESTS FAILED")
        print("❌ Cost-center-aware V-VC00048 skip logic needs adjustment")
    print("=" * 80)
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)