#!/usr/bin/env python3
"""
Unified CSV to JSON Converter

This unified converter replaces both csv_to_json_converter.py and csv_to_json_converter_enhanced.py.
It produces individual entries for all transaction types, eliminating the need for separate 
VCT consolidation processes.

Key principles:
1. Single processing pipeline for all entry types
2. No consolidation at CSV conversion stage
3. All entries are individual entries
4. VCT logic handled downstream in API processing
5. Consistent entry structure across all types
"""

import csv
import json
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.currency_converter import convert_amount, get_region_currency
from core.charset_converter import convert_file as charset_convert_file

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("csv_to_json_converter_unified")

class UnifiedCSVToJSONConverter:
    """
    Unified converter that handles all CSV to JSON conversion needs.
    Produces individual entries only - no consolidation logic.
    """
    
    def __init__(self):
        """
        Initialize the unified converter.
        """
        self.processed_entries = []
        self.validation_errors = []
        
    def convert_csv_to_json(self, csv_file_path: str, output_file_path: str,
                           company_code: str = "VicOne") -> Dict[str, Any]:
        """
        Convert CSV file to JSON with individual entries.
        
        Args:
            csv_file_path: Path to input CSV file
            output_file_path: Path to output JSON file
            company_code: Company code for processing
            
        Returns:
            Dictionary with conversion results and statistics
        """
        logger.info(f"Starting unified CSV to JSON conversion: {csv_file_path}")
        
        # Validate input file
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        # Process CSV file
        try:
            # Convert charset if needed
            converted_csv_path = self._convert_charset_if_needed(csv_file_path)
            
            # Read and process CSV
            entries = self._process_csv_file(converted_csv_path, company_code)
            
            # Validate entries
            valid_entries = self._validate_entries(entries)
            
            # Save to JSON
            self._save_to_json(valid_entries, output_file_path)
            
            # Generate conversion report
            report = self._generate_conversion_report(csv_file_path, output_file_path, 
                                                    len(entries), len(valid_entries))
            
            logger.info(f"Conversion completed successfully. Processed {len(valid_entries)} entries.")
            return report
            
        except Exception as e:
            logger.error(f"Error during conversion: {str(e)}")
            raise
    
    def _convert_charset_if_needed(self, csv_file_path: str) -> str:
        """Convert charset if the file is not UTF-8."""
        try:
            # Try to read as UTF-8 first
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                f.read(100)  # Read a small portion to test
            return csv_file_path
        except UnicodeDecodeError:
            # Convert charset
            logger.info("Converting charset to UTF-8")
            converted_path = csv_file_path.replace('.csv', '_utf8.csv')
            # Use the charset converter function
            from core.charset_converter import detect_encoding, convert_file
            encodings_to_try = detect_encoding(csv_file_path)
            success = convert_file(csv_file_path, converted_path, encodings_to_try)
            if success:
                return converted_path
            else:
                logger.warning("Charset conversion failed, using original file")
                return csv_file_path
    
    def _process_csv_file(self, csv_file_path: str, company_code: str) -> List[Dict[str, Any]]:
        """
        Process CSV file and create individual entries.
        
        Args:
            csv_file_path: Path to CSV file
            company_code: Company code
            
        Returns:
            List of individual journal entries
        """
        entries = []
        
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            # Detect delimiter
            sample = csvfile.read(1024)
            csvfile.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            for row_num, row in enumerate(reader, start=2):  # Start from 2 (header is row 1)
                try:
                    # Create individual entry from CSV row
                    entry = self._create_individual_entry(row, row_num, company_code)
                    if entry:
                        entries.append(entry)
                        
                except Exception as e:
                    logger.error(f"Error processing row {row_num}: {str(e)}")
                    self.validation_errors.append({
                        'row': row_num,
                        'error': str(e),
                        'data': dict(row)
                    })
        
        logger.info(f"Processed {len(entries)} entries from CSV")
        return entries
    
    
    def _create_individual_entry(self, row: Dict[str, str], row_num: int, 
                               company_code: str) -> Optional[Dict[str, Any]]:
        """
        Create an individual journal entry from a CSV row.
        
        Args:
            row: CSV row data
            row_num: Row number for error reporting
            company_code: Company code
            
        Returns:
            Individual journal entry or None if invalid
        """
        try:
            # Extract basic information
            voucher_no = self._clean_string(row.get('伝票番号', ''))
            document_date = self._parse_date(row.get('伝票日付', ''))
            external_doc_no = self._clean_string(row.get('外部証憑番号', ''))
            description = self._clean_string(row.get('摘要', ''))
            
            # Validate required fields
            if not voucher_no:
                logger.warning(f"Row {row_num}: Missing voucher number")
                return None
            
            # Extract debit information
            debit_account = self._clean_string(row.get('借方勘定科目', ''))
            debit_amount = self._parse_amount(row.get('借方金額', '0'))
            debit_currency = self._clean_string(row.get('借方通貨', 'NTD'))
            
            # Extract credit information
            credit_account = self._clean_string(row.get('貸方勘定科目', ''))
            credit_amount = self._parse_amount(row.get('貸方金額', '0'))
            credit_currency = self._clean_string(row.get('貸方通貨', 'NTD'))
            
            # Extract department and other fields
            department = self._clean_string(row.get('部門', ''))
            department_code = self._extract_department_code(department)
            applicant_code = self._clean_string(row.get('申請者コード', ''))
            
            # Extract vendor information
            vendor_code = self._clean_string(row.get('仕入先コード', ''))
            
            # Extract additional fields
            receipt_note = self._clean_string(row.get('Receipt/Invoice Note(明細)', ''))
            free_field = self._clean_string(row.get('自由項目', ''))
            remarks = self._clean_string(row.get('備考', ''))
            
            # Determine account types
            debit_gl_account = self._determine_gl_account_type(debit_account)
            credit_gl_account = self._determine_gl_account_type(credit_account)
            
            # Create individual entry structure
            entry = {
                "voucher_no": voucher_no,
                "Document_Date": document_date,
                "External_Document_No": external_doc_no,
                "description": description,
                "debit": {
                    "account": debit_account,
                    "amount": float(debit_amount),
                    "currency": debit_currency,
                    "department": department,
                    "department_code": department_code,
                    "applicant_code": applicant_code,
                    "gl_account": debit_gl_account,
                    "Receipt/Invoice Note(明細)": receipt_note,
                    "free_field": free_field
                },
                "credit": {
                    "account": credit_account,
                    "amount": float(credit_amount),
                    "currency": credit_currency,
                    "department": department,
                    "department_code": department_code,
                    "vendor_code": vendor_code,
                    "gl_account": credit_gl_account,
                    "account_source": self._determine_account_source(credit_account, vendor_code),
                    "Remarks": remarks,
                    "備考": remarks,
                    "consolidated": False  # All entries are individual
                }
            }
            
            # Apply currency conversion if needed
            entry = self._apply_currency_conversion(entry, company_code)
            
            return entry
            
        except Exception as e:
            logger.error(f"Error creating entry from row {row_num}: {str(e)}")
            return None
    
    def _clean_string(self, value: str) -> str:
        """Clean and normalize string values."""
        if not value:
            return ""
        return str(value).strip()
    
    def _parse_date(self, date_str: str) -> str:
        """Parse and format date string."""
        if not date_str:
            return datetime.now().strftime("%Y/%m/%d")
        
        # Try different date formats
        date_formats = [
            "%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
            "%Y年%m月%d日", "%m月%d日"
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                return parsed_date.strftime("%Y/%m/%d")
            except ValueError:
                continue
        
        # If no format matches, return current date
        logger.warning(f"Could not parse date: {date_str}, using current date")
        return datetime.now().strftime("%Y/%m/%d")
    
    def _parse_amount(self, amount_str: str) -> Decimal:
        """Parse amount string to Decimal."""
        if not amount_str:
            return Decimal('0')
        
        # Clean amount string
        cleaned = str(amount_str).replace(',', '').replace('¥', '').replace('$', '').strip()
        
        try:
            return Decimal(cleaned).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except:
            logger.warning(f"Could not parse amount: {amount_str}, using 0")
            return Decimal('0')
    
    def _extract_department_code(self, department: str) -> str:
        """Extract department code from department string."""
        if not department:
            return ""
        
        # Department format is usually like "VCP.1234" or "VCT.5678"
        if '.' in department:
            return department
        else:
            # If no dot, assume it's just the code
            return department
    
    def _determine_gl_account_type(self, account: str) -> str:
        """Determine GL account type based on account code."""
        if not account:
            return "G/L Account"
        
        # Vendor accounts typically start with 'V-'
        if account.startswith('V-'):
            return "Vendor"
        
        # Customer accounts typically start with 'C-'
        if account.startswith('C-'):
            return "Customer"
        
        # Bank accounts typically contain 'BANK' or start with specific codes
        if 'BANK' in account.upper() or account.startswith(('1110', '1120')):
            return "Bank Account"
        
        # Default to G/L Account
        return "G/L Account"
    
    def _determine_account_source(self, account: str, vendor_code: str) -> str:
        """Determine the source of the account."""
        if vendor_code and account.startswith('V-'):
            return "vendor_code"
        return "account_code"
    
    def _apply_currency_conversion(self, entry: Dict[str, Any], company_code: str) -> Dict[str, Any]:
        """Apply currency conversion if needed."""
        try:
            # Get currencies
            debit_currency = entry['debit']['currency']
            credit_currency = entry['credit']['currency']
            
            # Convert debit amount if not in base currency
            if debit_currency != 'NTD':
                original_amount = entry['debit']['amount']
                converted_amount, success = convert_amount(
                    original_amount, debit_currency, 'NTD', company_code
                )
                if success:
                    entry['debit']['amount'] = float(converted_amount)
                    entry['debit']['original_currency'] = debit_currency
                    entry['debit']['original_amount'] = original_amount
                    entry['debit']['currency'] = 'NTD'
            
            # Convert credit amount if not in base currency
            if credit_currency != 'NTD':
                original_amount = entry['credit']['amount']
                converted_amount, success = convert_amount(
                    original_amount, credit_currency, 'NTD', company_code
                )
                if success:
                    entry['credit']['amount'] = float(converted_amount)
                    entry['credit']['original_currency'] = credit_currency
                    entry['credit']['original_amount'] = original_amount
                    entry['credit']['currency'] = 'NTD'
            
        except Exception as e:
            logger.warning(f"Currency conversion failed for voucher {entry['voucher_no']}: {str(e)}")
        
        return entry
    
    def _validate_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate entries and filter out invalid ones."""
        valid_entries = []
        
        for entry in entries:
            if self._validate_single_entry(entry):
                valid_entries.append(entry)
        
        logger.info(f"Validated {len(valid_entries)} out of {len(entries)} entries")
        return valid_entries
    
    def _validate_single_entry(self, entry: Dict[str, Any]) -> bool:
        """Validate a single entry."""
        try:
            # Check required fields
            if not entry.get('voucher_no'):
                logger.warning("Entry missing voucher number")
                return False
            
            # Check amounts
            debit_amount = entry.get('debit', {}).get('amount', 0)
            credit_amount = entry.get('credit', {}).get('amount', 0)
            
            if debit_amount <= 0 and credit_amount <= 0:
                logger.warning(f"Entry {entry['voucher_no']} has no valid amounts")
                return False
            
            # Check account codes
            debit_account = entry.get('debit', {}).get('account', '')
            credit_account = entry.get('credit', {}).get('account', '')
            
            if not debit_account and not credit_account:
                logger.warning(f"Entry {entry['voucher_no']} has no account codes")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating entry: {str(e)}")
            return False
    
    def _save_to_json(self, entries: List[Dict[str, Any]], output_file_path: str):
        """Save entries to JSON file."""
        try:
            # Ensure output directory exists (handle case where dirname is empty)
            output_dir = os.path.dirname(output_file_path)
            if output_dir:  # Only create directory if dirname is not empty
                os.makedirs(output_dir, exist_ok=True)
            
            # Save to JSON
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Saved {len(entries)} entries to {output_file_path}")
            
        except Exception as e:
            logger.error(f"Error saving JSON file: {str(e)}")
            raise
    
    def _generate_conversion_report(self, input_file: str, output_file: str,
                                  total_rows: int, valid_entries: int) -> Dict[str, Any]:
        """Generate conversion report."""
        return {
            "input_file": input_file,
            "output_file": output_file,
            "conversion_time": datetime.now().isoformat(),
            "total_rows_processed": total_rows,
            "valid_entries_created": valid_entries,
            "validation_errors": len(self.validation_errors),
            "success_rate": (valid_entries / total_rows * 100) if total_rows > 0 else 0,
            "errors": self.validation_errors[:10]  # First 10 errors for review
        }


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified CSV to JSON Converter')
    parser.add_argument('input_csv', help='Input CSV file path')
    parser.add_argument('output_json', help='Output JSON file path')
    parser.add_argument('--company', default='VicOne', help='Company code')
    parser.add_argument('--report', help='Generate conversion report to specified file')
    
    args = parser.parse_args()
    
    # Create converter
    converter = UnifiedCSVToJSONConverter()
    
    try:
        # Convert CSV to JSON
        report = converter.convert_csv_to_json(
            args.input_csv, 
            args.output_json, 
            args.company
        )
        
        # Save report if requested
        if args.report:
            with open(args.report, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"Conversion report saved to: {args.report}")
        
        print(f"Conversion completed successfully!")
        print(f"Processed: {report['valid_entries_created']} entries")
        print(f"Success rate: {report['success_rate']:.1f}%")
        
    except Exception as e:
        print(f"Conversion failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
