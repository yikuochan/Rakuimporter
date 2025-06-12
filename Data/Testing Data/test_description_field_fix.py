#!/usr/bin/env python3
"""
Test script to verify that the fix for the empty Description field in BC payload works correctly.

This script:
1. Runs the fix_description_field.py script to modify the csv_to_json_converter.py script
2. Verifies that the "Remarks" field is populated in the credit object for VPA-0000116
3. Generates a new BC payload using the modified JSON file
4. Verifies that the Description field is no longer empty in the BC payload
"""

import os
import sys
import logging
import json
import subprocess
import tempfile
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_description_field_fix")

def run_fix_script():
    """
    Run the fix_description_field.py script to modify the csv_to_json_converter.py script.
    """
    try:
        cmd = "python fix_description_field.py"
        logger.info(f"Running command: {cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error running fix_description_field.py: {result.stderr}")
            return False
        
        logger.info(f"Successfully ran fix_description_field.py")
        logger.info(f"Output: {result.stdout}")
        return True
    
    except Exception as e:
        logger.error(f"Error running fix script: {e}")
        return False

def verify_json_fix(json_file="0526-Raku export- VCT GE.utf8_fixed.json", document_no="VPA-0000116"):
    """
    Verify that the "Remarks" field is populated in the credit object for the specified document_no.
    """
    try:
        # Read the JSON file
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Find the entry with the specified document_no
        for entry in data:
            if entry.get("voucher_no") == document_no:
                # Check if the entry has a consolidated credit entry
                if "consolidated" in entry.get("credit", {}):
                    remarks = entry["credit"].get("Remarks", "")
                    credit_description = entry.get("credit_description", "")
                    
                    logger.info(f"Found consolidated entry for {document_no}")
                    logger.info(f"credit_description: '{credit_description}'")
                    logger.info(f"Remarks: '{remarks}'")
                    
                    if remarks == credit_description:
                        logger.info(f"Fix successful! Remarks field matches credit_description for {document_no}")
                        return True
                    elif remarks:
                        logger.info(f"Fix partially successful! Remarks field is populated but doesn't match credit_description for {document_no}")
                        return True
                    else:
                        logger.warning(f"Fix failed! Remarks field is still empty for {document_no}")
                        return False
        
        logger.warning(f"Could not find consolidated entry for {document_no}")
        return False
    
    except Exception as e:
        logger.error(f"Error verifying JSON fix: {e}")
        return False

def generate_bc_payload(json_file="0526-Raku export- VCT GE.utf8_fixed.json", document_no="VPA-0000116"):
    """
    Generate a new BC payload using the modified JSON file for the specified document_no.
    """
    try:
        # Create a temporary file to store the BC payload
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Run the generate_bc_payload_test.py script
        cmd = f"python generate_bc_payload_test.py -i '{json_file}' -d '{document_no}' > '{temp_path}'"
        logger.info(f"Running command: {cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error running generate_bc_payload_test.py: {result.stderr}")
            return None
        
        logger.info(f"Successfully generated BC payload for {document_no}")
        
        # Read the BC payload from the temporary file
        with open(temp_path, 'r', encoding='utf-8') as file:
            payload = file.read()
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        return payload
    
    except Exception as e:
        logger.error(f"Error generating BC payload: {e}")
        return None

def verify_bc_payload(payload, document_no="VPA-0000116"):
    """
    Verify that the Description field is no longer empty in the BC payload.
    """
    try:
        if not payload:
            logger.error("BC payload is empty")
            return False
        
        # Check if the warning message about empty Description field is present
        warning_message = f"WARNING - Description field is empty for Document_No: {document_no}"
        
        if warning_message in payload:
            logger.warning(f"Fix failed! Warning message about empty Description field is still present in BC payload")
            return False
        
        # Check if the Description field is populated with a value other than the default
        default_description = f"Transaction for {document_no}"
        
        # Extract the Description field value from the payload
        description_start = payload.find('"Description": "')
        if description_start == -1:
            logger.error("Could not find Description field in BC payload")
            return False
        
        description_start += len('"Description": "')
        description_end = payload.find('"', description_start)
        if description_end == -1:
            logger.error("Could not find end of Description field in BC payload")
            return False
        
        description = payload[description_start:description_end]
        
        if description == default_description:
            logger.warning(f"Fix failed! Description field still has default value: '{default_description}'")
            return False
        
        logger.info(f"Fix successful! Description field is populated with: '{description}'")
        return True
    
    except Exception as e:
        logger.error(f"Error verifying BC payload: {e}")
        return False

def save_bc_payload(payload, document_no="VPA-0000116"):
    """
    Save the BC payload to a file for inspection.
    """
    try:
        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"bc-payload-{document_no}-fixed-{timestamp}.log"
        
        # Write the payload to the file
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(payload)
        
        logger.info(f"Saved BC payload to {filename}")
        return filename
    
    except Exception as e:
        logger.error(f"Error saving BC payload: {e}")
        return None

def main():
    """
    Main function to test the fix for the empty Description field in BC payload.
    """
    document_no = "VPA-0000116"
    json_file = "0526-Raku export- VCT GE.utf8_fixed.json"
    
    logger.info(f"Starting test for fix of empty Description field in BC payload for {document_no}")
    
    # Run the fix script
    if not run_fix_script():
        logger.error("Failed to run fix script")
        return False
    
    # Verify the JSON fix
    if not verify_json_fix(json_file, document_no):
        logger.error("Failed to verify JSON fix")
        return False
    
    # Generate a new BC payload
    payload = generate_bc_payload(json_file, document_no)
    if not payload:
        logger.error("Failed to generate BC payload")
        return False
    
    # Save the BC payload for inspection
    save_bc_payload(payload, document_no)
    
    # Verify the BC payload
    if not verify_bc_payload(payload, document_no):
        logger.error("Failed to verify BC payload")
        return False
    
    logger.info(f"Successfully tested fix for empty Description field in BC payload for {document_no}")
    return True

if __name__ == "__main__":
    main()
