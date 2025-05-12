#!/usr/bin/env python3
"""
Verify Currency Transformations

This script loads a JSON file, applies the currency transformation rules,
and saves the transformed data to a new file. It also generates a report
of all transformations made.

Usage:
    python verify_currency_transformations.py [input_json_file]

Example:
    python verify_currency_transformations.py Raku-export-1.json
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("erp_api_integration")

# Import the transform_currency_code function from process_japan_exports.py
try:
    from process_japan_exports import transform_currency_code
except ImportError:
    logger.error("Failed to import transform_currency_code from process_japan_exports.py")
    sys.exit(1)


def transform_entry_currencies(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform currency codes in a journal entry based on company code.
    
    Args:
        entry: The journal entry data
        
    Returns:
        Dict[str, Any]: The entry with transformed currency codes
    """
    # Create a deep copy of the entry to avoid modifying the original
    transformed_entry = json.loads(json.dumps(entry))
    
    # Transform debit line currency
    if "debit" in transformed_entry and "department" in transformed_entry["debit"]:
        debit_dept = transformed_entry["debit"]["department"]
        debit_company = debit_dept[:3] if debit_dept else ""
        
        if "currency" in transformed_entry["debit"] and debit_company:
            original_currency = transformed_entry["debit"]["currency"]
            transformed_currency = transform_currency_code(debit_company, original_currency)
            transformed_entry["debit"]["currency"] = transformed_currency
    
    # Transform credit line currency
    if "credit" in transformed_entry and "department" in transformed_entry["credit"]:
        credit_dept = transformed_entry["credit"]["department"]
        credit_company = credit_dept[:3] if credit_dept else ""
        
        if "currency" in transformed_entry["credit"] and credit_company:
            original_currency = transformed_entry["credit"]["currency"]
            transformed_currency = transform_currency_code(credit_company, original_currency)
            transformed_entry["credit"]["currency"] = transformed_currency
    
    return transformed_entry


def generate_currency_modification_report(entries: List[Dict[str, Any]], output_file: str) -> List[Dict[str, Any]]:
    """
    Generate a report of all currency code modifications.
    
    Args:
        entries: List of journal entries
        output_file: Path to the output report file
    
    Returns:
        List[Dict[str, Any]]: List of modifications made
    """
    modifications = []
    
    for entry in entries:
        voucher_no = entry.get("voucher_no", "Unknown")
        
        # Check debit line
        debit_dept = entry.get("debit", {}).get("department", "")
        debit_company = debit_dept[:3] if debit_dept else ""
        debit_currency = entry.get("debit", {}).get("currency", "")
        
        if debit_company and debit_currency:
            transformed_debit = transform_currency_code(debit_company, debit_currency)
            if transformed_debit != debit_currency:
                modifications.append({
                    "voucher_no": voucher_no,
                    "line_type": "debit",
                    "company_code": debit_company,
                    "original_currency": debit_currency,
                    "transformed_currency": transformed_debit
                })
        
        # Check credit line
        credit_dept = entry.get("credit", {}).get("department", "")
        credit_company = credit_dept[:3] if credit_dept else ""
        credit_currency = entry.get("credit", {}).get("currency", "")
        
        if credit_company and credit_currency:
            transformed_credit = transform_currency_code(credit_company, credit_currency)
            if transformed_credit != credit_currency:
                modifications.append({
                    "voucher_no": voucher_no,
                    "line_type": "credit",
                    "company_code": credit_company,
                    "original_currency": credit_currency,
                    "transformed_currency": transformed_credit
                })
    
    # Write the report to a markdown file
    with open(output_file, 'w') as f:
        f.write("# Currency Modification Report\n\n")
        f.write("| Voucher No | Line Type | Company Code | Original Currency | Transformed Currency |\n")
        f.write("|------------|-----------|--------------|-------------------|---------------------|\n")
        
        for mod in modifications:
            f.write(f"| {mod['voucher_no']} | {mod['line_type']} | {mod['company_code']} | {mod['original_currency']} | {mod['transformed_currency']} |\n")
        
        f.write(f"\n\nTotal modifications: {len(modifications)}\n")
        
        # Add a summary by company and currency
        company_currency_counts = {}
        for mod in modifications:
            key = (mod['company_code'], mod['original_currency'])
            if key not in company_currency_counts:
                company_currency_counts[key] = 0
            company_currency_counts[key] += 1
        
        f.write("\n## Modifications by Company and Currency\n\n")
        f.write("| Company Code | Original Currency | Count |\n")
        f.write("|--------------|-------------------|-------|\n")
        
        for (company, currency), count in sorted(company_currency_counts.items()):
            f.write(f"| {company} | {currency} | {count} |\n")
    
    logger.info(f"Generated currency modification report with {len(modifications)} modifications: {output_file}")
    return modifications


def main():
    """Main function to process the input file and apply currency transformations."""
    parser = argparse.ArgumentParser(description='Verify currency transformations in JSON file')
    parser.add_argument('input_file', nargs='?', default="Raku-export-1.json", help='Input JSON file path')
    parser.add_argument('--report', help='Output report file path', default="currency_modification_report.md")
    parser.add_argument('--output', help='Output JSON file path', default=None)
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Set default output file if not specified
    if args.output is None:
        base_name, ext = os.path.splitext(args.input_file)
        args.output = f"{base_name}.transformed{ext}"
    
    # Load input file
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        logger.info(f"Loaded {len(entries)} entries from {args.input_file}")
    except Exception as e:
        logger.error(f"Error loading input file: {str(e)}")
        sys.exit(1)
    
    # Transform entries
    transformed_entries = [transform_entry_currencies(entry) for entry in entries]
    
    # Save transformed entries
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(transformed_entries, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved transformed data to {args.output}")
    except Exception as e:
        logger.error(f"Error saving transformed data: {str(e)}")
        sys.exit(1)
    
    # Generate currency modification report
    modifications = generate_currency_modification_report(entries, args.report)


if __name__ == "__main__":
    main()