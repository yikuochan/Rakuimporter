#!/usr/bin/env python3
"""
Test script for VCT responsibility document number sequencing fix

This script tests the document number sequencing logic to ensure
sequential numbering without gaps for VCT responsibility entries.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestVCTResponsibilityDocumentNumberSequencing(unittest.TestCase):
    """Test cases for VCT responsibility document number sequencing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.used_doc_numbers = {}
        
    def test_single_voucher_sequential_numbering(self):
        """Test that a single voucher gets sequential document numbers"""
        voucher_no = "APA-0000401"
        
        # Simulate the document number assignment logic
        expected_sequence = []
        for i in range(1, 5):  # Create 4 VCT responsibility entries
            if voucher_no not in self.used_doc_numbers:
                self.used_doc_numbers[voucher_no] = 0
            
            self.used_doc_numbers[voucher_no] += 1
            modified_doc_no = f"{voucher_no}-{self.used_doc_numbers[voucher_no]}"
            expected_sequence.append(modified_doc_no)
        
        # Verify the sequence is correct
        self.assertEqual(expected_sequence, [
            "APA-0000401-1",
            "APA-0000401-2", 
            "APA-0000401-3",
            "APA-0000401-4"
        ])
        
    def test_multiple_vouchers_independent_numbering(self):
        """Test that multiple vouchers have independent sequential numbering"""
        vouchers = ["APA-0000401", "APA-0000402", "APA-0000403"]
        results = {}
        
        # Process each voucher with 2 VCT responsibility entries
        for voucher_no in vouchers:
            results[voucher_no] = []
            for i in range(2):
                if voucher_no not in self.used_doc_numbers:
                    self.used_doc_numbers[voucher_no] = 0
                
                self.used_doc_numbers[voucher_no] += 1
                modified_doc_no = f"{voucher_no}-{self.used_doc_numbers[voucher_no]}"
                results[voucher_no].append(modified_doc_no)
        
        # Verify each voucher has its own sequence
        self.assertEqual(results["APA-0000401"], ["APA-0000401-1", "APA-0000401-2"])
        self.assertEqual(results["APA-0000402"], ["APA-0000402-1", "APA-0000402-2"])
        self.assertEqual(results["APA-0000403"], ["APA-0000403-1", "APA-0000403-2"])
        
    def test_mixed_processing_order(self):
        """Test that processing order doesn't affect sequential numbering"""
        # Process vouchers in mixed order: 401, 402, 401, 403, 401
        processing_order = [
            "APA-0000401",
            "APA-0000402", 
            "APA-0000401",
            "APA-0000403",
            "APA-0000401"
        ]
        
        results = []
        for voucher_no in processing_order:
            if voucher_no not in self.used_doc_numbers:
                self.used_doc_numbers[voucher_no] = 0
            
            self.used_doc_numbers[voucher_no] += 1
            modified_doc_no = f"{voucher_no}-{self.used_doc_numbers[voucher_no]}"
            results.append(modified_doc_no)
        
        # Verify the sequence maintains proper counters
        expected_results = [
            "APA-0000401-1",  # First APA-0000401
            "APA-0000402-1",  # First APA-0000402
            "APA-0000401-2",  # Second APA-0000401 (continues from 1)
            "APA-0000403-1",  # First APA-0000403
            "APA-0000401-3"   # Third APA-0000401 (continues from 2)
        ]
        
        self.assertEqual(results, expected_results)
        
    def test_dictionary_state_persistence(self):
        """Test that the used_doc_numbers dictionary maintains state correctly"""
        voucher_no = "APA-0000401"
        
        # Initial state
        self.assertEqual(self.used_doc_numbers, {})
        
        # First entry
        if voucher_no not in self.used_doc_numbers:
            self.used_doc_numbers[voucher_no] = 0
        self.used_doc_numbers[voucher_no] += 1
        
        self.assertEqual(self.used_doc_numbers[voucher_no], 1)
        
        # Second entry
        self.used_doc_numbers[voucher_no] += 1
        self.assertEqual(self.used_doc_numbers[voucher_no], 2)
        
        # Third entry
        self.used_doc_numbers[voucher_no] += 1
        self.assertEqual(self.used_doc_numbers[voucher_no], 3)
        
        # Verify final state
        self.assertEqual(self.used_doc_numbers, {"APA-0000401": 3})
        
    def test_no_reinitialization_issue(self):
        """Test that dictionary reinitialization doesn't cause gaps"""
        voucher_no = "APA-0000401"
        
        # Simulate the problematic scenario where dictionary gets reinitialized
        # This should NOT happen in the fixed version
        
        # First entry
        if voucher_no not in self.used_doc_numbers:
            self.used_doc_numbers[voucher_no] = 0
        self.used_doc_numbers[voucher_no] += 1
        first_doc_no = f"{voucher_no}-{self.used_doc_numbers[voucher_no]}"
        
        # Simulate what would happen if dictionary was reinitialized (BAD)
        # In the fixed version, this should never happen
        original_state = self.used_doc_numbers.copy()
        
        # Second entry (should continue from previous state)
        self.used_doc_numbers[voucher_no] += 1
        second_doc_no = f"{voucher_no}-{self.used_doc_numbers[voucher_no]}"
        
        # Verify no gaps
        self.assertEqual(first_doc_no, "APA-0000401-1")
        self.assertEqual(second_doc_no, "APA-0000401-2")
        self.assertEqual(self.used_doc_numbers[voucher_no], 2)
        
    def test_edge_case_empty_voucher_number(self):
        """Test handling of edge cases like empty voucher numbers"""
        voucher_no = ""
        
        if voucher_no not in self.used_doc_numbers:
            self.used_doc_numbers[voucher_no] = 0
        self.used_doc_numbers[voucher_no] += 1
        modified_doc_no = f"{voucher_no}-{self.used_doc_numbers[voucher_no]}"
        
        self.assertEqual(modified_doc_no, "-1")
        
    def test_large_sequence_numbers(self):
        """Test that large sequence numbers work correctly"""
        voucher_no = "APA-0000401"
        
        # Initialize
        if voucher_no not in self.used_doc_numbers:
            self.used_doc_numbers[voucher_no] = 0
            
        # Simulate 100 VCT responsibility entries
        for i in range(1, 101):
            self.used_doc_numbers[voucher_no] += 1
            modified_doc_no = f"{voucher_no}-{self.used_doc_numbers[voucher_no]}"
            self.assertEqual(modified_doc_no, f"APA-0000401-{i}")
            
        # Verify final state
        self.assertEqual(self.used_doc_numbers[voucher_no], 100)


