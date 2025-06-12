#!/usr/bin/env python3
"""
Test script to verify that the postfixes have been removed from External_Document_No and Description fields.

This script:
1. Converts a CSV file to JSON using the modified csv_to_json_converter.py
2. Checks that the External_Document_No field doesn't have "-consolidated" postfix
3. Generates a BC payload using the modified process_japan_exports.py
4. Checks that the Description field doesn't have "Consolidated from X entries" postfix

Usage:
    python test_postfix_removal.py <input_csv_file>

Example:
    python test_postfix_removal.py "0526-Raku export- VCT GE.utf8.csv"
"""

import argparse
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
logger = logging.getLogger("postfix_removal_test")

def test_postfix_removal(csv_file_path):
    """Test that the postfixes have been removed from External_Document_No and Description fields"""
    try:
        # Step 1: Convert the CSV to JSON using the updated converter
        json_file_path = f"{os.path.splitext(csv_file_path)[0]}_postfix_test.json"
        entry_count = convert_csv_to_json(csv_file_path, json_file_path)
        logger.info(f"Converted {entry_count} entries to JSON format")
        
        # Step 2: Load the JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        # Step 3: Find consolidated entries
        consolidated_entries = [entry for entry in entries if entry.get("credit", {}).get("consolidated", False)]
        logger.info(f"Found {len(consolidated_entries)} consolidated entries in JSON")
        
        if not consolidated_entries:
            logger.warning("No consolidated entries found in the JSON data. Test may not be conclusive.")
            return False
        
        # Step 4: Check External_Document_No field for "-consolidated" postfix
        external_doc_no_success = True
        for entry in consolidated_entries:
            external_doc_no = entry.get("External_Document_No", "")
            if external_doc_no.endswith("-consolidated"):
                logger.error(f"❌ External_Document_No still has '-consolidated' postfix: {external_doc_no}")
                external_doc_no_success = False
            else:
                logger.info(f"✅ External_Document_No doesn't have '-consolidated' postfix: {external_doc_no}")
        
        # Step 5: Generate BC payload for each consolidated entry and check Description field
        description_success = True
        for entry in consolidated_entries:
            # Process credit line
            credit_line = create_journal_line(entry, "credit")
            description = credit_line.get("Description", "")
            
            # Check if description contains "Consolidated from X entries"
            if "Consolidated from" in description and "entries" in description:
                logger.error(f"❌ Description still contains consolidation note: '{description}'")
                description_success = False
            else:
                logger.info(f"✅ Description doesn't contain consolidation note: '{description}'")
        
        # Step 6: Log summary
        if external_doc_no_success and description_success:
            logger.info("✅ All tests passed! Postfixes have been successfully removed.")
            return True
        else:
            logger.error("❌ Some tests failed. Postfixes may not have been completely removed.")
            return False
            
    except Exception as e:
        logger.error(f"Error testing postfix removal: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Test that the postfixes have been removed from External_Document_No and Description fields.',
        epilog='Example: python test_postfix_removal.py "0526-Raku export- VCT GE.utf8.csv"'
    )
    parser.add_argument('input_file', help='Input CSV file path')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Test the postfix removal
    success = test_postfix_removal(args.input_file)
    
    if success:
        logger.info("Postfix removal test completed successfully")
        sys.exit(0)
    else:
        logger.error("Postfix removal test failed")
        sys.exit(1)
