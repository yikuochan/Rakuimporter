#!/usr/bin/env python3
"""
Script to fix currency rounding issues in the voucher processing system.
This specifically addresses the issue with OBA-0000027 where the consolidated
credit amount (83,870.1345 NTD) doesn't match the sum of individual entries (40,896.21 NTD).
"""

import json
import decimal
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("currency_rounding_fix")

# Set decimal precision
decimal.getcontext().prec = 10

def load_json_data(file_path):
    """
    Load JSON data from file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        list: List of voucher entries
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading JSON data: {str(e)}")
        return []

def filter_voucher_entries(data, voucher_no):
    """
    Filter entries for a specific voucher number.
    
    Args:
        data (list): List of voucher entries
        voucher_no (str): Voucher number to filter
        
    Returns:
        list: Filtered list of entries
    """
    return [entry for entry in data if entry.get("voucher_no") == voucher_no]

def analyze_currency_conversion_issue(entries):
    """
    Analyze currency conversion issues in the voucher entries.
    
    Args:
        entries (list): List of voucher entries
        
    Returns:
        dict: Analysis results
    """
    # Find the consolidated entry (the one with debit amount = 0)
    consolidated_entry = next((entry for entry in entries if entry.get("debit", {}).get("amount", 0) == 0), None)
    consolidated_amount = Decimal('0')
    if consolidated_entry:
        consolidated_amount = Decimal(str(consolidated_entry.get("credit", {}).get("amount", 0)))
    
    # Analyze individual entries
    individual_entries = [entry for entry in entries if entry.get("debit", {}).get("amount", 0) != 0]
    
    # Group entries by currency
    currency_groups = {}
    for entry in individual_entries:
        credit = entry.get("credit", {})
        credit_amount = Decimal(str(credit.get("amount", 0)))
        credit_currency = credit.get("currency", "")
        
        # Check if this is a currency conversion entry
        original_currency = entry.get("debit", {}).get("original_currency", "")
        
        if original_currency:
            if original_currency not in currency_groups:
                currency_groups[original_currency] = []
            
            original_amount = Decimal(str(entry.get("debit", {}).get("original_amount", 0)))
            
            currency_groups[original_currency].append({
                "description": entry.get("description", ""),
                "original_amount": original_amount,
                "ntd_amount": credit_amount,
                "exchange_rate": credit_amount / original_amount if original_amount != 0 else Decimal('0')
            })
        else:
            if credit_currency not in currency_groups:
                currency_groups[credit_currency] = []
            
            currency_groups[credit_currency].append({
                "description": entry.get("description", ""),
                "amount": credit_amount
            })
    
    # Calculate totals for each currency group
    currency_totals = {}
    for currency, entries in currency_groups.items():
        if currency == "NTD" or not currency:
            # For NTD entries, just sum the amounts
            total = sum(entry.get("amount", 0) for entry in entries)
            currency_totals[currency or "NTD"] = {
                "total": total,
                "entries_count": len(entries)
            }
        else:
            # For foreign currency entries, calculate both original and converted totals
            original_total = sum(entry.get("original_amount", 0) for entry in entries)
            ntd_total = sum(entry.get("ntd_amount", 0) for entry in entries)
            
            # Calculate average exchange rate
            avg_rate = ntd_total / original_total if original_total != 0 else Decimal('0')
            
            # Calculate what the total would be if we converted the sum directly
            direct_conversion = original_total * avg_rate
            
            currency_totals[currency] = {
                "original_total": original_total,
                "ntd_total": ntd_total,
                "avg_exchange_rate": avg_rate,
                "direct_conversion": direct_conversion,
                "difference": ntd_total - direct_conversion,
                "entries_count": len(entries)
            }
    
    # Calculate the total of all entries in NTD
    total_ntd = Decimal('0')
    for currency, data in currency_totals.items():
        if currency == "NTD":
            total_ntd += data["total"]
        else:
            total_ntd += data["ntd_total"]
    
    # Calculate the difference between consolidated and sum of individual entries
    difference = consolidated_amount - total_ntd
    
    return {
        "consolidated_amount": consolidated_amount,
        "total_individual_entries": total_ntd,
        "difference": difference,
        "currency_groups": currency_totals
    }

def fix_currency_rounding(entries):
    """
    Fix currency rounding issues in the voucher entries.
    
    Args:
        entries (list): List of voucher entries
        
    Returns:
        list: Fixed voucher entries
    """
    # Find the consolidated entry (the one with debit amount = 0)
    consolidated_entry = next((entry for entry in entries if entry.get("debit", {}).get("amount", 0) == 0), None)
    if not consolidated_entry:
        logger.error("No consolidated entry found")
        return entries
    
    # Calculate the correct total from individual entries
    individual_entries = [entry for entry in entries if entry.get("debit", {}).get("amount", 0) != 0]
    total_ntd = Decimal('0')
    
    for entry in individual_entries:
        credit = entry.get("credit", {})
        credit_amount = Decimal(str(credit.get("amount", 0)))
        total_ntd += credit_amount
    
    # Round the total to 2 decimal places
    total_ntd_rounded = total_ntd.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Update the consolidated entry with the correct total
    consolidated_entry["credit"]["amount"] = float(total_ntd_rounded)
    
    # Find the index of the consolidated entry in the original list
    for i, entry in enumerate(entries):
        if entry.get("debit", {}).get("amount", 0) == 0:
            entries[i] = consolidated_entry
            break
    
    return entries

def main():
    """
    Main function to analyze and fix currency rounding issues.
    """
    logger.info("Starting currency rounding analysis and fix")
    
    # Load data
    file_path = "0527-Raku export- VCT PR 1-2.utf8.json"
    data = load_json_data(file_path)
    
    if not data:
        logger.error("No data loaded")
        return
    
    # Filter for OBA-0000027
    voucher_entries = filter_voucher_entries(data, "OBA-0000027")
    
    if not voucher_entries:
        logger.error("No entries found for voucher OBA-0000027")
        return
    
    logger.info(f"Found {len(voucher_entries)} entries for voucher OBA-0000027")
    
    # Analyze currency conversion issues
    analysis = analyze_currency_conversion_issue(voucher_entries)
    
    # Print analysis results
    logger.info("\n=== Currency Conversion Analysis ===")
    logger.info(f"Consolidated amount: {analysis['consolidated_amount']}")
    logger.info(f"Total of individual entries: {analysis['total_individual_entries']}")
    logger.info(f"Difference: {analysis['difference']}")
    
    logger.info("\n=== Currency Groups ===")
    for currency, data in analysis['currency_groups'].items():
        logger.info(f"\n{currency}:")
        for key, value in data.items():
            logger.info(f"  {key}: {value}")
    
    # Fix the currency rounding issues
    fixed_entries = fix_currency_rounding(voucher_entries)
    
    # Verify the fix
    fixed_analysis = analyze_currency_conversion_issue(fixed_entries)
    
    logger.info("\n=== After Fix ===")
    logger.info(f"Consolidated amount: {fixed_analysis['consolidated_amount']}")
    logger.info(f"Total of individual entries: {fixed_analysis['total_individual_entries']}")
    logger.info(f"Difference: {fixed_analysis['difference']}")
    
    # Save the fixed data
    fixed_data = data.copy()
    for i, entry in enumerate(data):
        if entry.get("voucher_no") == "OBA-0000027":
            for fixed_entry in fixed_entries:
                if (fixed_entry.get("transaction_date") == entry.get("transaction_date") and
                    fixed_entry.get("description") == entry.get("description") and
                    fixed_entry.get("debit", {}).get("amount", 0) == entry.get("debit", {}).get("amount", 0)):
                    fixed_data[i] = fixed_entry
                    break
    
    with open("fixed_output.json", "w", encoding="utf-8") as f:
        json.dump(fixed_data, f, indent=2)
    
    logger.info("Fixed data saved to fixed_output.json")
    logger.info("Analysis and fix completed")

if __name__ == "__main__":
    main()
