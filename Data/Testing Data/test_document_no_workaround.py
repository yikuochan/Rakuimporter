#!/usr/bin/env python3
"""
Test script to verify the Document_No workaround in process_japan_exports.py.

This test ensures that when multiple journal entries with different voucher numbers are processed,
the voucher number is correctly added to the beginning of the Description field in the BC payload.
"""

import json
import logging
import unittest
from unittest.mock import patch, MagicMock, call

# Import the module to test
from process_japan_exports import create_journal_line, process_entries

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDocumentNoWorkaround(unittest.TestCase):
    """Test cases for the Document_No workaround in process_japan_exports.py."""

    def setUp(self):
        """Set up test data."""
        # Create test entries with different voucher numbers
        self.test_entries = [
            {
                "voucher_no": "VPA-0000119",
                "transaction_date": "2025/04/02",
                "application_date": "2025/04/26",
                "journal_generation_date": "2025/05/21",
                "description": "DFW to DTE CW15 Meetings in Detroit",
                "External_Document_No": "20250402",
                "Document_Date": "2025/04/02",
                "debit": {
                    "gl_account": "G/L Account",
                    "account": "72600-30",
                    "amount": 158.99,
                    "currency": "USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10126",
                    "vendor_code": "",
                    "department_code": "VCA.1342G",
                    "original_currency": "R-USD",
                    "original_amount": 158.99
                },
                "credit": {
                    "gl_account": "Vendor",
                    "account": "10126",
                    "amount": 158.99,
                    "currency": "R-USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10126",
                    "vendor_code": "10126",
                    "department_code": "VCA.9999"
                }
            },
            {
                "voucher_no": "VPA-0000120",
                "transaction_date": "2025/04/02",
                "application_date": "2025/04/26",
                "journal_generation_date": "2025/05/21",
                "description": "Return flight DTE to DFW CW15",
                "External_Document_No": "20250402",
                "Document_Date": "2025/04/02",
                "debit": {
                    "gl_account": "G/L Account",
                    "account": "72600-30",
                    "amount": 209.18,
                    "currency": "USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10126",
                    "vendor_code": "",
                    "department_code": "VCA.1342G",
                    "original_currency": "R-USD",
                    "original_amount": 209.18
                },
                "credit": {
                    "gl_account": "Vendor",
                    "account": "10126",
                    "amount": 209.18,
                    "currency": "R-USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10126",
                    "vendor_code": "10126",
                    "department_code": "VCA.9999"
                }
            },
            {
                "voucher_no": "VPA-0000121",
                "transaction_date": "2025/04/02",
                "application_date": "2025/04/26",
                "journal_generation_date": "2025/05/21",
                "description": "Rental car coverage",
                "External_Document_No": "20250402",
                "Document_Date": "2025/04/02",
                "debit": {
                    "gl_account": "G/L Account",
                    "account": "72600-30",
                    "amount": 40.00,
                    "currency": "USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10126",
                    "vendor_code": "",
                    "department_code": "VCA.1342G",
                    "original_currency": "R-USD",
                    "original_amount": 40.00
                },
                "credit": {
                    "gl_account": "Vendor",
                    "account": "10126",
                    "amount": 40.00,
                    "currency": "R-USD",
                    "department": "VCA.1342G",
                    "applicant_code": "10126",
                    "vendor_code": "10126",
                    "department_code": "VCA.9999"
                }
            }
        ]

    def test_voucher_number_in_description(self):
        """Test that the voucher number is correctly added to the Description field."""
        for entry in self.test_entries:
            voucher_no = entry["voucher_no"]
            original_description = entry["description"]
            
            # Test debit line
            debit_line = create_journal_line(entry, "debit")
            self.assertTrue(debit_line["Description"].startswith(voucher_no))
            self.assertIn(original_description, debit_line["Description"])
            self.assertEqual(debit_line["Description"], f"{voucher_no} - {original_description}")
            
            # Test credit line
            credit_line = create_journal_line(entry, "credit")
            self.assertTrue(credit_line["Description"].startswith(voucher_no))
            self.assertIn(original_description, credit_line["Description"])
            self.assertEqual(credit_line["Description"], f"{voucher_no} - {original_description}")

    def test_consolidated_credit_description(self):
        """Test that the voucher number is correctly added to the Description field for consolidated credit entries."""
        # Create a consolidated credit entry
        consolidated_entry = self.test_entries[0].copy()
        consolidated_entry["credit"] = consolidated_entry["credit"].copy()
        consolidated_entry["credit"]["consolidated"] = True
        consolidated_entry["credit"]["original_entries_count"] = 3
        
        # Test credit line with consolidation note
        credit_line = create_journal_line(consolidated_entry, "credit")
        voucher_no = consolidated_entry["voucher_no"]
        original_description = consolidated_entry["description"]
        consolidation_note = f"Consolidated from 3 entries"
        
        self.assertTrue(credit_line["Description"].startswith(voucher_no))
        self.assertIn(original_description, credit_line["Description"])
        self.assertIn(consolidation_note, credit_line["Description"])
        self.assertEqual(credit_line["Description"], f"{voucher_no} - {original_description} - {consolidation_note}")

    @patch('process_japan_exports.post_journal_line')
    def test_process_entries_with_workaround(self, mock_post_journal_line):
        """Test that the process_entries function correctly adds the voucher number to the Description field."""
        # Set up the mock to return success for all calls
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Process the test entries
        process_entries(self.test_entries, "fake_token")
        
        # Check that post_journal_line was called with the correct Description for each entry
        # We expect 2 calls per entry (debit and credit lines)
        expected_call_count = len(self.test_entries) * 2
        self.assertEqual(mock_post_journal_line.call_count, expected_call_count)
        
        # Extract the Description from each call
        descriptions = []
        for call in mock_post_journal_line.call_args_list:
            args, _ = call
            journal_line = args[0]
            descriptions.append(journal_line["Description"])
        
        # Log the Description values for debugging
        logger.info("Description values in API calls:")
        for i, desc in enumerate(descriptions):
            logger.info(f"Call {i+1}: Description = {desc}")
        
        # Check that each Description starts with the correct voucher number
        for i, entry in enumerate(self.test_entries):
            voucher_no = entry["voucher_no"]
            # Check debit line (even indices)
            self.assertTrue(descriptions[i*2].startswith(voucher_no))
            # Check credit line (odd indices)
            self.assertTrue(descriptions[i*2+1].startswith(voucher_no))

if __name__ == '__main__':
    unittest.main()
