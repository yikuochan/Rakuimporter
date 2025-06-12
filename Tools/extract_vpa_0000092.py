#!/usr/bin/env python3
"""
Extract entries with voucher_no VPA-0000092 from a JSON file.
"""

import json
import sys

def extract_entries(input_file, output_file, voucher_no):
    """
    Extract entries with the specified voucher_no from a JSON file.
    
    Args:
        input_file (str): Path to the input JSON file
        output_file (str): Path to the output JSON file
        voucher_no (str): Voucher number to extract
        
    Returns:
        int: Number of entries extracted
    """
    try:
        # Load the JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract entries with the specified voucher_no
        entries = [e for e in data if e.get('voucher_no') == voucher_no]
        
        # Write the extracted entries to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        
        print(f"Extracted {len(entries)} entries with voucher_no {voucher_no} to {output_file}")
        return len(entries)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 0

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python extract_vpa_0000092.py <input_file> <output_file> <voucher_no>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    voucher_no = sys.argv[3]
    
    num_entries = extract_entries(input_file, output_file, voucher_no)
    sys.exit(0 if num_entries > 0 else 1)
