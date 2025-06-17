#!/usr/bin/env python3
"""
Test for document number duplication fix for debit lines in consolidated entries.

This test verifies that the document number duplication fix for debit lines in consolidated entries
works correctly. It checks that when multiple debit lines are created with the same document number,
the document numbers are modified to avoid duplication.
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from core.process_japan_exports import process_entries, RateLimiter

class TestConsolidatedDebitDocumentNoFix(unittest.TestCase):
    """Test case for document number duplication fix for debit lines in consolidated entries."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock rate limiter
        self.rate_limiter = MagicMock(spec=RateLimiter)
        
        # Create a mock access token
        self.access_token = "mock_access_token"
        
        # Create mock entries with the same voucher number and vendor code
        self.entries = [
            {
                "voucher_no": "APA-0000501",
                "External_Document_No": "5224028807",
                "Document_Date": "2025-03-31",
                "description": "Test description 1",
                "debit": {
                    "account": "12345",
                    "department": "VCT.1234",
                    "amount": 500,
                    "currency": "USD"
                },
                "credit": {
                    "vendor_code": "V-VC12345",
                    "gl_account": "Vendor",
                    "department": "VCT.1234",
                    "amount": 500,
                    "currency": "USD"
                }
            },
            {
                "voucher_no": "APA-0000501",
                "External_Document_No": "5224028807",
                "Document_Date": "2025-03-31",
                "description": "Test description 2",
                "debit": {
                    "account": "12345",
                    "department": "VCT.1234",
                    "amount": 300,
                    "currency": "USD"
                },
                "credit": {
                    "vendor_code": "V-VC12345",
                    "gl_account": "Vendor",
                    "department": "VCT.1234",
                    "amount": 300,
                    "currency": "USD"
                }
            },
            {
                "voucher_no": "APA-0000501",
                "External_Document_No": "5224028807",
                "Document_Date": "2025-03-31",
                "description": "Test description 3",
                "debit": {
                    "account": "12345",
                    "department": "VCT.1234",
                    "amount": 200,
                    "currency": "USD"
                },
                "credit": {
                    "vendor_code": "V-VC12345",
                    "gl_account": "Vendor",
                    "department": "VCT.1234",
                    "amount": 200,
                    "currency": "USD"
                }
            }
        ]

    @patch('core.process_japan_exports.post_journal_line')
    @patch('core.process_japan_exports.verify_balanced_amounts')
    @patch('core.process_japan_exports.RateLimiter')
    def test_document_no_duplicate_fix(self, mock_rate_limiter_class, mock_verify_balanced_amounts, mock_post_journal_line):
        """Test that document numbers are modified to avoid duplication for debit lines in consolidated entries."""
        # Configure the mock to return success for all calls
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Configure the mock to indicate that entries are balanced
        mock_verify_balanced_amounts.return_value = (True, 0.0, 1000.0, 1000.0)
        
        # Configure the mock rate limiter class to return our mock rate limiter
        mock_rate_limiter_class.return_value = self.rate_limiter
        
        # Process the entries
        success_count, failure_count, balanced_count, unbalanced_count = process_entries(
            self.entries, 
            self.access_token
        )
        
        # Verify that all entries were processed successfully
        self.assertEqual(success_count, 6)  # 3 debit lines + 3 credit lines
        self.assertEqual(failure_count, 0)
        self.assertEqual(balanced_count, 1)  # 1 group of entries
        self.assertEqual(unbalanced_count, 0)
        
        # Extract the document numbers from the calls to post_journal_line
        doc_numbers = []
        for call in mock_post_journal_line.call_args_list:
            args, _ = call
            journal_line = args[0]
            doc_numbers.append((journal_line.get("Account_Type", ""), journal_line["Document_No"]))
        
        # Verify that the document numbers are as expected
        # First debit line should use the original document number
        # Subsequent debit lines should have a suffix appended
        # All credit lines should use the original document number
        expected_doc_numbers = [
            ("", "APA-0000501"),  # First debit line
            ("Vendor", "APA-0000501"),  # First credit line
            ("", "APA-0000501-1"),  # Second debit line
            ("Vendor", "APA-0000501"),  # Second credit line
            ("", "APA-0000501-2"),  # Third debit line
            ("Vendor", "APA-0000501"),  # Third credit line
        ]
        
        # Sort both lists to ensure consistent comparison
        doc_numbers.sort()
        expected_doc_numbers.sort()
        
        self.assertEqual(doc_numbers, expected_doc_numbers)

    @patch('core.process_japan_exports.post_journal_line')
    @patch('core.process_japan_exports.verify_balanced_amounts')
    @patch('core.process_japan_exports.RateLimiter')
    def test_document_no_duplicate_fix_with_different_voucher_numbers(self, mock_rate_limiter_class, mock_verify_balanced_amounts, mock_post_journal_line):
        """Test that document numbers are tracked separately for different voucher numbers."""
        # Configure the mock to return success for all calls
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Configure the mock to indicate that entries are balanced
        mock_verify_balanced_amounts.return_value = (True, 0.0, 1000.0, 1000.0)
        
        # Configure the mock rate limiter class to return our mock rate limiter
        mock_rate_limiter_class.return_value = self.rate_limiter
        
        # Create entries with different voucher numbers
        entries_group1 = self.entries.copy()
        
        entries_group2 = [
            {
                "voucher_no": "APA-0000502",
                "External_Document_No": "5224028808",
                "Document_Date": "2025-03-31",
                "description": "Test description 4",
                "debit": {
                    "account": "12345",
                    "department": "VCT.1234",
                    "amount": 400,
                    "currency": "USD"
                },
                "credit": {
                    "vendor_code": "V-VC12345",
                    "gl_account": "Vendor",
                    "department": "VCT.1234",
                    "amount": 400,
                    "currency": "USD"
                }
            },
            {
                "voucher_no": "APA-0000502",
                "External_Document_No": "5224028808",
                "Document_Date": "2025-03-31",
                "description": "Test description 5",
                "debit": {
                    "account": "12345",
                    "department": "VCT.1234",
                    "amount": 600,
                    "currency": "USD"
                },
                "credit": {
                    "vendor_code": "V-VC12345",
                    "gl_account": "Vendor",
                    "department": "VCT.1234",
                    "amount": 600,
                    "currency": "USD"
                }
            }
        ]
        
        # Process both groups of entries
        all_entries = entries_group1 + entries_group2
        success_count, failure_count, balanced_count, unbalanced_count = process_entries(
            all_entries, 
            self.access_token
        )
        
        # Verify that all entries were processed successfully
        self.assertEqual(success_count, 10)  # 5 debit lines + 5 credit lines
        self.assertEqual(failure_count, 0)
        self.assertEqual(balanced_count, 2)  # 2 groups of entries
        self.assertEqual(unbalanced_count, 0)
        
        # Extract the document numbers from the calls to post_journal_line
        doc_numbers = []
        for call in mock_post_journal_line.call_args_list:
            args, _ = call
            journal_line = args[0]
            doc_numbers.append((journal_line.get("Account_Type", ""), journal_line["Document_No"]))
        
        # Verify that the document numbers are as expected
        # Each group should have its own numbering sequence
        expected_doc_numbers = [
            # Group 1
            ("", "APA-0000501"),  # First debit line
            ("Vendor", "APA-0000501"),  # First credit line
            ("", "APA-0000501-1"),  # Second debit line
            ("Vendor", "APA-0000501"),  # Second credit line
            ("", "APA-0000501-2"),  # Third debit line
            ("Vendor", "APA-0000501"),  # Third credit line
            
            # Group 2
            ("", "APA-0000502"),  # First debit line
            ("Vendor", "APA-0000502"),  # First credit line
            ("", "APA-0000502-1"),  # Second debit line
            ("Vendor", "APA-0000502"),  # Second credit line
        ]
        
        # Sort both lists to ensure consistent comparison
        doc_numbers.sort()
        expected_doc_numbers.sort()
        
        self.assertEqual(doc_numbers, expected_doc_numbers)

if __name__ == '__main__':
    unittest.main()