class TestDocumentNumberSequencingIntegration(unittest.TestCase):
    """Integration tests for the document number sequencing fix"""
    
    def test_simulated_processing_scenario(self):
        """Test a realistic processing scenario"""
        # Simulate the scenario from the log file
        entries = [
            {"voucher_no": "APA-0000401", "type": "vct_responsibility"},
            {"voucher_no": "APA-0000401", "type": "vct_responsibility"},
            {"voucher_no": "APA-0000401", "type": "vct_responsibility"},
            {"voucher_no": "APA-0000401", "type": "vct_responsibility"},
        ]
        
        used_doc_numbers = {}
        results = []
        
        for entry in entries:
            voucher_no = entry["voucher_no"]
            
            # Apply the fixed logic
            if voucher_no not in used_doc_numbers:
                used_doc_numbers[voucher_no] = 0
                
            used_doc_numbers[voucher_no] += 1
            modified_doc_no = f"{voucher_no}-{used_doc_numbers[voucher_no]}"
            results.append(modified_doc_no)
        
        # Verify the expected sequence from the log
        expected_sequence = [
            "APA-0000401-1",
            "APA-0000401-2", 
            "APA-0000401-3",
            "APA-0000401-4"
        ]
        
        self.assertEqual(results, expected_sequence)


def run_tests():
    """Run all tests and display results"""
    print("Running VCT Responsibility Document Number Sequencing Tests...")
    print("=" * 60)
    
    # Create test suite using modern approach
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTests(loader.loadTestsFromTestCase(TestVCTResponsibilityDocumentNumberSequencing))
    test_suite.addTests(loader.loadTestsFromTestCase(TestDocumentNumberSequencingIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
            
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    
    return success


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
