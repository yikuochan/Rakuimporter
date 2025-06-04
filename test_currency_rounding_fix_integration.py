#!/usr/bin/env python3
"""
Test script to verify that the fixed currency converter correctly handles the rounding issue
that caused the OBA-0000027 voucher discrepancy.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_currency_rounding")

def test_with_original_converter():
    """Test with the original currency converter."""
    try:
        # Import the original converter
        import currency_converter
        
        logger.info("Testing with original currency_converter.py")
        
        # Test converting a batch of RMB amounts to NTD
        rmb_amounts = [12.0, 1800.0, 174.0, 103.4, 440.86, 55.97, 134.0, 103.0, 100.0]
        exchange_rate = 4.45
        
        # Convert each amount individually and sum
        individual_conversions = []
        for amount in rmb_amounts:
            converted, success = currency_converter.convert_amount(amount, "RMB", "NTD")
            individual_conversions.append(converted)
            logger.info(f"Converting {amount} RMB to NTD: {converted}")
        
        sum_individual = sum(individual_conversions)
        logger.info(f"Sum of individual conversions: {sum_individual}")
        
        # Convert the sum directly
        total_rmb = sum(rmb_amounts)
        total_converted, success = currency_converter.convert_amount(total_rmb, "RMB", "NTD")
        logger.info(f"Direct conversion of total ({total_rmb} RMB): {total_converted}")
        
        # Calculate the difference
        difference = sum_individual - total_converted
        logger.info(f"Difference: {difference}")
        
        return {
            "original_converter": {
                "individual_sum": sum_individual,
                "direct_conversion": total_converted,
                "difference": difference
            }
        }
    except Exception as e:
        logger.error(f"Error testing original converter: {str(e)}")
        return {"original_converter": "Error"}

def test_with_fixed_converter():
    """Test with the fixed currency converter."""
    try:
        # Import the fixed converter
        import currency_converter_fixed
        
        logger.info("Testing with currency_converter_fixed.py")
        
        # Test converting a batch of RMB amounts to NTD
        rmb_amounts = [Decimal('12.0'), Decimal('1800.0'), Decimal('174.0'), 
                      Decimal('103.4'), Decimal('440.86'), Decimal('55.97'), 
                      Decimal('134.0'), Decimal('103.0'), Decimal('100.0')]
        exchange_rate = Decimal('4.45')
        
        # Convert each amount individually and sum
        individual_conversions = []
        for amount in rmb_amounts:
            converted, success = currency_converter_fixed.convert_amount(amount, "RMB", "NTD")
            individual_conversions.append(converted)
            logger.info(f"Converting {amount} RMB to NTD: {converted}")
        
        sum_individual = sum(individual_conversions)
        logger.info(f"Sum of individual conversions: {sum_individual}")
        
        # Convert the sum directly
        total_rmb = sum(rmb_amounts)
        total_converted, success = currency_converter_fixed.convert_amount(total_rmb, "RMB", "NTD")
        logger.info(f"Direct conversion of total ({total_rmb} RMB): {total_converted}")
        
        # Calculate the difference
        difference = sum_individual - total_converted
        logger.info(f"Difference: {difference}")
        
        return {
            "fixed_converter": {
                "individual_sum": str(sum_individual),
                "direct_conversion": str(total_converted),
                "difference": str(difference)
            }
        }
    except Exception as e:
        logger.error(f"Error testing fixed converter: {str(e)}")
        return {"fixed_converter": "Error"}

def test_oba_0000027_scenario():
    """Test the specific scenario that caused the OBA-0000027 issue."""
    try:
        logger.info("Testing OBA-0000027 scenario")
        
        # Load the original data
        with open("0527-Raku export- VCT PR 1-2.utf8.json", "r") as f:
            data = json.load(f)
        
        # Filter for OBA-0000027
        voucher_entries = [entry for entry in data if entry.get("voucher_no") == "OBA-0000027"]
        
        # Find the consolidated entry
        consolidated_entry = next((entry for entry in voucher_entries if entry.get("debit", {}).get("amount", 0) == 0), None)
        consolidated_amount = Decimal(str(consolidated_entry.get("credit", {}).get("amount", 0)))
        
        # Find entries with foreign currency
        foreign_entries = [entry for entry in voucher_entries 
                          if entry.get("debit", {}).get("original_currency", "") == "R-RMB"]
        
        # Calculate total RMB amount
        total_rmb = sum(Decimal(str(entry.get("debit", {}).get("original_amount", 0))) for entry in foreign_entries)
        
        # Calculate total NTD amount (non-foreign entries)
        ntd_entries = [entry for entry in voucher_entries 
                      if entry.get("debit", {}).get("amount", 0) != 0 
                      and not entry.get("debit", {}).get("original_currency", "")]
        total_ntd = sum(Decimal(str(entry.get("debit", {}).get("amount", 0))) for entry in ntd_entries)
        
        logger.info(f"Total RMB amount: {total_rmb}")
        logger.info(f"Total NTD amount: {total_ntd}")
        
        # Test with fixed converter
        import currency_converter_fixed
        
        # Convert RMB to NTD
        converted_rmb, success = currency_converter_fixed.convert_amount(total_rmb, "RMB", "NTD")
        
        # Calculate total
        total_converted = total_ntd + converted_rmb
        
        logger.info(f"Converted RMB amount: {converted_rmb}")
        logger.info(f"Total converted amount: {total_converted}")
        logger.info(f"Consolidated amount in data: {consolidated_amount}")
        logger.info(f"Difference: {consolidated_amount - total_converted}")
        
        # Load the fixed data
        with open("0527-Raku export- VCT PR 1-2.utf8.roundfixed.json", "r") as f:
            fixed_data = json.load(f)
        
        # Find the consolidated entry in fixed data
        fixed_entries = [entry for entry in fixed_data if entry.get("voucher_no") == "OBA-0000027"]
        fixed_consolidated = next((entry for entry in fixed_entries if entry.get("debit", {}).get("amount", 0) == 0), None)
        fixed_amount = Decimal(str(fixed_consolidated.get("credit", {}).get("amount", 0)))
        
        logger.info(f"Fixed consolidated amount: {fixed_amount}")
        logger.info(f"Difference with calculated: {fixed_amount - total_converted}")
        
        return {
            "oba_0000027_scenario": {
                "total_rmb": str(total_rmb),
                "total_ntd": str(total_ntd),
                "converted_rmb": str(converted_rmb),
                "total_converted": str(total_converted),
                "original_consolidated": str(consolidated_amount),
                "fixed_consolidated": str(fixed_amount),
                "difference_original": str(consolidated_amount - total_converted),
                "difference_fixed": str(fixed_amount - total_converted)
            }
        }
    except Exception as e:
        logger.error(f"Error testing OBA-0000027 scenario: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"oba_0000027_scenario": "Error"}

def main():
    """Main function."""
    results = {}
    
    # Test with original converter
    original_results = test_with_original_converter()
    results.update(original_results)
    
    # Test with fixed converter
    fixed_results = test_with_fixed_converter()
    results.update(fixed_results)
    
    # Test OBA-0000027 scenario
    oba_results = test_oba_0000027_scenario()
    results.update(oba_results)
    
    # Save results to file
    with open("currency_rounding_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("Test results saved to currency_rounding_test_results.json")

if __name__ == "__main__":
    main()
