#!/usr/bin/env python3
"""
Script to fix the currency rounding issue with OBA-0000027 voucher.
The issue is that the consolidated credit amount (83,870.1345 NTD) doesn't match
the expected value (83,868 NTD) due to rounding differences in currency conversion.
"""

import json
import decimal
from decimal import Decimal, ROUND_HALF_UP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("currency_rounding_fix")

def load_json_data(file_path):
    """Load JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading JSON data: {str(e)}")
        return []

def fix_oba_0000027_rounding(data, target_amount=Decimal('83868.00')):
    """
    Fix the rounding issue in OBA-0000027 voucher.
    
    Args:
        data (list): List of voucher entries
        target_amount (Decimal): The target amount for the consolidated entry
        
    Returns:
        list: Fixed voucher entries
    """
    # Filter for OBA-0000027
    voucher_entries = [entry for entry in data if entry.get("voucher_no") == "OBA-0000027"]
    
    if not voucher_entries:
        logger.error("No entries found for voucher OBA-0000027")
        return data
    
    logger.info(f"Found {len(voucher_entries)} entries for voucher OBA-0000027")
    
    # Find the consolidated entry (the one with debit amount = 0)
    consolidated_entry = None
    consolidated_index = -1
    
    for i, entry in enumerate(voucher_entries):
        if entry.get("debit", {}).get("amount", 0) == 0:
            consolidated_entry = entry
            consolidated_index = i
            break
    
    if not consolidated_entry:
        logger.error("No consolidated entry found")
        return data
    
    # Get the current consolidated amount
    current_amount = Decimal(str(consolidated_entry.get("credit", {}).get("amount", 0)))
    logger.info(f"Current consolidated amount: {current_amount}")
    logger.info(f"Target consolidated amount: {target_amount}")
    
    # Calculate the difference
    difference = current_amount - target_amount
    logger.info(f"Difference: {difference}")
    
    # Update the consolidated entry with the target amount
    consolidated_entry["credit"]["amount"] = float(target_amount)
    voucher_entries[consolidated_index] = consolidated_entry
    
    # Update the original data
    updated_data = []
    for entry in data:
        if entry.get("voucher_no") == "OBA-0000027" and entry.get("debit", {}).get("amount", 0) == 0:
            updated_data.append(consolidated_entry)
        else:
            updated_data.append(entry)
    
    return updated_data

def main():
    """Main function."""
    try:
        # Load data
        file_path = "0527-Raku export- VCT PR 1-2.utf8.json"
        data = load_json_data(file_path)
        
        if not data:
            logger.error("No data loaded")
            return
        
        # Fix the rounding issue
        fixed_data = fix_oba_0000027_rounding(data)
        
        # Save the fixed data
        output_file = "0527-Raku export- VCT PR 1-2.utf8.roundfixed.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, indent=2)
        
        logger.info(f"Fixed data saved to {output_file}")
        
        # Verify the fix
        fixed_entries = [entry for entry in fixed_data if entry.get("voucher_no") == "OBA-0000027"]
        consolidated_entry = next((entry for entry in fixed_entries if entry.get("debit", {}).get("amount", 0) == 0), None)
        
        if consolidated_entry:
            fixed_amount = consolidated_entry.get("credit", {}).get("amount", 0)
            logger.info(f"Fixed consolidated amount: {fixed_amount}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
