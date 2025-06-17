#!/usr/bin/env python3
"""
Test for VCT responsibility document number fix.

This test verifies that document numbers are modified only for VCT responsibility entries.
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from core.process_japan_exports import create_vct_responsibility_entries

class TestVCTResponsibilityDocumentNoFix(unittest.TestCase):
    """Test case for VCT responsibility document number fix."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample entry for testing
        self.sample_entry = {
            "voucher_no": "APA-0000401",
            "External_Document_No": "EXT-0000401",
            "Document_Date": "2025/06/17",
            "description": "Test description",
            "debit": {
                "amount": 1000.0,
                "currency": "USD",
                "department": "VCA.1342G",
                "account": "18600-10",
                "gl_account": "G/L Account"
            },
            "credit": {
                "amount": 1000.0,
                "currency": "USD",
                "department": "VCA.1342G",
                "vendor_code": "V-VC00048",
                "gl_account": "Vendor"
            }
        }
        
        # Create a mock rate limiter
        self.mock_rate_limiter = MagicMock()
        
        # Create a mock access token
        self.mock_access_token = "mock_access_token"

    @patch('core.process_japan_exports.post_journal_line')
    def test_document_number_modification(self, mock_post_journal_line):
        """Test that document numbers are modified for VCT responsibility entries."""
        # Configure the mock to return success
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Create a dictionary to track used document numbers
        used_doc_numbers = {}
        
        # Call the function
        create_vct_responsibility_entries(
            self.sample_entry, 
            self.mock_access_token, 
            self.mock_rate_limiter, 
            used_doc_numbers
        )
        
        # Check that the document number was modified
        self.assertEqual(len(mock_post_journal_line.call_args_list), 2)
        
        # Get the document numbers used in the calls
        debit_call = mock_post_journal_line.call_args_list[0]
        credit_call = mock_post_journal_line.call_args_list[1]
        
        debit_doc_no = debit_call[0][0]["Document_No"]
        credit_doc_no = credit_call[0][0]["Document_No"]
        
        # Check that both document numbers are the same and have been modified
        self.assertEqual(debit_doc_no, credit_doc_no)
        self.assertEqual(debit_doc_no, "APA-0000401-1")
        
        # Check that the counter was incremented
        self.assertEqual(used_doc_numbers["APA-0000401"], 1)

    @patch('core.process_japan_exports.post_journal_line')
    def test_multiple_entries_increment_counter(self, mock_post_journal_line):
        """Test that multiple entries increment the counter correctly."""
        # Configure the mock to return success
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Create a dictionary to track used document numbers
        used_doc_numbers = {}
        
        # Call the function multiple times
        create_vct_responsibility_entries(
            self.sample_entry, 
            self.mock_access_token, 
            self.mock_rate_limiter, 
            used_doc_numbers
        )
        
        create_vct_responsibility_entries(
            self.sample_entry, 
            self.mock_access_token, 
            self.mock_rate_limiter, 
            used_doc_numbers
        )
        
        create_vct_responsibility_entries(
            self.sample_entry, 
            self.mock_access_token, 
            self.mock_rate_limiter, 
            used_doc_numbers
        )
        
        # Check that the document numbers were modified correctly
        self.assertEqual(len(mock_post_journal_line.call_args_list), 6)
        
        # Get the document numbers used in the calls
        calls = mock_post_journal_line.call_args_list
        
        # First entry
        self.assertEqual(calls[0][0][0]["Document_No"], "APA-0000401-1")
        self.assertEqual(calls[1][0][0]["Document_No"], "APA-0000401-1")
        
        # Second entry
        self.assertEqual(calls[2][0][0]["Document_No"], "APA-0000401-2")
        self.assertEqual(calls[3][0][0]["Document_No"], "APA-0000401-2")
        
        # Third entry
        self.assertEqual(calls[4][0][0]["Document_No"], "APA-0000401-3")
        self.assertEqual(calls[5][0][0]["Document_No"], "APA-0000401-3")
        
        # Check that the counter was incremented correctly
        self.assertEqual(used_doc_numbers["APA-0000401"], 3)

    @patch('core.process_japan_exports.post_journal_line')
    def test_different_document_numbers(self, mock_post_journal_line):
        """Test that different document numbers are tracked separately."""
        # Configure the mock to return success
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Create a dictionary to track used document numbers
        used_doc_numbers = {}
        
        # Create a second entry with a different voucher number
        second_entry = self.sample_entry.copy()
        second_entry["voucher_no"] = "APA-0000402"
        
        # Call the function with different entries
        create_vct_responsibility_entries(
            self.sample_entry, 
            self.mock_access_token, 
            self.mock_rate_limiter, 
            used_doc_numbers
        )
        
        create_vct_responsibility_entries(
            second_entry, 
            self.mock_access_token, 
            self.mock_rate_limiter, 
            used_doc_numbers
        )
        
        # Check that the document numbers were modified correctly
        self.assertEqual(len(mock_post_journal_line.call_args_list), 4)
        
        # Get the document numbers used in the calls
        calls = mock_post_journal_line.call_args_list
        
        # First entry
        self.assertEqual(calls[0][0][0]["Document_No"], "APA-0000401-1")
        self.assertEqual(calls[1][0][0]["Document_No"], "APA-0000401-1")
        
        # Second entry
        self.assertEqual(calls[2][0][0]["Document_No"], "APA-0000402-1")
        self.assertEqual(calls[3][0][0]["Document_No"], "APA-0000402-1")
        
        # Check that the counters were incremented correctly
        self.assertEqual(used_doc_numbers["APA-0000401"], 1)
        self.assertEqual(used_doc_numbers["APA-0000402"], 1)

if __name__ == '__main__':
    unittest.main()
