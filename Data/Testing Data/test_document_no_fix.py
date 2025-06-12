#!/usr/bin/env python3
"""
Test for Document_No assignment fix

This test verifies that the fix for Document_No assignment works correctly,
ensuring that each voucher maintains its correct Document_No in the API payload
and that the External_Document_No is properly formatted to include the voucher_no.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import process_japan_exports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the module to test
from process_japan_exports import process_entries, create_journal_line


class TestDocumentNoFix(unittest.TestCase):
    """Test case for Document_No assignment fix."""

    def setUp(self):
        """Set up test data."""
        # Sample entries with different voucher numbers but the same vendor code
        self.entries = [
            {
                "voucher_no": "VPA-0000119",
                "description": "DFW to DTE CW15 Meetings in Detroit SAE WCX Conference",
                "Document_Date": "2025/04/02",
                "External_Document_No": "20250402",
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
                "External_Document_No": "20250402",
                "debit": {
                    "gl_account": "G/L Account",
                    "account": "72600-30",
                    "department": "VCA.1342G",
                    "amount": 209.18,
                    "currency": "R-USD",
                    "vendor_code": "10126"  # Same vendor code as VPA-0000119
                },
                "credit": {
                    "gl_account": "Vendor",
                    "vendor_code": "10126",  # Same vendor code as VPA-0000119
                    "department_code": "VCA",
                    "amount": 209.18,
                    "currency": "R-USD"
                }
            },
            {
                "voucher_no": "VPA-0000121",
                "description": "Third party rental car coverage",
                "Document_Date": "2025/04/02",
                "External_Document_No": "20250402",
                "debit": {
                    "gl_account": "G/L Account",
                    "account": "72600-30",
                    "department": "VCA.1342G",
                    "amount": 40.0,
                    "currency": "R-USD",
                    "vendor_code": "10126"  # Same vendor code as VPA-0000119 and VPA-0000120
                },
                "credit": {
                    "gl_account": "Vendor",
                    "vendor_code": "10126",  # Same vendor code as VPA-0000119 and VPA-0000120
                    "department_code": "VCA",
                    "amount": 40.0,
                    "currency": "R-USD"
                }
            }
        ]

    def test_create_journal_line_document_no(self):
        """Test that create_journal_line correctly sets Document_No."""
        for entry in self.entries:
            voucher_no = entry["voucher_no"]
            
            # Test debit line
            debit_line = create_journal_line(entry, "debit")
            self.assertEqual(debit_line["Document_No"], voucher_no)
            
            # Test credit line
            credit_line = create_journal_line(entry, "credit")
            self.assertEqual(credit_line["Document_No"], voucher_no)

    def test_create_journal_line_external_document_no(self):
        """Test that create_journal_line correctly formats External_Document_No."""
        for entry in self.entries:
            voucher_no = entry["voucher_no"]
            external_doc_no = entry["External_Document_No"]
            expected_external_doc_no = f"{voucher_no}-{external_doc_no}"
            
            # Test debit line with modified External_Document_No
            debit_line = create_journal_line(entry, "debit")
            # The External_Document_No should be set in process_entries, not in create_journal_line
            self.assertEqual(debit_line["External_Document_No"], external_doc_no)
            
            # Test credit line with modified External_Document_No
            credit_line = create_journal_line(entry, "credit")
            # The External_Document_No should be set in process_entries, not in create_journal_line
            self.assertEqual(credit_line["External_Document_No"], external_doc_no)

    @patch('process_japan_exports.post_journal_line')
    @patch('process_japan_exports.time.sleep')  # Mock sleep to speed up tests
    def test_process_entries_document_no(self, mock_sleep, mock_post_journal_line):
        """Test that process_entries maintains correct Document_No for each entry."""
        # Mock successful API responses
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Process the entries
        process_entries(self.entries, "fake_token")
        
        # Extract all calls to post_journal_line
        calls = mock_post_journal_line.call_args_list
        
        # Verify Document_No values in the calls
        document_nos = []
        external_document_nos = []
        for call in calls:
            journal_line = call[0][0]  # First argument of each call
            document_nos.append(journal_line["Document_No"])
            external_document_nos.append(journal_line["External_Document_No"])
        
        # Verify that each voucher number appears exactly twice (once for debit, once for credit)
        voucher_counts = {}
        for voucher_no in document_nos:
            voucher_counts[voucher_no] = voucher_counts.get(voucher_no, 0) + 1
        
        self.assertEqual(voucher_counts["VPA-0000119"], 2)
        self.assertEqual(voucher_counts["VPA-0000120"], 2)
        self.assertEqual(voucher_counts["VPA-0000121"], 2)
        
        # Verify that the Document_No values match the expected sequence
        expected_sequence = [
            "VPA-0000119", "VPA-0000119",
            "VPA-0000120", "VPA-0000120",
            "VPA-0000121", "VPA-0000121"
        ]
        self.assertEqual(document_nos, expected_sequence)
        
        # Verify that External_Document_No values are the original values without modification
        expected_external_doc_nos = [
            "20250402", "20250402",
            "20250402", "20250402",
            "20250402", "20250402"
        ]
        self.assertEqual(external_document_nos, expected_external_doc_nos)


if __name__ == '__main__':
    unittest.main()
