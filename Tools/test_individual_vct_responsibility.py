#!/usr/bin/env python3
"""
Test script to verify individual VCT responsibility processing.
This tests the behavior we want AFTER removing consolidation - 
each V-VC00048 entry should be processed individually.
"""

import sys
import os
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_individual_vct_processing():
    """Test that V-VC00048 entries are processed individually without consolidation."""
    print("Testing individual VCT responsibility processing...")
    
    # Sample entries with V-VC00048 vendor code - these should be processed individually
    test_entries = [
        {
            "voucher_no": "APA-0000552",
            "description": "Test expense entry 1",
            "debit": {
                "amount": 1000.0,
                "department": "VCA.1234",
                "account": "62100-10",
                "currency": "NTD"
            },
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCA.1234",
                "amount": 1000.0,
                "gl_account": "Vendor",
                "currency": "NTD"
            }
        },
        {
            "voucher_no": "APA-0000552",
            "description": "Test expense entry 2",
            "debit": {
                "amount": 2000.0,
                "department": "VCA.5678",
                "account": "62200-10",
                "currency": "NTD"
            },
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCA.5678",
                "amount": 2000.0,
                "gl_account": "Vendor",
                "currency": "NTD"
            }
        },
        {
            "voucher_no": "APA-0000552",
            "description": "Test expense entry 3",
            "debit": {
                "amount": 500.0,
                "department": "VCP.9999",
                "account": "61100-10",
                "currency": "NTD"
            },
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCP.9999",
                "amount": 500.0,
                "gl_account": "Vendor",
                "currency": "NTD"
            }
        },
        {
            "voucher_no": "APA-0000552",
            "description": "Test expense entry 4",
            "debit": {
                "amount": 750.0,
                "department": "VCT.1111",
                "account": "63100-10",
                "currency": "NTD"
            },
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCT.1111",
                "amount": 750.0,
                "gl_account": "Vendor",
                "currency": "NTD"
            }
        }
    ]
    
    # Mock the post_journal_line function to track API calls
    api_calls = []
    def mock_post_journal_line(journal_line, access_token, rate_limiter=None, max_retries=3):
        api_calls.append({
            'document_no': journal_line.get('External_Document_No', ''),
            'account_type': journal_line.get('Account_Type', ''),
            'account_no': journal_line.get('Account_No', ''),
            'amount': journal_line.get('Amount', 0),
            'description': journal_line.get('Description', '')
        })
        return True, {"status": "success"}
    
    # Test individual processing (target behavior)
    with patch('core.process_japan_exports.post_journal_line', side_effect=mock_post_journal_line):
        with patch('core.process_japan_exports.get_access_token', return_value="fake_token"):
            try:
                from core.process_japan_exports import process_entries
                result = process_entries(test_entries, "fake_token")
                if len(result) == 4:
                    success_count, failure_count, balanced_count, unbalanced_count = result
                else:
                    success_count, failure_count = result
                
                print(f"API calls made: {len(api_calls)}")
                print(f"Success count: {success_count}")
                print(f"Failure count: {failure_count}")
                
                # Expected behavior for individual processing:
                # 4 entries × 2 lines each (debit + credit) = 8 API calls
                expected_api_calls = 8
                expected_success = 8
                
                # Analyze API calls
                document_numbers = set()
                debit_calls = []
                credit_calls = []
                
                for call in api_calls:
                    document_numbers.add(call['document_no'])
                    if call['amount'] > 0:
                        debit_calls.append(call)
                    else:
                        credit_calls.append(call)
                
                print(f"\nDocument numbers used: {sorted(document_numbers)}")
                print(f"Debit calls: {len(debit_calls)}")
                print(f"Credit calls: {len(credit_calls)}")
                
                # Verify individual processing behavior
                tests_passed = 0
                total_tests = 5
                
                # Test 1: Correct number of API calls
                if len(api_calls) == expected_api_calls:
                    print("✅ API call count test PASSED")
                    tests_passed += 1
                else:
                    print(f"❌ API call count test FAILED - Expected: {expected_api_calls}, Got: {len(api_calls)}")
                
                # Test 2: Correct success count
                if success_count == expected_success:
                    print("✅ Success count test PASSED")
                    tests_passed += 1
                else:
                    print(f"❌ Success count test FAILED - Expected: {expected_success}, Got: {success_count}")
                
                # Test 3: Individual document numbers (4 different document numbers)
                expected_doc_count = 4
                if len(document_numbers) == expected_doc_count:
                    print("✅ Individual document numbers test PASSED")
                    tests_passed += 1
                else:
                    print(f"❌ Individual document numbers test FAILED - Expected: {expected_doc_count}, Got: {len(document_numbers)}")
                
                # Test 4: Equal debit and credit calls
                if len(debit_calls) == len(credit_calls) == 4:
                    print("✅ Debit/Credit balance test PASSED")
                    tests_passed += 1
                else:
                    print(f"❌ Debit/Credit balance test FAILED - Debits: {len(debit_calls)}, Credits: {len(credit_calls)}")
                
                # Test 5: No consolidation (each entry has unique document number)
                expected_pattern = ["APA-0000552-1", "APA-0000552-2", "APA-0000552-3", "APA-0000552-4"]
                actual_docs = sorted(document_numbers)
                if actual_docs == expected_pattern:
                    print("✅ No consolidation test PASSED")
                    tests_passed += 1
                else:
                    print(f"❌ No consolidation test FAILED - Expected: {expected_pattern}, Got: {actual_docs}")
                
                return tests_passed == total_tests
                
            except ImportError as e:
                print(f"❌ Import test FAILED: {e}")
                return False
            except Exception as e:
                print(f"❌ Processing test FAILED: {e}")
                return False

