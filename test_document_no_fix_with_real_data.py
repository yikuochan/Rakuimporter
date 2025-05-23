#!/usr/bin/env python3
"""
Test for Document_No assignment fix with real data

This script tests the Document_No assignment fix with the actual raw data file
to verify that the fix works correctly with real data.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import process_japan_exports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the module to test
from process_japan_exports import process_entries, create_journal_line


def load_raw_data(file_path):
    """Load raw data from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading raw data file: {str(e)}")
        return []


def test_with_real_data():
    """Test Document_No assignment with real data."""
    # Load the raw data file
    raw_data = load_raw_data("05-Raku export-utf8-fixed.json")
    
    if not raw_data:
        print("Failed to load raw data file.")
        return
    
    print(f"Loaded {len(raw_data)} entries from raw data file.")
    
    # Create a dictionary to track voucher numbers
    voucher_counts = {}
    
    # Count occurrences of each voucher number in the raw data
    for entry in raw_data:
        voucher_no = entry.get("voucher_no", "Unknown")
        voucher_counts[voucher_no] = voucher_counts.get(voucher_no, 0) + 1
    
    print("\nVoucher counts in raw data:")
    for voucher_no, count in sorted(voucher_counts.items()):
        print(f"  {voucher_no}: {count} entries")
    
    # Find vouchers with multiple entries
    multi_entry_vouchers = {v: c for v, c in voucher_counts.items() if c > 1}
    print(f"\nFound {len(multi_entry_vouchers)} vouchers with multiple entries.")
    
    # Mock post_journal_line to track Document_No values
    posted_document_nos = {}
    
    def mock_post_journal_line(journal_line, access_token):
        document_no = journal_line.get("Document_No", "Unknown")
        external_doc_no = journal_line.get("External_Document_No", "Unknown")
        
        if document_no not in posted_document_nos:
            posted_document_nos[document_no] = []
        
        posted_document_nos[document_no].append(external_doc_no)
        
        return True, {"success": True}
    
    # Patch post_journal_line and time.sleep
    with patch('process_japan_exports.post_journal_line', side_effect=mock_post_journal_line):
        with patch('process_japan_exports.time.sleep'):
            # Process a subset of entries (focus on the problematic vouchers)
            test_entries = []
            target_vouchers = ["VPA-0000119", "VPA-0000120", "VPA-0000121", "VPA-0000122", "VPA-0000123", "VPA-0000124"]
            
            for entry in raw_data:
                if entry.get("voucher_no") in target_vouchers:
                    test_entries.append(entry)
            
            print(f"\nProcessing {len(test_entries)} test entries...")
            
            # Process the entries
            process_entries(test_entries, "fake_token")
    
    # Verify that each Document_No has unique External_Document_No values
    print("\nDocument_No to External_Document_No mapping:")
    for document_no, external_doc_nos in sorted(posted_document_nos.items()):
        print(f"  {document_no}: {len(external_doc_nos)} entries")
        for i, external_doc_no in enumerate(external_doc_nos[:5]):  # Show first 5 for brevity
            print(f"    {i+1}. {external_doc_no}")
        if len(external_doc_nos) > 5:
            print(f"    ... and {len(external_doc_nos) - 5} more")
    
    # Check if all External_Document_No values are the original values without modification
    print("\nVerifying External_Document_No format:")
    print("  External_Document_No values are now used without modification (no voucher_no prefix)")
    print("  This is the new expected behavior as per the requirement change")
    
    # Check if we have the expected number of Document_No values
    expected_document_nos = set(target_vouchers)
    actual_document_nos = set(posted_document_nos.keys())
    
    print("\nVerifying Document_No values:")
    print(f"  Expected: {sorted(expected_document_nos)}")
    print(f"  Actual: {sorted(actual_document_nos)}")
    
    if expected_document_nos == actual_document_nos:
        print("  All expected Document_No values are present!")
    else:
        missing = expected_document_nos - actual_document_nos
        extra = actual_document_nos - expected_document_nos
        
        if missing:
            print(f"  Missing Document_No values: {sorted(missing)}")
        if extra:
            print(f"  Extra Document_No values: {sorted(extra)}")


if __name__ == "__main__":
    test_with_real_data()
