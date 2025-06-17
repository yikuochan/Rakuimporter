#!/usr/bin/env python3
"""
Test to verify the fix for document number duplication in consolidated debit lines.

This test verifies that the document number duplication fix works for all document numbers,
not just specific ones. The fix ensures that each debit line has a unique document number
by appending a suffix (-1, -2, etc.) to duplicate document numbers.
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from core.process_japan_exports import process_entries, RateLimiter

class TestDocumentNoDuplicateFixVerification(unittest.TestCase):
    """Test case to verify the document number duplication fix for problematic document numbers."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock rate limiter
        self.rate_limiter = MagicMock(spec=RateLimiter)
        
        # Create a mock access token
        self.access_token = "mock_access_token"
        
        # Create mock entries with the problematic document numbers
        self.entries_apa_0000401 = [
            {
                "voucher_no": "APA-0000401",
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
                "voucher_no": "APA-0000401",
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
                "voucher_no": "APA-0000401",
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
        
        self.entries_apa_0000451 = [
            {
                "voucher_no": "APA-0000451",
                "External_Document_No": "5224028808",
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
                "voucher_no": "APA-0000451",
                "External_Document_No": "5224028808",
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
            }
        ]

    @patch('core.process_japan_exports.post_journal_line')
    @patch('core.process_japan_exports.verify_balanced_amounts')
    @patch('core.process_japan_exports.RateLimiter')
    def test_document_no_duplicate_fix_for_apa_0000401(self, mock_rate_limiter_class, mock_verify_balanced_amounts, mock_post_journal_line):
        """Test that document numbers are modified correctly for APA-0000401."""
        # Configure the mock to return success for all calls
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Configure the mock to indicate that entries are balanced
        mock_verify_balanced_amounts.return_value = (True, 0.0, 1000.0, 1000.0)
        
        # Configure the mock rate limiter class to return our mock rate limiter
        mock_rate_limiter_class.return_value = self.rate_limiter
        
        # Process the entries
        success_count, failure_count, balanced_count, unbalanced_count = process_entries(
            self.entries_apa_0000401, 
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
            ("", "APA-0000401"),  # First debit line
            ("Vendor", "APA-0000401"),  # First credit line
            ("", "APA-0000401-1"),  # Second debit line
            ("Vendor", "APA-0000401"),  # Second credit line
            ("", "APA-0000401-2"),  # Third debit line
            ("Vendor", "APA-0000401"),  # Third credit line
        ]
        
        # Sort both lists to ensure consistent comparison
        doc_numbers.sort()
        expected_doc_numbers.sort()
        
        self.assertEqual(doc_numbers, expected_doc_numbers)

    @patch('core.process_japan_exports.post_journal_line')
    @patch('core.process_japan_exports.verify_balanced_amounts')
    @patch('core.process_japan_exports.RateLimiter')
    def test_document_no_duplicate_fix_for_apa_0000451(self, mock_rate_limiter_class, mock_verify_balanced_amounts, mock_post_journal_line):
        """Test that document numbers are modified correctly for APA-0000451."""
        # Configure the mock to return success for all calls
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Configure the mock to indicate that entries are balanced
        mock_verify_balanced_amounts.return_value = (True, 0.0, 800.0, 800.0)
        
        # Configure the mock rate limiter class to return our mock rate limiter
        mock_rate_limiter_class.return_value = self.rate_limiter
        
        # Process the entries
        success_count, failure_count, balanced_count, unbalanced_count = process_entries(
            self.entries_apa_0000451, 
            self.access_token
        )
        
        # Verify that all entries were processed successfully
        self.assertEqual(success_count, 4)  # 2 debit lines + 2 credit lines
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
        # Second debit line should have a suffix appended
        # All credit lines should use the original document number
        expected_doc_numbers = [
            ("", "APA-0000451"),  # First debit line
            ("Vendor", "APA-0000451"),  # First credit line
            ("", "APA-0000451-1"),  # Second debit line
            ("Vendor", "APA-0000451"),  # Second credit line
        ]
        
        # Sort both lists to ensure consistent comparison
        doc_numbers.sort()
        expected_doc_numbers.sort()
        
        self.assertEqual(doc_numbers, expected_doc_numbers)

    @patch('core.process_japan_exports.post_journal_line')
    @patch('core.process_japan_exports.verify_balanced_amounts')
    @patch('core.process_japan_exports.RateLimiter')
    def test_document_no_duplicate_fix_for_both_problematic_numbers(self, mock_rate_limiter_class, mock_verify_balanced_amounts, mock_post_journal_line):
        """Test that document numbers are modified correctly when both problematic document numbers are present."""
        # Configure the mock to return success for all calls
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Configure the mock to indicate that entries are balanced
        mock_verify_balanced_amounts.return_value = (True, 0.0, 1800.0, 1800.0)
        
        # Configure the mock rate limiter class to return our mock rate limiter
        mock_rate_limiter_class.return_value = self.rate_limiter
        
        # Combine both sets of entries
        combined_entries = self.entries_apa_0000401 + self.entries_apa_0000451
        
        # Process the entries
        success_count, failure_count, balanced_count, unbalanced_count = process_entries(
            combined_entries, 
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
        expected_doc_numbers = [
            # APA-0000401 group
            ("", "APA-0000401"),  # First debit line
            ("Vendor", "APA-0000401"),  # First credit line
            ("", "APA-0000401-1"),  # Second debit line
            ("Vendor", "APA-0000401"),  # Second credit line
            ("", "APA-0000401-2"),  # Third debit line
            ("Vendor", "APA-0000401"),  # Third credit line
            
            # APA-0000451 group
            ("", "APA-0000451"),  # First debit line
            ("Vendor", "APA-0000451"),  # First credit line
            ("", "APA-0000451-1"),  # Second debit line
            ("Vendor", "APA-0000451"),  # Second credit line
        ]
        
        # Sort both lists to ensure consistent comparison
        doc_numbers.sort()
        expected_doc_numbers.sort()
        
        self.assertEqual(doc_numbers, expected_doc_numbers)

    @patch('core.process_japan_exports.post_journal_line')
    @patch('core.process_japan_exports.verify_balanced_amounts')
    @patch('core.process_japan_exports.RateLimiter')
    def test_document_no_duplicate_fix_for_any_document_number(self, mock_rate_limiter_class, mock_verify_balanced_amounts, mock_post_journal_line):
        """Test that document numbers are modified correctly for any document number."""
        # Configure the mock to return success for all calls
        mock_post_journal_line.return_value = (True, {"success": True})
        
        # Configure the mock to indicate that entries are balanced
        mock_verify_balanced_amounts.return_value = (True, 0.0, 1000.0, 1000.0)
        
        # Configure the mock rate limiter class to return our mock rate limiter
        mock_rate_limiter_class.return_value = self.rate_limiter
        
        # Create entries with random document numbers
        entries_random = [
            {
                "voucher_no": "XYZ-0000123",
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
                "voucher_no": "XYZ-0000123",
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
                "voucher_no": "XYZ-0000123",
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
        
        # Process the entries
        success_count, failure_count, balanced_count, unbalanced_count = process_entries(
            entries_random, 
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
            ("", "XYZ-0000123"),  # First debit line
            ("Vendor", "XYZ-0000123"),  # First credit line
            ("", "XYZ-0000123-1"),  # Second debit line
            ("Vendor", "XYZ-0000123"),  # Second credit line
            ("", "XYZ-0000123-2"),  # Third debit line
            ("Vendor", "XYZ-0000123"),  # Third credit line
        ]
        
        # Sort both lists to ensure consistent comparison
        doc_numbers.sort()
        expected_doc_numbers.sort()
        
        self.assertEqual(doc_numbers, expected_doc_numbers)

if __name__ == '__main__':
    unittest.main()
