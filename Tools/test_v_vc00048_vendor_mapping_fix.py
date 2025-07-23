#!/usr/bin/env python3
"""
Test script to verify V-VC00048 vendor mapping fix.

This script tests that:
1. V-VC00048 entries with non-VCT cost centers get mapped to VCT vendor (simple mapping)
2. V-VC00048 entries are excluded from VCT responsibility consolidation (no duplicate billing)
3. The simple vendor mapping works as intended per GitHub issue #78

Usage:
    python Tools/test_v_vc00048_vendor_mapping_fix.py
"""

import sys
import os
import json
import logging
from typing import Dict, List, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we want to test
from core.vct_responsibility_consolidation import collect_vct_responsibility_candidates
from core.process_japan_exports import create_journal_line

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_v_vc00048_entry(cost_center: str, voucher_no: str = "TEST001") -> Dict[str, Any]:
    """
    Create a test entry with V-VC00048 vendor for testing.
    
    Args:
        cost_center: The cost center code (e.g., "VCA", "VCP", "VCT")
        voucher_no: The voucher number
        
    Returns:
        Dict[str, Any]: Test journal entry
    """
    return {
        "voucher_no": voucher_no,
        "External_Document_No": voucher_no,
        "Document_Date": "2025/01/15",
        "description": "Test V-VC00048 entry",
        "debit": {
            "account": "72600-10",
            "gl_account": "G/L Account",
            "amount": 1000.0,
            "currency": "USD",
            "department": f"{cost_center}.1234",
            "department_code": f"{cost_center}.1234",
            "applicant_code": "TEST_USER"
        },
        "credit": {
            "vendor_code": "V-VC00048",
            "gl_account": "Vendor",
            "amount": 1000.0,
            "currency": "USD",
            "department": f"{cost_center}.1234",
            "department_code": f"{cost_center}.1234",
            "Remarks": "Test credit card expense"
        }
    }

def test_vct_responsibility_exclusion():
    """
    Test that V-VC00048 entries are excluded from VCT responsibility consolidation.
    """
    logger.info("=== Testing VCT Responsibility Exclusion ===")
    
    # Create test entries with V-VC00048 vendor for different cost centers
    test_entries = [
        create_test_v_vc00048_entry("VCA", "TEST001"),  # Non-VCT cost center
        create_test_v_vc00048_entry("VCP", "TEST002"),  # Non-VCT cost center
        create_test_v_vc00048_entry("VCT", "TEST003"),  # VCT cost center
    ]
    
    # Test the VCT responsibility candidate collection
    vct_candidates = collect_vct_responsibility_candidates(test_entries)
    
    # Verify that NO V-VC00048 entries are collected for VCT responsibility
    if len(vct_candidates) == 0:
        logger.info("✅ PASS: No V-VC00048 entries collected for VCT responsibility consolidation")
        return True
    else:
        logger.error(f"❌ FAIL: {len(vct_candidates)} V-VC00048 entries were collected for VCT responsibility")
        for voucher_no, entries in vct_candidates.items():
            logger.error(f"  - Voucher {voucher_no}: {len(entries)} entries")
        return False

def test_vendor_mapping():
    """
    Test that V-VC00048 vendor mapping works correctly in journal line creation.
    """
    logger.info("=== Testing V-VC00048 Vendor Mapping ===")
    
    test_cases = [
        {
            "name": "Non-VCT cost center (VCA) - should map to VCT",
            "entry": create_test_v_vc00048_entry("VCA", "TEST001"),
            "expected_vendor": "VCT"
        },
        {
            "name": "Non-VCT cost center (VCP) - should map to VCT", 
            "entry": create_test_v_vc00048_entry("VCP", "TEST002"),
            "expected_vendor": "VCT"
        },
        {
            "name": "VCT cost center - should remain V-VC00048",
            "entry": create_test_v_vc00048_entry("VCT", "TEST003"),
            "expected_vendor": "V-VC00048"
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        logger.info(f"Testing: {test_case['name']}")
        
        # Create credit journal line (where vendor mapping occurs)
        credit_line = create_journal_line(test_case["entry"], "credit")
        
        actual_vendor = credit_line.get("Account_No", "")
        expected_vendor = test_case["expected_vendor"]
        
        if actual_vendor == expected_vendor:
            logger.info(f"  ✅ PASS: Vendor mapped correctly to {actual_vendor}")
        else:
            logger.error(f"  ❌ FAIL: Expected {expected_vendor}, got {actual_vendor}")
            all_passed = False
    
    return all_passed

def test_intercompany_code_logic():
    """
    Test that intercompany codes are set correctly for V-VC00048 entries.
    """
    logger.info("=== Testing Intercompany Code Logic ===")
    
    test_cases = [
        {
            "name": "Non-VCT cost center (VCA) credit line - should have VCT intercompany code",
            "entry": create_test_v_vc00048_entry("VCA", "TEST001"),
            "line_type": "credit",
            "expected_intercompany": "VCT"
        },
        {
            "name": "VCT cost center credit line - should have empty intercompany code",
            "entry": create_test_v_vc00048_entry("VCT", "TEST002"),
            "line_type": "credit", 
            "expected_intercompany": ""
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        logger.info(f"Testing: {test_case['name']}")
        
        # Create journal line
        journal_line = create_journal_line(test_case["entry"], test_case["line_type"])
        
        actual_intercompany = journal_line.get("ShortcutDimCode3", "")
        expected_intercompany = test_case["expected_intercompany"]
        
        if actual_intercompany == expected_intercompany:
            logger.info(f"  ✅ PASS: Intercompany code set correctly to '{actual_intercompany}'")
        else:
            logger.error(f"  ❌ FAIL: Expected '{expected_intercompany}', got '{actual_intercompany}'")
            all_passed = False
    
    return all_passed

def main():
    """
    Run all tests for V-VC00048 vendor mapping fix.
    """
    logger.info("Starting V-VC00048 vendor mapping fix tests...")
    
    tests = [
        ("VCT Responsibility Exclusion", test_vct_responsibility_exclusion),
        ("Vendor Mapping", test_vendor_mapping),
        ("Intercompany Code Logic", test_intercompany_code_logic)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {str(e)}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! V-VC00048 vendor mapping fix is working correctly.")
        return True
    else:
        logger.error("💥 Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
