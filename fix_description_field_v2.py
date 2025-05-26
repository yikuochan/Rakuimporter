#!/usr/bin/env python3
"""
Script to fix the issue with empty Description field in BC payload for Document_No: VPA-0000116.

The issue is that the "備考" column value from the CSV file is stored in the "credit_description" field
at the entry level, but it's not being properly transferred to the "Remarks" field of the consolidated credit object.

This script modifies the csv_to_json_converter.py script to:
1. Add the "Remarks" field to the credit object in the entry dictionary
2. Ensure the "Remarks" field is properly transferred to the consolidated credit entry
"""

import os
import sys
import logging
import json
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("description_field_fix_v2")

def fix_csv_to_json_converter():
    """
    Modify the csv_to_json_converter.py script to add the "Remarks" field to the credit object
    and ensure it's properly transferred to the consolidated credit entry.
    """
    try:
        # Read the original file
        with open('csv_to_json_converter.py', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Make a backup of the original file
        with open('csv_to_json_converter.py.bak', 'w', encoding='utf-8') as file:
            file.write(content)
        
        logger.info("Created backup of csv_to_json_converter.py as csv_to_json_converter.py.bak")
        
        # Find the section where the entry dictionary is created
        entry_dict_start = content.find('entry = {')
        if entry_dict_start == -1:
            logger.error("Could not find the entry dictionary creation in csv_to_json_converter.py")
            return False
        
        # Find the "credit" section in the entry dictionary
        credit_section_start = content.find('"credit": {', entry_dict_start)
        if credit_section_start == -1:
            logger.error("Could not find the credit section in the entry dictionary")
            return False
        
        # Find the end of the credit section
        credit_section_end = content.find('}', credit_section_start)
        if credit_section_end == -1:
            logger.error("Could not find the end of the credit section")
            return False
        
        # Extract the credit section
        credit_section = content[credit_section_start:credit_section_end + 1]
        
        # Add the "Remarks" field to the credit section
        new_credit_section = credit_section.replace(
            '"department_code": credit_data.get("借方：負担部門コード") or ""',
            '"department_code": credit_data.get("借方：負担部門コード") or "",'
            '\n                "Remarks": credit_data.get("Remarks") or credit_data.get("備考") or ""'
        )
        
        # Replace the credit section in the content
        new_content = content.replace(credit_section, new_credit_section)
        
        # Now fix the consolidated credit entry creation
        consolidated_credit_section_start = new_content.find('"credit": {', new_content.find('consolidated_credit_entry = {'))
        if consolidated_credit_section_start == -1:
            logger.error("Could not find the consolidated credit section")
            return False
        
        consolidated_credit_section_end = new_content.find('}', consolidated_credit_section_start)
        if consolidated_credit_section_end == -1:
            logger.error("Could not find the end of the consolidated credit section")
            return False
        
        # Extract the consolidated credit section
        consolidated_credit_section = new_content[consolidated_credit_section_start:consolidated_credit_section_end + 1]
        
        # Update the "Remarks" field in the consolidated credit section
        new_consolidated_credit_section = consolidated_credit_section.replace(
            '"Remarks": template_entry["credit"].get("Remarks", "") or template_entry["credit"].get("備考", "")',
            '"Remarks": template_entry["credit_description"] or template_entry["credit"].get("Remarks", "") or template_entry["credit"].get("備考", "")'
        )
        
        # Replace the consolidated credit section in the content
        final_content = new_content.replace(consolidated_credit_section, new_consolidated_credit_section)
        
        # Write the modified content back to the file
        with open('csv_to_json_converter.py', 'w', encoding='utf-8') as file:
            file.write(final_content)
        
        logger.info("Successfully modified csv_to_json_converter.py to fix the Description field issue")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing csv_to_json_converter.py: {e}")
        return False

def regenerate_json_file(csv_file, json_file):
    """
    Regenerate the JSON file from the CSV file using the modified csv_to_json_converter.py script.
    """
    try:
        # Run the csv_to_json_converter.py script
        cmd = f"python csv_to_json_converter.py -i '{csv_file}' -o '{json_file}'"
        logger.info(f"Running command: {cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error running csv_to_json_converter.py: {result.stderr}")
            return False
        
        logger.info(f"Successfully regenerated {json_file} from {csv_file}")
        logger.info(f"Output: {result.stdout}")
        return True
    
    except Exception as e:
        logger.error(f"Error regenerating JSON file: {e}")
        return False

def verify_fix(json_file, document_no="VPA-0000116"):
    """
    Verify that the fix worked by checking if the "Remarks" field is populated in the credit object
    for the specified document_no.
    """
    try:
        # Read the JSON file
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Find the entry with the specified document_no
        for entry in data:
            if entry.get("voucher_no") == document_no:
                # Check if the entry has a consolidated credit entry
                if entry.get("credit", {}).get("consolidated", False):
                    remarks = entry["credit"].get("Remarks", "")
                    credit_description = entry.get("credit_description", "")
                    
                    logger.info(f"Found consolidated entry for {document_no}")
                    logger.info(f"credit_description: '{credit_description}'")
                    logger.info(f"Remarks: '{remarks}'")
                    
                    if remarks:
                        logger.info(f"Fix successful! Remarks field is populated for {document_no}")
                        return True
                    else:
                        logger.warning(f"Fix failed! Remarks field is still empty for {document_no}")
                        return False
        
        logger.warning(f"Could not find consolidated entry for {document_no}")
        return False
    
    except Exception as e:
        logger.error(f"Error verifying fix: {e}")
        return False

def generate_bc_payload(json_file, document_no="VPA-0000116"):
    """
    Generate a BC payload for the specified document_no to verify that the Description field is populated.
    """
    try:
        # Create a filename for the BC payload
        bc_payload_file = f"bc-payload-{document_no}-fixed.log"
        
        # Run the generate_bc_payload_test.py script
        cmd = f"python generate_bc_payload_test.py -i '{json_file}' -d '{document_no}' > '{bc_payload_file}'"
        logger.info(f"Running command: {cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error running generate_bc_payload_test.py: {result.stderr}")
            return False
        
        logger.info(f"Successfully generated BC payload for {document_no}")
        logger.info(f"BC payload saved to {bc_payload_file}")
        
        # Check if the BC payload contains the warning about empty Description field
        with open(bc_payload_file, 'r', encoding='utf-8') as file:
            payload = file.read()
        
        warning_message = f"WARNING - Description field is empty for Document_No: {document_no}"
        
        if warning_message in payload:
            logger.warning(f"Fix failed! Warning message about empty Description field is still present in BC payload")
            return False
        
        logger.info(f"Fix successful! No warning message about empty Description field in BC payload")
        return True
    
    except Exception as e:
        logger.error(f"Error generating BC payload: {e}")
        return False

def main():
    """
    Main function to fix the issue with empty Description field in BC payload.
    """
    csv_file = "0526-Raku export- VCT GE.utf8.csv"
    json_file = "0526-Raku export- VCT GE.utf8_fixed.json"
    document_no = "VPA-0000116"
    
    logger.info(f"Starting fix for empty Description field in BC payload for {document_no}")
    
    # Fix the csv_to_json_converter.py script
    if not fix_csv_to_json_converter():
        logger.error("Failed to fix csv_to_json_converter.py")
        return False
    
    # Regenerate the JSON file
    if not regenerate_json_file(csv_file, json_file):
        logger.error("Failed to regenerate JSON file")
        return False
    
    # Verify the fix in the JSON file
    if not verify_fix(json_file, document_no):
        logger.error("Failed to verify fix in JSON file")
        return False
    
    # Generate a BC payload to verify the fix
    if not generate_bc_payload(json_file, document_no):
        logger.error("Failed to verify fix in BC payload")
        return False
    
    logger.info(f"Successfully fixed the issue with empty Description field in BC payload for {document_no}")
    return True

if __name__ == "__main__":
    main()
