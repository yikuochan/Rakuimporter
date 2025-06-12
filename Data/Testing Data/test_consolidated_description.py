#!/usr/bin/env python3
"""
Test script to verify the description field handling for consolidated entries
in process_japan_exports.py

This script tests that:
1. For consolidated credit lines, the description comes from column U (備考)
2. The consolidation note is properly added to the description
"""

import json
import logging
import sys
from process_japan_exports import create_journal_line

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("consolidated_description_test")

def test_consolidated_description():
    """Test the description field handling for consolidated entries"""
    
    # Create a test consolidated entry
    consolidated_entry = {
        "voucher_no": "TEST-CONSOLIDATED-001",
        "debit": {
            "gl_account": "G/L Account",
            "amount": 0,  # Empty debit for consolidated entry
            "currency": "NTD",
            "department": "VCT.1342G",
            "Receipt/Invoice Note(明細)": "This should not be used",
            "free_field": "This should not be used either",
            "備考": "This should not be used for debit"
        },
        "credit": {
            "gl_account": "Vendor",
            "amount": 5000,
            "currency": "NTD",
            "department": "VCT.1342G",
            "Receipt/Invoice Note(明細)": "This should not be used for credit",
            "free_field": "This should not be used for credit either",
            "備考": "Credit description from column U",
            "consolidated": True,
            "original_entries_count": 5,
            "consolidation_note": "Consolidated from 5 entries"
        }
    }
    
    # Test cases with different combinations of description fields
    test_cases = [
        # Case 1: Column U has value
        {
            "voucher_no": "TEST-CONSOLIDATED-001",
            "credit": {
                "gl_account": "Vendor",
                "amount": 5000,
                "currency": "NTD",
                "department": "VCT.1342G",
                "Receipt/Invoice Note(明細)": "This should not be used for credit",
                "free_field": "This should not be used for credit either",
                "備考": "Credit description from column U",
                "consolidated": True,
                "original_entries_count": 5
            }
        },
        # Case 2: Column U is empty
        {
            "voucher_no": "TEST-CONSOLIDATED-002",
            "credit": {
                "gl_account": "Vendor",
                "amount": 5000,
                "currency": "NTD",
                "department": "VCT.1342G",
                "Receipt/Invoice Note(明細)": "This should not be used for credit",
                "free_field": "This should not be used for credit either",
                "備考": "",
                "consolidated": True,
                "original_entries_count": 3
            }
        },
        # Case 3: Long description in column U
        {
            "voucher_no": "TEST-CONSOLIDATED-003",
            "credit": {
                "gl_account": "Vendor",
                "amount": 5000,
                "currency": "NTD",
                "department": "VCT.1342G",
                "Receipt/Invoice Note(明細)": "This should not be used for credit",
                "free_field": "This should not be used for credit either",
                "備考": "This is a very long description that should be combined with the consolidation note but might exceed the 100 character limit when combined with the consolidation note",
                "consolidated": True,
                "original_entries_count": 10
            }
        }
    ]
    
    # Process each test case
    for i, entry in enumerate(test_cases):
        logger.info(f"Testing consolidated entry {i+1}: {entry['voucher_no']}")
        
        # Process credit line
        credit_line = create_journal_line(entry, "credit")
        
        # Log the results
        logger.info(f"Original 備考 value: '{entry['credit'].get('備考', '')}'")
        logger.info(f"Final description: '{credit_line['Description']}'")
        
        # Verify that the description contains the consolidation note
        if "Consolidated from" in credit_line["Description"]:
            logger.info(f"✅ Description contains consolidation note")
        else:
            logger.error(f"❌ Description does not contain consolidation note")
        
        # Verify that the description starts with the 備考 value if it's not empty
        if entry['credit'].get('備考'):
            if credit_line["Description"].startswith(entry['credit']['備考']):
                logger.info(f"✅ Description starts with 備考 value")
            else:
                logger.error(f"❌ Description does not start with 備考 value")
        
        logger.info("-" * 50)

if __name__ == "__main__":
    logger.info("Starting consolidated description field test")
    test_consolidated_description()
    logger.info("Consolidated description field test completed")
