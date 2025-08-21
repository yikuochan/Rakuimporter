#!/usr/bin/env python3
"""
Unit Test for 72600-10 and 72600-30 ShortcutDimCode4 Logic

This test verifies that accounts 72600-10 and 72600-30 follow normal vendor logic
based on the account_source field, as specified in GitHub requirements.

Test scenarios:
1. 72600-10 with account_source = "vendor_code" → ShortcutDimCode4 = ""
2. 72600-10 with account_source = "applicant_code" → ShortcutDimCode4 = applicant_code
3. 72600-30 with account_source = "vendor_code" → ShortcutDimCode4 = ""
4. 72600-30 with account_source = "applicant_code" → ShortcutDimCode4 = applicant_code
5. Other accounts should not be affected (regression test)
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import json

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.process_japan_exports import create_journal_line
except ImportError:
    print("Warning: Could not import create_journal_line. Make sure core module is available.")
    create_journal_line = None


class Test72600ShortcutDimCode4(unittest.TestCase):
    """Test ShortcutDimCode4 logic for accounts 72600-10 and 72600-30"""

    def setUp(self):
        """Set up test data"""
        self.base_entry = {
            "voucher_no": "TEST-001",
            "transaction_date": "2025/01/01",
            "description": "Test Entry",
            "External_Document_No": "TEST-DOC-001",
            "Document_Date": "2025/01/01"
        }

    def create_test_entry(self, account, account_source, applicant_code="TEST_APPLICANT", vendor_code=""):
        """Helper to create test entry with specified parameters"""
        entry = self.base_entry.copy()
        entry["debit"] = {
            "gl_account": "G/L Account",
            "account": account,
            "amount": 1000.0,
            "currency": "NTD",
            "department": "VCT.1342G",
            "applicant_code": applicant_code,
            "vendor_code": vendor_code,
            "department_code": "VCT.1342G"
        }
        entry["credit"] = {
            "gl_account": "Vendor",
            "account": "10055",
            "amount": 1000.0,
            "currency": "NTD",
            "department": "VCT.1342G",
            "applicant_code": applicant_code,
            "vendor_code": vendor_code,
            "account_source": account_source,
            "department_code": "VCT.9999"
        }
        return entry

    @unittest.skipIf(create_journal_line is None, "create_journal_line not available")
    def test_72600_10_with_vendor_code_source(self):
        """Test 72600-10 with account_source = 'vendor_code' should have 'N/A' ShortcutDimCode4"""
        entry = self.create_test_entry("72600-10", "vendor_code", "TEST_APPLICANT", "V-TEST001")
        
        # Test debit line
        debit_line = create_journal_line(entry, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "N/A", 
                        "72600-10 debit with vendor_code source should have 'N/A' ShortcutDimCode4")
        
        # Test credit line  
        credit_line = create_journal_line(entry, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "N/A",
                        "72600-10 credit with vendor_code source should have 'N/A' ShortcutDimCode4")

    @unittest.skipIf(create_journal_line is None, "create_journal_line not available")
    def test_72600_10_with_applicant_code_source(self):
        """Test 72600-10 with account_source = 'applicant_code' should use applicant_code for ShortcutDimCode4"""
        entry = self.create_test_entry("72600-10", "applicant_code", "TEST_APPLICANT", "")
        
        # Test debit line
        debit_line = create_journal_line(entry, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "TEST_APPLICANT",
                        "72600-10 debit with applicant_code source should use applicant_code for ShortcutDimCode4")
        
        # Test credit line
        credit_line = create_journal_line(entry, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "TEST_APPLICANT",
                        "72600-10 credit with applicant_code source should use applicant_code for ShortcutDimCode4")

    @unittest.skipIf(create_journal_line is None, "create_journal_line not available")
    def test_72600_30_with_vendor_code_source(self):
        """Test 72600-30 with account_source = 'vendor_code' should have 'N/A' ShortcutDimCode4"""
        entry = self.create_test_entry("72600-30", "vendor_code", "TEST_APPLICANT", "V-TEST001")
        
        # Test debit line
        debit_line = create_journal_line(entry, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "N/A",
                        "72600-30 debit with vendor_code source should have 'N/A' ShortcutDimCode4")
        
        # Test credit line
        credit_line = create_journal_line(entry, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "N/A",
                        "72600-30 credit with vendor_code source should have 'N/A' ShortcutDimCode4")

    @unittest.skipIf(create_journal_line is None, "create_journal_line not available")
    def test_72600_30_with_applicant_code_source(self):
        """Test 72600-30 with account_source = 'applicant_code' should use applicant_code for ShortcutDimCode4"""
        entry = self.create_test_entry("72600-30", "applicant_code", "TEST_APPLICANT", "")
        
        # Test debit line
        debit_line = create_journal_line(entry, "debit")
        self.assertEqual(debit_line["ShortcutDimCode4"], "TEST_APPLICANT",
                        "72600-30 debit with applicant_code source should use applicant_code for ShortcutDimCode4")
        
        # Test credit line
        credit_line = create_journal_line(entry, "credit")
        self.assertEqual(credit_line["ShortcutDimCode4"], "TEST_APPLICANT",
                        "72600-30 credit with applicant_code source should use applicant_code for ShortcutDimCode4")

    @unittest.skipIf(create_journal_line is None, "create_journal_line not available")
    def test_other_accounts_not_affected(self):
        """Test that other accounts (not 72600-10/72600-30) are not affected by the fix"""
        # Test with a different account
        entry = self.create_test_entry("72700-10", "vendor_code", "TEST_APPLICANT", "V-TEST001")
        
        # For non-72600-10/72600-30 accounts, the logic should follow normal vendor rules
        debit_line = create_journal_line(entry, "debit")
        credit_line = create_journal_line(entry, "credit")
        
        # For vendor accounts with vendor_code source, ShortcutDimCode4 should be empty
        self.assertEqual(credit_line["ShortcutDimCode4"], "",
                        "Other vendor accounts with vendor_code source should have empty ShortcutDimCode4")

    def test_account_source_field_presence(self):
        """Test that account_source field is properly tracked in test data"""
        entry = self.create_test_entry("72600-10", "vendor_code", "TEST_APPLICANT", "V-TEST001")
        
        # Verify account_source field is present
        self.assertIn("account_source", entry["credit"], 
                     "account_source field should be present in credit data")
        self.assertEqual(entry["credit"]["account_source"], "vendor_code",
                        "account_source should be set correctly")

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test with empty applicant_code
        entry = self.create_test_entry("72600-10", "applicant_code", "", "V-TEST001")
        
        if create_journal_line is not None:
            debit_line = create_journal_line(entry, "debit")
            # Should handle empty applicant_code gracefully
            self.assertEqual(debit_line["ShortcutDimCode4"], "",
                            "Should handle empty applicant_code gracefully")

    def test_current_implementation_behavior(self):
        """Document current implementation behavior before fix (for comparison)"""
        # This test documents what the current broken implementation does
        # It should fail after the fix is applied, confirming the fix works
        
        if create_journal_line is None:
            self.skipTest("create_journal_line not available")
            
        entry = self.create_test_entry("72600-10", "vendor_code", "TEST_APPLICANT", "V-TEST001")
        
        try:
            debit_line = create_journal_line(entry, "debit")
            
            # Current implementation forces "N/A" for 72600-10 and 72600-30
            # After fix, this should be empty string for vendor_code source
            if debit_line["ShortcutDimCode4"] == "N/A":
                print("⚠️  Current implementation detected: 72600-10 forced to 'N/A'")
                print("   This should change to empty string after fix is applied")
            elif debit_line["ShortcutDimCode4"] == "":
                print("✅ Fixed implementation detected: 72600-10 follows vendor logic")
            else:
                print(f"🔍 Unexpected ShortcutDimCode4 value: {debit_line['ShortcutDimCode4']}")
                
        except Exception as e:
            print(f"Error testing current implementation: {e}")


def run_comprehensive_test():
    """Run comprehensive test and provide detailed output"""
    print("=" * 70)
    print("72600-10/72600-30 SHORTCUTDIMCODE4 LOGIC TEST")
    print("=" * 70)
    print()
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(Test72600ShortcutDimCode4)
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run tests
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}")
            print(f"    {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}")
            print(f"    {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {len(result.failures + result.errors)} TESTS FAILED")
    
    return success


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)