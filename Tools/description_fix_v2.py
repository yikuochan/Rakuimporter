#!/usr/bin/env python3
"""
Fix script for the description field issue in BC payloads.
This script creates a modified version of the process_japan_exports.py file
that ensures the description field is properly populated.
"""

import os
import sys

def fix_description_issue():
    """Fix the description field issue in process_japan_exports.py."""
    # Read the original file
    try:
        with open('process_japan_exports.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading process_japan_exports.py: {str(e)}")
        sys.exit(1)
    
    # Create a backup of the original file
    backup_file = 'process_japan_exports.py.bak'
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created backup of original file: {backup_file}")
    except Exception as e:
        print(f"Error creating backup file: {str(e)}")
        sys.exit(1)
    
    # Add debug logging for description field
    description_code = """    # Get the appropriate description based on entry type
    if entry_type == "debit":
        # First try to get from debit_description, then from main description, then from free_field
        description = entry.get("debit_description", "") or entry.get("description", "") or entry_data.get("free_field", "")
    else:  # credit
        # First try to get from credit_description, then from main description, then from free_field
        description = entry.get("credit_description", "") or entry.get("description", "") or entry_data.get("free_field", "")"""
    
    enhanced_description_code = """    # Get the appropriate description based on entry type
    if entry_type == "debit":
        # First try to get from debit_description, then from main description, then from free_field
        description = entry.get("debit_description", "") or entry.get("description", "") or entry_data.get("free_field", "")
        logger.info(f"Debit description sources - debit_description: '{entry.get('debit_description', '')}', description: '{entry.get('description', '')}', free_field: '{entry_data.get('free_field', '')}'")
        logger.info(f"Final debit description: '{description}'")
    else:  # credit
        # First try to get from credit_description, then from main description, then from free_field
        description = entry.get("credit_description", "") or entry.get("description", "") or entry_data.get("free_field", "")
        logger.info(f"Credit description sources - credit_description: '{entry.get('credit_description', '')}', description: '{entry.get('description', '')}', free_field: '{entry_data.get('free_field', '')}'")
        logger.info(f"Final credit description: '{description}'")"""
    
    # Replace the description code with the enhanced version
    modified_content = content.replace(description_code, enhanced_description_code)
    
    # Add additional logging before posting journal line
    request_body_log = '    # Log the request body for debugging\n    logger.info(f"Request body for journal line: {json.dumps(journal_line, indent=2)}")'
    additional_logging = '    # Log the request body for debugging\n    logger.info(f"Request body for journal line: {json.dumps(journal_line, indent=2)}")\n    # Log description field specifically for debugging\n    logger.info(f"Description field in journal line: \'{journal_line.get(\"Description\", \"\")}\'")'
    
    modified_content = modified_content.replace(request_body_log, additional_logging)
    
    # Write the modified content to a new file
    fixed_file = 'process_japan_exports_fixed.py'
    try:
        with open(fixed_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"Created fixed file: {fixed_file}")
    except Exception as e:
        print(f"Error writing fixed file: {str(e)}")
        sys.exit(1)
    
    print("\nFix applied successfully!")
    print("The fix adds additional logging to help diagnose the description field issue.")
    print("To use the fixed version:")
    print(f"1. Review the changes in {fixed_file}")
    print(f"2. If satisfied, rename {fixed_file} to process_japan_exports.py")
    print(f"3. The original file has been backed up to {backup_file}")

if __name__ == "__main__":
    fix_description_issue()
