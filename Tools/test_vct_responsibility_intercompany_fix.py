#!/usr/bin/env python3
"""
Test script to verify VCT responsibility intercompany code fix.

This test verifies that:
1. VCT responsibility entries have correct intercompany codes
2. Debit lines have original cost center as intercompany code
3. Credit lines have empty intercompany code (not "VCT")
"""

import sys
import os
import json
import logging

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vct_responsibility_consolidation import (
    collect_vct_responsibility_candidates,
    create_consolidated_vct_responsibility_entries
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_vct_responsibility_intercompany_codes():
    """Test that VCT responsibility entries have correct intercompany codes."""
    
    # Test data: V-VC00048 entries with non-VCT cost centers
    test_entries = [
        {
            "voucher_no": "APA-0000401",
            "External_Document_No": "20250505",
            "Document_Date": "2025/05/05",
            "description": "Test expense",
            "debit": {
                "amount": 750.0,
                "currency": "USD",
                "department": "VCA.1342G",
                "account": "18600-10",
                "gl_account": "G/L Account"
            },
            "credit": {
                "amount": 750.0,
                "currency": "USD",
                "department": "VCA.1342G",
                "vendor_code": "V-VC00048",
                "gl_account": "Vendor"
            }
        },
        {
            "voucher_no": "APA-0000402",
            "External_Document_No": "20250506",
            "Document_Date": "2025/05/06",
            "description": "Another test expense",
            "debit": {
                "amount": 1000.0,
                "currency": "USD",
                "department": "VCP.2000",
                "account": "18600-10",
                "gl_account": "G/L Account"
            },
            "credit": {
                "amount": 1000.0,
                "currency": "USD",
                "department": "VCP.2000",
                "vendor_code": "V-VC00048",
                "gl_account": "Vendor"
            }
        }
    ]
    
    logger.info("Testing VCT responsibility intercompany code logic...")
    
    # Test 1: Collect VCT responsibility candidates
    logger.info("Test 1: Collecting VCT responsibility candidates")
    vct_candidates = collect_vct_responsibility_candidates(test_entries)
    
    expected_vouchers = {"APA-0000401", "APA-0000402"}
    actual_vouchers = set(vct_candidates.keys())
    
    if actual_vouchers == expected_vouchers:
        logger.info("✅ VCT responsibility candidate collection: PASSED")
        logger.info(f"   Found candidates for vouchers: {actual_vouchers}")
    else:
        logger.error("❌ VCT responsibility candidate collection: FAILED")
        logger.error(f"   Expected: {expected_vouchers}")
        logger.error(f"   Actual: {actual_vouchers}")
        return False
    
    # Test 2: Verify intercompany code logic for individual entries
    logger.info("Test 2: Verifying intercompany code logic")
    
    # Mock the post_journal_line function to capture the payloads
    captured_payloads = []
    
    def mock_post_journal_line(journal_line, access_token, rate_limiter, max_retries):
        captured_payloads.append(journal_line.copy())
        return True, {"success": True}
    
    # Temporarily replace the post_journal_line function
    import core.vct_responsibility_consolidation
    original_post_function = None
    
    # Create a mock rate limiter
    class MockRateLimiter:
        def wait_before_request(self):
            pass
        def record_success(self):
            pass
        def record_failure(self):
            pass
    
    # Test the consolidated VCT responsibility entry creation
    for voucher_no, voucher_entries in vct_candidates.items():
        logger.info(f"Testing VCT responsibility entries for voucher {voucher_no}")
        
        # Clear captured payloads
        captured_payloads.clear()
        
        # Mock the post_journal_line function
        core.vct_responsibility_consolidation.post_journal_line = mock_post_journal_line
        
        try:
            # Create VCT responsibility entries
            success_count, failure_count = create_consolidated_vct_responsibility_entries(
                voucher_entries, 
                "mock_token", 
                MockRateLimiter(), 
                {}, 
                {}, 
                3
            )
            
            logger.info(f"   Created {len(captured_payloads)} journal lines")
            
            # Verify the payloads
            debit_lines = [p for p in captured_payloads if p.get("Amount", 0) > 0]
            credit_lines = [p for p in captured_payloads if p.get("Amount", 0) < 0]
            
            logger.info(f"   Debit lines: {len(debit_lines)}, Credit lines: {len(credit_lines)}")
            
            # Check debit lines
            for i, debit_line in enumerate(debit_lines):
                account_no = debit_line.get("Account_No")
                shortcut_dim_code3 = debit_line.get("ShortcutDimCode3")
                amount = debit_line.get("Amount")
                
                logger.info(f"   Debit line {i+1}: Account={account_no}, Amount={amount}, ShortcutDimCode3='{shortcut_dim_code3}'")
                
                # Verify debit line has correct intercompany code (original cost center)
                if account_no == "18600-10" and shortcut_dim_code3 in ["VCA", "VCP"]:
                    logger.info(f"   ✅ Debit line {i+1} intercompany code: CORRECT")
                else:
                    logger.error(f"   ❌ Debit line {i+1} intercompany code: INCORRECT")
                    logger.error(f"      Expected: VCA or VCP, Actual: '{shortcut_dim_code3}'")
                    return False
            
            # Check credit lines
            for i, credit_line in enumerate(credit_lines):
                account_no = credit_line.get("Account_No")
                shortcut_dim_code3 = credit_line.get("ShortcutDimCode3")
                amount = credit_line.get("Amount")
                
                logger.info(f"   Credit line {i+1}: Account={account_no}, Amount={amount}, ShortcutDimCode3='{shortcut_dim_code3}'")
                
                # Verify credit line has empty intercompany code
                if account_no == "V-VC00048" and shortcut_dim_code3 == "":
                    logger.info(f"   ✅ Credit line {i+1} intercompany code: CORRECT (empty)")
                else:
                    logger.error(f"   ❌ Credit line {i+1} intercompany code: INCORRECT")
                    logger.error(f"      Expected: empty string, Actual: '{shortcut_dim_code3}'")
                    return False
            
        except Exception as e:
            logger.error(f"   ❌ Error creating VCT responsibility entries: {str(e)}")
            return False
        finally:
            # Restore the original function (if we had one)
            if original_post_function:
                core.vct_responsibility_consolidation.post_journal_line = original_post_function
    
    logger.info("✅ All VCT responsibility intercompany code tests: PASSED")
    return True

def test_vct_responsibility_entry_structure():
    """Test the structure of VCT responsibility entries."""
    
    logger.info("Testing VCT responsibility entry structure...")
    
    # Test data
    test_entry = {
        "voucher_no": "APA-0000401",
        "External_Document_No": "20250505",
        "Document_Date": "2025/05/05",
        "description": "Test expense",
        "credit": {
            "amount": 750.0,
            "currency": "USD",
            "department": "VCA.1342G",
            "vendor_code": "V-VC00048",
            "gl_account": "Vendor"
        }
    }
    
    # Test the extract_description_from_entry function
    from core.vct_responsibility_consolidation import extract_description_from_entry
    
    description = extract_description_from_entry(test_entry)
    expected_description = "Test expense"
    
    if description == expected_description:
        logger.info("✅ Description extraction: PASSED")
    else:
        logger.error("❌ Description extraction: FAILED")
        logger.error(f"   Expected: '{expected_description}', Actual: '{description}'")
        return False
    
    logger.info("✅ VCT responsibility entry structure test: PASSED")
    return True

def main():
    """Run all tests."""
    logger.info("Starting VCT responsibility intercompany code fix tests...")
    
    tests = [
        test_vct_responsibility_intercompany_codes,
        test_vct_responsibility_entry_structure
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ Test {test.__name__} failed with exception: {str(e)}")
            failed += 1
    
    logger.info(f"\nTest Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All tests passed! VCT responsibility intercompany code fix is working correctly.")
        return True
    else:
        logger.error("💥 Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
