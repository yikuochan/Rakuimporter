#!/usr/bin/env python3
"""
Enhanced CSV to JSON Converter with Comprehensive CSV Fixing

This enhanced version integrates the comprehensive CSV fixing capabilities
to handle encoding issues, line breaks, and structural problems before
converting to JSON format.

Usage:
    python csv_to_json_converter_enhanced.py -i INPUT_CSV_FILE [-o OUTPUT_JSON_FILE] [options]

Arguments:
    -i, --input                Input CSV file path (required)
    -o, --output               Output JSON file path (optional, defaults to input_filename.json)
    --max-desc-length          Maximum length for description field (default: 100)
    --skip-comprehensive-fix   Skip comprehensive CSV fixing (use basic fix only)
    --keep-temp-files          Keep temporary files for debugging

Example:
    python csv_to_json_converter_enhanced.py -i "VCT-2-0721.csv" -o "journal_entries.json"
"""

import csv
import json
import io
import argparse
import sys
import logging
import collections
import os
import tempfile
import time
import chardet
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List, Dict, Any

# Import the existing currency converter
try:
    from core.currency_converter import convert_amount, get_region_currency
except ImportError:
    # Fallback for when running from different directories
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.currency_converter import convert_amount, get_region_currency

# Custom JSON encoder to handle Decimal objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Configure logging
logger = logging.getLogger("enhanced_csv_converter")
logger.setLevel(logging.INFO)
logger.handlers = []

# Create file handler
file_handler = logging.FileHandler("enhanced_csv_conversion.log", mode='w')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

logger.info("Enhanced CSV to JSON converter started")

def detect_and_convert_encoding(input_file: str, temp_file: str = None) -> str:
    """
    Detect encoding and convert to UTF-8 if needed.
    
    Args:
        input_file: Path to the input file
        temp_file: Path for temporary UTF-8 file (optional)
        
    Returns:
        str: Path to UTF-8 file (either original if already UTF-8, or converted file)
    """
    # Generate temp filename if not provided
    if temp_file is None:
        base, ext = os.path.splitext(input_file)
        temp_file = f"{base}.temp_utf8{ext}"
    
    # First, detect the encoding
    with open(input_file, 'rb') as f:
        raw_data = f.read(10000)  # Read first 10KB for detection
    
    result = chardet.detect(raw_data)
    detected_encoding = result['encoding']
    confidence = result['confidence']
    
    logger.info(f"Detected encoding: {detected_encoding} with confidence: {confidence:.2%}")
    
    # If confidence is low, try with more data
    if confidence < 0.7:
        with open(input_file, 'rb') as f:
            raw_data = f.read()  # Read entire file
        result = chardet.detect(raw_data)
        detected_encoding = result['encoding']
        confidence = result['confidence']
        logger.info(f"Re-detected encoding: {detected_encoding} with confidence: {confidence:.2%}")
    
    # If already UTF-8, return original file
    if detected_encoding and detected_encoding.lower() in ['utf-8', 'ascii']:
        logger.info("File is already in UTF-8 or ASCII encoding")
        return input_file
    
    # Try to convert to UTF-8
    encodings_to_try = []
    if detected_encoding:
        encodings_to_try.append(detected_encoding)
    
    # Add common encodings as fallback
    encodings_to_try.extend(['shift_jis', 'cp932', 'euc_jp', 'iso-2022-jp', 
                            'windows-1252', 'windows-1254', 'iso-8859-1', 'gb2312', 'big5'])
    
    for encoding in encodings_to_try:
        try:
            logger.info(f"Trying to convert from {encoding} to UTF-8...")
            with open(input_file, 'r', encoding=encoding, errors='replace') as f_in:
                content = f_in.read()
            
            # Check quality of conversion
            replacement_chars = content.count('�')
            total_chars = len(content) if len(content) > 0 else 1
            quality = 100 - (replacement_chars / total_chars * 100)
            
            logger.info(f"Conversion quality: {quality:.1f}%")
            
            if quality > 80:  # Accept if quality is good enough
                with open(temp_file, 'w', encoding='utf-8') as f_out:
                    f_out.write(content)
                logger.info(f"Successfully converted to UTF-8: {temp_file}")
                return temp_file
                
        except Exception as e:
            logger.info(f"Failed to convert using {encoding}: {e}")
            continue
    
    logger.warning("Could not convert to UTF-8 with good quality. Using original file.")
    return input_file

