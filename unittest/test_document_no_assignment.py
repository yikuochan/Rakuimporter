#!/usr/bin/env python3
"""
Test for Document_No assignment in process_japan_exports.py

This test verifies that the Document_No in the journal line payload correctly
matches the voucher_no of the entry being processed.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import process_japan_exports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
from process_japan_exports import create_journal_line, process_entries


class TestDocumentNoAssignment(unittest.TestCase):
    """Test case for Document_No assignment in journal line payloads."""

    def setUp(self):
        """Set up test data."""
        # Sample entries with different voucher numbers
        self.entries = [
            {
                "voucher_no": "VPA-0000119",
                "description": "DFW to DTE CW15 Meetings in Detroit SAE WCX Conference",
                "Document_Date": "2025/04/02",
                "debit": {
                    "gl_account": "G/L Account",
                    "account": "72600-30",
                    "department": "VCA.1342G",
                    "amount": 158.99,
                    "currency": "R-USD",
                    "vendor_code": "10126"
                },
                "credit": {
                    "gl_account": "Vendor",
                    "vendor_code": "10126",
                    "department_code": "VCA",
                    "amount": 158.99,
                    "currency": "R-USD"
                }
            },
            {
                "voucher_no": "VPA-0000120",
                "description": "Return flight DTE to DFW CW15",
                "Document_Date": "2025/04/02",
                "debit": {
                    "gl_account": "G/L Account",
                    "account": "72600-30",
                    "department": "VCA.1342G",
                    "amount": 209.18,
                    "currency": "R-USD",
                    "vendor_code": "10126"
                },
                "credit": {
                    "gl_account": "Vendor",
                    "vendor_code": "10126",
                    "department_code": "VCA",
                    "amount": 209.18,
                    "currency": "R-USD"
                }
            },
            {
                "voucher_no": "VPA-0000121",
                "description": "Third party rental car coverage",
                "Document_Date": "2025/04/02",
                "debit": {
                    "gl_account": "G/L Account",
                    "account": "72600-30",
                    "department": "VCA.1342G",
                    "amount": 40.0,
                    "currency": "R-USD",
                    "vendor_code": "10126"
                },
                "credit": {
                    "gl_account": "Vendor",
                    "vendor_code": "10126",
                    "department_code": "VCA",
                    "amount": 40.0,
                    "currency": "R-USD"
                }
            }
        ]

    def test_create_journal_line_document_no(self):
        """Test that create_journal_line sets Document_No correctly."""
        for entry in self.entries:
            # Test debit line
            debit_line = create_journal_line(entry, "debit")
            self.assertEqual(debit_line["Document_No"], entry["voucher_no"])
            
            # Test credit line
            credit_line = create_journal_line(entry, "credit")
            self.assertEqual(credit_line["Document_No"], entry["voucher_no"])

    @patch('process_japan_exports.post_journal_line')
    @patch('process_japan_exports.time.sleep')  # Mock sleep to speed up tests
    def test_process_entries_document_no(self, mock_sleep, mock_post_journal_line):
        """Test that process_entries maintains correct Document_No for each entry."""
        # Mock successful API responses
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Process the entries
        process_entries(self.entries, "fake_token")
        
        # Check that post_journal_line was called with correct Document_No for each entry
        expected_document_nos = []
        for entry in self.entries:
            # Each entry should result in two calls (debit and credit)
            expected_document_nos.extend([entry["voucher_no"], entry["voucher_no"]])
        
        actual_document_nos = []
        for call in mock_post_journal_line.call_args_list:
            journal_line = call[0][0]  # First argument of each call
            actual_document_nos.append(journal_line["Document_No"])
        
        # Verify that the Document_No values match the expected voucher numbers
        self.assertEqual(actual_document_nos, expected_document_nos)


if __name__ == '__main__':
    unittest.main()
