#!/usr/bin/env python3
"""
Test cases for External_Document_No length limit fix

This test verifies that External_Document_No fields are properly truncated to 35 characters
to comply with Business Central API limits.
"""

import unittest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from core.csv_to_json_converter import convert_csv_to_json
from core.process_japan_exports import create_journal_line


class TestExternalDocumentNoLengthFix(unittest.TestCase):
    """Test cases for External_Document_No length limit fix"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_csv_content = '''伝票No.,仕訳日,申請日,仕訳データ生成日,勘定奉行：伝票区切,G/L Account,借方：勘定科目：会計連携項目,借方：補助科目：会計連携項目,換算前額,単位,借方：負担部門：会計連携項目,申請者CD/支払先CD,支払先CD,フリー２(明細),借方：負担部門コード,Note(明細),Receipt/Invoice #(明細),Receipt/Invoice No.(明細),Receipt/Invoice Note(明細),Remarks,備考
,,,,,,,,,,,,,,,,,,,
VPA-0000001,2025/06/01,2025/06/01,2025/06/01,1,G/L Account,72600-30,,100,NTD,VCT.1342G,10001,,Test description,1000,Note,INV001,This is a very long external document number that exceeds the 35 character limit and should be truncated,Test note,Test remarks,Test remarks
VPA-0000001,2025/06/01,2025/06/01,2025/06/01,2,Vendor,,,100,NTD,VCT.1342G,10001,10001,,1000,Note,INV001,This is a very long external document number that exceeds the 35 character limit and should be truncated,Test note,Test remarks,Test remarks'''

    def test_external_document_no_truncation_in_csv_converter(self):
        """Test that External_Document_No is truncated to 35 characters in CSV converter"""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_csv:
            temp_csv.write(self.test_csv_content)
            temp_csv_path = temp_csv.name

        # Create temporary JSON file path
        temp_json_path = temp_csv_path.replace('.csv', '.json')

        try:
            # Convert CSV to JSON
            entry_count = convert_csv_to_json(temp_csv_path, temp_json_path)
            
            # Verify conversion succeeded
            self.assertGreater(entry_count, 0)
            
            # Read the generated JSON
            with open(temp_json_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)
            
            # Verify entries were created
            self.assertGreater(len(entries), 0)
            
            # Check that External_Document_No is truncated to 35 characters
            for entry in entries:
                external_doc_no = entry.get('External_Document_No', '')
                self.assertLessEqual(len(external_doc_no), 35, 
                    f"External_Document_No '{external_doc_no}' exceeds 35 characters (length: {len(external_doc_no)})")
                
                # Verify the truncated value is correct
                if external_doc_no.startswith('This is a very long external'):
                    expected_truncated = 'This is a very long external docume'
                    self.assertEqual(external_doc_no, expected_truncated,
                        f"Expected truncated value '{expected_truncated}', got '{external_doc_no}'")

        finally:
            # Clean up temporary files
            if os.path.exists(temp_csv_path):
                os.unlink(temp_csv_path)
            if os.path.exists(temp_json_path):
                os.unlink(temp_json_path)

    def test_external_document_no_truncation_in_process_japan_exports(self):
        """Test that External_Document_No is truncated to 35 characters in process_japan_exports"""
        # Create test entry with long External_Document_No
        test_entry = {
            'voucher_no': 'VPA-0000001',
            'External_Document_No': 'This is a very long external document number that exceeds the 35 character limit and should be truncated',
            'Document_Date': '2025/06/01',
            'debit': {
                'gl_account': 'G/L Account',
                'account': '72600-30',
                'amount': 100,
                'currency': 'NTD',
                'department': 'VCT.1342G',
                'applicant_code': '10001',
                'vendor_code': '',
                'free_field': 'Test description',
                'department_code': '1000'
            },
            'credit': {
                'gl_account': 'Vendor',
                'account': '10001',
                'amount': 100,
                'currency': 'NTD',
                'department': 'VCT.1342G',
                'applicant_code': '10001',
                'vendor_code': '10001',
                'free_field': '',
                'department_code': '1000',
                'Remarks': 'Test remarks'
            }
        }

        # Create journal lines
        debit_line = create_journal_line(test_entry, 'debit')
        credit_line = create_journal_line(test_entry, 'credit')

        # Verify External_Document_No is truncated to 35 characters
        self.assertLessEqual(len(debit_line['External_Document_No']), 35,
            f"Debit line External_Document_No exceeds 35 characters: {debit_line['External_Document_No']}")
        self.assertLessEqual(len(credit_line['External_Document_No']), 35,
            f"Credit line External_Document_No exceeds 35 characters: {credit_line['External_Document_No']}")

        # Verify the truncated value is correct
        expected_truncated = 'This is a very long external docume'
        self.assertEqual(debit_line['External_Document_No'], expected_truncated)
        self.assertEqual(credit_line['External_Document_No'], expected_truncated)

    def test_external_document_no_no_truncation_when_within_limit(self):
        """Test that External_Document_No is not truncated when within 35 character limit"""
        # Create test entry with short External_Document_No
        test_entry = {
            'voucher_no': 'VPA-0000001',
            'External_Document_No': 'Short document number',  # 21 characters
            'Document_Date': '2025/06/01',
            'debit': {
                'gl_account': 'G/L Account',
                'account': '72600-30',
                'amount': 100,
                'currency': 'NTD',
                'department': 'VCT.1342G',
                'applicant_code': '10001',
                'vendor_code': '',
                'free_field': 'Test description',
                'department_code': '1000'
            },
            'credit': {
                'gl_account': 'Vendor',
                'account': '10001',
                'amount': 100,
                'currency': 'NTD',
                'department': 'VCT.1342G',
                'applicant_code': '10001',
                'vendor_code': '10001',
                'free_field': '',
                'department_code': '1000',
                'Remarks': 'Test remarks'
            }
        }

        # Create journal lines
        debit_line = create_journal_line(test_entry, 'debit')
        credit_line = create_journal_line(test_entry, 'credit')

        # Verify External_Document_No is not truncated
        self.assertEqual(debit_line['External_Document_No'], 'Short document number')
        self.assertEqual(credit_line['External_Document_No'], 'Short document number')

    def test_external_document_no_exactly_35_characters(self):
        """Test that External_Document_No with exactly 35 characters is not truncated"""
        # Create test entry with exactly 35 character External_Document_No
        external_doc_no_35_chars = 'This is exactly thirty-five chars!!'  # Exactly 35 characters
        self.assertEqual(len(external_doc_no_35_chars), 35)

        test_entry = {
            'voucher_no': 'VPA-0000001',
            'External_Document_No': external_doc_no_35_chars,
            'Document_Date': '2025/06/01',
            'debit': {
                'gl_account': 'G/L Account',
                'account': '72600-30',
                'amount': 100,
                'currency': 'NTD',
                'department': 'VCT.1342G',
                'applicant_code': '10001',
                'vendor_code': '',
                'free_field': 'Test description',
                'department_code': '1000'
            },
            'credit': {
                'gl_account': 'Vendor',
                'account': '10001',
                'amount': 100,
                'currency': 'NTD',
                'department': 'VCT.1342G',
                'applicant_code': '10001',
                'vendor_code': '10001',
                'free_field': '',
                'department_code': '1000',
                'Remarks': 'Test remarks'
            }
        }

        # Create journal lines
        debit_line = create_journal_line(test_entry, 'debit')
        credit_line = create_journal_line(test_entry, 'credit')

        # Verify External_Document_No is not truncated
        self.assertEqual(debit_line['External_Document_No'], external_doc_no_35_chars)
        self.assertEqual(credit_line['External_Document_No'], external_doc_no_35_chars)
        self.assertEqual(len(debit_line['External_Document_No']), 35)
        self.assertEqual(len(credit_line['External_Document_No']), 35)


if __name__ == '__main__':
    unittest.main()
