#!/usr/bin/env python3
"""
Test script for V-VC00048 VCT responsibility entries functionality.

This script tests the changes made to the create_vct_responsibility_entries function
to use the full department code instead of just the cost center (first 3 characters)
in the description field.
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock
from process_japan_exports import create_vct_responsibility_entries

class TestVCTResponsibilityEntries(unittest.TestCase):
    """Test cases for VCT responsibility entries functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample entry with department code
        self.sample_entry = {
            'voucher_no': 'TEST001',
            'External_Document_No': 'EXT001',
            'Document_Date': '2025/06/05',
            'credit': {
                'department': 'VCP.1234',  # Full department code
                'Remarks': 'Test transaction',
                'amount': 1000.0,
                'currency': 'USD',
                'vendor_code': 'V-VC00048'
            },
            'description': 'Default description'
        }
        
        # Mock access token and rate limiter
        self.mock_token = 'mock_token'
        self.mock_rate_limiter = MagicMock()
        
    @patch('process_japan_exports.post_journal_line')
    def test_full_department_in_description(self, mock_post_journal_line):
        """Test that the full department code is used in the description."""
        # Configure the mock to return success for both calls
        mock_post_journal_line.side_effect = [(True, {}), (True, {})]
        
        # Create a sample entry with main description
        entry = self.sample_entry.copy()
        entry['credit'] = self.sample_entry['credit'].copy()
        entry['credit']['Remarks'] = ''  # Clear Remarks field
        entry['description'] = 'Test transaction'  # Set main description
        
        # Call the function
        success_count, failure_count = create_vct_responsibility_entries(
            entry, 
            self.mock_token, 
            self.mock_rate_limiter
        )
        
        # Check the results
        self.assertEqual(success_count, 2)
        self.assertEqual(failure_count, 0)
        
        # Check that post_journal_line was called twice
        self.assertEqual(mock_post_journal_line.call_count, 2)
        
        # Get the arguments for the first call (debit line)
        debit_args = mock_post_journal_line.call_args_list[0][0]
        debit_line = debit_args[0]
        
        # Get the arguments for the second call (credit line)
        credit_args = mock_post_journal_line.call_args_list[1][0]
        credit_line = credit_args[0]
        
        # Check that both lines have the full department code in the description
        expected_description = "VCP.1234 Test transaction"
        self.assertEqual(debit_line["Description"], expected_description)
        self.assertEqual(credit_line["Description"], expected_description)
        
    @patch('process_japan_exports.post_journal_line')
    def test_description_truncation(self, mock_post_journal_line):
        """Test that the description is truncated if it's too long."""
        # Create a sample entry with a very long description
        long_description = "X" * 100
        entry_with_long_desc = self.sample_entry.copy()
        entry_with_long_desc['description'] = long_description
        
        # Configure the mock to return success for both calls
        mock_post_journal_line.side_effect = [(True, {}), (True, {})]
        
        # Call the function
        success_count, failure_count = create_vct_responsibility_entries(
            entry_with_long_desc, 
            self.mock_token, 
            self.mock_rate_limiter
        )
        
        # Check the results
        self.assertEqual(success_count, 2)
        self.assertEqual(failure_count, 0)
        
        # Get the arguments for the first call (debit line)
        debit_args = mock_post_journal_line.call_args_list[0][0]
        debit_line = debit_args[0]
        
        # Check that the description is truncated to 100 characters
        expected_prefix = "VCP.1234 "
        self.assertEqual(len(debit_line["Description"]), 100)
        self.assertTrue(debit_line["Description"].startswith(expected_prefix))
        
    @patch('process_japan_exports.post_journal_line')
    def test_post_failure(self, mock_post_journal_line):
        """Test handling of post_journal_line failures."""
        # Configure the mock to return failure for both calls
        mock_post_journal_line.side_effect = [(False, {"error": "Test error"}), (False, {"error": "Test error"})]
        
        # Call the function
        success_count, failure_count = create_vct_responsibility_entries(
            self.sample_entry, 
            self.mock_token, 
            self.mock_rate_limiter
        )
        
        # Check the results
        self.assertEqual(success_count, 0)
        self.assertEqual(failure_count, 2)
        
    @patch('process_japan_exports.post_journal_line')
    def test_description_sources(self, mock_post_journal_line):
        """Test that the function uses all possible sources for description."""
        # Configure the mock to return success for both calls
        mock_post_journal_line.side_effect = [(True, {}), (True, {})]
        
        # Test case 1: Remarks field (already tested in test_full_department_in_description)
        
        # Test case 2: 備考 field (with no main description)
        entry_with_japanese_remarks = self.sample_entry.copy()
        entry_with_japanese_remarks['credit'] = self.sample_entry['credit'].copy()
        entry_with_japanese_remarks['credit']['Remarks'] = ''
        entry_with_japanese_remarks['credit']['備考'] = '日本語の備考'
        entry_with_japanese_remarks['description'] = ''  # Clear main description
        
        success_count, failure_count = create_vct_responsibility_entries(
            entry_with_japanese_remarks, 
            self.mock_token, 
            self.mock_rate_limiter
        )
        
        # Get the arguments for the first call (debit line)
        debit_args = mock_post_journal_line.call_args_list[0][0]
        debit_line = debit_args[0]
        
        # Check that the description contains the Japanese remarks
        expected_description = "VCP.1234 日本語の備考"
        self.assertEqual(debit_line["Description"], expected_description)
        
        # Reset the mock
        mock_post_journal_line.reset_mock()
        mock_post_journal_line.side_effect = [(True, {}), (True, {})]
        
        # Test case 3: credit_description field (with no main description)
        entry_with_credit_desc = self.sample_entry.copy()
        entry_with_credit_desc['credit'] = self.sample_entry['credit'].copy()
        entry_with_credit_desc['credit']['Remarks'] = ''
        entry_with_credit_desc['credit_description'] = 'Credit description field'
        entry_with_credit_desc['description'] = ''  # Clear main description
        
        success_count, failure_count = create_vct_responsibility_entries(
            entry_with_credit_desc, 
            self.mock_token, 
            self.mock_rate_limiter
        )
        
        # Get the arguments for the first call (debit line)
        debit_args = mock_post_journal_line.call_args_list[0][0]
        debit_line = debit_args[0]
        
        # Check that the description contains the credit description
        expected_description = "VCP.1234 Credit description field"
        self.assertEqual(debit_line["Description"], expected_description)
        
        # Reset the mock
        mock_post_journal_line.reset_mock()
        mock_post_journal_line.side_effect = [(True, {}), (True, {})]
        
        # Test case 4: main description field
        entry_with_main_desc = self.sample_entry.copy()
        entry_with_main_desc['credit'] = self.sample_entry['credit'].copy()
        entry_with_main_desc['credit']['Remarks'] = ''
        entry_with_main_desc['description'] = 'Main description field'
        
        success_count, failure_count = create_vct_responsibility_entries(
            entry_with_main_desc, 
            self.mock_token, 
            self.mock_rate_limiter
        )
        
        # Get the arguments for the first call (debit line)
        debit_args = mock_post_journal_line.call_args_list[0][0]
        debit_line = debit_args[0]
        
        # Check that the description contains the main description
        expected_description = "VCP.1234 Main description field"
        self.assertEqual(debit_line["Description"], expected_description)
        
        # Reset the mock
        mock_post_journal_line.reset_mock()
        mock_post_journal_line.side_effect = [(True, {}), (True, {})]
        
        # Test case 5: Receipt/Invoice Note(明細) field (with no main description or other fields)
        entry_with_receipt_note = self.sample_entry.copy()
        entry_with_receipt_note['credit'] = self.sample_entry['credit'].copy()
        entry_with_receipt_note['credit']['Remarks'] = ''
        entry_with_receipt_note['credit']['Receipt/Invoice Note(明細)'] = 'Receipt note field'
        entry_with_receipt_note['description'] = ''  # Clear main description
        entry_with_receipt_note['credit_description'] = ''  # Clear credit description
        
        success_count, failure_count = create_vct_responsibility_entries(
            entry_with_receipt_note, 
            self.mock_token, 
            self.mock_rate_limiter
        )
        
        # Get the arguments for the first call (debit line)
        debit_args = mock_post_journal_line.call_args_list[0][0]
        debit_line = debit_args[0]
        
        # Check that the description contains the receipt note
        expected_description = "VCP.1234 Receipt note field"
        self.assertEqual(debit_line["Description"], expected_description)
        
        # Reset the mock
        mock_post_journal_line.reset_mock()
        mock_post_journal_line.side_effect = [(True, {}), (True, {})]
        
        # Test case 6: free_field field (with no main description or other fields)
        entry_with_free_field = self.sample_entry.copy()
        entry_with_free_field['credit'] = self.sample_entry['credit'].copy()
        entry_with_free_field['credit']['Remarks'] = ''
        entry_with_free_field['credit']['free_field'] = 'Free field content'
        entry_with_free_field['description'] = ''  # Clear main description
        entry_with_free_field['credit_description'] = ''  # Clear credit description
        
        success_count, failure_count = create_vct_responsibility_entries(
            entry_with_free_field, 
            self.mock_token, 
            self.mock_rate_limiter
        )
        
        # Get the arguments for the first call (debit line)
        debit_args = mock_post_journal_line.call_args_list[0][0]
        debit_line = debit_args[0]
        
        # Check that the description contains the free field content
        expected_description = "VCP.1234 Free field content"
        self.assertEqual(debit_line["Description"], expected_description)
        
    @patch('process_japan_exports.post_journal_line')
    def test_description_priority(self, mock_post_journal_line):
        """Test that the function prioritizes the main description field over other fields."""
        # Configure the mock to return success for both calls
        mock_post_journal_line.side_effect = [(True, {}), (True, {})]
        
        # Create an entry with multiple description sources
        entry_with_multiple_sources = self.sample_entry.copy()
        entry_with_multiple_sources['credit'] = self.sample_entry['credit'].copy()
        entry_with_multiple_sources['description'] = 'AUTO IQ AUTOMOTIVE CYBERSECURITY SUMMIT September in Cali'
        entry_with_multiple_sources['credit_description'] = 'Credit description should not be used'
        entry_with_multiple_sources['credit']['Remarks'] = 'Events'
        entry_with_multiple_sources['credit']['備考'] = '備考 should not be used'
        entry_with_multiple_sources['credit']['Receipt/Invoice Note(明細)'] = 'Receipt note should not be used'
        entry_with_multiple_sources['credit']['free_field'] = 'Free field should not be used'
        
        # Call the function
        success_count, failure_count = create_vct_responsibility_entries(
            entry_with_multiple_sources, 
            self.mock_token, 
            self.mock_rate_limiter
        )
        
        # Get the arguments for the first call (debit line)
        debit_args = mock_post_journal_line.call_args_list[0][0]
        debit_line = debit_args[0]
        
        # Check that the description contains the main description field, not the Remarks field
        expected_description = "VCP.1234 AUTO IQ AUTOMOTIVE CYBERSECURITY SUMMIT September in Cali"
        self.assertEqual(debit_line["Description"], expected_description)
        
        # Reset the mock
        mock_post_journal_line.reset_mock()
        mock_post_journal_line.side_effect = [(True, {}), (True, {})]
        
        # Test with a consolidated entry (similar to APA-0000401)
        consolidated_entry = {
            'voucher_no': 'APA-0000401',
            'External_Document_No': '20250502',
            'Document_Date': '2025/05/02',
            'description': 'AUTO IQ AUTOMOTIVE CYBERSECURITY SUMMIT September in Cali',
            'credit_description': 'Events',
            'credit': {
                'department': 'VCA.1342G',
                'Remarks': 'Events',
                'amount': 7284.55,
                'currency': 'R-USD',
                'vendor_code': 'V-VC00048',
                'consolidated': True,
                'original_entries_count': 2
            }
        }
        
        # Call the function with the consolidated entry
        success_count, failure_count = create_vct_responsibility_entries(
            consolidated_entry, 
            self.mock_token, 
            self.mock_rate_limiter
        )
        
        # Get the arguments for the first call (debit line)
        debit_args = mock_post_journal_line.call_args_list[0][0]
        debit_line = debit_args[0]
        
        # Check that the description contains the main description field, not the Remarks field
        expected_description = "VCA.1342G AUTO IQ AUTOMOTIVE CYBERSECURITY SUMMIT September in Cali"
        self.assertEqual(debit_line["Description"], expected_description)

if __name__ == '__main__':
    print("Starting VCT responsibility tests...")
    # Run the tests and capture the result
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVCTResponsibilityEntries)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Print the test results
    print("\nTest Results:")
    print(f"Ran {result.testsRun} tests")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    # Print details of failures
    if result.failures:
        print("\nFailures:")
        for i, (test, traceback) in enumerate(result.failures):
            print(f"\nFailure {i+1}: {test}")
            print(traceback)
    
    # Print details of errors
    if result.errors:
        print("\nErrors:")
        for i, (test, traceback) in enumerate(result.errors):
            print(f"\nError {i+1}: {test}")
            print(traceback)
