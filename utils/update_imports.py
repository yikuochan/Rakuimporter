#!/usr/bin/env python3
"""
Update Imports Utility

This script updates import statements in Python files to reflect the new project structure.
It scans Python files in the specified directories and updates import statements accordingly.
"""

import os
import re
import sys
from pathlib import Path

# Define import mappings
IMPORT_MAPPINGS = {
    # Core modules
    'charset_converter': 'core.charset_converter',
    'csv_to_json_converter': 'core.csv_to_json_converter',
    'currency_converter': 'core.currency_converter',
    'exchange_rate_api': 'core.exchange_rate_api',
    'exchange_rate_query': 'core.exchange_rate_query',
    'process_japan_exports': 'core.process_japan_exports',
    
    # Utility modules
    'company_currency_mapping': 'utils.company_currency_mapping',
    'env_config': 'utils.env_config',
    'oauth_token_helper': 'utils.oauth_token_helper',
    'config': 'utils.config',
}

def update_imports(file_path):
    """
    Update import statements in a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        bool: True if file was modified, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    modified = False
    
    # Update import statements
    for old_import, new_import in IMPORT_MAPPINGS.items():
        # Match "import old_import" or "from old_import import ..."
        pattern1 = rf'import\s+{old_import}(?:\s+as\s+\w+)?'
        pattern2 = rf'from\s+{old_import}\s+import'
        
        # Replace "import old_import" with "import new_import"
        content = re.sub(pattern1, f'import {new_import}', content)
        
        # Replace "from old_import import ..." with "from new_import import ..."
        content = re.sub(pattern2, f'from {new_import} import', content)
    
    # Check if content was modified
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        modified = True
    
    return modified

def scan_directory(directory):
    """
    Scan a directory for Python files and update imports.
    
    Args:
        directory: Directory to scan
        
    Returns:
        tuple: (total_files, modified_files)
    """
    total_files = 0
    modified_files = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                total_files += 1
                
                try:
                    if update_imports(file_path):
                        modified_files += 1
                        print(f"Updated imports in {file_path}")
                except Exception as e:
                    print(f"Error updating imports in {file_path}: {str(e)}")
    
    return total_files, modified_files

def main():
    """Main function to update imports in Python files."""
    # Get directories to scan from command line arguments
    if len(sys.argv) > 1:
        directories = sys.argv[1:]
    else:
        # Default directories to scan
        directories = ['core', 'utils']
    
    total_files = 0
    modified_files = 0
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"Scanning directory: {directory}")
            dir_total, dir_modified = scan_directory(directory)
            total_files += dir_total
            modified_files += dir_modified
        else:
            print(f"Directory not found: {directory}")
    
    print(f"\nSummary: Updated imports in {modified_files} out of {total_files} Python files.")

if __name__ == "__main__":
    main()
