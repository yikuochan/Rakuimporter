#!/usr/bin/env python3
"""
Fix account_source field for consolidated entries in JSON files.

This script adds the account_source field to consolidated entries in JSON files
based on the account_source field of the template entry.

Usage:
    python fix_consolidated_account_source.py <input_json_file>

Example:
    python fix_consolidated_account_source.py vpa-0000092.json
"""

import json
import sys
import os

def fix_consolidated_account_source(input_file):
    """
    Fix account_source field for consolidated entries in JSON files.
    
    Args:
        input_file (str): Path to the input JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load the JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        # Group entries by voucher_no
        voucher_groups = {}
        for entry in entries:
            voucher_no = entry.get('voucher_no', '')
            if voucher_no not in voucher_groups:
                voucher_groups[voucher_no] = []
            voucher_groups[voucher_no].append(entry)
        
        # Process each voucher group
        for voucher_no, group in voucher_groups.items():
            # Find consolidated entries
            consolidated_entries = [e for e in group if e.get('credit', {}).get('consolidated', False)]
            
            # Find non-consolidated entries with the same voucher_no
            non_consolidated_entries = [e for e in group if not e.get('credit', {}).get('consolidated', False)]
            
            # For each consolidated entry, set account_source based on non-consolidated entries
            for consolidated_entry in consolidated_entries:
                if non_consolidated_entries:
                    # Use the account_source from the first non-consolidated entry
                    account_source = non_consolidated_entries[0].get('credit', {}).get('account_source', '')
                    if account_source:
                        consolidated_entry['credit']['account_source'] = account_source
                        print(f"Set account_source to '{account_source}' for consolidated entry with voucher_no '{voucher_no}'")
        
        # Write the updated entries back to the file
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully updated {input_file}")
        return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_consolidated_account_source.py <input_json_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    success = fix_consolidated_account_source(input_file)
    sys.exit(0 if success else 1)