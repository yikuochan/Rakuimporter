#!/usr/bin/env python3
"""
Script to analyze the OBA-0000027 voucher and identify rounding issues.
"""

import json
import decimal
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("analyze_oba_0000027")

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

def analyze_voucher(entries):
    """
    Analyze voucher entries to identify rounding issues.
    
    Args:
        entries (list): List of voucher entries
        
    Returns:
        dict: Analysis results
    """
    # Initialize counters
    total_credit_ntd = Decimal('0')
    total_credit_ntd_rounded = Decimal('0')
    total_credit_original = {}
    
    # Track entries with currency conversion
    converted_entries = []
    
    # Analyze each entry
    for entry in entries:
        # Skip consolidated entries (the ones with debit amount = 0)
        if entry.get("debit", {}).get("amount", 0) == 0:
            continue
        
        credit = entry.get("credit", {})
        credit_amount = Decimal(str(credit.get("amount", 0)))
        credit_currency = credit.get("currency", "")
        
        # Add to total NTD
        total_credit_ntd += credit_amount
        
        # Round and add to rounded total
        rounded_amount = credit_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_credit_ntd_rounded += rounded_amount
        
        # Check if this is a currency conversion entry
        if "original_currency" in entry.get("debit", {}):
            original_currency = entry["debit"]["original_currency"]
            original_amount = Decimal(str(entry["debit"]["original_amount"]))
            
            # Track original currency totals
            if original_currency not in total_credit_original:
                total_credit_original[original_currency] = Decimal('0')
            
            total_credit_original[original_currency] += original_amount
            
            # Calculate implied exchange rate
            exchange_rate = credit_amount / original_amount if original_amount != 0 else Decimal('0')
            
            # Add to converted entries list
            converted_entries.append({
                "description": entry.get("description", ""),
                "original_currency": original_currency,
                "original_amount": original_amount,
                "ntd_amount": credit_amount,
                "exchange_rate": exchange_rate,
                "rounded_ntd": rounded_amount,
                "rounding_diff": rounded_amount - credit_amount
            })
    
    # Calculate the consolidated credit amount from the consolidated entry
    consolidated_entry = next((entry for entry in entries if entry.get("debit", {}).get("amount", 0) == 0), None)
    consolidated_amount = Decimal('0')
    if consolidated_entry:
        consolidated_amount = Decimal(str(consolidated_entry.get("credit", {}).get("amount", 0)))
    
    # Calculate differences
    diff_raw_vs_consolidated = total_credit_ntd - consolidated_amount
    diff_rounded_vs_consolidated = total_credit_ntd_rounded - consolidated_amount
    
    return {
        "total_entries": len(entries) - 1,  # Subtract 1 for the consolidated entry
        "total_credit_ntd": total_credit_ntd,
        "total_credit_ntd_rounded": total_credit_ntd_rounded,
        "consolidated_amount": consolidated_amount,
        "diff_raw_vs_consolidated": diff_raw_vs_consolidated,
        "diff_rounded_vs_consolidated": diff_rounded_vs_consolidated,
        "total_credit_original": total_credit_original,
        "converted_entries": converted_entries
    }

def analyze_rounding_methods(entries):
    """
    Analyze different rounding methods to see which one matches the expected result.
    
    Args:
        entries (list): List of voucher entries
        
    Returns:
        dict: Analysis results for different rounding methods
    """
    # Initialize results
    results = {}
    
    # Skip consolidated entries (the ones with debit amount = 0)
    entries = [entry for entry in entries if entry.get("debit", {}).get("amount", 0) != 0]
    
    # Method 1: Round each entry individually, then sum
    sum_of_rounded = Decimal('0')
    for entry in entries:
        credit = entry.get("credit", {})
        credit_amount = Decimal(str(credit.get("amount", 0)))
        rounded_amount = credit_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        sum_of_rounded += rounded_amount
    
    results["sum_of_rounded_entries"] = sum_of_rounded
    
    # Method 2: Sum first, then round
    sum_then_round = Decimal('0')
    for entry in entries:
        credit = entry.get("credit", {})
        credit_amount = Decimal(str(credit.get("amount", 0)))
        sum_then_round += credit_amount
    
    sum_then_round = sum_then_round.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    results["sum_then_round"] = sum_then_round
    
    # Method 3: Round each entry individually with ROUND_HALF_EVEN (banker's rounding), then sum
    sum_of_banker_rounded = Decimal('0')
    for entry in entries:
        credit = entry.get("credit", {})
        credit_amount = Decimal(str(credit.get("amount", 0)))
        rounded_amount = credit_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        sum_of_banker_rounded += rounded_amount
    
    results["sum_of_banker_rounded"] = sum_of_banker_rounded
    
    # Method 4: Sum first, then round with ROUND_HALF_EVEN
    sum_then_banker_round = Decimal('0')
    for entry in entries:
        credit = entry.get("credit", {})
        credit_amount = Decimal(str(credit.get("amount", 0)))
        sum_then_banker_round += credit_amount
    
    sum_then_banker_round = sum_then_banker_round.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
    results["sum_then_banker_round"] = sum_then_banker_round
    
    return results

