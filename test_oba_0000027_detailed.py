#!/usr/bin/env python3
"""
Detailed analysis script for OBA-0000027 voucher to understand the currency conversion issue.
"""

import json
import decimal
from decimal import Decimal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("oba_0000027_analysis")

def load_json_data(file_path):
    """Load JSON data from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def analyze_oba_0000027(data):
    """Analyze OBA-0000027 voucher entries in detail."""
    # Filter for OBA-0000027
    voucher_entries = [entry for entry in data if entry.get("voucher_no") == "OBA-0000027"]
    
    if not voucher_entries:
        logger.error("No entries found for voucher OBA-0000027")
        return
    
    logger.info(f"Found {len(voucher_entries)} entries for voucher OBA-0000027")
    
    # Find the consolidated entry
    consolidated_entry = next((entry for entry in voucher_entries if entry.get("debit", {}).get("amount", 0) == 0), None)
    consolidated_amount = Decimal('0')
    if consolidated_entry:
        consolidated_amount = Decimal(str(consolidated_entry.get("credit", {}).get("amount", 0)))
        logger.info(f"Consolidated entry amount: {consolidated_amount}")
        logger.info(f"Consolidated entry description: {consolidated_entry.get('credit_description', '')}")
    else:
        logger.error("No consolidated entry found")
        return
    
    # Analyze individual entries
    individual_entries = [entry for entry in voucher_entries if entry.get("debit", {}).get("amount", 0) != 0]
    logger.info(f"Individual entries count: {len(individual_entries)}")
    
    # Calculate total in NTD
    total_ntd = Decimal('0')
    total_rmb = Decimal('0')
    
    # Detailed analysis of each entry
    logger.info("\n=== Detailed Entry Analysis ===")
    for i, entry in enumerate(individual_entries):
        debit = entry.get("debit", {})
        credit = entry.get("credit", {})
        
        debit_amount = Decimal(str(debit.get("amount", 0)))
        credit_amount = Decimal(str(credit.get("amount", 0)))
        
        original_currency = debit.get("original_currency", "")
        original_amount = Decimal(str(debit.get("original_amount", 0))) if original_currency else Decimal('0')
        
        logger.info(f"\nEntry {i+1}:")
        logger.info(f"  Description: {entry.get('description', '')}")
        logger.info(f"  Debit amount (NTD): {debit_amount}")
        logger.info(f"  Credit amount: {credit_amount} {credit.get('currency', 'NTD')}")
        
        if original_currency:
            logger.info(f"  Original currency: {original_currency}")
            logger.info(f"  Original amount: {original_amount}")
            
            # Calculate exchange rate
            exchange_rate = debit_amount / original_amount if original_amount != 0 else Decimal('0')
            logger.info(f"  Exchange rate: {exchange_rate}")
            
            if original_currency == "R-RMB":
                total_rmb += original_amount
        
        total_ntd += credit_amount
    
    logger.info("\n=== Summary ===")
    logger.info(f"Total credit amount (NTD): {total_ntd}")
    logger.info(f"Total RMB amount: {total_rmb}")
    logger.info(f"Consolidated amount: {consolidated_amount}")
    logger.info(f"Difference: {consolidated_amount - total_ntd}")
    
    # Check if the consolidated amount is the sum of all RMB entries
    if total_rmb > 0:
        logger.info(f"\nChecking if consolidated amount is based on RMB total:")
        logger.info(f"  Total RMB: {total_rmb}")
        logger.info(f"  Consolidated amount: {consolidated_amount}")
        logger.info(f"  Ratio (consolidated/RMB): {consolidated_amount / total_rmb if total_rmb != 0 else 0}")
    
    # Check if there's a pattern in the difference
    logger.info("\n=== Investigating Difference ===")
    difference = consolidated_amount - total_ntd
    logger.info(f"Absolute difference: {difference}")
    logger.info(f"Percentage difference: {(difference / total_ntd * 100) if total_ntd != 0 else 0}%")
    
    # Check if the difference could be due to rounding
    logger.info("\n=== Rounding Analysis ===")
    # Count entries with foreign currency
    foreign_currency_entries = [entry for entry in individual_entries if entry.get("debit", {}).get("original_currency", "")]
    logger.info(f"Entries with foreign currency: {len(foreign_currency_entries)}")
    
    # Check if the consolidated amount is exactly the sum of debit amounts
    total_debit = sum(Decimal(str(entry.get("debit", {}).get("amount", 0))) for entry in individual_entries)
    logger.info(f"Total debit amount: {total_debit}")
    logger.info(f"Difference from consolidated: {consolidated_amount - total_debit}")
    
    # Check if the consolidated amount matches any specific pattern
    logger.info("\n=== Pattern Analysis ===")
    # Check if it's a simple multiplication of the total
    for factor in [1.0, 2.0, 2.05, 4.45]:
        logger.info(f"Factor {factor}: {total_ntd * Decimal(str(factor))}")

def main():
    """Main function."""
    try:
        # Load data
        file_path = "0527-Raku export- VCT PR 1-2.utf8.json"
        data = load_json_data(file_path)
        
        # Analyze OBA-0000027
        analyze_oba_0000027(data)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
