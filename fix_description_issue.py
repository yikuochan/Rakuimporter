#!/usr/bin/env python3
"""
Script to fix the description field issue in the process_japan_exports.py file.
This script creates a modified version of the file that ensures the description field
is properly populated in the BC payload.
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
    if not os.path.exists(backup_file):
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created backup of original file: {backup_file}")
        except Exception as e:
            print(f"Error creating backup file: {str(e)}")
            sys.exit(1)
    
    # Find the create_journal_line function
    create_journal_line_start = content.find("def create_journal_line(entry, entry_type):")
    if create_journal_line_start == -1:
        print("Error: Could not find create_journal_line function in the file.")
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
    
    # Fix the issue with the description field not being properly populated
    # Look for the post_journal_line function
    post_journal_line_start = modified_content.find("def post_journal_line(journal_line, company_code):")
    if post_journal_line_start == -1:
        print("Error: Could not find post_journal_line function in the file.")
        sys.exit(1)
    
    # Add a check to ensure the description field is populated
    post_journal_line_code = """def post_journal_line(journal_line, company_code):
    """
    
    post_journal_line_fixed = """def post_journal_line(journal_line, company_code):
    # Ensure the description field is populated
    if not journal_line.get("Description"):
        # Get the document number for logging
        doc_no = journal_line.get("Document_No", "Unknown")
        logger.warning(f"Description field is empty for Document_No: {doc_no}. Setting default description.")
        
        # Set a default description based on the document number
        journal_line["Description"] = f"Transaction for {doc_no}"
    
    """
    
    modified_content = modified_content.replace(post_journal_line_code, post_journal_line_fixed)
    
    # Write the modified content to a new file
    fixed_file = 'process_japan_exports_fixed_v2.py'
    try:
        with open(fixed_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"Created fixed file: {fixed_file}")
    except Exception as e:
        print(f"Error writing fixed file: {str(e)}")
        sys.exit(1)
    
    print("\nFix applied successfully!")
    print("The fix adds additional logging and ensures the description field is never empty.")
    print("To use the fixed version:")
    print(f"1. Review the changes in {fixed_file}")
    print(f"2. If satisfied, rename {fixed_file} to process_japan_exports.py")
    print(f"3. The original file has been backed up to {backup_file}")

if __name__ == "__main__":
    fix_description_issue()
