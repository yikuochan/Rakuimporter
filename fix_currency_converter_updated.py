#!/usr/bin/env python3
"""
Updated Currency Converter Fix

This script fixes the rounding issue in the currency_converter.py module
by replacing NumPy's rounding with Decimal's ROUND_HALF_UP method.
"""

import logging
from decimal import Decimal, ROUND_HALF_UP

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fix_currency_converter_updated")

def fix_currency_converter():
    """
    Generate a fixed version of the currency_converter.py file
    that uses Decimal for more predictable rounding behavior
    """
    # Read the original file
    with open('currency_converter.py', 'r') as f:
        content = f.read()
    
    # Add import for Decimal
    if 'from decimal import Decimal, ROUND_HALF_UP' not in content:
        import_line = 'import numpy as np'
        new_import = 'import numpy as np\nfrom decimal import Decimal, ROUND_HALF_UP'
        content = content.replace(import_line, new_import)
    
    # Replace the rounding code in convert_amount function
    old_rounding = """        raw_conversion = amount * rate
        
        # Apply NumPy rounding with specified decimal precision
        converted = np.round(raw_conversion, decimal_precision)
        
        logger.info(f"Converted {amount} {from_currency} to {converted:.2f} {to_currency} (rate: {rate})")
        logger.info(f"Raw conversion: {raw_conversion}, After NumPy rounding: {converted}")
        
        # Return as Python float but ensure the rounding is preserved
        return float(converted), True"""
    
    new_rounding = """        raw_conversion = amount * rate
        
        # Use Decimal for more predictable rounding behavior
        decimal_amount = Decimal(str(raw_conversion))
        decimal_precision_str = '0.' + '0' * (decimal_precision - 1) + '1'
        converted = decimal_amount.quantize(Decimal(decimal_precision_str), rounding=ROUND_HALF_UP)
        
        logger.info(f"Converted {amount} {from_currency} to {float(converted):.2f} {to_currency} (rate: {rate})")
        logger.info(f"Raw conversion: {raw_conversion}, After Decimal rounding: {float(converted)}")
        
        # Return as Python float
        return float(converted), True"""
    
    # Replace the rounding code
    fixed_content = content.replace(old_rounding, new_rounding)
    
    # Write the fixed file
    with open('currency_converter_fixed.py', 'w') as f:
        f.write(fixed_content)
    
    logger.info("Fixed currency_converter.py written to currency_converter_fixed.py")

if __name__ == "__main__":
    fix_currency_converter()
