#!/usr/bin/env python3
"""
Compare a failing voucher (APA-0000401) with a successful voucher to identify differences.

This script extracts and compares two vouchers from a JSON file to help diagnose
why one voucher's credit line posting fails while the other succeeds.

Usage:
    python compare_vouchers.py <input_json_file> --failing <failing_voucher> --success <successful_voucher>

Example:
    python compare_vouchers.py 0604-Raku\ export-\ VCT\ credit\ card\ 1.utf8.json --failing APA-0000401 --success APA-0000402
"""

import argparse
import json
import logging
import os
import sys
from process_japan_exports import DecimalEncoder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("voucher_comparison.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("voucher_comparison")

def extract_voucher(entries, voucher_no):
    """
    Extract entries with the specified voucher number.
    
    Args:
        entries: List of journal entries
        voucher_no: Voucher number to extract
        
    Returns:
        List of entries with the specified voucher number
    """
    extracted = [entry for entry in entries if entry.get('voucher_no') == voucher_no]
    logger.info(f"Found {len(extracted)} entries with voucher number {voucher_no}")
    return extracted

def compare_vouchers(failing_entry, success_entry):
    """
    Compare a failing voucher with a successful voucher to identify differences.
    
    Args:
        failing_entry: The failing journal entry
        success_entry: The successful journal entry
        
    Returns:
        Dict: Differences between the two entries
    """
    differences = {
        "debit": {},
        "credit": {},
        "metadata": {}
    }
    
    # Compare metadata fields (top-level fields)
    for key in set(list(failing_entry.keys()) + list(success_entry.keys())):
        if key not in ["debit", "credit"]:
            if key not in failing_entry:
                differences["metadata"][key] = {
                    "failing": "MISSING",
                    "success": success_entry.get(key)
                }
            elif key not in success_entry:
                differences["metadata"][key] = {
                    "failing": failing_entry.get(key),
                    "success": "MISSING"
                }
            elif failing_entry.get(key) != success_entry.get(key):
                differences["metadata"][key] = {
                    "failing": failing_entry.get(key),
                    "success": success_entry.get(key)
                }
    
    # Compare debit fields
    failing_debit = failing_entry.get("debit", {})
    success_debit = success_entry.get("debit", {})
    
    for key in set(list(failing_debit.keys()) + list(success_debit.keys())):
        if key not in failing_debit:
            differences["debit"][key] = {
                "failing": "MISSING",
                "success": success_debit.get(key)
            }
        elif key not in success_debit:
            differences["debit"][key] = {
                "failing": failing_debit.get(key),
                "success": "MISSING"
            }
        elif failing_debit.get(key) != success_debit.get(key):
            differences["debit"][key] = {
                "failing": failing_debit.get(key),
                "success": success_debit.get(key)
            }
    
    # Compare credit fields
    failing_credit = failing_entry.get("credit", {})
    success_credit = success_entry.get("credit", {})
    
    for key in set(list(failing_credit.keys()) + list(success_credit.keys())):
        if key not in failing_credit:
            differences["credit"][key] = {
                "failing": "MISSING",
                "success": success_credit.get(key)
            }
        elif key not in success_credit:
            differences["credit"][key] = {
                "failing": failing_credit.get(key),
                "success": "MISSING"
            }
        elif failing_credit.get(key) != success_credit.get(key):
            differences["credit"][key] = {
                "failing": failing_credit.get(key),
                "success": success_credit.get(key)
            }
    
    # Remove empty sections
    if not differences["debit"]:
        del differences["debit"]
    if not differences["credit"]:
        del differences["credit"]
    if not differences["metadata"]:
        del differences["metadata"]
    
    return differences

def generate_comparison_report(differences, failing_voucher, success_voucher, output_file):
    """
    Generate a markdown report of the differences between vouchers.
    
    Args:
        differences: Dictionary of differences
        failing_voucher: Failing voucher number
        success_voucher: Successful voucher number
        output_file: Path to the output report file
    """
    with open(output_file, 'w') as f:
        f.write(f"# Voucher Comparison Report\n\n")
        f.write(f"Comparing failing voucher **{failing_voucher}** with successful voucher **{success_voucher}**\n\n")
        
        if not differences:
            f.write("No differences found between the vouchers.\n")
            return
        
        # Write metadata differences
        if "metadata" in differences:
            f.write("## Metadata Differences\n\n")
            f.write("| Field | Failing Voucher | Successful Voucher |\n")
            f.write("|-------|----------------|--------------------|\n")
            
            for key, diff in differences["metadata"].items():
                f.write(f"| {key} | {diff['failing']} | {diff['success']} |\n")
            
            f.write("\n")
        
        # Write debit differences
        if "debit" in differences:
            f.write("## Debit Line Differences\n\n")
            f.write("| Field | Failing Voucher | Successful Voucher |\n")
            f.write("|-------|----------------|--------------------|\n")
            
            for key, diff in differences["debit"].items():
                f.write(f"| {key} | {diff['failing']} | {diff['success']} |\n")
            
            f.write("\n")
        
        # Write credit differences
        if "credit" in differences:
            f.write("## Credit Line Differences\n\n")
            f.write("| Field | Failing Voucher | Successful Voucher |\n")
            f.write("|-------|----------------|--------------------|\n")
            
            for key, diff in differences["credit"].items():
                f.write(f"| {key} | {diff['failing']} | {diff['success']} |\n")
            
            f.write("\n")
        
        f.write("## Potential Issues\n\n")
        f.write("Based on the differences above, here are potential issues that might be causing the credit line posting failure:\n\n")
        
        # Analyze potential issues based on differences
        issues = []
        
        # Check for common issues in credit line
        if "credit" in differences:
            credit_diff = differences["credit"]
            
            # Check for vendor code issues
            if "vendor_code" in credit_diff:
                issues.append(f"- **Vendor Code**: The failing voucher uses vendor code `{credit_diff['vendor_code']['failing']}` while the successful one uses `{credit_diff['vendor_code']['success']}`.")
            
            # Check for department code issues
            if "department" in credit_diff:
                issues.append(f"- **Department Code**: The failing voucher uses department `{credit_diff['department']['failing']}` while the successful one uses `{credit_diff['department']['success']}`.")
            
            # Check for currency issues
            if "currency" in credit_diff:
                issues.append(f"- **Currency**: The failing voucher uses currency `{credit_diff['currency']['failing']}` while the successful one uses `{credit_diff['currency']['success']}`.")
            
            # Check for amount issues
            if "amount" in credit_diff:
                issues.append(f"- **Amount**: The failing voucher has amount `{credit_diff['amount']['failing']}` while the successful one has `{credit_diff['amount']['success']}`.")
        
        # Check for metadata issues
        if "metadata" in differences:
            metadata_diff = differences["metadata"]
            
            # Check for document date issues
            if "Document_Date" in metadata_diff:
                issues.append(f"- **Document Date**: The failing voucher has document date `{metadata_diff['Document_Date']['failing']}` while the successful one has `{metadata_diff['Document_Date']['success']}`.")
            
            # Check for description issues
            if "description" in metadata_diff:
                issues.append(f"- **Description**: The failing voucher has description `{metadata_diff['description']['failing']}` while the successful one has `{metadata_diff['description']['success']}`.")
        
        # Write issues
        if issues:
            for issue in issues:
                f.write(f"{issue}\n\n")
        else:
            f.write("No obvious issues identified based on the differences.\n\n")
        
        f.write("## Next Steps\n\n")
        f.write("1. Check if the vendor code in the failing voucher exists in the ERP system\n")
        f.write("2. Verify that the department code in the failing voucher is valid\n")
        f.write("3. Check if there are any restrictions on the currency used in the failing voucher\n")
        f.write("4. Verify that the amount in the failing voucher is within acceptable limits\n")
        f.write("5. Check if there are any special validation rules for the failing voucher's fields\n")

def main():
    """Main function to compare vouchers and generate a report."""
    parser = argparse.ArgumentParser(description='Compare a failing voucher with a successful voucher')
    parser.add_argument('input_file', help='Input JSON file path')
    parser.add_argument('--failing', default="APA-0000401", help='Failing voucher number (default: APA-0000401)')
    parser.add_argument('--success', required=True, help='Successful voucher number')
    parser.add_argument('--output', default="voucher_comparison_report.md", help='Output report file path')
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Load input file
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        logger.info(f"Loaded {len(entries)} entries from {args.input_file}")
    except Exception as e:
        logger.error(f"Error loading input file: {str(e)}")
        sys.exit(1)
    
    # Extract voucher entries
    failing_entries = extract_voucher(entries, args.failing)
    success_entries = extract_voucher(entries, args.success)
    
    if not failing_entries:
        logger.error(f"No entries found with failing voucher number {args.failing}")
        sys.exit(1)
    
    if not success_entries:
        logger.error(f"No entries found with successful voucher number {args.success}")
        sys.exit(1)
    
    # Use the first entry from each voucher for comparison
    failing_entry = failing_entries[0]
    success_entry = success_entries[0]
    
    # Compare vouchers
    differences = compare_vouchers(failing_entry, success_entry)
    
    # Generate comparison report
    generate_comparison_report(differences, args.failing, args.success, args.output)
    logger.info(f"Comparison report generated: {args.output}")
    
    # Log full entries for reference
    logger.info(f"Failing entry: {json.dumps(failing_entry, indent=2, cls=DecimalEncoder)}")
    logger.info(f"Success entry: {json.dumps(success_entry, indent=2, cls=DecimalEncoder)}")

if __name__ == "__main__":
    main()
