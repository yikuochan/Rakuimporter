#!/usr/bin/env python3
"""
Reorganize Project Script

This script helps reorganize the Power Importer project structure.
It creates the necessary directories, moves files to their appropriate locations,
and updates import statements in Python files.
"""

import os
import shutil
import sys
from pathlib import Path

# Define the project structure
PROJECT_STRUCTURE = {
    'core': {
        'api': {},
        'converters': {},
        'currency': {},
    },
    'utils': {},
    'docs': {},
    'examples': {},
    'Temp': {
        'data': {},
        'tests': {},
        'rate_table': {},  # Added for rate table POC
    },
}

# Define file mappings
FILE_MAPPINGS = {
    # Core files
    'charset_converter.py': 'core/charset_converter.py',
    'exchange_rate_api.py': 'core/exchange_rate_api.py',
    'exchange_rate_query.py': 'core/exchange_rate_query.py',
    'currency_converter.py': 'core/currency_converter.py',
    'csv_to_json_converter.py': 'core/csv_to_json_converter.py',
    'process_japan_exports.py': 'core/process_japan_exports.py',
    
    # Utility files
    'company_currency_mapping.py': 'utils/company_currency_mapping.py',
    'env_config.py': 'utils/env_config.py',
    'oauth_token_helper.py': 'utils/oauth_token_helper.py',
    
    # Documentation files
    'balance_verification_guide.md': 'docs/balance_verification_guide.md',
    'currency_rounding_integration_guide.md': 'docs/currency_rounding_integration_guide.md',
    'currency_modification_report.md': 'docs/currency_modification_report.md',
    'currency_rounding_fix_implementation.md': 'docs/currency_rounding_fix_implementation.md',
    'currency_rounding_fix_summary.md': 'docs/currency_rounding_fix_summary.md',
    'description_field_fix_documentation.md': 'docs/description_field_fix_documentation.md',
    'dimension4_update.md': 'docs/dimension4_update.md',
    'document_no_discrepancy_report.md': 'docs/document_no_discrepancy_report.md',
    'issue_consolidated_account_source_fix.md': 'docs/issue_consolidated_account_source_fix.md',
    'issue_currency_handling_fix.md': 'docs/issue_currency_handling_fix.md',
    'issue_currency_prefix_enhancement.md': 'docs/issue_currency_prefix_enhancement.md',
    'issue_currency_prefix_fix.md': 'docs/issue_currency_prefix_fix.md',
    'issue_document_no_duplicate_fix_update.md': 'docs/issue_document_no_duplicate_fix_update.md',
    'issue_document_no_duplicate_fix.md': 'docs/issue_document_no_duplicate_fix.md',
    'issue_document_no_fix_update.md': 'docs/issue_document_no_fix_update.md',
    'issue_document_no_fix.md': 'docs/issue_document_no_fix.md',
    'issue_summary.md': 'docs/issue_summary.md',
    'oba_0000027_fix_summary.md': 'docs/oba_0000027_fix_summary.md',
    'overseas_vendor_currency_fix.md': 'docs/overseas_vendor_currency_fix.md',
    'postfix_removal_documentation.md': 'docs/postfix_removal_documentation.md',
    'rate_limiting_documentation.md': 'docs/rate_limiting_documentation.md',
    'README_bc_api_setup.md': 'docs/README_bc_api_setup.md',
    'README_charset_converter.md': 'docs/README_charset_converter.md',
    'README_document_no_analysis.md': 'docs/README_document_no_analysis.md',
    'README_erp_integration.md': 'docs/README_erp_integration.md',
    'README_exchange_rate_api.md': 'docs/README_exchange_rate_api.md',
    'README_oauth_token.md': 'docs/README_oauth_token.md',
    'README_postman_bc_api.md': 'docs/README_postman_bc_api.md',
    'README_postman_guide.md': 'docs/README_postman_guide.md',
    'v_vc00048_vct_responsibility_implementation_summary.md': 'docs/v_vc00048_vct_responsibility_implementation_summary.md',
    'v_vc00048_vct_responsibility_implementation.md': 'docs/v_vc00048_vct_responsibility_implementation.md',
}

# Define test file patterns
TEST_FILE_PATTERNS = [
    'test_*.py',
    'analyze_*.py',
    'check_*.py',
    'debug_*.py',
    'fix_*.py',
    'verify_*.py',
    'currency_rounding_fix.py',
    'currency_rounding_fix_updated.py',
]

# Define tool file mappings
TOOL_FILE_MAPPINGS = {
    'description_fix.py': 'Tools/description_fix.py',
    'description_fix_v2.py': 'Tools/description_fix_v2.py',
    'run_test.py': 'Tools/run_test.py',
    'run_tests.py': 'Tools/run_tests.py',
    'sync_client_secret.py': 'Tools/sync_client_secret.py',
}