def analyze_currency_conversion(entries):
    """
    Analyze currency conversion to identify potential issues.
    
    Args:
        entries (list): List of voucher entries
        
    Returns:
        dict: Analysis of currency conversion
    """
    # Group entries by original currency
    currency_groups = {}
    
    for entry in entries:
        # Skip consolidated entries and entries without currency conversion
        if entry.get("debit", {}).get("amount", 0) == 0 or "original_currency" not in entry.get("debit", {}):
            continue
        
        original_currency = entry["debit"]["original_currency"]
        original_amount = Decimal(str(entry["debit"]["original_amount"]))
        ntd_amount = Decimal(str(entry["credit"]["amount"]))
        
        if original_currency not in currency_groups:
            currency_groups[original_currency] = []
        
        currency_groups[original_currency].append({
            "description": entry.get("description", ""),
            "original_amount": original_amount,
            "ntd_amount": ntd_amount,
            "exchange_rate": ntd_amount / original_amount if original_amount != 0 else Decimal('0')
        })
    
    # Analyze each currency group
    results = {}
    for currency, entries in currency_groups.items():
        # Calculate total in original currency
        total_original = sum(entry["original_amount"] for entry in entries)
        
        # Calculate total in NTD by summing individual conversions
        total_ntd_individual = sum(entry["ntd_amount"] for entry in entries)
        
        # Calculate average exchange rate
        avg_rate = total_ntd_individual / total_original if total_original != 0 else Decimal('0')
        
        # Calculate what the total would be if we converted the sum directly
        total_ntd_direct = total_original * avg_rate
        
        # Calculate the difference
        difference = total_ntd_individual - total_ntd_direct
        
        results[currency] = {
            "total_original": total_original,
            "total_ntd_individual": total_ntd_individual,
            "avg_exchange_rate": avg_rate,
            "total_ntd_direct": total_ntd_direct,
            "difference": difference,
            "entries": entries
        }
    
    return results

def main():
    """
    Main function to run the analysis.
    """
    logger.info("Starting analysis of OBA-0000027 voucher")
    
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
    
    # Analyze voucher
    analysis = analyze_voucher(voucher_entries)
    
    # Print analysis results
    logger.info("\n=== Voucher Analysis ===")
    logger.info(f"Total entries: {analysis['total_entries']}")
    logger.info(f"Total credit amount (NTD): {analysis['total_credit_ntd']}")
    logger.info(f"Total credit amount (NTD, rounded): {analysis['total_credit_ntd_rounded']}")
    logger.info(f"Consolidated amount: {analysis['consolidated_amount']}")
    logger.info(f"Difference (raw vs consolidated): {analysis['diff_raw_vs_consolidated']}")
    logger.info(f"Difference (rounded vs consolidated): {analysis['diff_rounded_vs_consolidated']}")
    
    logger.info("\n=== Original Currency Totals ===")
    for currency, amount in analysis['total_credit_original'].items():
        logger.info(f"{currency}: {amount}")
    
    # Analyze different rounding methods
    rounding_analysis = analyze_rounding_methods(voucher_entries)
    
    logger.info("\n=== Rounding Methods Analysis ===")
    logger.info(f"Sum of rounded entries (ROUND_HALF_UP): {rounding_analysis['sum_of_rounded_entries']}")
    logger.info(f"Sum then round (ROUND_HALF_UP): {rounding_analysis['sum_then_round']}")
    logger.info(f"Sum of banker's rounded entries (ROUND_HALF_EVEN): {rounding_analysis['sum_of_banker_rounded']}")
    logger.info(f"Sum then banker's round (ROUND_HALF_EVEN): {rounding_analysis['sum_then_banker_round']}")
    
    # Analyze currency conversion
    currency_analysis = analyze_currency_conversion(voucher_entries)
    
    logger.info("\n=== Currency Conversion Analysis ===")
    for currency, analysis in currency_analysis.items():
        logger.info(f"\n{currency}:")
        logger.info(f"  Total in original currency: {analysis['total_original']}")
        logger.info(f"  Total in NTD (individual conversions): {analysis['total_ntd_individual']}")
        logger.info(f"  Average exchange rate: {analysis['avg_exchange_rate']}")
        logger.info(f"  Total in NTD (direct conversion): {analysis['total_ntd_direct']}")
        logger.info(f"  Difference: {analysis['difference']}")
    
    logger.info("\n=== Entries with Currency Conversion ===")
    if 'converted_entries' in analysis:
        for entry in analysis['converted_entries']:
            logger.info(f"{entry['description']}: {entry['original_currency']} {entry['original_amount']} -> NTD {entry['ntd_amount']} (rate: {entry['exchange_rate']}, rounded: {entry['rounded_ntd']}, diff: {entry['rounding_diff']})")
    
    logger.info("Analysis completed")

if __name__ == "__main__":
    main()
