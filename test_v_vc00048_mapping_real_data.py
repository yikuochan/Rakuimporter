#!/usr/bin/env python3
"""
Test script for V-VC00048 mapping to VCT for non-VCT cost centers using real data.

This script tests the implementation of Issue #78 using the real data file:
0604-Raku export- VCT credit card 1.utf8.json
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
logger = logging.getLogger("test_v_vc00048_mapping_real_data")

def test_v_vc00048_mapping_real_data():
    """
    Test the mapping of vendor code V-VC00048 to VCT for non-VCT cost centers using real data.
    """
    # Load the JSON file
    with open("0604-Raku export- VCT credit card 1.utf8.json", "r") as f:
        entries = json.load(f)
    
    logger.info(f"Loaded {len(entries)} entries from 0604-Raku export- VCT credit card 1.utf8.json")
    
    # Process each entry and check if the vendor code mapping is applied correctly
    for entry in entries:
        voucher_no = entry.get("voucher_no", "Unknown")
        
        # Check if this is a credit entry with V-VC00048 vendor code
        if entry.get("credit", {}).get("vendor_code") == "V-VC00048":
            # Get the cost center from the department field
            department = entry.get("credit", {}).get("department", "")
            cost_center = department[:3] if department else ""
            
            # Process the credit line
            credit_line = create_journal_line(entry, "credit")
            
            # Check if the vendor code mapping is applied correctly
            if cost_center == "VCT":
                # For VCT cost center, vendor code should remain V-VC00048
                expected_account_no = "V-VC00048"
                mapping_applied = False
            else:
                # For non-VCT cost center, vendor code should be mapped to VCT
                expected_account_no = "VCT"
                mapping_applied = True
            
            actual_account_no = credit_line.get("Account_No", "")
            
            # Log the result
            logger.info(f"Voucher: {voucher_no}, Cost Center: {cost_center}, Vendor Code: V-VC00048")
            logger.info(f"Expected Account_No: {expected_account_no}, Actual Account_No: {actual_account_no}")
            
            # Assert that the mapping is applied correctly
            assert actual_account_no == expected_account_no, \
                f"Vendor code mapping not applied correctly for voucher {voucher_no}. " \
                f"Expected: {expected_account_no}, Actual: {actual_account_no}"
            
            # Log the result
            if mapping_applied:
                logger.info(f"✅ Vendor code mapping correctly applied: V-VC00048 -> VCT for cost center {cost_center}")
            else:
                logger.info(f"✅ Vendor code correctly preserved as V-VC00048 for cost center {cost_center}")
    
    logger.info("All vendor code mappings are applied correctly!")

if __name__ == "__main__":
    test_v_vc00048_mapping_real_data()