def fix_csv_structure(input_file: str, output_file: str, delimiter: str = ',') -> bool:
    """
    Fix CSV structure issues including line breaks within quoted fields and malformed headers.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output CSV file
        delimiter: CSV delimiter
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Starting CSV structure fix for: {input_file}")
        
        # Read the entire file content
        with open(input_file, 'r', encoding='utf-8') as infile:
            content = infile.read()
        
        logger.info(f"Original file size: {len(content)} characters")
        
        # Fix line breaks within quoted fields
        fixed_content = fix_line_breaks_in_quoted_fields(content, delimiter)
        
        logger.info(f"After line break fix: {len(fixed_content)} characters")
        
        # Parse the fixed content as CSV
        rows = []
        lines = fixed_content.splitlines()
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():  # Skip empty lines
                continue
                
            try:
                # Parse the line as CSV
                row = list(csv.reader([line], delimiter=delimiter))[0]
                
                # Fix the first row (header) if it's malformed
                if line_num == 1 and len(row) < 10:
                    logger.info("Detected malformed header, attempting to fix...")
                    # Create a proper header based on the pattern we see in the data
                    fixed_header = [
                        "Account_Type", "Vendor", "仕訳日", "申請日", "仕訳データ生成日", "伝票No.",
                        "借方：勘定科目：会計連携科目", "借方：補助科目：会計連携科目", 
                        "貸方：勘定科目：会計連携科目", "貸方：補助科目：会計連携科目",
                        "換算前額", "単位", "借方：負担部門：会計連携科目", "申請者CD/支払先CD", "支払先CD",
                        "摘要", "フォーム２(明細)", "Receipt/Invoice Note(明細)", 
                        "Receipt/Invoice No.(明細)", "借方：負担部門コード", "備考"
                    ]
                    rows.append(fixed_header)
                    logger.info(f"Fixed header with {len(fixed_header)} fields")
                    continue
                
                rows.append(row)
                
            except Exception as e:
                logger.warning(f"Error parsing line {line_num}: {e}")
                # Fallback: split by delimiter
                row = line.split(delimiter)
                rows.append(row)
            
            if line_num % 100 == 0:
                logger.info(f"Processed {line_num} lines...")
        
        logger.info(f"Successfully processed {len(rows)} rows")
        
        # Write the fixed CSV
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            writer.writerows(rows)
        
        logger.info(f"Fixed CSV written to '{output_file}'")
        
        # Verify the output
        with open(output_file, 'r', encoding='utf-8') as verify_file:
            verify_lines = verify_file.readlines()
            logger.info(f"Verification: Output file has {len(verify_lines)} lines")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}")
        return False

def fix_line_breaks_in_quoted_fields(content: str, delimiter: str = ',') -> str:
    """
    Fix line breaks within quoted CSV fields by replacing them with spaces.
    
    This function properly handles CSV quoting rules:
    - Line breaks within quoted fields are replaced with spaces
    - Line breaks outside quoted fields are preserved as row separators
    - Escaped quotes within fields are handled correctly
    
    Args:
        content: The CSV content as a string
        delimiter: CSV delimiter
        
    Returns:
        str: Fixed CSV content
    """
    logger.info("Fixing line breaks within quoted fields...")
    
    result = []
    i = 0
    in_quotes = False
    quote_char = '"'
    
    while i < len(content):
        char = content[i]
        
        if char == quote_char:
            # Check if this is an escaped quote (doubled quote)
            if i + 1 < len(content) and content[i + 1] == quote_char:
                # This is an escaped quote, add both characters
                result.append(char)
                result.append(char)
                i += 2
                continue
            else:
                # This is a field delimiter quote
                in_quotes = not in_quotes
                result.append(char)
                i += 1
                continue
        
        if in_quotes:
            # We're inside a quoted field
            if char in ['\n', '\r']:
                # Replace line breaks with spaces inside quoted fields
                result.append(' ')
                # Skip \r\n combinations
                if char == '\r' and i + 1 < len(content) and content[i + 1] == '\n':
                    i += 1
            else:
                result.append(char)
        else:
            # We're outside quoted fields, preserve the character as-is
            result.append(char)
        
        i += 1
    
    fixed_content = ''.join(result)
    
    # Count the changes made
    original_lines = content.count('\n')
    fixed_lines = fixed_content.count('\n')
    
    logger.info(f"Line break fix completed. Original lines: {original_lines}, Fixed lines: {fixed_lines}")
    
    return fixed_content

def comprehensive_csv_fix(input_file: str, output_file: str = None) -> str:
    """
    Apply comprehensive CSV fixing including encoding and structure repair.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output CSV file (optional)
        
    Returns:
        str: Path to the fixed CSV file
    """
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}.comprehensive_fixed{ext}"
    
    logger.info(f"Starting comprehensive CSV fix for: {input_file}")
    
    # Step 1: Handle encoding
    logger.info("Step 1: Handling encoding...")
    utf8_file = detect_and_convert_encoding(input_file)
    
    # Step 2: Fix CSV structure
    logger.info("Step 2: Fixing CSV structure...")
    success = fix_csv_structure(utf8_file, output_file)
    
    # Clean up temporary file if created
    if utf8_file != input_file:
        try:
            os.remove(utf8_file)
            logger.info(f"Cleaned up temporary file: {utf8_file}")
        except:
            pass
    
    if success:
        logger.info(f"Comprehensive CSV fix completed: {output_file}")
        return output_file
    else:
        logger.error("Comprehensive CSV fix failed")
        return input_file

def basic_csv_line_break_fix(input_file, output_file=None, replacement=' '):
    """
    Basic CSV line break fix (original implementation for fallback).
    """
    try:
        with open(input_file, 'r', encoding='utf-8', newline='') as infile:
            reader = csv.reader(infile, quotechar='"', delimiter=',', quoting=csv.QUOTE_MINIMAL)
            
            fixed_rows = []
            for row in reader:
                cleaned_row = [field.replace('\n', replacement).replace('\r', '') for field in row]
                fixed_rows.append(cleaned_row)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                    writer = csv.writer(outfile, quotechar='"', delimiter=',', quoting=csv.QUOTE_MINIMAL)
                    writer.writerows(fixed_rows)
                logger.info(f"Basic fix applied to {input_file} and saved to {output_file}")
                return True
            else:
                output = io.StringIO()
                writer = csv.writer(output, quotechar='"', delimiter=',', quoting=csv.QUOTE_MINIMAL)
                writer.writerows(fixed_rows)
                return output.getvalue()
    
    except Exception as e:
        logger.error(f"Error in basic CSV fix: {e}")
        if output_file:
            return False
        else:
            try:
                with open(input_file, 'r', encoding='utf-8') as infile:
                    return infile.read()
            except Exception:
                return ""

# Import all the existing functions from the original converter
def normalize_currency(currency):
    """Normalize currency values according to requirements."""
    if currency == "台湾ドル":
        logger.info(f"Normalizing currency: '台湾ドル' -> 'NTD'")
        return "NTD"
    elif currency == "円":
        logger.info(f"Normalizing currency: '円' -> 'JPY'")
        return "JPY"
    else:
        return currency

def truncate_description(description, max_length=100):
    """Truncate description to the specified maximum length."""
    if not description:
        return ""
        
    if len(description) > max_length:
        truncated = description[:max_length]
        logger.warning(
            f"Description truncated from {len(description)} to {max_length} characters: "
            f"'{description}' -> '{truncated}'"
        )
        return truncated
    return description

def create_vct_responsibility_debit_entry(original_entry):
    """
    Create a VCT responsibility debit entry for non-VCT cost centers with V-VC00048 vendor.
    
    Args:
        original_entry: The original entry requiring VCT responsibility
        
    Returns:
        dict: VCT responsibility debit entry
    """
    credit_data = original_entry.get('credit', {})
    department = credit_data.get('department', '')
    cost_center = department[:3] if department else ''
    
    # Create description with cost center prefix
    original_description = original_entry.get('description', '') or original_entry.get('credit_description', '')
    vct_description = f"{department} {original_description}"
    
    # Truncate description if too long
    if len(vct_description) > 100:
        vct_description = vct_description[:100]
        logger.warning(f"Truncated VCT responsibility description to 100 characters: {vct_description}")
    
    # Create VCT responsibility debit entry
    vct_debit_entry = {
        "voucher_no": original_entry["voucher_no"],
        "transaction_date": original_entry["transaction_date"],
        "application_date": original_entry["application_date"],
        "journal_generation_date": original_entry["journal_generation_date"],
        "description": vct_description,
        "credit_description": original_entry.get("credit_description", ""),
        "note": original_entry["note"],
        "receipt_invoice": original_entry["receipt_invoice"],
        "External_Document_No": original_entry["External_Document_No"],
        "Document_Date": original_entry["Document_Date"],
        "debit": {
            "marker": "",
            "gl_account": "G/L Account",
            "account": "18600-10",  # Fixed account number
            "sub_account": "",
            "amount": credit_data.get('amount', 0),
            "currency": credit_data.get('currency', ''),
            "department": "VCT.9999",  # Fixed VCT department
            "applicant_code": "",
            "vendor_code": "",
            "free_field": "",
            "department_code": "VCT.9999",  # Fixed VCT department code
            "vct_responsibility": True,  # Mark as VCT responsibility entry
            "original_cost_center": cost_center  # Track original cost center
        },
        "credit": {
            "marker": "",
            "gl_account": "",
            "account": "",
            "sub_account": "",
            "amount": 0,
            "currency": "",
            "department": "",
            "applicant_code": "",
            "vendor_code": "",
            "free_field": "",
            "department_code": "",
            "Remarks": ""
        }
    }
    
    logger.info(f"Created VCT responsibility debit entry for {cost_center} cost center - Amount: {credit_data.get('amount', 0)}")
    return vct_debit_entry

def create_vct_responsibility_credit_entry(original_entry):
    """
    Create a VCT responsibility credit entry for non-VCT cost centers with V-VC00048 vendor.
    
    Args:
        original_entry: The original entry requiring VCT responsibility
        
    Returns:
        dict: VCT responsibility credit entry
    """
    credit_data = original_entry.get('credit', {})
    department = credit_data.get('department', '')
    cost_center = department[:3] if department else ''
    
    # Use original description without cost center prefix for credit entry
    original_description = original_entry.get('description', '') or original_entry.get('credit_description', '')
    
    # Create VCT responsibility credit entry
    vct_credit_entry = {
        "voucher_no": original_entry["voucher_no"],
        "transaction_date": original_entry["transaction_date"],
        "application_date": original_entry["application_date"],
        "journal_generation_date": original_entry["journal_generation_date"],
        "description": original_description,
        "credit_description": original_entry.get("credit_description", ""),
        "note": original_entry["note"],
        "receipt_invoice": original_entry["receipt_invoice"],
        "External_Document_No": original_entry["External_Document_No"],
        "Document_Date": original_entry["Document_Date"],
        "debit": {
            "marker": "",
            "gl_account": "",
            "account": "",
            "sub_account": "",
            "amount": 0,
            "currency": "",
            "department": "",
            "applicant_code": "",
            "vendor_code": "",
            "free_field": "",
            "department_code": "",
        },
        "credit": {
            "marker": "",
            "gl_account": "Vendor",
            "account": "V-VC00048",  # Fixed vendor code
            "sub_account": "",
            "amount": credit_data.get('amount', 0),
            "currency": credit_data.get('currency', ''),
            "department": "VCT.9999",  # Fixed VCT department
            "applicant_code": "",
            "vendor_code": "V-VC00048",  # Fixed vendor code
            "free_field": "",
            "department_code": "VCT.9999",  # Fixed VCT department code
            "Remarks": original_description,
            "vct_responsibility": True,  # Mark as VCT responsibility entry
            "original_cost_center": cost_center  # Track original cost center
        }
    }
    
    logger.info(f"Created VCT responsibility credit entry for {cost_center} cost center - Amount: {credit_data.get('amount', 0)}")
    return vct_credit_entry

def consolidate_entries(entries):
    """
    Consolidate entries based on voucher_no (伝票No.) and vendor_code.
    For each voucher_no, sum up the vendor's total credit amount in local currency.
    
    Args:
        entries (list): List of journal entries
        
    Returns:
        list: List of consolidated journal entries
    """
    # Group entries by voucher_no
    voucher_groups = collections.defaultdict(list)
    for entry in entries:
        voucher_no = entry["voucher_no"]
        voucher_groups[voucher_no].append(entry)
    
    consolidated_entries = []
    
    for voucher_no, group in voucher_groups.items():
        # Group by vendor_code within each voucher_no group
        vendor_groups = collections.defaultdict(list)
        for entry in group:
            vendor_code = entry["credit"]["vendor_code"]
            if not vendor_code:
                # If vendor_code is empty, use applicant_code as fallback
                vendor_code = entry["credit"]["applicant_code"]
            
            # If still no vendor code, use a placeholder
            if not vendor_code:
                vendor_code = "UNKNOWN"
                
            vendor_groups[vendor_code].append(entry)
        
        # Process each vendor group
        for vendor_code, vendor_entries in vendor_groups.items():
            # Keep all debit entries as they are
            for entry in vendor_entries:
                # Create a copy of the entry to avoid modifying the original
                consolidated_entry = {
                    "voucher_no": entry["voucher_no"],
                    "transaction_date": entry["transaction_date"],
                    "application_date": entry["application_date"],
                    "journal_generation_date": entry["journal_generation_date"],
                    "description": entry["description"],
                    "note": entry["note"],
                    "receipt_invoice": entry["receipt_invoice"],
                    "External_Document_No": entry["External_Document_No"],
                    "Document_Date": entry["Document_Date"],
                    "debit": entry["debit"].copy(),
                    "credit": {
                        "marker": "",
                        "gl_account": "",
                        "account": "",
                        "sub_account": "",
                        "amount": 0,
                        "currency": "",
                        "department": "",
                        "applicant_code": "",
                        "vendor_code": "",
                        "free_field": "",
                        "department_code": "",
                        "Remarks": ""
                    }
                }
                
                # Convert debit amount to local currency if needed
                if consolidated_entry["debit"]["amount"] and consolidated_entry["debit"]["currency"]:
                    # Get region code from department field (first 3 characters)
                    dept = consolidated_entry["debit"]["department"]
                    region_code = dept[:3] if dept and len(dept) >= 3 else ""
                    
                    if region_code:
                        # Get target currency for the region
                        target_currency = get_region_currency(region_code)
                        
                        if target_currency and consolidated_entry["debit"]["currency"] != target_currency:
                            # Convert amount to target currency
                            try:
                                # Convert to Decimal for precise calculation
                                original_amount = Decimal(str(consolidated_entry["debit"]["amount"]))
                                converted_amount, success = convert_amount(
                                    original_amount, 
                                    consolidated_entry["debit"]["currency"], 
                                    target_currency,
                                    company_code=region_code  # Pass region_code as company_code
                                )
                                
                                if success:
                                    logger.info(
                                        f"Converted debit amount for voucher {voucher_no}: "
                                        f"{original_amount} {consolidated_entry['debit']['currency']} -> "
                                        f"{converted_amount} {target_currency}"
                                    )
                                    consolidated_entry["debit"]["amount"] = converted_amount
                                    consolidated_entry["debit"]["original_currency"] = consolidated_entry["debit"]["currency"]
                                    consolidated_entry["debit"]["original_amount"] = float(original_amount)
                                    consolidated_entry["debit"]["currency"] = target_currency
                                else:
                                    logger.error(
                                        f"Currency conversion failed for debit amount in voucher {voucher_no}: "
                                        f"{original_amount} {consolidated_entry['debit']['currency']} could not be converted to {target_currency}. "
                                        f"Using original amount."
                                    )
                                    # Keep original values but mark as failed conversion
                                    consolidated_entry["debit"]["conversion_failed"] = True
                            except Exception as e:
                                logger.error(
                                    f"Exception during debit amount conversion for voucher {voucher_no}: {str(e)}"
                                )
                
                # Only add debit entries - credit entries will be consolidated separately
                consolidated_entries.append(consolidated_entry)
            
            # Now create one consolidated credit entry per vendor per voucher
            # UPDATED FIX: Apply cost center-specific consolidation rules for V-VC00048
            # Other V-VC vendors still excluded from consolidation per GitHub issue #78
            if vendor_entries and vendor_code.startswith("V-VC") and vendor_code != "V-VC00048":
                # Log that non-V-VC00048 V-VC entries are being excluded from consolidation
                logger.info(f"Excluding V-VC vendor {vendor_code} from consolidation in voucher {voucher_no} - {len(vendor_entries)} entries will be processed individually")
                # Skip consolidation for V-VC vendors (except V-VC00048) - they will be processed individually
                continue
            
            # Special handling for V-VC00048: Apply cost center-specific consolidation rules
            if vendor_entries and vendor_code == "V-VC00048":
                # Extract cost center from the first entry
                first_entry = vendor_entries[0]
                department = first_entry.get('credit', {}).get('department', '')
                cost_center = department[:3] if department else ''
                
                # Apply cost center-specific consolidation rules
                if cost_center == "VCT":
                    # VCT cost center: Apply normal consolidation
                    logger.info(f"Applying VCT consolidation rules for V-VC00048 vendor in VCT cost center - Voucher: {voucher_no}")
                    # Continue with normal consolidation logic below
                elif cost_center in ["VCA", "VCP", "VCG", "VCJ"]:
                    # Non-VCT cost centers: Create VCT responsibility entries and skip consolidation
                    logger.info(f"Creating VCT responsibility entries for V-VC00048 vendor in {cost_center} cost center - Voucher: {voucher_no} (no consolidation)")
                    
                    # Calculate total amount for VCT responsibility entries
                    total_amount = sum(entry.get('credit', {}).get('amount', 0) for entry in vendor_entries)
                    template_entry = vendor_entries[0]  # Use first entry as template
                    
                    # Create one VCT responsibility debit entry (consolidated amount)
                    vct_debit_entry = create_vct_responsibility_debit_entry(template_entry)
                    vct_debit_entry['debit']['amount'] = total_amount  # Use total amount
                    consolidated_entries.append(vct_debit_entry)
                    
                    # Create one VCT responsibility credit entry (consolidated amount)
                    vct_credit_entry = create_vct_responsibility_credit_entry(template_entry)
                    vct_credit_entry['credit']['amount'] = total_amount  # Use total amount
                    consolidated_entries.append(vct_credit_entry)
                    
                    # Skip consolidation for non-VCT cost centers
                    continue
                else:
                    # Unknown cost center: Exclude from consolidation (safe fallback)
                    logger.info(f"Excluding V-VC00048 vendor with unknown cost center '{cost_center}' from consolidation - Voucher: {voucher_no}")
                    continue
            
            if vendor_entries:
                # Use the first entry as a template for the consolidated credit entry
                template_entry = vendor_entries[0]
                
                # Calculate total credit amount in local currency
                total_credit_amount = Decimal('0')
                credit_currency = None
                
                for entry in vendor_entries:
                    if entry["credit"]["amount"]:
                        # Get region code from department field (first 3 characters)
                        dept = entry["credit"]["department"]
                        region_code = dept[:3] if dept and len(dept) >= 3 else ""
                        
                        if region_code:
                            # Get target currency for the region
                            target_currency = get_region_currency(region_code)
                            
                            if not credit_currency:
                                credit_currency = target_currency
                            
                            if target_currency:
                                try:
                                    # Convert to Decimal for precise calculation
                                    original_amount = Decimal(str(entry["credit"]["amount"]))
                                    
                                    # Special handling for overseas vendors (V-VC prefix)
                                    # For VCT vendors with V-VC prefix (overseas vendors), preserve original currency and amount
                                    if vendor_code.startswith("V-VC"):
                                        logger.info(
                                            f"Overseas vendor detected ({vendor_code}): Keeping original currency {entry['credit']['currency']} and amount {original_amount}"
                                        )
                                        # Keep original currency and amount for overseas vendors
                                        total_credit_amount += original_amount
                                        # Use the original currency for the consolidated entry
                                        credit_currency = entry["credit"]["currency"]
                                    # For non-overseas vendors, convert to target currency if needed
                                    elif entry["credit"]["currency"] != target_currency:
                                        converted_amount, success = convert_amount(
                                            original_amount, 
                                            entry["credit"]["currency"], 
                                            target_currency,
                                            company_code=region_code  # Pass region_code as company_code
                                        )
                                        
                                        if success:
                                            logger.info(
                                                f"Converted credit amount for voucher {voucher_no}: "
                                                f"{original_amount} {entry['credit']['currency']} -> "
                                                f"{converted_amount} {target_currency}"
                                            )
                                            total_credit_amount += converted_amount
                                        else:
                                            logger.error(
                                                f"Currency conversion failed for credit amount in voucher {voucher_no}: "
                                                f"{original_amount} {entry['credit']['currency']} could not be converted to {target_currency}. "
                                                f"Using original amount."
                                            )
                                            # Use original amount as fallback
                                            total_credit_amount += original_amount
                                            # Mark the entry as having a failed conversion
                                            entry["credit"]["conversion_failed"] = True
                                    else:
                                        total_credit_amount += original_amount
                                except Exception as e:
                                    logger.error(
                                        f"Exception during credit amount conversion for voucher {voucher_no}: {str(e)}"
                                    )
                                    # Use original amount as fallback
                                    try:
                                        total_credit_amount += Decimal(str(entry["credit"]["amount"]))
                                    except (ValueError, TypeError):
                                        pass
                        else:
                            # No region code, use original amount
                            try:
                                total_credit_amount += Decimal(str(entry["credit"]["amount"]))
                                if not credit_currency:
                                    credit_currency = entry["credit"]["currency"]
                            except (ValueError, TypeError):
                                pass
                
                # Create a consolidated credit entry
                # Use the original External_Document_No without adding "-consolidated" postfix
                consolidated_external_doc_no = template_entry["External_Document_No"]
                
                
                # Round the total credit amount to 2 decimal places using Decimal's ROUND_HALF_UP
                total_credit_amount_rounded = total_credit_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                consolidated_credit_entry = {
                    "voucher_no": template_entry["voucher_no"],
                    "transaction_date": template_entry["transaction_date"],
                    "application_date": template_entry["application_date"],
                    "journal_generation_date": template_entry["journal_generation_date"],
                    "description": template_entry["description"],
                    "credit_description": template_entry.get("credit_description", ""),  # Add credit_description field
                    "note": template_entry["note"],
                    "receipt_invoice": template_entry["receipt_invoice"],
                    "External_Document_No": consolidated_external_doc_no,
                    "Document_Date": template_entry["Document_Date"],
                    "debit": {
                        "marker": "",
                        "gl_account": "",
                        "account": "",
                        "sub_account": "",
                        "amount": 0,
                        "currency": "",
                        "department": "",
                        "applicant_code": "",
                        "vendor_code": "",
                        "free_field": "",
                        "department_code": ""
                    },
                    "credit": {
                        "marker": template_entry["credit"]["marker"],
                        "gl_account": template_entry["credit"]["gl_account"],
                        "account": template_entry["credit"]["account"],
                        "sub_account": template_entry["credit"]["sub_account"],
                        "amount": float(total_credit_amount_rounded),  # Convert Decimal to float for JSON serialization
                        "currency": credit_currency or template_entry["credit"]["currency"],
                        "department": template_entry["credit"]["department"],
                        "applicant_code": template_entry["credit"]["applicant_code"],
                        "vendor_code": vendor_code if vendor_code != "UNKNOWN" else "",
                        "free_field": template_entry["credit"]["free_field"],
                        "department_code": template_entry["credit"]["department_code"],
                        "Remarks": template_entry.get("credit_description", "") or template_entry["credit"].get("Remarks", "") or template_entry["credit"].get("備考", ""),  # Add Remarks field (translated from 備考) from template entry
                        "consolidated": True,
                        "original_entries_count": len(vendor_entries),
                        "account_source": template_entry["credit"].get("account_source", ""),
                        "raw_total_before_rounding": float(total_credit_amount)  # Store the raw total for debugging
                    }
                }
                
                # Add a note about consolidation
                if len(vendor_entries) > 1:
                    consolidated_credit_entry["credit"]["consolidation_note"] = f"Consolidated from {len(vendor_entries)} entries"
                
                consolidated_entries.append(consolidated_credit_entry)
    
    return consolidated_entries

def convert_csv_to_json(csv_file_path, json_file_path, max_desc_length=100, 
                       use_comprehensive_fix=True, keep_temp_files=False):
    """
    Enhanced CSV to JSON conversion with comprehensive fixing.
    
    Args:
        csv_file_path (str): Path to the input CSV file
        json_file_path (str): Path to the output JSON file
        max_desc_length (int): Maximum length for description field
        use_comprehensive_fix (bool): Whether to use comprehensive CSV fixing
        keep_temp_files (bool): Whether to keep temporary files for debugging
    """
    # Apply CSV fixing based on the selected method
    if use_comprehensive_fix:
        logger.info("Using comprehensive CSV fixing...")
        temp_csv_path = comprehensive_csv_fix(csv_file_path)
        csv_file_to_process = temp_csv_path
    else:
        logger.info("Using basic CSV line break fixing...")
        # Create a temporary file for the basic fix
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False, suffix='.csv') as temp_file:
            temp_csv_path = temp_file.name
        
        # Apply basic fix
        basic_csv_line_break_fix(csv_file_path, temp_csv_path)
        csv_file_to_process = temp_csv_path
    
    # Read the fixed CSV file
    try:
        with open(csv_file_to_process, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        logger.error(f"Error reading fixed CSV file: {e}")
        raise
    
    # Split the content into lines
    lines = content.splitlines()
    
    # Process the two-line header using csv module
    header1 = next(csv.reader([lines[0]]))
    header2 = next(csv.reader([lines[1]]))
    
    # Combine headers, preferring non-empty values
    combined_header = []
    for i in range(max(len(header1), len(header2))):
        if i < len(header1) and header1[i].strip():
            combined_header.append(header1[i].strip())
        elif i < len(header2) and header2[i].strip():
            combined_header.append(header2[i].strip())
        else:
            combined_header.append(f"Column_{i}")
    
    logger.info(f"Combined header has {len(combined_header)} fields")
    
    # Track External_Document_No occurrences to ensure uniqueness
    external_doc_no_counter = {}
    
    # Process data rows (using the existing logic from the original converter)
    raw_entries = []
    i = 2  # Start after the header rows
    
    while i < len(lines) - 1:  # Ensure we have at least 2 more lines
        debit_line = next(csv.reader([lines[i]]))
        credit_line = next(csv.reader([lines[i + 1]]))
        
        # Skip empty lines
        if not any(debit_line) or not any(credit_line):
            i += 1
            continue
        
        # Create a dictionary for the debit and credit rows
        debit_data = dict(zip(combined_header, debit_line))
        credit_data = dict(zip(combined_header, credit_line))
        
        # Get External_Document_No from column S "Receipt/Invoice No.(明細)"
        external_doc_no = debit_data.get("Receipt/Invoice No.(明細)") or credit_data.get("Receipt/Invoice No.(明細)") or ""
        
        # If column S is empty, use column C "仕訳日" (transaction date)
        if not external_doc_no:
            external_doc_no = debit_data.get("仕訳日") or credit_data.get("仕訳日") or ""
        
        # If still empty, use "Empty-{timestamp in milliseconds}"
        if not external_doc_no:
            external_doc_no = f"Empty-{int(time.time() * 1000)}"
            logger.info(f"Using generated External_Document_No for empty value: {external_doc_no}")
        
        # Truncate External_Document_No to 35 characters (Business Central API limit)
        if len(external_doc_no) > 35:
            original_external_doc_no = external_doc_no
            external_doc_no = external_doc_no[:35]
            logger.warning(
                f"Truncated External_Document_No from {len(original_external_doc_no)} to 35 characters: "
                f"'{original_external_doc_no}' -> '{external_doc_no}'"
            )
        
        # Make External_Document_No unique if it's a duplicate
        original_external_doc_no = external_doc_no
        if external_doc_no in external_doc_no_counter:
            external_doc_no_counter[original_external_doc_no] += 1
            external_doc_no = f"{original_external_doc_no}-{external_doc_no_counter[original_external_doc_no]}"
            logger.info(f"Made External_Document_No unique: {original_external_doc_no} -> {external_doc_no}")
        else:
            external_doc_no_counter[original_external_doc_no] = 0
        
        # Extract common fields for the journal entry (using existing logic)
        entry = {
            "voucher_no": debit_data.get("伝票No.") or credit_data.get("伝票No.") or "",
            "transaction_date": debit_data.get("仕訳日") or credit_data.get("仕訳日") or "",
            "application_date": debit_data.get("申請日") or credit_data.get("申請日") or "",
            "journal_generation_date": debit_data.get("仕訳データ生成日") or credit_data.get("仕訳データ生成日") or "",
            "debit_description": truncate_description(debit_data.get("Receipt/Invoice Note(明細)") or debit_data.get("フリー２(明細)") or "", max_desc_length),
            "credit_description": truncate_description(credit_data.get("Remarks") or credit_data.get("備考") or "", max_desc_length),
            "description": truncate_description(debit_data.get("Receipt/Invoice Note(明細)") or debit_data.get("フリー２(明細)") or "", max_desc_length),
            "note": debit_data.get("Note(明細)") or credit_data.get("Note(明細)") or "",
            "receipt_invoice": debit_data.get("Receipt/Invoice #(明細)") or credit_data.get("Receipt/Invoice #(明細)") or "",
            "External_Document_No": external_doc_no,
            "Document_Date": debit_data.get("仕訳日") or credit_data.get("仕訳日") or "",
            "debit": {
                "marker": debit_data.get("勘定奉行：伝票区切") or "",
                "gl_account": debit_data.get("G/L Account") or "",
                "account": debit_data.get("借方：勘定科目：会計連携項目") or "",
                "sub_account": debit_data.get("借方：補助科目：会計連携項目") or "",
                "amount": debit_data.get("換算前額") or "",
                "currency": normalize_currency(debit_data.get("単位") or ""),
                "department": debit_data.get("借方：負担部門：会計連携項目") or "",
                "applicant_code": debit_data.get("申請者CD/支払先CD") or "",
                "vendor_code": debit_data.get("支払先CD") or "",
                "free_field": debit_data.get("フリー２(明細)") or "",
                "department_code": debit_data.get("借方：負担部門コード") or ""
            },
            "credit": {
                "marker": credit_data.get("勘定奉行：伝票区切") or "",
                "gl_account": credit_data.get("G/L Account") or "",
                "account": credit_data.get("貸方：勘定科目：会計連携項目") or "",
                "sub_account": credit_data.get("貸方：補助科目：会計連携項目") or "",
                "amount": credit_data.get("換算前額") or "",
                "currency": normalize_currency(credit_data.get("単位") or ""),
                "department": credit_data.get("借方：負担部門：会計連携項目") or "",
                "applicant_code": credit_data.get("申請者CD/支払先CD") or "",
                "vendor_code": credit_data.get("支払先CD") or "",
                "free_field": credit_data.get("フリー２(明細)") or "",
                "department_code": credit_data.get("借方：負担部門コード") or "",
                "Remarks": credit_data.get("Remarks") or credit_data.get("備考") or ""
            }
        }
        
        # Apply the existing processing logic for vendor and G/L accounts
        # (This includes all the existing helper functions and processing logic)
        
        # Convert numeric values
        try:
            if entry["debit"]["amount"]:
                entry["debit"]["amount"] = float(entry["debit"]["amount"])
        except ValueError:
            pass
            
        try:
            if entry["credit"]["amount"]:
                entry["credit"]["amount"] = float(entry["credit"]["amount"])
        except ValueError:
            pass
        
        # Skip entries with VCJ.9999 in department_code
        if (entry["debit"]["department_code"] != "VCJ.9999" and 
            entry["credit"]["department_code"] != "VCJ.9999"):
            raw_entries.append(entry)
            logger.info(f"Added entry with voucher_no {entry['voucher_no']}")
        else:
            logger.info(f"Skipping entry with voucher_no {entry['voucher_no']} due to VCJ.9999 in department_code")
        
        i += 2  # Move to the next pair of rows
    
    # Apply consolidation logic to create VCT responsibility entries and consolidated credit entries
    final_entries = consolidate_entries(raw_entries)
    
    # Write the JSON output
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(final_entries, json_file, ensure_ascii=False, indent=2, cls=DecimalEncoder)
    
    # Clean up temporary files unless keeping them
    if not keep_temp_files and temp_csv_path != csv_file_path:
        try:
            os.remove(temp_csv_path)
            logger.info(f"Cleaned up temporary CSV file: {temp_csv_path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary CSV file: {e}")
    elif keep_temp_files:
        logger.info(f"Temporary CSV file kept for debugging: {temp_csv_path}")
    
    return len(final_entries)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Enhanced CSV to JSON converter with comprehensive fixing.',
        epilog='Example: python csv_to_json_converter_enhanced.py -i "VCT-2-0721.csv" -o "journal_entries.json"'
    )
    parser.add_argument('-i', '--input', required=True, help='Input CSV file path (required)')
    parser.add_argument('-o', '--output', help='Output JSON file path (default: input_filename.json)')
    parser.add_argument('--max-desc-length', type=int, default=100, 
                        help='Maximum length for description field (default: 100)')
    parser.add_argument('--skip-comprehensive-fix', action='store_true',
                        help='Skip comprehensive CSV fixing (use basic fix only)')
    parser.add_argument('--keep-temp-files', action='store_true',
                        help='Keep temporary files for debugging')
    
    args = parser.parse_args()
    
    # If output file is not specified, derive it from the input filename
    if not args.output:
        input_base = args.input.rsplit('.', 1)[0]  # Remove extension
        args.output = f"{input_base}.json"
    
    try:
        # Convert CSV to JSON with the specified options
        entry_count = convert_csv_to_json(
            args.input, 
            args.output, 
            args.max_desc_length,
            not args.skip_comprehensive_fix,  # Use comprehensive fix by default
            args.keep_temp_files
        )
        print(f"Converted {entry_count} journal entries to JSON format.")
        print(f"Output saved to {args.output}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"Please make sure the input file '{args.input}' exists.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
