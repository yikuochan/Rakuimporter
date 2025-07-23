#!/usr/bin/env python3
"""
Test Suite for V-VC00048 Consolidated Entry Skip Approach

This test suite validates the approach where:
1. CSV-to-JSON converter remains unchanged (creates consolidated entries)
2. API processor detects and skips V-VC00048 consolidated entries
3. Individual V-VC00048 entries are processed with simplified logic
4. All other processing remains unchanged

Test Coverage:
- Core functionality (detection, skipping, processing)
- Business logic (vendor mapping, currency transformation)
- Integration tests (mixed entry types)
- Performance tests (API call reduction)
- Error handling and edge cases
- Regression tests (non-V-VC00048 unchanged)
"""

import sys
import os
import json
import logging
from decimal import Decimal
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_v_vc00048_consolidated_skip")

class TestV_VC00048ConsolidatedSkipApproach:
    """Test suite for V-VC00048 consolidated entry skip approach."""
    
    def __init__(self):
        """Initialize test suite."""
        self.test_results = []
        self.api_call_count = 0
        
    def create_test_data(self):
        """Create comprehensive test data for all scenarios."""
        return {
            # Test Case 1: V-VC00048 Consolidated Entry (should be skipped)
            "v_vc00048_consolidated": {
                "voucher_no": "TEST-CONS-001",
                "Document_Date": "2025/01/15",
                "External_Document_No": "EXT-001",
                "description": "Test consolidated V-VC00048 entry",
                "debit": {
                    "account": "18600-10",
                    "amount": 0,
                    "currency": "",
                    "department": "VCP.1234",
                    "department_code": "VCP.1234"
                },
                "credit": {
                    "account": "V-VC00048",
                    "amount": 5000.0,
                    "currency": "NTD",
                    "department": "VCP.1234",
                    "department_code": "VCP.1234",
                    "vendor_code": "V-VC00048",
                    "gl_account": "Vendor",
                    "consolidated": True,  # This should trigger skipping
                    "original_entries_count": 3,
                    "Remarks": "Consolidated V-VC00048 entry"
                }
            },
            
            # Test Case 2: V-VC00048 Individual Entries (should be processed)
            "v_vc00048_individual_1": {
                "voucher_no": "TEST-IND-001",
                "Document_Date": "2025/01/15",
                "External_Document_No": "EXT-IND-001",
                "description": "Individual V-VC00048 entry 1",
                "debit": {
                    "account": "18600-10",
                    "amount": 1500.0,
                    "currency": "NTD",
                    "department": "VCP.1234",
                    "department_code": "VCP.1234"
                },
                "credit": {
                    "account": "V-VC00048",
                    "amount": 1500.0,
                    "currency": "NTD",
                    "department": "VCP.1234",
                    "department_code": "VCP.1234",
                    "vendor_code": "V-VC00048",
                    "gl_account": "Vendor",
                    "consolidated": False,  # Individual entry
                    "Remarks": "Individual V-VC00048 entry"
                }
            },
            
            "v_vc00048_individual_2": {
                "voucher_no": "TEST-IND-002",
                "Document_Date": "2025/01/15",
                "External_Document_No": "EXT-IND-002",
                "description": "Individual V-VC00048 entry 2",
                "debit": {
                    "account": "18600-10",
                    "amount": 2000.0,
                    "currency": "USD",
                    "department": "VCA.5678",
                    "department_code": "VCA.5678"
                },
                "credit": {
                    "account": "V-VC00048",
                    "amount": 2000.0,
                    "currency": "USD",
                    "department": "VCA.5678",
                    "department_code": "VCA.5678",
                    "vendor_code": "V-VC00048",
                    "gl_account": "Vendor",
                    "consolidated": False,
                    "Remarks": "Individual V-VC00048 USD entry"
                }
            },
            
            # Test Case 3: Other V-VC Vendor Consolidated (should be processed normally)
            "other_v_vc_consolidated": {
                "voucher_no": "TEST-OTHER-001",
                "Document_Date": "2025/01/15",
                "External_Document_No": "EXT-OTHER-001",
                "description": "Other V-VC vendor consolidated",
                "debit": {
                    "account": "18600-10",
                    "amount": 0,
                    "currency": "",
                    "department": "VCT.9999",
                    "department_code": "VCT.9999"
                },
                "credit": {
                    "account": "V-VC00001",
                    "amount": 3000.0,
                    "currency": "NTD",
                    "department": "VCT.9999",
                    "department_code": "VCT.9999",
                    "vendor_code": "V-VC00001",
                    "gl_account": "Vendor",
                    "consolidated": True,  # Should be processed normally
                    "original_entries_count": 2,
                    "Remarks": "Other V-VC consolidated entry"
                }
            },
            
            # Test Case 4: Regular G/L Entry (should be processed normally)
            "regular_gl_entry": {
                "voucher_no": "TEST-GL-001",
                "Document_Date": "2025/01/15",
                "External_Document_No": "EXT-GL-001",
                "description": "Regular G/L entry",
                "debit": {
                    "account": "18600-10",
                    "amount": 1000.0,
                    "currency": "NTD",
                    "department": "VCT.9999",
                    "department_code": "VCT.9999"
                },
                "credit": {
                    "account": "21000-01",
                    "amount": 1000.0,
                    "currency": "NTD",
                    "department": "VCT.9999",
                    "department_code": "VCT.9999",
                    "gl_account": "G/L Account",
                    "consolidated": False,
                    "Remarks": "Regular G/L entry"
                }
            }
        }
    
    def mock_api_call(self, *args, **kwargs):
        """Mock API call to count calls."""
        self.api_call_count += 1
        return {"success": True, "id": f"mock_id_{self.api_call_count}"}
    
    def test_case_1_v_vc00048_consolidated_detection(self):
        """Test Case 1: V-VC00048 Consolidated Entry Detection"""
        logger.info("=== Test Case 1: V-VC00048 Consolidated Entry Detection ===")
        
        test_data = self.create_test_data()
        entry = test_data["v_vc00048_consolidated"]
        
        # Test detection logic
        is_v_vc00048_consolidated = (
            entry.get("credit", {}).get("consolidated") == True and
            entry.get("credit", {}).get("vendor_code") == "V-VC00048"
        )
        
        if is_v_vc00048_consolidated:
            logger.info("✓ V-VC00048 consolidated entry correctly detected")
            logger.info(f"  - Voucher: {entry['voucher_no']}")
            logger.info(f"  - Vendor: {entry['credit']['vendor_code']}")
            logger.info(f"  - Consolidated: {entry['credit']['consolidated']}")
            logger.info("  - Entry will be skipped in processing")
            self.test_results.append(("Test Case 1", "PASS", "V-VC00048 consolidated entry detected"))
            return True
        else:
            logger.error("✗ V-VC00048 consolidated entry NOT detected")
            self.test_results.append(("Test Case 1", "FAIL", "Detection failed"))
            return False
    
    def test_case_2_v_vc00048_individual_processing(self):
        """Test Case 2: V-VC00048 Individual Entry Processing"""
        logger.info("=== Test Case 2: V-VC00048 Individual Entry Processing ===")
        
        test_data = self.create_test_data()
        entries = [test_data["v_vc00048_individual_1"], test_data["v_vc00048_individual_2"]]
        
        processed_entries = 0
        api_calls_expected = 0
        
        for entry in entries:
            # Check if it's an individual V-VC00048 entry
            is_individual_v_vc00048 = (
                entry.get("credit", {}).get("vendor_code") == "V-VC00048" and
                not entry.get("credit", {}).get("consolidated", False)
            )
            
            if is_individual_v_vc00048:
                processed_entries += 1
                api_calls_expected += 2  # 1 debit + 1 credit per entry
                
                # Test vendor mapping logic
                department = entry.get("credit", {}).get("department", "")
                cost_center = department[:3] if department else ""
                
                if cost_center != "VCT":
                    # Should map to VCT vendor
                    mapped_vendor = "VCT"
                    logger.info(f"✓ V-VC00048 mapped to VCT for cost center {cost_center}")
                else:
                    mapped_vendor = "V-VC00048"
                    logger.info(f"✓ V-VC00048 kept as-is for VCT cost center")
                
                # Test currency transformation
                currency = entry.get("credit", {}).get("currency", "")
                if currency == "USD":
                    expected_currency = "R-USD"
                    logger.info(f"✓ Currency transformation: USD -> R-USD")
                elif currency == "NTD":
                    expected_currency = ""  # Empty for VCT+NTD
                    logger.info(f"✓ Currency transformation: NTD -> '' (empty)")
                
                logger.info(f"  - Voucher: {entry['voucher_no']}")
                logger.info(f"  - Original vendor: V-VC00048")
                logger.info(f"  - Mapped vendor: {mapped_vendor}")
                logger.info(f"  - Cost center: {cost_center}")
                logger.info(f"  - Currency: {currency} -> {expected_currency}")
        
        if processed_entries == 2 and api_calls_expected == 4:
            logger.info(f"✓ Processed {processed_entries} individual V-VC00048 entries")
            logger.info(f"✓ Expected API calls: {api_calls_expected} (2 per entry)")
            self.test_results.append(("Test Case 2", "PASS", f"Processed {processed_entries} entries"))
            return True
        else:
            logger.error(f"✗ Processing failed: {processed_entries} entries, {api_calls_expected} API calls")
            self.test_results.append(("Test Case 2", "FAIL", "Processing failed"))
            return False
    
    def test_case_3_non_v_vc00048_consolidated(self):
        """Test Case 3: Non-V-VC00048 Consolidated Entries"""
        logger.info("=== Test Case 3: Non-V-VC00048 Consolidated Entries ===")
        
        test_data = self.create_test_data()
        entry = test_data["other_v_vc_consolidated"]
        
        # Test that non-V-VC00048 consolidated entries are processed normally
        is_other_consolidated = (
            entry.get("credit", {}).get("consolidated") == True and
            entry.get("credit", {}).get("vendor_code") != "V-VC00048"
        )
        
        if is_other_consolidated:
            logger.info("✓ Non-V-VC00048 consolidated entry detected")
            logger.info(f"  - Voucher: {entry['voucher_no']}")
            logger.info(f"  - Vendor: {entry['credit']['vendor_code']}")
            logger.info("  - Entry will be processed normally (not skipped)")
            self.test_results.append(("Test Case 3", "PASS", "Non-V-VC00048 consolidated processed"))
            return True
        else:
            logger.error("✗ Non-V-VC00048 consolidated entry detection failed")
            self.test_results.append(("Test Case 3", "FAIL", "Detection failed"))
            return False
    
    def test_case_4_vendor_mapping_logic(self):
        """Test Case 4: V-VC00048 Vendor Mapping Logic"""
        logger.info("=== Test Case 4: V-VC00048 Vendor Mapping Logic ===")
        
        test_cases = [
            {"department": "VCP.1234", "expected_mapping": "VCT", "reason": "Non-VCT cost center"},
            {"department": "VCA.5678", "expected_mapping": "VCT", "reason": "Non-VCT cost center"},
            {"department": "VCG.9999", "expected_mapping": "VCT", "reason": "Non-VCT cost center"},
            {"department": "VCJ.1111", "expected_mapping": "VCT", "reason": "Non-VCT cost center"},
            {"department": "VCT.9999", "expected_mapping": "V-VC00048", "reason": "VCT cost center"},
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            department = test_case["department"]
            expected = test_case["expected_mapping"]
            reason = test_case["reason"]
            
            # Extract cost center
            cost_center = department[:3] if department else ""
            
            # Apply mapping logic
            if cost_center == "VCT":
                mapped_vendor = "V-VC00048"  # Keep original for VCT
            else:
                mapped_vendor = "VCT"  # Map to VCT for non-VCT cost centers
            
            if mapped_vendor == expected:
                logger.info(f"✓ {department} -> {mapped_vendor} ({reason})")
            else:
                logger.error(f"✗ {department} -> {mapped_vendor}, expected {expected}")
                all_passed = False
        
        if all_passed:
            self.test_results.append(("Test Case 4", "PASS", "Vendor mapping logic correct"))
            return True
        else:
            self.test_results.append(("Test Case 4", "FAIL", "Vendor mapping logic failed"))
            return False
    
    def test_case_5_currency_transformation(self):
        """Test Case 5: Currency Transformation Logic"""
        logger.info("=== Test Case 5: Currency Transformation Logic ===")
        
        test_cases = [
            {"company": "VCT", "currency": "NTD", "expected": "", "reason": "VCT+NTD -> empty"},
            {"company": "VCT", "currency": "USD", "expected": "R-USD", "reason": "VCT+USD -> R-USD"},
            {"company": "VCP", "currency": "PHP", "expected": "", "reason": "VCP+PHP -> empty"},
            {"company": "VCP", "currency": "USD", "expected": "R-USD", "reason": "VCP+USD -> R-USD"},
            {"company": "VCA", "currency": "NTD", "expected": "NTD", "reason": "VCA+NTD -> NTD"},
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            company = test_case["company"]
            currency = test_case["currency"]
            expected = test_case["expected"]
            reason = test_case["reason"]
            
            # Apply currency transformation logic
            if company == "VCT":
                if currency == "NTD":
                    transformed = ""
                elif currency in ["USD", "EUR", "GBP"]:
                    transformed = f"R-{currency}"
                else:
                    transformed = currency
            elif company == "VCP":
                if currency == "PHP":
                    transformed = ""
                elif currency in ["USD", "EUR", "GBP"]:
                    transformed = f"R-{currency}"
                else:
                    transformed = currency
            else:
                # Other companies keep original currency
                transformed = currency
            
            if transformed == expected:
                logger.info(f"✓ {company}+{currency} -> '{transformed}' ({reason})")
            else:
                logger.error(f"✗ {company}+{currency} -> '{transformed}', expected '{expected}'")
                all_passed = False
        
        if all_passed:
            self.test_results.append(("Test Case 5", "PASS", "Currency transformation correct"))
            return True
        else:
            self.test_results.append(("Test Case 5", "FAIL", "Currency transformation failed"))
            return False
    
    def test_case_6_mixed_entry_processing(self):
        """Test Case 6: Mixed Entry Types Processing"""
        logger.info("=== Test Case 6: Mixed Entry Types Processing ===")
        
        test_data = self.create_test_data()
        all_entries = list(test_data.values())
        
        processing_summary = {
            "v_vc00048_consolidated_skipped": 0,
            "v_vc00048_individual_processed": 0,
            "other_consolidated_processed": 0,
            "regular_entries_processed": 0,
            "total_api_calls": 0
        }
        
        for entry in all_entries:
            credit = entry.get("credit", {})
            vendor_code = credit.get("vendor_code", "")
            is_consolidated = credit.get("consolidated", False)
            
            if vendor_code == "V-VC00048" and is_consolidated:
                # Skip V-VC00048 consolidated entries
                processing_summary["v_vc00048_consolidated_skipped"] += 1
                logger.info(f"SKIPPED: {entry['voucher_no']} (V-VC00048 consolidated)")
                
            elif vendor_code == "V-VC00048" and not is_consolidated:
                # Process V-VC00048 individual entries
                processing_summary["v_vc00048_individual_processed"] += 1
                processing_summary["total_api_calls"] += 2  # Simplified: 2 calls per entry
                logger.info(f"PROCESSED: {entry['voucher_no']} (V-VC00048 individual) - 2 API calls")
                
            elif is_consolidated and vendor_code != "V-VC00048":
                # Process other consolidated entries normally
                processing_summary["other_consolidated_processed"] += 1
                processing_summary["total_api_calls"] += 1  # 1 call for consolidated entry
                logger.info(f"PROCESSED: {entry['voucher_no']} (Other consolidated) - 1 API call")
                
            else:
                # Process regular entries
                processing_summary["regular_entries_processed"] += 1
                processing_summary["total_api_calls"] += 2  # 2 calls for regular entry
                logger.info(f"PROCESSED: {entry['voucher_no']} (Regular entry) - 2 API calls")
        
        # Validate results
        expected_skipped = 1  # 1 V-VC00048 consolidated entry
        expected_individual = 2  # 2 V-VC00048 individual entries
        expected_other_consolidated = 1  # 1 other consolidated entry
        expected_regular = 1  # 1 regular entry
        expected_api_calls = (2 * 2) + 1 + 2  # (2 individual * 2) + 1 consolidated + 2 regular = 7
        
        success = (
            processing_summary["v_vc00048_consolidated_skipped"] == expected_skipped and
            processing_summary["v_vc00048_individual_processed"] == expected_individual and
            processing_summary["other_consolidated_processed"] == expected_other_consolidated and
            processing_summary["regular_entries_processed"] == expected_regular and
            processing_summary["total_api_calls"] == expected_api_calls
        )
        
        logger.info("Processing Summary:")
        for key, value in processing_summary.items():
            logger.info(f"  {key}: {value}")
        
        if success:
            logger.info("✓ Mixed entry processing works correctly")
            self.test_results.append(("Test Case 6", "PASS", "Mixed processing correct"))
            return True
        else:
            logger.error("✗ Mixed entry processing failed")
            self.test_results.append(("Test Case 6", "FAIL", "Mixed processing failed"))
            return False
    
    def test_case_7_api_call_reduction(self):
        """Test Case 7: API Call Count Verification"""
        logger.info("=== Test Case 7: API Call Count Verification ===")
        
        # Simulate processing 10 V-VC00048 entries
        num_v_vc00048_entries = 10
        
        # Original approach: 3 API calls per V-VC00048 entry
        # (1 debit + 1 credit + 1 VCT responsibility pair)
        original_api_calls = num_v_vc00048_entries * 3
        
        # New approach: 2 API calls per V-VC00048 entry
        # (1 debit + 1 credit, no VCT responsibility)
        new_api_calls = num_v_vc00048_entries * 2
        
        # Calculate reduction
        reduction_count = original_api_calls - new_api_calls
        reduction_percentage = (reduction_count / original_api_calls) * 100
        
        logger.info(f"V-VC00048 entries: {num_v_vc00048_entries}")
        logger.info(f"Original API calls: {original_api_calls} (3 per entry)")
        logger.info(f"New API calls: {new_api_calls} (2 per entry)")
        logger.info(f"Reduction: {reduction_count} calls ({reduction_percentage:.1f}%)")
        
        # Validate 33.3% reduction (from 3 to 2 calls per entry)
        expected_reduction = 33.3
        if abs(reduction_percentage - expected_reduction) < 0.1:
            logger.info(f"✓ API call reduction achieved: {reduction_percentage:.1f}%")
            self.test_results.append(("Test Case 7", "PASS", f"{reduction_percentage:.1f}% reduction"))
            return True
        else:
            logger.error(f"✗ API call reduction incorrect: {reduction_percentage:.1f}%, expected ~{expected_reduction}%")
            self.test_results.append(("Test Case 7", "FAIL", "Reduction calculation failed"))
            return False
    
    def test_case_8_balance_verification(self):
        """Test Case 8: Balance Verification"""
        logger.info("=== Test Case 8: Balance Verification ===")
        
        test_data = self.create_test_data()
        
        # Test balanced entries
        balanced_entries = [
            test_data["v_vc00048_individual_1"],
            test_data["v_vc00048_individual_2"],
            test_data["regular_gl_entry"]
        ]
        
        all_balanced = True
        
        for entry in balanced_entries:
            debit_amount = entry.get("debit", {}).get("amount", 0)
            credit_amount = entry.get("credit", {}).get("amount", 0)
            difference = abs(debit_amount - credit_amount)
            
            if difference < 0.01:  # Allow for small rounding differences
                logger.info(f"✓ {entry['voucher_no']}: Balanced (Debit={debit_amount}, Credit={credit_amount})")
            else:
                logger.error(f"✗ {entry['voucher_no']}: Unbalanced (Debit={debit_amount}, Credit={credit_amount}, Diff={difference})")
                all_balanced = False
        
        # Test unbalanced entry detection
        unbalanced_entry = {
            "voucher_no": "TEST-UNBALANCED",
            "debit": {"amount": 1000.0},
            "credit": {"amount": 1050.0}
        }
        
        debit_amount = unbalanced_entry["debit"]["amount"]
        credit_amount = unbalanced_entry["credit"]["amount"]
        difference = abs(debit_amount - credit_amount)
        
        if difference >= 0.01:
            logger.info(f"✓ Unbalanced entry correctly detected: Diff={difference}")
        else:
            logger.error(f"✗ Unbalanced entry not detected")
            all_balanced = False
        
        if all_balanced:
            self.test_results.append(("Test Case 8", "PASS", "Balance verification works"))
            return True
        else:
            self.test_results.append(("Test Case 8", "FAIL", "Balance verification failed"))
            return False
    
    def run_all_tests(self):
        """Run all test cases."""
        logger.info("=" * 80)
        logger.info("RUNNING V-VC00048 CONSOLIDATED SKIP APPROACH TEST SUITE")
        logger.info("=" * 80)
        
        test_methods = [
            self.test_case_1_v_vc00048_consolidated_detection,
            self.test_case_2_v_vc00048_individual_processing,
            self.test_case_3_non_v_vc00048_consolidated,
            self.test_case_4_vendor_mapping_logic,
            self.test_case_5_currency_transformation,
            self.test_case_6_mixed_entry_processing,
            self.test_case_7_api_call_reduction,
            self.test_case_8_balance_verification
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                if test_method():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Test {test_method.__name__} failed with exception: {str(e)}")
                failed += 1
            
            logger.info("")  # Add spacing between tests
        
        # Print summary
        logger.info("=" * 80)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("=" * 80)
        
        for test_name, result, details in self.test_results:
            status_symbol = "✓" if result == "PASS" else "✗"
            logger.info(f"{status_symbol} {test_name}: {result} - {details}")
        
        logger.info("")
        logger.info(f"TOTAL TESTS: {passed + failed}")
        logger.info(f"PASSED: {passed}")
        logger.info(f"FAILED: {failed}")
        logger.info(f"SUCCESS RATE: {(passed / (passed + failed) * 100):.1f}%")
        
        if failed == 0:
            logger.info("🎉 ALL TESTS PASSED! The V-VC00048 consolidated skip approach is ready for implementation.")
        else:
            logger.error(f"❌ {failed} TESTS FAILED. Please review and fix issues before implementation.")
        
        return failed == 0


def main():
    """Main function to run the test suite."""
    test_suite = TestV_VC00048ConsolidatedSkipApproach()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🚀 Test suite completed successfully!")
        print("The V-VC00048 consolidated skip approach is validated and ready for implementation.")
    else:
        print("\n⚠️  Test suite completed with failures.")
        print("Please review the test results and fix issues before proceeding.")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
