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
        
        # Call the function
        success_count, failure_count = create_vct_responsibility_entries(
            self.sample_entry, 
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
        entry_with_long_desc['credit']['Remarks'] = long_description
        
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

if __name__ == '__main__':
    unittest.main()
