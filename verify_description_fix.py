#!/usr/bin/env python3
"""
Script to verify that the description field fix is working correctly.

This script:
1. Takes a JSON file as input
2. Processes a few entries using the create_journal_line function from process_japan_exports.py
3. Verifies that the descriptions in the journal lines are correct

Usage:
    python verify_description_fix.py <input_json_file>

Example:
    python verify_description_fix.py fixed_output.json
"""

import argparse
import json
import logging
import sys
from process_japan_exports import create_journal_line

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("description_fix_verifier")

def verify_description_fix(json_file_path):
    """Verify that the description field fix is working correctly"""
    try:
        # Load the JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        # Find consolidated entries
        consolidated_entries = [entry for entry in entries if entry.get("credit", {}).get("consolidated", False)]
        logger.info(f"Found {len(consolidated_entries)} consolidated entries in JSON")
        
        # Process a few consolidated entries
        for i, entry in enumerate(consolidated_entries[:5]):  # Process up to 5 entries
            voucher_no = entry.get("voucher_no", "Unknown")
            logger.info(f"Processing consolidated entry {i+1}: {voucher_no}")
            
            # Get the credit description from the JSON
            json_credit_description = entry.get("credit_description", "")
            logger.info(f"JSON credit_description: '{json_credit_description}'")
            
            # Get the Remarks (備考) value from the credit data
            biko_value = entry.get("credit", {}).get("Remarks", "") or entry.get("credit", {}).get("備考", "")
            logger.info(f"Credit Remarks (備考) value: '{biko_value}'")
            
            # Process credit line
            credit_line = create_journal_line(entry, "credit")
            
            # Log the results
            logger.info(f"Final description from create_journal_line: '{credit_line['Description']}'")
            
            # Verify that the description contains the credit_description
            if json_credit_description and json_credit_description in credit_line["Description"]:
                logger.info(f"✅ Description contains credit_description")
            else:
                logger.error(f"❌ Description does not contain credit_description")
            
            # Verify that the description contains the consolidation note
            if "Consolidated from" in credit_line["Description"]:
                logger.info(f"✅ Description contains consolidation note")
            else:
                logger.error(f"❌ Description does not contain consolidation note")
            
            logger.info("-" * 50)
        
        return True
    
    except Exception as e:
        logger.error(f"Error verifying description fix: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Verify that the description field fix is working correctly.',
        epilog='Example: python verify_description_fix.py fixed_output.json'
    )
    parser.add_argument('input_file', help='Input JSON file path')
    
    args = parser.parse_args()
    
    # Verify the description fix
    success = verify_description_fix(args.input_file)
    
    if success:
        logger.info("Description fix verification completed successfully")
    else:
        logger.error("Description fix verification failed")
        sys.exit(1)
