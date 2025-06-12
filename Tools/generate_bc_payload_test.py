#!/usr/bin/env python3
"""
Test script to generate a BC payload for VPA-0000093 using the fixed version of process_japan_exports.py.
"""

import json
import sys
import os
import logging
from process_japan_exports import create_journal_line

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_bc_payload():
    """Generate a BC payload for VPA-0000093 using the fixed version of process_japan_exports.py."""
    # Load the JSON data for VPA-0000093
    try:
        with open('0526-Raku export- VCT GE.utf8.json', 'r', encoding='utf-8') as f:
            entries = json.load(f)
    except Exception as e:
        logger.error(f"Error loading input file: {str(e)}")
        sys.exit(1)
    
    # Find the entry for VPA-0000093
    vpa_0000093_entry = None
    for entry in entries:
        if entry.get('voucher_no') == 'VPA-0000093':
            vpa_0000093_entry = entry
            break
    
    if not vpa_0000093_entry:
        logger.error("Entry for VPA-0000093 not found in the JSON file.")
        sys.exit(1)
    
    # Print the entry data to verify the description fields
    logger.info("Entry data for VPA-0000093:")
    logger.info(f"Main description: '{vpa_0000093_entry.get('description', '')}'")
    logger.info(f"Debit free_field: '{vpa_0000093_entry.get('debit', {}).get('free_field', '')}'")
    logger.info(f"Credit free_field: '{vpa_0000093_entry.get('credit', {}).get('free_field', '')}'")
    
    # Create journal lines for debit and credit
    debit_line = create_journal_line(vpa_0000093_entry, "debit")
    credit_line = create_journal_line(vpa_0000093_entry, "credit")
    
    # Print the description fields from the journal lines
    logger.info("\nJournal line descriptions:")
    logger.info(f"Debit line description: '{debit_line['Description']}'")
    logger.info(f"Credit line description: '{credit_line['Description']}'")
    
    # Create a sample payload for testing
    payload = {
        "debit_line": debit_line,
        "credit_line": credit_line
    }
    
    # Save the payload to a file
    output_file = 'bc-payload-vpa-0000093-generated.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.info(f"\nSample payload saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving payload: {str(e)}")
    
    # Create a test case with empty description
    logger.info("\nTesting with empty description:")
    empty_desc_entry = vpa_0000093_entry.copy()
    empty_desc_entry['description'] = ''
    empty_desc_entry['debit']['free_field'] = ''
    empty_desc_entry['credit']['free_field'] = ''
    
    # Create journal lines for the empty description entry
    empty_debit_line = create_journal_line(empty_desc_entry, "debit")
    empty_credit_line = create_journal_line(empty_desc_entry, "credit")
    
    # Print the description fields from the journal lines
    logger.info("\nJournal line descriptions (empty description test):")
    logger.info(f"Debit line description: '{empty_debit_line['Description']}'")
    logger.info(f"Credit line description: '{empty_credit_line['Description']}'")
    
    # Create a sample payload for the empty description test
    empty_desc_payload = {
        "debit_line": empty_debit_line,
        "credit_line": empty_credit_line
    }
    
    # Save the payload to a file
    empty_desc_output_file = 'bc-payload-vpa-0000093-empty-desc.json'
    try:
        with open(empty_desc_output_file, 'w', encoding='utf-8') as f:
            json.dump(empty_desc_payload, f, ensure_ascii=False, indent=2)
        logger.info(f"\nEmpty description test payload saved to {empty_desc_output_file}")
    except Exception as e:
        logger.error(f"Error saving empty description payload: {str(e)}")

if __name__ == "__main__":
    generate_bc_payload()
