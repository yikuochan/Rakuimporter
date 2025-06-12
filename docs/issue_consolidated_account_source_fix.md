# Fix for ShortcutDimCode4 in Consolidated Credit Entries

## Issue Description

When processing consolidated credit entries, the `ShortcutDimCode4` field was incorrectly set to empty for vendor payments, even when the account source was `applicant_code`. This was happening because the `account_source` field was not being set for consolidated entries in the `csv_to_json_converter.py` file.

## Root Cause

In the `csv_to_json_converter.py` file, when creating consolidated credit entries, the code was not copying the `account_source` field from the template entry to the consolidated entry. This caused the `process_japan_exports.py` script to default to setting `ShortcutDimCode4` to empty for consolidated credit entries, even when the account source was `applicant_code`.

## Fix

1. Modified `csv_to_json_converter.py` to set the `account_source` field for consolidated entries based on the template entry:

```python
consolidated_credit_entry = {
    # ... existing fields ...
    "credit": {
        # ... existing fields ...
        "consolidated": True,
        "original_entries_count": len(vendor_entries),
        "account_source": template_entry["credit"].get("account_source", "")  # Added this line
    }
}
```

2. Created a `fix_consolidated_account_source.py` script to fix existing JSON files that don't have the `account_source` field set for consolidated entries:

```python
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
```

## Testing

1. Tested the fix by converting a CSV file to JSON and processing it with `process_japan_exports.py`:

```bash
python csv_to_json_converter.py -i "0523-Raku export-VCT GE-1.utf8.csv" -o "test-consolidated-account-source.json"
python process_japan_exports.py test-consolidated-account-source.json --sample-payload test-consolidated-payload.json
```

2. Verified that `ShortcutDimCode4` is now correctly set to the applicant_code value for both debit and credit lines:

```json
{
  "debit_line": {
    "Journal_Template_Name": "PURCHASES",
    "Journal_Batch_Name": "PURCHASE",
    "Document_Type": "Invoice",
    "External_Document_No": "2007/04/07",
    "Document_No": "VPA-0000108",
    "Document_Date": "2007-04-07",
    "Account_Type": "G/L Account",
    "Account_No": "74840-10",
    "Description": "",
    "Currency_Code": "",
    "Amount": 904.0,
    "Shortcut_Dimension_1_Code": "VCT",
    "Shortcut_Dimension_2_Code": "VCT.1342G",
    "ShortcutDimCode3": "",
    "ShortcutDimCode4": "10055",
    "ShortcutDimCode5": "",
    "ShortcutDimCode6": "",
    "ShortcutDimCode7": "",
    "ShortcutDimCode8": "",
    "ShortcutDimCode9": "",
    "ShortcutDimCode10": "",
    "ShortcutDimCode11": "",
    "ShortcutDimCode12": "",
    "ShortcutDimCode13": "",
    "ShortcutDimCode14": "VCT_TW0001",
    "ShortcutDimCode15": ""
  },
  "credit_line": {
    "Journal_Template_Name": "PURCHASES",
    "Journal_Batch_Name": "PURCHASE",
    "Document_Type": "Invoice",
    "External_Document_No": "2007/04/07",
    "Document_No": "VPA-0000108",
    "Document_Date": "2007-04-07",
    "Account_Type": "Vendor",
    "Account_No": "10055",
    "Description": "",
    "Currency_Code": "",
    "Amount": -904.0,
    "Shortcut_Dimension_1_Code": "VCT",
    "Shortcut_Dimension_2_Code": "VCT.9999",
    "ShortcutDimCode3": "",
    "ShortcutDimCode4": "10055",
    "ShortcutDimCode5": "",
    "ShortcutDimCode6": "",
    "ShortcutDimCode7": "",
    "ShortcutDimCode8": "",
    "ShortcutDimCode9": "",
    "ShortcutDimCode10": "",
    "ShortcutDimCode11": "",
    "ShortcutDimCode12": "",
    "ShortcutDimCode13": "",
    "ShortcutDimCode14": "",
    "ShortcutDimCode15": ""
  }
}
```

## Conclusion

This fix ensures that `ShortcutDimCode4` is correctly set for consolidated credit entries based on the account source, which is now properly propagated from the template entry to the consolidated entry.
