#!/usr/bin/env python3
"""
Script to create a truncated version of the JSON file with all string fields limited to 100 characters.
"""

import json
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("truncation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("truncation")

def truncate_string(value, max_length=100):
    """
    Truncate a string to the specified maximum length.
    
    Args:
        value: The string to truncate
        max_length: Maximum allowed length
        
    Returns:
        str: The truncated string
    """
    if not value or not isinstance(value, str):
        return value
        
    if len(value) > max_length:
        truncated = value[:max_length]
        logger.warning(f"Truncated string from {len(value)} to {max_length} characters: '{value}' -> '{truncated}'")
        return truncated
    return value

def truncate_all_strings(data, max_length=100):
    """
    Truncate all string fields in the data to the specified maximum length.
    
    Args:
        data: The JSON data to process
        max_length: Maximum allowed string length
    
    Returns:
        list: The processed data with truncated strings
    """
    truncated_count = 0
    
    for entry in data:
        # Truncate top-level string fields
        for key, value in list(entry.items()):
            if isinstance(value, str) and len(value) > max_length:
                entry[key] = truncate_string(value, max_length)
                truncated_count += 1
        
        # Truncate debit section
        if "debit" in entry:
            for key, value in list(entry["debit"].items()):
                if isinstance(value, str) and len(value) > max_length:
                    entry["debit"][key] = truncate_string(value, max_length)
                    truncated_count += 1
        
        # Truncate credit section
        if "credit" in entry:
            for key, value in list(entry["credit"].items()):
                if isinstance(value, str) and len(value) > max_length:
                    entry["credit"][key] = truncate_string(value, max_length)
                    truncated_count += 1
    
    logger.info(f"Truncated {truncated_count} string values")
    return data

def main():
    input_file = "Test Raku export-all-noNTD.json"
    output_file = "Test Raku export-all-noNTD-truncated-100.json"
    
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            logger.error(f"Input file '{input_file}' not found.")
            return
        
        logger.info(f"Reading input file: {input_file}")
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Found {len(data)} entries in the input file.")
        
        # Truncate all string fields
        truncated_data = truncate_all_strings(data)
        
        # Write the truncated data to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(truncated_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Truncated data saved to {output_file}")
        
        # Verify the output file was created
        if os.path.exists(output_file):
            logger.info(f"Output file '{output_file}' successfully created.")
            logger.info(f"File size: {os.path.getsize(output_file)} bytes")
        else:
            logger.error(f"Error: Failed to create output file '{output_file}'.")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
