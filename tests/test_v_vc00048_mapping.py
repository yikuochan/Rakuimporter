import unittest
import json
import os
import sys
from decimal import Decimal
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.process_japan_exports import create_journal_line, create_vct_responsibility_entries

class TestVVC00048Mapping(unittest.TestCase):
    """Test the V-VC00048 mapping to VCT for non-VCT cost centers."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample entry with V-VC00048 vendor code and non-VCT cost center
        self.entry_non_vct = {
            "voucher_no": "TEST-001",
            "description": "Test V-VC00048 mapping",
            "Document_Date": "2025/06/01",
            "External_Document_No": "EXT-001",
            "debit": {
                "amount": 1000.0,
                "currency": "USD",
                "department": "VCP.1234",
                "gl_account": "G/L Account",
                "account": "12345-67",
                "applicant_code": "EMP001"
            },
            "credit": {
                "amount": 1000.0,
                "currency": "USD",
                "department": "VCP.1234",
                "gl_account": "Vendor",
                "vendor_code": "V-VC00048",
                "applicant_code": "EMP001"
            }
        }

        # Sample entry with V-VC00048 vendor code and VCT cost center
        self.entry_vct = {
            "voucher_no": "TEST-002",
            "description": "Test V-VC00048 mapping",
            "Document_Date": "2025/06/01",
            "External_Document_No": "EXT-002",
            "debit": {
                "amount": 1000.0,
                "currency": "USD",
                "department": "VCT.1234",
                "gl_account": "G/L Account",
                "account": "12345-67",
                "applicant_code": "EMP001"
            },
            "credit": {
                "amount": 1000.0,
                "currency": "USD",
                "department": "VCT.1234",
                "gl_account": "Vendor",
                "vendor_code": "V-VC00048",
                "applicant_code": "EMP001"
            }
        }

        # Sample entry with non-V-VC00048 vendor code
        self.entry_other_vendor = {
            "voucher_no": "TEST-003",
            "description": "Test other vendor",
            "Document_Date": "2025/06/01",
            "External_Document_No": "EXT-003",
            "debit": {
                "amount": 1000.0,
                "currency": "USD",
                "department": "VCP.1234",
                "gl_account": "G/L Account",
                "account": "12345-67",
                "applicant_code": "EMP001"
            },
            "credit": {
                "amount": 1000.0,
                "currency": "USD",
                "department": "VCP.1234",
                "gl_account": "Vendor",
                "vendor_code": "OTHER-VENDOR",
                "applicant_code": "EMP001"
            }
        }

    def test_v_vc00048_mapping_non_vct(self):
        """Test that V-VC00048 is mapped to VCT for non-VCT cost centers."""
        # Create a credit journal line for the non-VCT entry
        credit_line = create_journal_line(self.entry_non_vct, "credit")
        
        # Verify that the Account_No is changed to VCT
        self.assertEqual(credit_line["Account_No"], "VCT")
        self.assertEqual(credit_line["Shortcut_Dimension_1_Code"], "VCP")
        self.assertEqual(credit_line["Shortcut_Dimension_2_Code"], "VCP.1234")

    def test_v_vc00048_no_mapping_vct(self):
        """Test that V-VC00048 is not mapped for VCT cost centers."""
        # Create a credit journal line for the VCT entry
        credit_line = create_journal_line(self.entry_vct, "credit")
        
        # Verify that the Account_No remains V-VC00048
        self.assertEqual(credit_line["Account_No"], "V-VC00048")
        self.assertEqual(credit_line["Shortcut_Dimension_1_Code"], "VCT")
        self.assertEqual(credit_line["Shortcut_Dimension_2_Code"], "VCT.1234")

    def test_other_vendor_no_mapping(self):
        """Test that other vendors are not mapped."""
        # Create a credit journal line for the other vendor entry
        credit_line = create_journal_line(self.entry_other_vendor, "credit")
        
        # Verify that the Account_No remains the same
        self.assertEqual(credit_line["Account_No"], "OTHER-VENDOR")
        self.assertEqual(credit_line["Shortcut_Dimension_1_Code"], "VCP")
        self.assertEqual(credit_line["Shortcut_Dimension_2_Code"], "VCP.1234")

    @patch('core.process_japan_exports.post_journal_line')
    def test_create_vct_responsibility_entries(self, mock_post_journal_line):
        """Test that VCT responsibility entries are created correctly."""
        # Mock the post_journal_line function to return success
        mock_post_journal_line.return_value = (True, {})
        
        # Create a mock rate limiter
        mock_rate_limiter = MagicMock()
        
        # Call the function with the non-VCT entry
        success_count, failure_count = create_vct_responsibility_entries(
            self.entry_non_vct, "fake_token", mock_rate_limiter, 3
        )
        
        # Verify that two entries were created successfully
        self.assertEqual(success_count, 2)
        self.assertEqual(failure_count, 0)
        
        # Verify that post_journal_line was called twice
        self.assertEqual(mock_post_journal_line.call_count, 2)
        
        # Get the arguments for the first call (debit line)
        debit_line = mock_post_journal_line.call_args_list[0][0][0]
        
        # Verify the debit line properties
        self.assertEqual(debit_line["Account_Type"], "G/L Account")
        self.assertEqual(debit_line["Account_No"], "18600-10")
        self.assertEqual(debit_line["Shortcut_Dimension_1_Code"], "VCT")
        self.assertEqual(debit_line["Shortcut_Dimension_2_Code"], "VCT.9999")
        self.assertEqual(debit_line["ShortcutDimCode3"], "VCP")  # Intercompany code set to original cost center
        self.assertEqual(debit_line["Amount"], 1000.0)
        
        # Get the arguments for the second call (credit line)
        credit_line = mock_post_journal_line.call_args_list[1][0][0]
        
        # Verify the credit line properties
        self.assertEqual(credit_line["Account_Type"], "Vendor")
        self.assertEqual(credit_line["Account_No"], "V-VC00048")
        self.assertEqual(credit_line["Shortcut_Dimension_1_Code"], "VCT")
        self.assertEqual(credit_line["Shortcut_Dimension_2_Code"], "VCT.9999")
        self.assertEqual(credit_line["ShortcutDimCode3"], "")  # Intercompany code empty for credit line
        self.assertEqual(credit_line["Amount"], -1000.0)  # Negative for credit

if __name__ == '__main__':
    unittest.main()