# Define data file patterns
DATA_FILE_PATTERNS = [
    '*.csv',
    '*.json',
    '*.xlsx',
]

def create_directory_structure(base_dir):
    """Create the directory structure."""
    def create_dirs(structure, current_path):
        for name, substructure in structure.items():
            path = os.path.join(current_path, name)
            os.makedirs(path, exist_ok=True)
            
            # Create __init__.py for Python packages
            if name in ['core', 'utils'] or (current_path.endswith('core') and name in ['api', 'converters', 'currency']):
                init_file = os.path.join(path, '__init__.py')
                if not os.path.exists(init_file):
                    with open(init_file, 'w') as f:
                        f.write('"""' + name.capitalize() + ' package."""\n')
            
            create_dirs(substructure, path)
    
    create_dirs(PROJECT_STRUCTURE, base_dir)
    print("Directory structure created.")

def copy_files(base_dir):
    """Copy files to their new locations."""
    # Copy files defined in FILE_MAPPINGS
    for source, dest in FILE_MAPPINGS.items():
        source_path = os.path.join(base_dir, source)
        dest_path = os.path.join(base_dir, dest)
        
        if os.path.exists(source_path):
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(source_path, dest_path)
            print(f"Copied {source} to {dest}")
        else:
            print(f"Warning: Source file {source} not found.")
    
    # Copy tool files defined in TOOL_FILE_MAPPINGS
    for source, dest in TOOL_FILE_MAPPINGS.items():
        source_path = os.path.join(base_dir, source)
        dest_path = os.path.join(base_dir, dest)
        
        if os.path.exists(source_path):
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(source_path, dest_path)
            print(f"Copied {source} to {dest}")
        else:
            print(f"Warning: Tool file {source} not found.")

def copy_test_files(base_dir):
    """Copy test files to the Temp/tests directory."""
    tests_dir = os.path.join(base_dir, 'Temp', 'tests')
    os.makedirs(tests_dir, exist_ok=True)
    
    for pattern in TEST_FILE_PATTERNS:
        for file in Path(base_dir).glob(pattern):
            if file.is_file():
                dest_path = os.path.join(tests_dir, file.name)
                shutil.copy2(file, dest_path)
                print(f"Copied test file {file.name} to Temp/tests/")

def copy_data_files(base_dir):
    """Copy data files to the Temp/data directory."""
    data_dir = os.path.join(base_dir, 'Temp', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Exclude package.json and package-lock.json
    exclude_files = ['package.json', 'package-lock.json', 'requirements.txt']
    
    for pattern in DATA_FILE_PATTERNS:
        for file in Path(base_dir).glob(pattern):
            if file.is_file() and file.name not in exclude_files:
                dest_path = os.path.join(data_dir, file.name)
                shutil.copy2(file, dest_path)
                print(f"Copied data file {file.name} to Temp/data/")
    
    # Move Data/Rate Table to Temp/rate_table
    rate_table_src = os.path.join(base_dir, 'Data', 'Rate Table')
    rate_table_dest = os.path.join(base_dir, 'Temp', 'rate_table')
    
    if os.path.exists(rate_table_src):
        os.makedirs(rate_table_dest, exist_ok=True)
        
        # Copy Excel files only, skip the virtual environment
        for file in Path(rate_table_src).glob('*.xlsx'):
            if file.is_file():
                dest_path = os.path.join(rate_table_dest, file.name)
                shutil.copy2(file, dest_path)
                print(f"Copied rate table file {file.name} to Temp/rate_table/")
        
        print(f"Moved rate table files from Data/Rate Table to Temp/rate_table")

def copy_example_files(base_dir):
    """Copy example files to the examples directory."""
    examples_dir = os.path.join(base_dir, 'examples')
    os.makedirs(examples_dir, exist_ok=True)
    
    # Create a .gitkeep file to ensure the directory is tracked by Git
    with open(os.path.join(examples_dir, '.gitkeep'), 'w') as f:
        pass
    
    print("Created examples directory with .gitkeep file.")

def main():
    """Main function to reorganize the project."""
    # Get the base directory
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = os.getcwd()
    
    print(f"Reorganizing project in {base_dir}")
    
    # Create the directory structure
    create_directory_structure(base_dir)
    
    # Copy files
    copy_files(base_dir)
    copy_test_files(base_dir)
    copy_data_files(base_dir)
    copy_example_files(base_dir)
    
    print("\nProject reorganization completed successfully!")
    print("\nNext steps:")
    print("1. Run 'python utils/update_imports.py' to update import statements in Python files.")
    print("2. Review the reorganized files and make any necessary adjustments.")
    print("3. Update the documentation to reflect the new project structure.")
    print("4. Test the application to ensure everything works correctly.")

if __name__ == "__main__":
    main()
