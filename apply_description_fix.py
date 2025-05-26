#!/usr/bin/env python3
"""
Apply Description Field Fix

This script applies the description field fix to a CSV file and generates a fixed JSON file.
It uses the updated csv_to_json_converter.py to extract the Remarks (備考) values from the CSV file
and sets them as the credit_description field in the JSON data.

Usage:
    python apply_description_fix.py <input_csv_file> [<output_json_file>]

Example:
    python apply_description_fix.py "0526-Raku export- VCT GE.utf8.csv" "fixed_output.json"
"""

import argparse
import json
import logging
import os
import sys
from csv_to_json_converter import convert_csv_to_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("description_fix_applier")

def apply_description_fix(csv_file_path, output_json_path=None):
    """
    Apply the description field fix to a CSV file and generate a fixed JSON file.
    
    Args:
        csv_file_path (str): Path to the input CSV file
        output_json_path (str, optional): Path to the output JSON file. If not provided,
                                         defaults to input_filename_fixed.json
    
    Returns:
        str: Path to the generated JSON file
    """
    # If output_json_path is not provided, generate a default one
    if not output_json_path:
        base_name = os.path.splitext(csv_file_path)[0]
        output_json_path = f"{base_name}_fixed.json"
    
    logger.info(f"Applying description field fix to {csv_file_path}")
    logger.info(f"Output will be saved to {output_json_path}")
    
    # Convert CSV to JSON using the updated converter
    entry_count = convert_csv_to_json(csv_file_path, output_json_path)
    logger.info(f"Converted {entry_count} entries to JSON format")
    
    # Load the generated JSON file to verify the fix
    with open(output_json_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    
    # Count entries with credit_description field
    entries_with_credit_description = sum(1 for entry in entries if "credit_description" in entry)
    logger.info(f"Found {entries_with_credit_description} entries with credit_description field")
    
    # Count consolidated entries
    consolidated_entries = sum(1 for entry in entries if entry.get("credit", {}).get("consolidated", False))
    logger.info(f"Found {consolidated_entries} consolidated entries")
    
    # Verify that all consolidated entries have a credit_description field
    consolidated_with_description = sum(1 for entry in entries 
                                      if entry.get("credit", {}).get("consolidated", False) 
                                      and "credit_description" in entry)
    
    if consolidated_with_description == consolidated_entries:
        logger.info(f"✅ All {consolidated_entries} consolidated entries have a credit_description field")
    else:
        logger.warning(f"❌ Only {consolidated_with_description} out of {consolidated_entries} consolidated entries have a credit_description field")
    
    return output_json_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Apply description field fix to a CSV file and generate a fixed JSON file.',
        epilog='Example: python apply_description_fix.py "0526-Raku export- VCT GE.utf8.csv" "fixed_output.json"'
    )
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('output_file', nargs='?', help='Output JSON file path (optional)')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Apply the description field fix
    output_path = apply_description_fix(args.input_file, args.output_file)
    
    logger.info(f"Description field fix applied successfully")
    logger.info(f"Fixed JSON file saved to {output_path}")