def test_mixed_vendor_processing():
    """Test that non-V-VC00048 entries are processed normally while V-VC00048 entries are individual."""
    print("\nTesting mixed vendor processing...")
    
    test_entries = [
        # Regular vendor entry (should be processed normally)
        {
            "voucher_no": "APA-0000553",
            "description": "Regular vendor entry",
            "debit": {
                "amount": 1000.0,
                "department": "VCA.1234",
                "account": "62100-10",
                "currency": "NTD"
            },
            "credit": {
                "vendor_code": "V-REGULAR",
                "department": "VCA.1234",
                "amount": 1000.0,
                "gl_account": "Vendor",
                "currency": "NTD"
            }
        },
        # V-VC00048 entry (should be processed individually)
        {
            "voucher_no": "APA-0000554",
            "description": "VCT responsibility entry",
            "debit": {
                "amount": 500.0,
                "department": "VCA.5678",
                "account": "62200-10",
                "currency": "NTD"
            },
            "credit": {
                "vendor_code": "V-VC00048",
                "department": "VCA.5678",
                "amount": 500.0,
                "gl_account": "Vendor",
                "currency": "NTD"
            }
        }
    ]
    
    api_calls = []
    def mock_post_journal_line(journal_line, access_token, rate_limiter=None, max_retries=3):
        api_calls.append({
            'document_no': journal_line.get('External_Document_No', ''),
            'account_type': journal_line.get('Account_Type', ''),
            'account_no': journal_line.get('Account_No', ''),
            'amount': journal_line.get('Amount', 0)
        })
        return True, {"status": "success"}
    
    with patch('core.process_japan_exports.post_journal_line', side_effect=mock_post_journal_line):
        with patch('core.process_japan_exports.get_access_token', return_value="fake_token"):
            try:
                from core.process_japan_exports import process_entries
                result = process_entries(test_entries, "fake_token")
                if len(result) == 4:
                    success_count, failure_count, balanced_count, unbalanced_count = result
                else:
                    success_count, failure_count = result
                
                # Expected: 2 entries × 2 lines each = 4 API calls
                # Both should be processed individually (no special consolidation)
                expected_calls = 4
                
                if len(api_calls) == expected_calls and success_count == expected_calls:
                    print("✅ Mixed vendor processing test PASSED")
                    return True
                else:
                    print(f"❌ Mixed vendor processing test FAILED - Expected: {expected_calls}, Got: {len(api_calls)}")
                    return False
                    
            except Exception as e:
                print(f"❌ Mixed vendor processing test FAILED: {e}")
                return False

def test_vct_responsibility_entries_creation():
    """Test that VCT responsibility entries are created correctly for V-VC00048."""
    print("\nTesting VCT responsibility entries creation...")
    
    test_entry = {
        "voucher_no": "APA-0000555",
        "description": "VCT responsibility test",
        "debit": {
            "amount": 1000.0,
            "department": "VCA.1234",
            "account": "62100-10",
            "currency": "NTD"
        },
        "credit": {
            "vendor_code": "V-VC00048",
            "department": "VCA.1234",
            "amount": 1000.0,
            "gl_account": "Vendor",
            "currency": "NTD"
        }
    }
    
    journal_lines = []
    def mock_post_journal_line(journal_line, access_token, rate_limiter=None, max_retries=3):
        journal_lines.append(journal_line.copy())
        return True, {"status": "success"}
    
    with patch('core.process_japan_exports.post_journal_line', side_effect=mock_post_journal_line):
        with patch('core.process_japan_exports.get_access_token', return_value="fake_token"):
            try:
                from core.process_japan_exports import process_entries
                process_entries([test_entry], "fake_token")
                
                if len(journal_lines) == 2:
                    debit_line = next((line for line in journal_lines if line['Amount'] > 0), None)
                    credit_line = next((line for line in journal_lines if line['Amount'] < 0), None)
                    
                    # Check VCT responsibility debit line
                    if (debit_line and 
                        debit_line.get('Account_Type') == 'G/L Account' and
                        debit_line.get('Account_No') == '18600-10' and
                        debit_line.get('Shortcut_Dimension_1_Code') == 'VCT' and
                        debit_line.get('Shortcut_Dimension_2_Code') == 'VCT.9999' and
                        debit_line.get('ShortcutDimCode3') == 'VCA'):
                        
                        # Check regular credit line
                        if (credit_line and
                            credit_line.get('Account_Type') == 'Vendor' and
                            credit_line.get('Account_No') == 'V-VC00048'):
                            
                            print("✅ VCT responsibility entries creation test PASSED")
                            return True
                
                print("❌ VCT responsibility entries creation test FAILED")
                print(f"Journal lines created: {len(journal_lines)}")
                for i, line in enumerate(journal_lines):
                    print(f"  Line {i+1}: {line}")
                return False
                
            except Exception as e:
                print(f"❌ VCT responsibility entries creation test FAILED: {e}")
                return False

def main():
    """Run all individual VCT responsibility tests."""
    print("=" * 80)
    print("INDIVIDUAL VCT RESPONSIBILITY PROCESSING TEST SUITE")
    print("=" * 80)
    print("Testing the target behavior AFTER removing consolidation")
    print("Each V-VC00048 entry should be processed individually")
    print("=" * 80)
    
    tests = [
        test_individual_vct_processing,
        test_mixed_vendor_processing,
        test_vct_responsibility_entries_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 80)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests PASSED! Individual VCT processing is working correctly.")
        print("\nExpected behavior confirmed:")
        print("- Each V-VC00048 entry processed individually")
        print("- No consolidation of VCT responsibility entries")
        print("- Each entry gets its own document number")
        print("- VCT responsibility debit lines created correctly")
        return 0
    else:
        print("⚠️  Some tests FAILED. Implementation needs adjustment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
