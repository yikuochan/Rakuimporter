#!/usr/bin/env python3
"""
CSV to JSON Converter for General Journal Entries

This script converts a General Journal CSV file to JSON format.
It processes the CSV file with a two-line header and pairs of debit/credit entries,
converting them into a structured JSON format.

The script can also handle CSV files with line breaks within quoted fields,
which can cause parsing errors. It can automatically fix these issues by replacing
line breaks with spaces or another specified character.

Usage:
    python csv_to_json_converter.py -i INPUT_CSV_FILE [-o OUTPUT_JSON_FILE] [--no-fix-line-breaks] [--line-break-replacement CHAR]

Arguments:
    -i, --input                Input CSV file path (required)
    -o, --output               Output JSON file path (optional, defaults to input_filename.json)
    --no-fix-line-breaks       Disable fixing line breaks in CSV fields (enabled by default)
    --line-break-replacement   Character to replace line breaks with (default: space)
    --max-desc-length          Maximum length for description field (default: 100)

Example:
    python csv_to_json_converter.py -i "Raku export.csv" -o "journal_entries.json"
    python csv_to_json_converter.py -i "Problematic export.csv" --line-break-replacement "|"
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
from currency_converter import convert_amount, get_region_currency

# Configure logging
# Reset any existing handlers to avoid duplicates
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Create logger
logger = logging.getLogger("csv_converter")
logger.setLevel(logging.INFO)
logger.handlers = []  # Remove any existing handlers

# Create file handler
file_handler = logging.FileHandler("csv_conversion.log", mode='w')
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Add a startup message to verify logging is working
logger.info("CSV to JSON converter started")

def fix_csv_line_breaks(input_file, output_file=None, replacement=' '):
    """
    Fix CSV file by replacing line breaks within fields with the specified replacement character.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str, optional): Path to the output CSV file. If None, returns the fixed content as a string.
        replacement (str): Character to replace line breaks with (default: space)
        
    Returns:
        str or bool: If output_file is None, returns the fixed content as a string.
                    Otherwise, returns True if successful, False if an error occurred.
    """
    try:
        # Open the input file with proper newline handling
        with open(input_file, 'r', encoding='utf-8', newline='') as infile:
            # Create a CSV reader that can handle quoted fields with line breaks
            reader = csv.reader(infile, quotechar='"', delimiter=',', quoting=csv.QUOTE_MINIMAL)
            
            # Process each row
            fixed_rows = []
            for row in reader:
                # Replace line breaks within each field
                cleaned_row = [field.replace('\n', replacement).replace('\r', '') for field in row]
                fixed_rows.append(cleaned_row)
            
            # If output_file is provided, write to file
            if output_file:
                with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                    writer = csv.writer(outfile, quotechar='"', delimiter=',', quoting=csv.QUOTE_MINIMAL)
                    writer.writerows(fixed_rows)
                logger.info(f"Fixed line breaks in {input_file} and saved to {output_file}")
                return True
            else:
                # Return the fixed content as a string
                output = io.StringIO()
                writer = csv.writer(output, quotechar='"', delimiter=',', quoting=csv.QUOTE_MINIMAL)
                writer.writerows(fixed_rows)
                return output.getvalue()
    
    except Exception as e:
        error_msg = f"Error fixing line breaks in CSV file: {e}"
        logger.error(error_msg)
        if output_file:
            return False
        else:
            # Return the original content if there's an error
            try:
                with open(input_file, 'r', encoding='utf-8') as infile:
                    return infile.read()
            except Exception:
                return ""

def normalize_currency(currency):
    """
    Normalize currency values according to requirements.
    
    Args:
        currency (str): The currency value to normalize
        
    Returns:
        str: The normalized currency value
    """
    if currency == "台湾ドル":
        logger.info(f"Normalizing currency: '台湾ドル' -> 'NTD'")
        return "NTD"
    elif currency == "円":
        logger.info(f"Normalizing currency: '円' -> 'JPY'")
        return "JPY"
    else:
        return currency

def truncate_description(description, max_length=100):
    """
    Truncate description to the specified maximum length.
    
    Args:
        description (str): The description to truncate
        max_length (int): Maximum allowed length
        
    Returns:
        str: The truncated description
    """
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

def convert_csv_to_json(csv_file_path, json_file_path, max_desc_length=100, fix_line_breaks=True, line_break_replacement=' '):
    """
    Convert a General Journal CSV file to JSON format.
    
    Args:
        csv_file_path (str): Path to the input CSV file
        json_file_path (str): Path to the output JSON file
        max_desc_length (int): Maximum length for description field
        fix_line_breaks (bool): Whether to fix line breaks in CSV fields
        line_break_replacement (str): Character to replace line breaks with
    """
    # Check if we need to fix line breaks in the CSV file
    if fix_line_breaks:
        logger.info(f"Checking for line breaks in CSV file: {csv_file_path}")
        try:
            # Create a temporary file for the fixed CSV content
            with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False, suffix='.csv') as temp_file:
                temp_csv_path = temp_file.name
                
            # Fix line breaks in the CSV file
            fix_csv_line_breaks(csv_file_path, temp_csv_path, line_break_replacement)
            logger.info(f"Fixed CSV file saved to temporary file: {temp_csv_path}")
            
            # Use the fixed CSV file for processing
            csv_file_to_process = temp_csv_path
        except Exception as e:
            logger.error(f"Error fixing line breaks in CSV file: {e}")
            logger.warning("Proceeding with original CSV file")
            csv_file_to_process = csv_file_path
    else:
        # Use the original CSV file
        csv_file_to_process = csv_file_path
    
    # Read the CSV file with proper encoding
    try:
        with open(csv_file_to_process, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Clean up temporary file if it was created
        if fix_line_breaks and 'temp_csv_path' in locals():
            try:
                os.remove(temp_csv_path)
                logger.info(f"Removed temporary CSV file: {temp_csv_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary CSV file: {e}")
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
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
    
    # Process data rows
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
        
        # Extract common fields for the journal entry
        entry = {
            "voucher_no": debit_data.get("伝票No.") or credit_data.get("伝票No.") or "",
            "transaction_date": debit_data.get("仕訳日") or credit_data.get("仕訳日") or "",
            "application_date": debit_data.get("申請日") or credit_data.get("申請日") or "",
            "journal_generation_date": debit_data.get("仕訳データ生成日") or credit_data.get("仕訳データ生成日") or "",
            "description": truncate_description(debit_data.get("Receipt/Invoice Note(明細)") or credit_data.get("Receipt/Invoice Note(明細)") or "", max_desc_length),
            "note": debit_data.get("Note(明細)") or credit_data.get("Note(明細)") or "",
            "receipt_invoice": debit_data.get("Receipt/Invoice #(明細)") or credit_data.get("Receipt/Invoice #(明細)") or "",
            "External_Document_No": debit_data.get("Receipt/Invoice No.(明細)") or credit_data.get("Receipt/Invoice No.(明細)") or debit_data.get("仕訳日") or credit_data.get("仕訳日") or "",
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
                "department_code": credit_data.get("借方：負担部門コード") or ""
            }
        }
        
        # Helper functions to reduce code duplication
        def process_vendor_account(side, side_data, entry_side, is_credit=False):
            """Process vendor account data for either debit or credit side"""
            if entry_side["gl_account"] == "Vendor":
                # For Vendor accounts, prioritize vendor_code first, then applicant_code
                entry_side["account"] = side_data.get("支払先CD") or side_data.get("申請者CD/支払先CD") or ""
                
                # Update vendor_code according to new requirement: use 支払先CD, if empty use 申請者CD/支払先CD
                entry_side["vendor_code"] = side_data.get("支払先CD") or side_data.get("申請者CD/支払先CD") or ""
                
                # Transform department_code for Vendor gl_account type
                if entry_side["department_code"]:
                    # Special case for credit side with department "VCJ.9999" and department_code "1000"
                    if is_credit and entry_side["department"] == "VCJ.9999" and entry_side["department_code"] == "1000":
                        entry_side["department_code"] = "VCJ.9999"
                    # For all other cases, take first 3 characters and append .9999
                    elif len(entry_side["department_code"]) >= 3:
                        entry_side["department_code"] = entry_side["department_code"][:3] + ".9999"
        
        def process_gl_account(side, side_data, entry_side, voucher_no, is_credit=False):
            """Process G/L Account data for either debit or credit side"""
            if entry_side["gl_account"] == "G/L Account":
                # For G/L Account, prioritize 借方：補助科目：会計連携項目 first, then 借方：勘定科目：会計連携項目
                original_account = entry_side["account"]
                
                if is_credit:
                    # For credit side, implement the new priority logic
                    entry_side["account"] = side_data.get("貸方：補助科目：会計連携項目") or side_data.get("貸方：勘定科目：会計連携項目") or side_data.get("支払先CD") or entry_side["account"]
                else:
                    # For debit side, implement the new priority logic
                    entry_side["account"] = side_data.get("借方：補助科目：会計連携項目") or side_data.get("借方：勘定科目：会計連携項目") or side_data.get("支払先CD") or entry_side["account"]
                
                if entry_side["account"] != original_account:
                    side_name = "credit" if is_credit else "debit"
                    logger.info(f"Updated {side_name} account for G/L Account in voucher {voucher_no} to {entry_side['account']}")
        
        # Process both sides using the helper functions
        process_vendor_account("debit", debit_data, entry["debit"])
        process_vendor_account("credit", credit_data, entry["credit"], is_credit=True)
        
        process_gl_account("debit", debit_data, entry["debit"], entry["voucher_no"])
        process_gl_account("credit", credit_data, entry["credit"], entry["voucher_no"], is_credit=True)
        
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
    
    # Consolidate entries based on voucher_no and vendor_code
    consolidated_entries = consolidate_entries(raw_entries)
    
    # Write the JSON output
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(consolidated_entries, json_file, ensure_ascii=False, indent=2)
    
    return len(consolidated_entries)

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
                    "credit": entry["credit"].copy()
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
                                original_amount = float(consolidated_entry["debit"]["amount"])
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
                                    consolidated_entry["debit"]["original_amount"] = original_amount
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
                
                # For credit entries, we'll consolidate them later
                consolidated_entries.append(consolidated_entry)
            
            # Now create one consolidated credit entry per vendor per voucher
            if vendor_entries:
                # Use the first entry as a template for the consolidated credit entry
                template_entry = vendor_entries[0]
                
                # Calculate total credit amount in local currency
                total_credit_amount = 0
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
                                    original_amount = float(entry["credit"]["amount"])
                                    
                                    # Convert to target currency if needed
                                    if entry["credit"]["currency"] != target_currency:
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
                                        total_credit_amount += float(entry["credit"]["amount"])
                                    except (ValueError, TypeError):
                                        pass
                        else:
                            # No region code, use original amount
                            try:
                                total_credit_amount += float(entry["credit"]["amount"])
                                if not credit_currency:
                                    credit_currency = entry["credit"]["currency"]
                            except (ValueError, TypeError):
                                pass
                
                # Create a consolidated credit entry
                consolidated_credit_entry = {
                    "voucher_no": template_entry["voucher_no"],
                    "transaction_date": template_entry["transaction_date"],
                    "application_date": template_entry["application_date"],
                    "journal_generation_date": template_entry["journal_generation_date"],
                    "description": template_entry["description"],
                    "note": template_entry["note"],
                    "receipt_invoice": template_entry["receipt_invoice"],
                    "External_Document_No": template_entry["External_Document_No"],
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
                        "amount": total_credit_amount,
                        "currency": credit_currency or template_entry["credit"]["currency"],
                        "department": template_entry["credit"]["department"],
                        "applicant_code": template_entry["credit"]["applicant_code"],
                        "vendor_code": vendor_code if vendor_code != "UNKNOWN" else "",
                        "free_field": template_entry["credit"]["free_field"],
                        "department_code": template_entry["credit"]["department_code"],
                        "consolidated": True,
                        "original_entries_count": len(vendor_entries)
                    }
                }
                
                # Add a note about consolidation
                if len(vendor_entries) > 1:
                    consolidated_credit_entry["credit"]["consolidation_note"] = f"Consolidated from {len(vendor_entries)} entries"
                
                consolidated_entries.append(consolidated_credit_entry)
    
    return consolidated_entries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Convert General Journal CSV file to JSON format.',
        epilog='Example: python csv_to_json_converter.py -i "Raku export.csv" -o "journal_entries.json"'
    )
    parser.add_argument('-i', '--input', required=True, help='Input CSV file path (required)')
    parser.add_argument('-o', '--output', help='Output JSON file path (default: input_filename.json)')
    parser.add_argument('--max-desc-length', type=int, default=100, 
                        help='Maximum length for description field (default: 100)')
    parser.add_argument('--no-fix-line-breaks', action='store_true',
                        help='Disable fixing line breaks in CSV fields (enabled by default)')
    parser.add_argument('--line-break-replacement', default=' ',
                        help='Character to replace line breaks with (default: space)')
    
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
            not args.no_fix_line_breaks,  # Invert the flag since our function expects fix_line_breaks
            args.line_break_replacement
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
