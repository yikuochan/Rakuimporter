#!/usr/bin/env python3
"""
Test for Document_No assignment with multiple vouchers for the same vendor

This test verifies that when processing multiple vouchers for the same vendor,
each voucher maintains its correct Document_No in the API payload.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import process_japan_exports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the module to test
from process_japan_exports import process_entries


class TestMultipleVouchersWithSameVendor(unittest.TestCase):
    """Test case for Document_No assignment with multiple vouchers for the same vendor."""

    def setUp(self):
        """Set up test data."""
        # Sample entries with different voucher numbers but the same vendor code
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

    @patch('process_japan_exports.post_journal_line')
    @patch('process_japan_exports.time.sleep')  # Mock sleep to speed up tests
    def test_multiple_vouchers_same_vendor(self, mock_sleep, mock_post_journal_line):
        """Test that process_entries maintains correct Document_No for each entry with the same vendor."""
        # Mock successful API responses
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Process the entries
        process_entries(self.entries, "fake_token")
        
        # Extract Document_No values from the calls to post_journal_line
        document_nos = []
        for call in mock_post_journal_line.call_args_list:
            journal_line = call[0][0]  # First argument of each call
            document_nos.append(journal_line["Document_No"])
        
        # Verify that each voucher number appears exactly twice (once for debit, once for credit)
        voucher_counts = {}
        for voucher_no in document_nos:
            voucher_counts[voucher_no] = voucher_counts.get(voucher_no, 0) + 1
        
        self.assertEqual(voucher_counts["VPA-0000119"], 2)
        self.assertEqual(voucher_counts["VPA-0000120"], 2)
        self.assertEqual(voucher_counts["VPA-0000121"], 2)
        
        # Verify that the Document_No values match the expected sequence
        # For each entry, we should have a debit line followed by a credit line with the same Document_No
        expected_sequence = [
            "VPA-0000119", "VPA-0000119",
            "VPA-0000120", "VPA-0000120",
            "VPA-0000121", "VPA-0000121"
        ]
        self.assertEqual(document_nos, expected_sequence)


if __name__ == '__main__':
    unittest.main()
