#!/usr/bin/env python3
"""
Unit tests for consolidated entries handling in process_japan_exports.py
"""

import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from process_japan_exports import create_journal_line, process_entries


class TestConsolidatedEntries(unittest.TestCase):
    """Test cases for handling consolidated entries in process_japan_exports.py"""

    def setUp(self):
        """Set up test fixtures"""
        # Sample regular entry
        self.regular_entry = {
            "voucher_no": "VPA-0000107",
            "transaction_date": "2025-04-01",
            "description": "Test Entry",
            "debit": {
                "gl_account": "G/L Account",
                "account": "123456",
                "amount": 100.0,
                "currency": "USD",
                "department": "VCT.DEPT",
                "department_code": "VCT.1234"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "VENDOR123",
                "amount": 100.0,
                "currency": "USD",
                "department": "VCT.DEPT",
                "department_code": "VCT.1234",
                "vendor_code": "VENDOR123"
            }
        }
        
        # Sample consolidated entry
        self.consolidated_entry = {
            "voucher_no": "VPA-0000095",
            "transaction_date": "2025-04-01",
            "description": "Consolidated Test Entry",
            "debit": {
                "gl_account": "G/L Account",
                "account": "123456",
                "amount": 0.0,  # Empty debit amount
                "currency": "",
                "department": "",
                "department_code": ""
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "VENDOR456",
                "amount": 500.0,
                "currency": "USD",
                "department": "VCT.DEPT",
                "department_code": "VCT.1234",
                "vendor_code": "VENDOR456",
                "consolidated": True,
                "original_entries_count": 5,
                "consolidation_note": "Consolidated from 5 entries"
            }
        }

    def test_create_journal_line_regular_entry(self):
        """Test create_journal_line with a regular entry"""
        # Test debit line
        debit_line = create_journal_line(self.regular_entry, "debit")
        self.assertEqual(debit_line["External_Document_No"], "VPA-0000107")
        self.assertEqual(debit_line["Account_Type"], "G/L Account")
        self.assertEqual(debit_line["Description"], "Test Entry")
        
        # Test credit line
        credit_line = create_journal_line(self.regular_entry, "credit")
        self.assertEqual(credit_line["External_Document_No"], "VPA-0000107")
        self.assertEqual(credit_line["Account_Type"], "Vendor")
        self.assertEqual(credit_line["Description"], "Test Entry")

    def test_create_journal_line_consolidated_entry(self):
        """Test create_journal_line with a consolidated entry"""
        # Test credit line with consolidation note
        credit_line = create_journal_line(self.consolidated_entry, "credit")
        self.assertEqual(credit_line["External_Document_No"], "VPA-0000095")
        self.assertEqual(credit_line["Account_Type"], "Vendor")
        
        # Check if consolidation note is added to description
        self.assertIn("Consolidated from 5 entries", credit_line["Description"])

    @patch('process_japan_exports.post_journal_line')
    @patch('process_japan_exports.create_journal_line')
    @patch('process_japan_exports.time.sleep')  # Mock sleep to speed up tests
    def test_process_entries_regular(self, mock_sleep, mock_create_line, mock_post_line):
        """Test process_entries with regular entries"""
        # Setup mocks
        mock_create_line.side_effect = lambda entry, entry_type: {"type": entry_type}
        mock_post_line.return_value = (True, {})
        
        # Call process_entries with a list containing one regular entry
        success, failure = process_entries([self.regular_entry], "fake_token")
        
        # Verify both debit and credit lines were processed
        self.assertEqual(mock_create_line.call_count, 2)  # Called for both debit and credit
        self.assertEqual(mock_post_line.call_count, 2)    # Posted both debit and credit
        self.assertEqual(success, 2)  # Both lines successful
        self.assertEqual(failure, 0)  # No failures

    @patch('process_japan_exports.post_journal_line')
    @patch('process_japan_exports.create_journal_line')
    @patch('process_japan_exports.time.sleep')  # Mock sleep to speed up tests
    def test_process_entries_consolidated(self, mock_sleep, mock_create_line, mock_post_line):
        """Test process_entries with consolidated entries"""
        # Setup mocks
        mock_create_line.side_effect = lambda entry, entry_type: {"type": entry_type}
        mock_post_line.return_value = (True, {})
        
        # Create a debit entry that will be paired with the consolidated credit
        debit_entry = {
            "voucher_no": "VPA-0000095",
            "transaction_date": "2025-04-01",
            "description": "Debit Entry for Consolidated",
            "debit": {
                "gl_account": "G/L Account",
                "account": "123456",
                "amount": 500.0,
                "currency": "USD",
                "department": "VCT.DEPT",
                "department_code": "VCT.1234"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "VENDOR456",
                "amount": 500.0,
                "currency": "USD",
                "department": "VCT.DEPT",
                "department_code": "VCT.1234",
                "vendor_code": "VENDOR456"
            }
        }
        
        # Call process_entries with both the debit entry and consolidated entry
        success, failure = process_entries([debit_entry, self.consolidated_entry], "fake_token")
        
        # Verify debit line and consolidated credit line were processed
        self.assertEqual(mock_create_line.call_count, 2)  # Called for debit and consolidated credit
        self.assertEqual(mock_post_line.call_count, 2)    # Posted debit and consolidated credit
        self.assertEqual(success, 2)  # Two lines successful
        self.assertEqual(failure, 0)  # No failures

    @patch('process_japan_exports.post_journal_line')
    @patch('process_japan_exports.create_journal_line')
    @patch('process_japan_exports.time.sleep')  # Mock sleep to speed up tests
    def test_process_entries_mixed(self, mock_sleep, mock_create_line, mock_post_line):
        """Test process_entries with a mix of regular and consolidated entries"""
        # Setup mocks
        mock_create_line.side_effect = lambda entry, entry_type: {"type": entry_type}
        mock_post_line.return_value = (True, {})
        
        # Create a debit entry that will be paired with the consolidated credit
        debit_entry = {
            "voucher_no": "VPA-0000095",
            "transaction_date": "2025-04-01",
            "description": "Debit Entry for Consolidated",
            "debit": {
                "gl_account": "G/L Account",
                "account": "123456",
                "amount": 500.0,
                "currency": "USD",
                "department": "VCT.DEPT",
                "department_code": "VCT.1234"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "VENDOR456",
                "amount": 500.0,
                "currency": "USD",
                "department": "VCT.DEPT",
                "department_code": "VCT.1234",
                "vendor_code": "VENDOR456"
            }
        }
        
        # Call process_entries with a list containing both types of entries
        success, failure = process_entries(
            [self.regular_entry, debit_entry, self.consolidated_entry], 
            "fake_token"
        )
        
        # Verify correct number of lines were processed
        # Regular entry: debit + credit = 2 lines
        # Debit entry + Consolidated entry: debit + consolidated credit = 2 lines
        # Total: 4 lines
        self.assertEqual(mock_create_line.call_count, 4)
        self.assertEqual(mock_post_line.call_count, 4)
        self.assertEqual(success, 4)
        self.assertEqual(failure, 0)


if __name__ == '__main__':
    unittest.main()
