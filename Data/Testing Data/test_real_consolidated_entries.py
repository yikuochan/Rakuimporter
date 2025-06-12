#!/usr/bin/env python3
"""
Test script to verify that the description field fix is working correctly with real CSV data.

This script:
1. Extracts Remarks (備考) values directly from the CSV file
2. Converts the CSV to JSON using the updated converter
3. Checks if the Remarks (備考) values are preserved in the JSON data
4. Tests if the description field in the journal lines starts with the Remarks (備考) value

Usage:
    python test_real_consolidated_entries.py <input_csv_file>

Example:
    python test_real_consolidated_entries.py "0526-Raku export- VCT GE.utf8.csv"
"""

import argparse
import csv
import json
import logging
import os
import sys
from csv_to_json_converter import convert_csv_to_json
from process_japan_exports import create_journal_line

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("description_fix_tester")

def get_biko_values_from_csv(csv_file_path):
    """Extract Remarks (備考) values from the CSV file by voucher_no"""
    biko_by_voucher = {}
    try:
        # Open the CSV file with proper encoding
        with open(csv_file_path, 'r', encoding='utf-8', newline='') as file:
            # Create a CSV reader
            reader = csv.reader(file)
            
            # Read the header row to find the index of the Remarks (備考) column and 伝票No. column
            header = next(reader)
            biko_index = header.index('Remarks') if 'Remarks' in header else (header.index('備考') if '備考' in header else -1)
            voucher_index = header.index('伝票No.') if '伝票No.' in header else -1
            
            if biko_index == -1 or voucher_index == -1:
                logger.error("Could not find required columns in the CSV file")
                return biko_by_voucher
            
            # Skip the second header row
            next(reader)
            
            # Read the data rows and collect Remarks (備考) values by voucher_no
            for row in reader:
                # Skip empty rows
                if not any(row):
                    continue
                
                # Check if the row has enough columns
                if len(row) > max(biko_index, voucher_index):
                    voucher_no = row[voucher_index]
                    biko_value = row[biko_index]
                    
                    if voucher_no and biko_value:
                        if voucher_no not in biko_by_voucher:
                            biko_by_voucher[voucher_no] = []
                        biko_by_voucher[voucher_no].append(biko_value)
            
    except Exception as e:
        logger.error(f"Error extracting Remarks (備考) values from CSV: {e}")
    
    return biko_by_voucher

def test_description_fix(csv_file_path):
    """Test that the description field fix is working correctly with real CSV data"""
    try:
        # Step 1: Extract Remarks (備考) values from the CSV file
        biko_by_voucher = get_biko_values_from_csv(csv_file_path)
        logger.info(f"Found Remarks (備考) values for {len(biko_by_voucher)} vouchers in CSV")
        
        # Print a few examples
        for i, (voucher_no, biko_values) in enumerate(list(biko_by_voucher.items())[:5]):
            logger.info(f"Example {i+1}: Voucher {voucher_no} has Remarks (備考) values: {biko_values}")
        
        # Step 2: Convert the CSV to JSON using the updated converter
        json_file_path = f"{os.path.splitext(csv_file_path)[0]}_test.json"
        entry_count = convert_csv_to_json(csv_file_path, json_file_path)
        logger.info(f"Converted {entry_count} entries to JSON format")
        
        # Step 3: Check if the Remarks (備考) values are preserved in the JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        # Find consolidated entries
        consolidated_entries = [entry for entry in entries if entry.get("credit", {}).get("consolidated", False)]
        logger.info(f"Found {len(consolidated_entries)} consolidated entries in JSON")
        
        # Check if the Remarks (備考) values are preserved in the credit_description field
        preserved_count = 0
        missing_count = 0
        
        for entry in consolidated_entries:
            voucher_no = entry.get("voucher_no", "Unknown")
            
            # Check if we have Remarks (備考) values for this voucher from the CSV
            csv_biko_values = biko_by_voucher.get(voucher_no, [])
            
            # Get the credit description from the JSON
            json_credit_description = entry.get("credit_description", "")
            
            # Log the results
            logger.info(f"Checking consolidated entry: {voucher_no}")
            logger.info(f"CSV Remarks (備考) values: {csv_biko_values}")
            logger.info(f"JSON credit_description: '{json_credit_description}'")
            
            # Verify that the credit_description matches a Remarks (備考) value from the CSV if available
            if csv_biko_values:
                # Check if any of the CSV Remarks (備考) values matches the credit_description
                found_match = False
                for biko_value in csv_biko_values:
                    if biko_value and biko_value == json_credit_description:
                        found_match = True
                        break
                
                if found_match:
                    logger.info(f"✅ credit_description matches a Remarks (備考) value from CSV")
                    preserved_count += 1
                else:
                    logger.error(f"❌ credit_description does not match any Remarks (備考) value from CSV")
                    missing_count += 1
            
            logger.info("-" * 50)
        
        # Step 4: Test if the description field in the journal lines starts with the Remarks (備考) value
        journal_line_success = 0
        journal_line_failure = 0
        
        for entry in consolidated_entries:
            voucher_no = entry.get("voucher_no", "Unknown")
            
            # Get the credit description from the JSON
            json_credit_description = entry.get("credit_description", "")
            
            # Process credit line
            credit_line = create_journal_line(entry, "credit")
            
            # Log the results
            logger.info(f"Testing journal line for consolidated entry: {voucher_no}")
            logger.info(f"JSON credit_description: '{json_credit_description}'")
            logger.info(f"Journal line description: '{credit_line['Description']}'")
            
            # Verify that the description starts with the credit_description
            if json_credit_description and credit_line["Description"].startswith(json_credit_description):
                logger.info(f"✅ Journal line description starts with credit_description")
                journal_line_success += 1
            else:
                logger.error(f"❌ Journal line description does not start with credit_description")
                journal_line_failure += 1
            
            logger.info("-" * 50)
        
        # Log summary
        logger.info(f"Summary:")
        logger.info(f"CSV to JSON conversion: {preserved_count} preserved, {missing_count} missing")
        logger.info(f"Journal line description: {journal_line_success} correct, {journal_line_failure} incorrect")
        
        return preserved_count > 0 and journal_line_success > 0
    
    except Exception as e:
        logger.error(f"Error testing description fix: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Test that the description field fix is working correctly with real CSV data.',
        epilog='Example: python test_real_consolidated_entries.py "0526-Raku export- VCT GE.utf8.csv"'
    )
    parser.add_argument('input_file', help='Input CSV file path')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Test the description fix
    success = test_description_fix(args.input_file)
    
    if success:
        logger.info("Description fix test completed successfully")
    else:
        logger.error("Description fix test failed")
        sys.exit(1)
