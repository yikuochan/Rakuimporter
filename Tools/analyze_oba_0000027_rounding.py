#!/usr/bin/env python3
"""
Script to analyze the rounding issue with OBA-0000027 voucher.
This script focuses specifically on the rounding of currency conversion
without making assumptions about the structure.
"""

import json
import decimal
from decimal import Decimal, ROUND_HALF_UP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("oba_rounding_analysis")

def load_json_data(file_path):
    """Load JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading JSON data: {str(e)}")
        return []

def analyze_oba_0000027(data):
    """
    Analyze OBA-0000027 voucher entries with focus on rounding issues.
    This function examines the raw data structure without assumptions.
    """
    # Filter for OBA-0000027
    voucher_entries = [entry for entry in data if entry.get("voucher_no") == "OBA-0000027"]
    
    if not voucher_entries:
        logger.error("No entries found for voucher OBA-0000027")
        return
    
    logger.info(f"Found {len(voucher_entries)} entries for voucher OBA-0000027")
    
    # Print the structure of the first entry to understand the data format
    logger.info("\n=== Sample Entry Structure ===")
    first_entry = voucher_entries[0]
    for key, value in first_entry.items():
        if isinstance(value, dict):
            logger.info(f"{key}: {type(value)}")
            for subkey, subvalue in value.items():
                logger.info(f"  {subkey}: {subvalue}")
        else:
            logger.info(f"{key}: {value}")
    
    # Analyze credit and debit amounts
    logger.info("\n=== Credit/Debit Analysis ===")
    for i, entry in enumerate(voucher_entries):
        logger.info(f"\nEntry {i+1}:")
        logger.info(f"Description: {entry.get('description', '')}")
        
        # Analyze debit
        debit = entry.get("debit", {})
        if debit:
            debit_amount = Decimal(str(debit.get("amount", 0)))
            debit_currency = debit.get("currency", "")
            logger.info(f"Debit: {debit_amount} {debit_currency}")
            
            # Check for original currency in debit
            original_currency = debit.get("original_currency", "")
            if original_currency:
                original_amount = Decimal(str(debit.get("original_amount", 0)))
                logger.info(f"Original Currency: {original_currency}")
                logger.info(f"Original Amount: {original_amount}")
                
                # Calculate implied exchange rate
                if original_amount != 0:
                    exchange_rate = debit_amount / original_amount
                    logger.info(f"Implied Exchange Rate: {exchange_rate}")
        
        # Analyze credit
        credit = entry.get("credit", {})
        if credit:
            credit_amount = Decimal(str(credit.get("amount", 0)))
            credit_currency = credit.get("currency", "")
            logger.info(f"Credit: {credit_amount} {credit_currency}")
            
            # Check for original currency in credit
            original_currency = credit.get("original_currency", "")
            if original_currency:
                original_amount = Decimal(str(credit.get("original_amount", 0)))
                logger.info(f"Original Currency: {original_currency}")
                logger.info(f"Original Amount: {original_amount}")
                
                # Calculate implied exchange rate
                if original_amount != 0:
                    exchange_rate = credit_amount / original_amount
                    logger.info(f"Implied Exchange Rate: {exchange_rate}")
    
    # Analyze rounding issues
    logger.info("\n=== Rounding Analysis ===")
    
    # Find entries with non-zero credit amounts
    credit_entries = [entry for entry in voucher_entries if entry.get("credit", {}).get("amount", 0) != 0]
    logger.info(f"Entries with non-zero credit: {len(credit_entries)}")
    
    # Calculate total credit amount
    total_credit = sum(Decimal(str(entry.get("credit", {}).get("amount", 0))) for entry in credit_entries)
    logger.info(f"Total credit amount: {total_credit}")
    
    # Round to 2 decimal places
    total_credit_rounded = total_credit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    logger.info(f"Total credit amount (rounded to 2 decimal places): {total_credit_rounded}")
    
    # Find entries with non-zero debit amounts
    debit_entries = [entry for entry in voucher_entries if entry.get("debit", {}).get("amount", 0) != 0]
    logger.info(f"Entries with non-zero debit: {len(debit_entries)}")
    
    # Calculate total debit amount
    total_debit = sum(Decimal(str(entry.get("debit", {}).get("amount", 0))) for entry in debit_entries)
    logger.info(f"Total debit amount: {total_debit}")
    
    # Round to 2 decimal places
    total_debit_rounded = total_debit.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    logger.info(f"Total debit amount (rounded to 2 decimal places): {total_debit_rounded}")
    
    # Check if there's a balance
    logger.info(f"Difference (credit - debit): {total_credit - total_debit}")
    logger.info(f"Difference (rounded): {total_credit_rounded - total_debit_rounded}")
    
    # Check for entries with both credit and debit
    both_entries = [entry for entry in voucher_entries 
                   if entry.get("credit", {}).get("amount", 0) != 0 
                   and entry.get("debit", {}).get("amount", 0) != 0]
    logger.info(f"Entries with both credit and debit: {len(both_entries)}")
    
    # Check for entries with foreign currency
    foreign_entries = [entry for entry in voucher_entries 
                      if (entry.get("credit", {}).get("original_currency", "") 
                          or entry.get("debit", {}).get("original_currency", ""))]
    logger.info(f"Entries with foreign currency: {len(foreign_entries)}")
    
    # Analyze foreign currency entries
    if foreign_entries:
        logger.info("\n=== Foreign Currency Analysis ===")
        
        # Group by currency
        currency_groups = {}
        for entry in foreign_entries:
            credit = entry.get("credit", {})
            debit = entry.get("debit", {})
            
            credit_original_currency = credit.get("original_currency", "")
            debit_original_currency = debit.get("original_currency", "")
            
            if credit_original_currency:
                if credit_original_currency not in currency_groups:
                    currency_groups[credit_original_currency] = []
                currency_groups[credit_original_currency].append(entry)
            
            if debit_original_currency:
                if debit_original_currency not in currency_groups:
                    currency_groups[debit_original_currency] = []
                currency_groups[debit_original_currency].append(entry)
        
        # Analyze each currency group
        for currency, entries in currency_groups.items():
            logger.info(f"\nCurrency: {currency}")
            logger.info(f"Number of entries: {len(entries)}")
            
            # Calculate total original amount and converted amount
            total_original = Decimal('0')
            total_converted = Decimal('0')
            
            for entry in entries:
                credit = entry.get("credit", {})
                debit = entry.get("debit", {})
                
                if credit.get("original_currency", "") == currency:
                    total_original += Decimal(str(credit.get("original_amount", 0)))
                    total_converted += Decimal(str(credit.get("amount", 0)))
                
                if debit.get("original_currency", "") == currency:
                    total_original += Decimal(str(debit.get("original_amount", 0)))
                    total_converted += Decimal(str(debit.get("amount", 0)))
            
            logger.info(f"Total original amount: {total_original}")
            logger.info(f"Total converted amount: {total_converted}")
            
            # Calculate average exchange rate
            if total_original != 0:
                avg_rate = total_converted / total_original
                logger.info(f"Average exchange rate: {avg_rate}")
            
            # Check if rounding could be an issue
            sum_rounded = sum(Decimal(str(entry.get("credit", {}).get("amount", 0))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) 
                             for entry in entries if entry.get("credit", {}).get("original_currency", "") == currency)
            sum_rounded += sum(Decimal(str(entry.get("debit", {}).get("amount", 0))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) 
                              for entry in entries if entry.get("debit", {}).get("original_currency", "") == currency)
            
            total_converted_rounded = total_converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            logger.info(f"Sum of individually rounded amounts: {sum_rounded}")
            logger.info(f"Total converted amount (rounded): {total_converted_rounded}")
            logger.info(f"Difference: {sum_rounded - total_converted_rounded}")

def main():
    """Main function."""
    try:
        # Load data
        file_path = "0527-Raku export- VCT PR 1-2.utf8.json"
        data = load_json_data(file_path)
        
        if not data:
            logger.error("No data loaded")
            return
        
        # Analyze OBA-0000027
        analyze_oba_0000027(data)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
