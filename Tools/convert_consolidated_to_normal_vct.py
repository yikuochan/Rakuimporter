#!/usr/bin/env python3
"""
Convert Consolidated Billing Entries to Normal VCT Entries

This script takes consolidated billing entries and converts them back to individual normal VCT entries.
Consolidated entries have a 'consolidated=True' flag in the credit section and contain aggregated amounts
from multiple original entries. This script reverses that process.

Usage:
    python convert_consolidated_to_normal_vct.py <input_json_file> <output_json_file>

Example:
    python convert_consolidated_to_normal_vct.py consolidated_entries.json normal_vct_entries.json
"""

import argparse
import json
import logging
import os
import sys
from decimal import Decimal
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("convert_consolidated_to_normal_vct.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("convert_consolidated_to_normal_vct")

# Custom JSON encoder to handle Decimal objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def identify_consolidated_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify entries that have consolidated billing information.
    
    Args:
        entries: List of journal entries
        
    Returns:
        List of consolidated entries
    """
    consolidated_entries = []
    
    for entry in entries:
        credit_data = entry.get("credit", {})
        
        # Check if this is a consolidated entry
        if credit_data.get("consolidated", False):
            consolidated_entries.append(entry)
            logger.info(f"Found consolidated entry - Voucher: {entry.get('voucher_no', 'Unknown')}, "
                       f"Original entries count: {credit_data.get('original_entries_count', 'N/A')}")
    
    logger.info(f"Identified {len(consolidated_entries)} consolidated entries out of {len(entries)} total entries")
    return consolidated_entries


def extract_original_entry_data(consolidated_entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract original entry data from a consolidated entry.
    
    Args:
        consolidated_entry: A consolidated billing entry
        
    Returns:
        List of individual entries reconstructed from consolidated data
    """
    individual_entries = []
    credit_data = consolidated_entry.get("credit", {})
    
    # Get consolidated information
    total_amount = credit_data.get("amount", 0)
    original_count = credit_data.get("original_entries_count", 1)
    voucher_no = consolidated_entry.get("voucher_no", "Unknown")
    
    logger.info(f"Extracting {original_count} individual entries from consolidated entry {voucher_no}")
    
    # If we have stored original entries data, use it
    if "original_entries" in credit_data:
        original_entries_data = credit_data["original_entries"]
        logger.info(f"Found stored original entries data for {len(original_entries_data)} entries")
        
        for i, original_data in enumerate(original_entries_data):
            individual_entry = create_individual_entry_from_original_data(
                consolidated_entry, original_data, i + 1
            )
            individual_entries.append(individual_entry)
    else:
        # If no original entries data is stored, we need to reconstruct based on available information
        logger.warning(f"No original entries data found for consolidated entry {voucher_no}. "
                      f"Attempting to reconstruct {original_count} individual entries.")
        
        # Calculate individual amount (distribute evenly)
        individual_amount = total_amount / original_count if original_count > 0 else total_amount
        
        for i in range(original_count):
            individual_entry = create_individual_entry_from_consolidated(
                consolidated_entry, individual_amount, i + 1
            )
            individual_entries.append(individual_entry)
    
    logger.info(f"Successfully extracted {len(individual_entries)} individual entries from consolidated entry {voucher_no}")
    return individual_entries


def create_individual_entry_from_original_data(consolidated_entry: Dict[str, Any], 
                                             original_data: Dict[str, Any], 
                                             entry_index: int) -> Dict[str, Any]:
    """
    Create an individual entry from stored original data.
    
    Args:
        consolidated_entry: The consolidated entry
        original_data: Original entry data stored in the consolidated entry
        entry_index: Index of this individual entry
        
    Returns:
        Individual VCT entry
    """
    voucher_no = consolidated_entry.get("voucher_no", "Unknown")
    
    # Create individual entry structure
    individual_entry = {
        "voucher_no": f"{voucher_no}-{entry_index}",  # Create unique voucher number
        "Document_Date": consolidated_entry.get("Document_Date", ""),
        "External_Document_No": consolidated_entry.get("External_Document_No", ""),
        "description": original_data.get("description", ""),
        "debit": {
            "account": original_data.get("debit_account", ""),
            "amount": original_data.get("debit_amount", 0),
            "currency": original_data.get("debit_currency", ""),
            "department": original_data.get("debit_department", ""),
            "department_code": original_data.get("debit_department_code", ""),
            "applicant_code": original_data.get("applicant_code", ""),
            "gl_account": original_data.get("debit_gl_account", "G/L Account"),
            "Receipt/Invoice Note(明細)": original_data.get("receipt_invoice_note", ""),
            "free_field": original_data.get("free_field", "")
        },
        "credit": {
            "account": consolidated_entry.get("credit", {}).get("account", ""),
            "amount": original_data.get("credit_amount", original_data.get("debit_amount", 0)),
            "currency": consolidated_entry.get("credit", {}).get("currency", ""),
            "department": consolidated_entry.get("credit", {}).get("department", ""),
            "department_code": consolidated_entry.get("credit", {}).get("department_code", ""),
            "vendor_code": consolidated_entry.get("credit", {}).get("vendor_code", ""),
            "gl_account": consolidated_entry.get("credit", {}).get("gl_account", "Vendor"),
            "account_source": consolidated_entry.get("credit", {}).get("account_source", ""),
            "Remarks": original_data.get("remarks", ""),
            "備考": original_data.get("remarks", ""),
            "consolidated": False  # Mark as no longer consolidated
        }
    }
    
    logger.info(f"Created individual entry {entry_index} from original data - Voucher: {individual_entry['voucher_no']}")
    return individual_entry


def create_individual_entry_from_consolidated(consolidated_entry: Dict[str, Any], 
                                            individual_amount: float, 
                                            entry_index: int) -> Dict[str, Any]:
    """
    Create an individual entry by reconstructing from consolidated entry data.
    
    Args:
        consolidated_entry: The consolidated entry
        individual_amount: Amount for this individual entry
        entry_index: Index of this individual entry
        
    Returns:
        Individual VCT entry
    """
    voucher_no = consolidated_entry.get("voucher_no", "Unknown")
    credit_data = consolidated_entry.get("credit", {})
    
    # Create individual entry structure
    individual_entry = {
        "voucher_no": f"{voucher_no}-{entry_index}",  # Create unique voucher number
        "Document_Date": consolidated_entry.get("Document_Date", ""),
        "External_Document_No": consolidated_entry.get("External_Document_No", ""),
        "description": consolidated_entry.get("description", f"Individual entry {entry_index}"),
        "debit": {
            "account": "",  # Will need to be filled based on business logic
            "amount": individual_amount,
            "currency": credit_data.get("currency", ""),
            "department": credit_data.get("department", ""),
            "department_code": credit_data.get("department_code", ""),
            "applicant_code": "",
            "gl_account": "G/L Account",
            "Receipt/Invoice Note(明細)": f"Reconstructed entry {entry_index}",
            "free_field": ""
        },
        "credit": {
            "account": credit_data.get("account", ""),
            "amount": individual_amount,
            "currency": credit_data.get("currency", ""),
            "department": credit_data.get("department", ""),
            "department_code": credit_data.get("department_code", ""),
            "vendor_code": credit_data.get("vendor_code", ""),
            "gl_account": credit_data.get("gl_account", "Vendor"),
            "account_source": credit_data.get("account_source", ""),
            "Remarks": credit_data.get("Remarks", ""),
            "備考": credit_data.get("備考", ""),
            "consolidated": False  # Mark as no longer consolidated
        }
    }
    
    logger.info(f"Created reconstructed individual entry {entry_index} - Voucher: {individual_entry['voucher_no']}")
    return individual_entry


def convert_consolidated_to_normal_vct(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert consolidated billing entries to normal VCT entries.
    
    Args:
        entries: List of journal entries (may include consolidated entries)
        
    Returns:
        List of entries with consolidated entries converted to individual entries
    """
    converted_entries = []
    consolidated_count = 0
    individual_count = 0
    
    for entry in entries:
        credit_data = entry.get("credit", {})
        
        # Check if this is a consolidated entry
        if credit_data.get("consolidated", False):
            consolidated_count += 1
            logger.info(f"Converting consolidated entry - Voucher: {entry.get('voucher_no', 'Unknown')}")
            
            # Extract individual entries from consolidated entry
            individual_entries = extract_original_entry_data(entry)
            converted_entries.extend(individual_entries)
            individual_count += len(individual_entries)
            
            logger.info(f"Converted 1 consolidated entry to {len(individual_entries)} individual entries")
        else:
            # Keep non-consolidated entries as they are
            converted_entries.append(entry)
    
    logger.info(f"Conversion complete: {consolidated_count} consolidated entries converted to {individual_count} individual entries")
    logger.info(f"Total entries after conversion: {len(converted_entries)}")
    
    return converted_entries


def validate_conversion_results(original_entries: List[Dict[str, Any]], 
                              converted_entries: List[Dict[str, Any]]) -> bool:
    """
    Validate that the conversion preserved the total amounts and key data.
    
    Args:
        original_entries: Original entries before conversion
        converted_entries: Entries after conversion
        
    Returns:
        True if validation passes, False otherwise
    """
    logger.info("Validating conversion results...")
    
    # Calculate total amounts before and after conversion
    original_total_debit = 0
    original_total_credit = 0
    converted_total_debit = 0
    converted_total_credit = 0
    
    for entry in original_entries:
        debit_amount = entry.get("debit", {}).get("amount", 0)
        credit_amount = entry.get("credit", {}).get("amount", 0)
        original_total_debit += debit_amount
        original_total_credit += credit_amount
    
    for entry in converted_entries:
        debit_amount = entry.get("debit", {}).get("amount", 0)
        credit_amount = entry.get("credit", {}).get("amount", 0)
        converted_total_debit += debit_amount
        converted_total_credit += credit_amount
    
    # Check if totals match (within small tolerance for floating point)
    debit_diff = abs(original_total_debit - converted_total_debit)
    credit_diff = abs(original_total_credit - converted_total_credit)
    tolerance = 0.01
    
    logger.info(f"Original totals - Debit: {original_total_debit:.2f}, Credit: {original_total_credit:.2f}")
    logger.info(f"Converted totals - Debit: {converted_total_debit:.2f}, Credit: {converted_total_credit:.2f}")
    logger.info(f"Differences - Debit: {debit_diff:.2f}, Credit: {credit_diff:.2f}")
    
    if debit_diff <= tolerance and credit_diff <= tolerance:
        logger.info("✅ Validation PASSED: Total amounts preserved")
        return True
    else:
        logger.error("❌ Validation FAILED: Total amounts do not match")
        return False


def generate_conversion_report(original_entries: List[Dict[str, Any]], 
                             converted_entries: List[Dict[str, Any]], 
                             output_file: str):
    """
    Generate a report of the conversion process.
    
    Args:
        original_entries: Original entries before conversion
        converted_entries: Entries after conversion
        output_file: Path to the output report file
    """
    consolidated_entries = identify_consolidated_entries(original_entries)
    
    with open(output_file, 'w') as f:
        f.write("# Consolidated to Normal VCT Conversion Report\n\n")
        f.write(f"**Conversion Date:** {import_datetime().datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- **Original entries:** {len(original_entries)}\n")
        f.write(f"- **Consolidated entries found:** {len(consolidated_entries)}\n")
        f.write(f"- **Entries after conversion:** {len(converted_entries)}\n")
        f.write(f"- **Individual entries created:** {len(converted_entries) - (len(original_entries) - len(consolidated_entries))}\n\n")
        
        f.write("## Consolidated Entries Processed\n\n")
        f.write("| Original Voucher | Original Count | Individual Entries Created |\n")
        f.write("|------------------|----------------|----------------------------|\n")
        
        for entry in consolidated_entries:
            voucher_no = entry.get("voucher_no", "Unknown")
            original_count = entry.get("credit", {}).get("original_entries_count", 1)
            f.write(f"| {voucher_no} | {original_count} | {original_count} |\n")
        
        f.write("\n## Validation Results\n\n")
        validation_passed = validate_conversion_results(original_entries, converted_entries)
        f.write(f"**Validation Status:** {'✅ PASSED' if validation_passed else '❌ FAILED'}\n\n")
        
        f.write("## Notes\n\n")
        f.write("- Consolidated entries have been converted to individual normal VCT entries\n")
        f.write("- Each individual entry has a unique voucher number with suffix (e.g., APA-0000552-1, APA-0000552-2)\n")
        f.write("- The `consolidated=False` flag has been set on all converted entries\n")
        f.write("- Original entry data has been preserved where available\n")


def import_datetime():
    """Import datetime module (for report generation)"""
    import datetime
    return datetime


def main():
    """Main function to convert consolidated entries to normal VCT entries."""
    parser = argparse.ArgumentParser(description='Convert consolidated billing entries to normal VCT entries')
    parser.add_argument('input_file', help='Input JSON file path containing consolidated entries')
    parser.add_argument('output_file', help='Output JSON file path for normal VCT entries')
    parser.add_argument('--report', help='Generate conversion report to specified file path', 
                       default="consolidated_to_normal_conversion_report.md")
    parser.add_argument('--validate', action='store_true', help='Perform validation after conversion')
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Load input file
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            original_entries = json.load(f)
        logger.info(f"Loaded {len(original_entries)} entries from {args.input_file}")
    except Exception as e:
        logger.error(f"Error loading input file: {str(e)}")
        sys.exit(1)
    
    # Identify consolidated entries
    consolidated_entries = identify_consolidated_entries(original_entries)
    
    if not consolidated_entries:
        logger.info("No consolidated entries found. Nothing to convert.")
        # Copy original entries to output file
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(original_entries, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
        logger.info(f"Original entries copied to {args.output_file}")
        sys.exit(0)
    
    # Convert consolidated entries to normal VCT entries
    try:
        converted_entries = convert_consolidated_to_normal_vct(original_entries)
        logger.info(f"Conversion completed. Generated {len(converted_entries)} entries.")
    except Exception as e:
        logger.error(f"Error during conversion: {str(e)}")
        sys.exit(1)
    
    # Validate conversion if requested
    if args.validate:
        validation_passed = validate_conversion_results(original_entries, converted_entries)
        if not validation_passed:
            logger.error("Validation failed. Please check the conversion logic.")
            sys.exit(1)
    
    # Save converted entries to output file
    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(converted_entries, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
        logger.info(f"Converted entries saved to {args.output_file}")
    except Exception as e:
        logger.error(f"Error saving output file: {str(e)}")
        sys.exit(1)
    
    # Generate conversion report
    try:
        generate_conversion_report(original_entries, converted_entries, args.report)
        logger.info(f"Conversion report generated: {args.report}")
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
    
    logger.info("Conversion process completed successfully!")


if __name__ == "__main__":
    main()
