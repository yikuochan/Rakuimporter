#!/usr/bin/env python3
"""
Test for External_Document_No uniqueness in CSV to JSON conversion.

This test verifies that the CSV to JSON converter correctly makes External_Document_No values unique
by adding suffixes to duplicates and handling empty values.
"""

import os
import tempfile
import unittest
import json
import csv
import time
from csv_to_json_converter import convert_csv_to_json

class TestExternalDocumentNoUniqueness(unittest.TestCase):
    """Test case for External_Document_No uniqueness."""

    def setUp(self):
        """Set up test data."""
        # Create a temporary CSV file with test data
        self.temp_csv = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        self.temp_json = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        
        # Create CSV content with duplicate External_Document_No values
        csv_content = [
            ["伝票No.", "仕訳日", "Receipt/Invoice No.(明細)", "Receipt/Invoice Note(明細)", "G/L Account", "借方：勘定科目：会計連携項目", "借方：補助科目：会計連携項目", "換算前額", "単位", "借方：負担部門：会計連携項目", "申請者CD/支払先CD", "支払先CD", "フリー２(明細)", "借方：負担部門コード", "勘定奉行：伝票区切"],
            ["", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
            ["VPA-0000119", "2025/04/02", "2025/4/18", "First entry", "G/L Account", "72600-30", "", "158.99", "USD", "VCA.1342G", "10126", "", "", "VCA.1342G", ""],
            ["", "", "", "", "Vendor", "", "", "158.99", "USD", "VCA.1342G", "10126", "10126", "", "VCA.9999", ""],
            ["VPA-0000120", "2025/04/02", "2025/4/18", "Second entry - same External_Document_No", "G/L Account", "72600-30", "", "209.18", "USD", "VCA.1342G", "10126", "", "", "VCA.1342G", ""],
            ["", "", "", "", "Vendor", "", "", "209.18", "USD", "VCA.1342G", "10126", "10126", "", "VCA.9999", ""],
            ["VPA-0000121", "2025/04/02", "2025/4/18", "Third entry - same External_Document_No", "G/L Account", "72600-30", "", "40.00", "USD", "VCA.1342G", "10126", "", "", "VCA.1342G", ""],
            ["", "", "", "", "Vendor", "", "", "40.00", "USD", "VCA.1342G", "10126", "10126", "", "VCA.9999", ""],
            ["VPA-0000122", "2025/04/03", "", "Empty External_Document_No, should use transaction date", "G/L Account", "72600-30", "", "75.50", "USD", "VCA.1342G", "10126", "", "", "VCA.1342G", ""],
            ["", "", "", "", "Vendor", "", "", "75.50", "USD", "VCA.1342G", "10126", "10126", "", "VCA.9999", ""],
            ["VPA-0000123", "2025/04/03", "", "Another empty External_Document_No", "G/L Account", "72600-30", "", "120.75", "USD", "VCA.1342G", "10126", "", "", "VCA.1342G", ""],
            ["", "", "", "", "Vendor", "", "", "120.75", "USD", "VCA.1342G", "10126", "10126", "", "VCA.9999", ""],
            ["VPA-0000124", "", "", "Completely empty External_Document_No and transaction date", "", "72600-30", "", "90.25", "USD", "VCA.1342G", "10126", "", "", "VCA.1342G", ""],
            ["", "", "", "", "Vendor", "", "", "90.25", "USD", "VCA.1342G", "10126", "10126", "", "VCA.9999", ""],
        ]
        
        with open(self.temp_csv.name, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_content)
    
    def tearDown(self):
        """Clean up temporary files."""
        os.unlink(self.temp_csv.name)
        os.unlink(self.temp_json.name)
    
    def test_external_document_no_uniqueness(self):
        """Test that External_Document_No values are made unique."""
        # Convert CSV to JSON
        convert_csv_to_json(self.temp_csv.name, self.temp_json.name)
        
        # Load the JSON output
        with open(self.temp_json.name, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        # Extract External_Document_No values
        external_doc_nos = [entry["External_Document_No"] for entry in entries]
        
        # Check that all External_Document_No values are unique
        self.assertEqual(len(external_doc_nos), len(set(external_doc_nos)), 
                         "External_Document_No values should be unique")
        
        # Check that the first occurrence of "2025/4/18" has no suffix
        self.assertIn("2025/4/18", external_doc_nos)
        
        # Check that the second occurrence has "-2" suffix
        self.assertIn("2025/4/18-2", external_doc_nos)
        
        # Check that the third occurrence has "-3" suffix
        self.assertIn("2025/4/18-3", external_doc_nos)
        
        # Check that empty values use transaction date
        transaction_date_values = ["2025/04/03", "2025/04/03-2"]
        for value in transaction_date_values:
            self.assertTrue(any(doc_no == value for doc_no in external_doc_nos),
                           f"Expected to find '{value}' in External_Document_No values")
        
        # Check that completely empty values use "Empty-" prefix
        empty_values = [doc_no for doc_no in external_doc_nos if doc_no.startswith("Empty-")]
        self.assertTrue(len(empty_values) > 0, "Empty External_Document_No values should use 'Empty-' prefix")
        
        # Print all External_Document_No values for debugging
        print("\nExternal_Document_No values:")
        for i, doc_no in enumerate(external_doc_nos):
            print(f"  {i+1}. {doc_no}")

if __name__ == '__main__':
    unittest.main()
