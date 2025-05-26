#!/usr/bin/env python3
"""
Verification script for the description field fix

This script verifies that the description field is properly populated in the BC payload
for VPA-0000116 and VPA-0000150.
"""

import json
import logging
import sys
import os
import importlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def generate_bc_payload(entry, entry_type):
    """
    Generate a BC payload for the given entry and entry type
    """
    # Import the process_japan_exports module
    import process_japan_exports
    importlib.reload(process_japan_exports)
    
    # Create the journal line
    journal_line = process_japan_exports.create_journal_line(entry, entry_type)
    
    # Return the journal line
    return journal_line

def verify_with_real_data():
    """
    Verify the fix with real data from the JSON file
    """
    # Path to the JSON file
    json_file = '0526-Raku export- VCT GE.utf8.json'
    
    # Check if the file exists
    if not os.path.exists(json_file):
        logger.error(f"File not found: {json_file}")
        return False
    
    try:
        # Load the JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        # Find the entries for VPA-0000116 and VPA-0000150
        entry_116 = next((e for e in entries if e['voucher_no'] == 'VPA-0000116' and e['description'] == '2025/02 Mobile'), None)
        entry_150 = next((e for e in entries if e['voucher_no'] == 'VPA-0000150'), None)
        
        if not entry_116 or not entry_150:
            logger.error("Could not find the required entries in the JSON file")
            return False
        
        # Generate BC payloads for debit entries
        debit_payload_116 = generate_bc_payload(entry_116, "debit")
        debit_payload_150 = generate_bc_payload(entry_150, "debit")
        
        # Generate BC payloads for credit entries
        credit_payload_116 = generate_bc_payload(entry_116, "credit")
        credit_payload_150 = generate_bc_payload(entry_150, "credit")
        
        # Save the BC payloads to files for inspection
        with open('bc-payload-VPA-0000116-debit-fixed.json', 'w', encoding='utf-8') as f:
            json.dump(debit_payload_116, f, ensure_ascii=False, indent=2)
        
        with open('bc-payload-VPA-0000150-debit-fixed.json', 'w', encoding='utf-8') as f:
            json.dump(debit_payload_150, f, ensure_ascii=False, indent=2)
            
        with open('bc-payload-VPA-0000116-credit-fixed.json', 'w', encoding='utf-8') as f:
            json.dump(credit_payload_116, f, ensure_ascii=False, indent=2)
        
        with open('bc-payload-VPA-0000150-credit-fixed.json', 'w', encoding='utf-8') as f:
            json.dump(credit_payload_150, f, ensure_ascii=False, indent=2)
        
        # Check if the descriptions are correctly populated for debit entries
        debit_check = (debit_payload_116['Description'] == "2025/02 Mobile" and 
                       debit_payload_150['Description'] == "Group interview_Robot cybersecurity")
        
        # Check if the descriptions are correctly populated for credit entries
        # For credit entries, the description should come from the Remarks (備考) field or credit_description
        credit_check = (credit_payload_116['Description'] != "" and 
                        credit_payload_150['Description'] != "")
        
        if debit_check:
            logger.info("Verification passed: Descriptions are correctly populated in debit BC payloads")
            logger.info(f"VPA-0000116 debit description: {debit_payload_116['Description']}")
            logger.info(f"VPA-0000150 debit description: {debit_payload_150['Description']}")
        else:
            logger.error("Verification failed: Descriptions are not correctly populated in debit BC payloads")
            logger.error(f"VPA-0000116 debit description: {debit_payload_116['Description']}")
            logger.error(f"VPA-0000150 debit description: {debit_payload_150['Description']}")
        
        if credit_check:
            logger.info("Verification passed: Descriptions are populated in credit BC payloads")
            logger.info(f"VPA-0000116 credit description: {credit_payload_116['Description']}")
            logger.info(f"VPA-0000150 credit description: {credit_payload_150['Description']}")
        else:
            logger.error("Verification failed: Descriptions are not populated in credit BC payloads")
            logger.error(f"VPA-0000116 credit description: {credit_payload_116['Description']}")
            logger.error(f"VPA-0000150 credit description: {credit_payload_150['Description']}")
        
        return debit_check and credit_check
    
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the verification
    if verify_with_real_data():
        print("\nVerification passed! The description field is now properly populated in both debit and credit BC payloads.")
    else:
        print("\nVerification failed! The description field is not properly populated in one or more BC payloads.")
