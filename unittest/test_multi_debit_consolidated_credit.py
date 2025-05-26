#!/usr/bin/env python3
"""
Unit tests for the multi-debit consolidated credit functionality in process_japan_exports.py
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock, call

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from process_japan_exports import process_entries


class TestMultiDebitConsolidatedCredit(unittest.TestCase):
    """Test cases for handling multiple debit entries with consolidated credit in process_japan_exports.py"""

    def setUp(self):
        """Set up test fixtures"""
        # Sample entries with the same voucher number and vendor code
        self.debit_entry1 = {
            "voucher_no": "VPA-0000078",
            "transaction_date": "2025-04-01",
            "description": "Debit Entry 1",
            "debit": {
                "gl_account": "G/L Account",
                "account": "123456",
                "amount": 100.0,
                "currency": "USD",
                "department": "VCT.DEPT1",
                "department_code": "VCT.1234"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "VENDOR789",
                "amount": 100.0,
                "currency": "USD",
                "department": "VCT.DEPT1",
                "department_code": "VCT.1234",
                "vendor_code": "VENDOR789"
            }
        }
        
        self.debit_entry2 = {
            "voucher_no": "VPA-0000078",
            "transaction_date": "2025-04-01",
            "description": "Debit Entry 2",
            "debit": {
                "gl_account": "G/L Account",
                "account": "789012",
                "amount": 200.0,
                "currency": "USD",
                "department": "VCT.DEPT2",
                "department_code": "VCT.5678"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "VENDOR789",
                "amount": 200.0,
                "currency": "USD",
                "department": "VCT.DEPT2",
                "department_code": "VCT.5678",
                "vendor_code": "VENDOR789"
            }
        }
        
        # Sample consolidated credit entry
        self.consolidated_credit_entry = {
            "voucher_no": "VPA-0000078",
            "transaction_date": "2025-04-01",
            "description": "Consolidated Credit Entry",
            "debit": {
                "gl_account": "G/L Account",
                "account": "",
                "amount": 0.0,  # Empty debit amount
                "currency": "",
                "department": "",
                "department_code": ""
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "VENDOR789",
                "amount": 300.0,  # Sum of debit_entry1 and debit_entry2
                "currency": "USD",
                "department": "VCT.DEPT",
                "department_code": "VCT.1234",
                "vendor_code": "VENDOR789",
                "consolidated": True,
                "original_entries_count": 2,
                "consolidation_note": "Consolidated from 2 entries"
            }
        }

    @patch('process_japan_exports.post_journal_line')
    @patch('process_japan_exports.create_journal_line')
    @patch('process_japan_exports.time.sleep')  # Mock sleep to speed up tests
    def test_process_entries_with_multiple_debits_one_consolidated_credit(self, mock_sleep, mock_create_line, mock_post_line):
        """Test process_entries with multiple debit entries and one consolidated credit"""
        # Setup mocks
        mock_create_line.side_effect = lambda entry, entry_type: {
            "type": entry_type,
            "voucher": entry.get("voucher_no", ""),
            "description": entry.get("description", ""),
            "amount": entry.get(entry_type, {}).get("amount", 0)
        }
        mock_post_line.return_value = (True, {})
        
        # Call process_entries with both debit entries and the consolidated credit entry
        entries = [self.debit_entry1, self.debit_entry2, self.consolidated_credit_entry]
        success, failure = process_entries(entries, "fake_token")
        
        # Verify the correct number of lines were processed:
        # - Two debit lines (one from each debit entry)
        # - One consolidated credit line
        self.assertEqual(mock_create_line.call_count, 3)
        self.assertEqual(mock_post_line.call_count, 3)
        
        # Check that the correct entries were created
        expected_calls = [
            # First debit entry's debit line
            call(self.debit_entry1, "debit"),
            # Second debit entry's debit line
            call(self.debit_entry2, "debit"),
            # Consolidated credit line
            call(self.consolidated_credit_entry, "credit")
        ]
        mock_create_line.assert_has_calls(expected_calls, any_order=False)
        
        # Verify success count
        self.assertEqual(success, 3)
        self.assertEqual(failure, 0)

    @patch('process_japan_exports.post_journal_line')
    @patch('process_japan_exports.create_journal_line')
    @patch('process_japan_exports.time.sleep')  # Mock sleep to speed up tests
    def test_process_entries_auto_consolidates_multiple_debits(self, mock_sleep, mock_create_line, mock_post_line):
        """Test process_entries automatically consolidates multiple debits without explicit consolidated entry"""
        # Setup mocks
        mock_create_line.side_effect = lambda entry, entry_type: {
            "type": entry_type,
            "voucher": entry.get("voucher_no", ""),
            "description": entry.get("description", ""),
            "amount": entry.get(entry_type, {}).get("amount", 0)
        }
        mock_post_line.return_value = (True, {})
        
        # Call process_entries with just the debit entries (no explicit consolidated credit)
        entries = [self.debit_entry1, self.debit_entry2]
        success, failure = process_entries(entries, "fake_token")
        
        # Verify the correct number of lines were processed:
        # - Two debit lines (one from each debit entry)
        # - One auto-generated consolidated credit line
        self.assertEqual(mock_create_line.call_count, 3)
        self.assertEqual(mock_post_line.call_count, 3)
        
        # Check that the correct entries were created
        # The first two calls should be for the debit lines
        mock_create_line.assert_any_call(self.debit_entry1, "debit")
        mock_create_line.assert_any_call(self.debit_entry2, "debit")
        
        # The third call should be for a credit line with consolidated flag
        # We can't check the exact entry since it's created dynamically,
        # but we can verify it was a credit line
        last_call = mock_create_line.call_args_list[2]
        self.assertEqual(last_call[0][1], "credit")
        
        # Verify the entry passed to create_journal_line has the consolidated flag
        consolidated_entry = last_call[0][0]
        self.assertTrue(consolidated_entry["credit"].get("consolidated", False))
        self.assertEqual(consolidated_entry["credit"].get("original_entries_count"), 2)
        self.assertEqual(consolidated_entry["credit"].get("amount"), 300.0)  # Sum of both debits
        
        # Verify success count
        self.assertEqual(success, 3)
        self.assertEqual(failure, 0)

    @patch('process_japan_exports.post_journal_line')
    @patch('process_japan_exports.create_journal_line')
    @patch('process_japan_exports.time.sleep')  # Mock sleep to speed up tests
    def test_process_entries_single_entry_not_consolidated(self, mock_sleep, mock_create_line, mock_post_line):
        """Test process_entries doesn't consolidate single entries"""
        # Setup mocks
        mock_create_line.side_effect = lambda entry, entry_type: {
            "type": entry_type,
            "voucher": entry.get("voucher_no", ""),
            "description": entry.get("description", ""),
            "amount": entry.get(entry_type, {}).get("amount", 0)
        }
        mock_post_line.return_value = (True, {})
        
        # Call process_entries with just one debit entry
        entries = [self.debit_entry1]
        success, failure = process_entries(entries, "fake_token")
        
        # Verify both debit and credit lines were processed normally
        self.assertEqual(mock_create_line.call_count, 2)
        self.assertEqual(mock_post_line.call_count, 2)
        
        # Check that both debit and credit lines were created for the single entry
        expected_calls = [
            call(self.debit_entry1, "debit"),
            call(self.debit_entry1, "credit")
        ]
        mock_create_line.assert_has_calls(expected_calls, any_order=False)
        
        # Verify success count
        self.assertEqual(success, 2)
        self.assertEqual(failure, 0)


if __name__ == '__main__':
    unittest.main()
