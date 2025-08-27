#!/usr/bin/env python3
"""
Company-Specific Currency Rounding Logic Module

This module provides functions to apply company-specific rounding rules
to currency amounts based on business requirements.

Key Features:
- Company-specific rounding rules (VCA/VCP round down, VCT rounds down to whole numbers)
- Decimal precision for financial calculations
- Flexible override capabilities
- Comprehensive logging and validation
"""

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
import logging
from typing import Optional, Union
from .company_rounding_config import get_company_rounding_config, RoundingMethod

# Configure logging
logger = logging.getLogger("erp_api_integration")

def apply_company_rounding(amount: Union[float, Decimal], 
                          company_code: str, 
                          target_currency: Optional[str] = None,
                          override_precision: Optional[int] = None, 
                          override_method: Optional[RoundingMethod] = None) -> Decimal:
    """
    Apply company-specific rounding rules to an amount.
    
    Args:
        amount: Amount to round (float or Decimal)
        company_code: Company code (VCT, VCA, VCP, etc.)
        target_currency: Target currency (for future currency-specific rules)
        override_precision: Override decimal places (None = use company default)
        override_method: Override rounding method (None = use company default)
        
    Returns:
        Decimal: Rounded amount according to company rules
        
    Examples:
        >>> apply_company_rounding(10.118, "VCA")  # VCA rounds down to 2 decimals
        Decimal('10.11')
        
        >>> apply_company_rounding(99.9, "VCT")   # VCT rounds down to 0 decimals
        Decimal('99')
        
        >>> apply_company_rounding(10.115, "VCG")  # VCG uses standard rounding
        Decimal('10.12')
    """
    # Convert amount to Decimal if it's not already
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    # Get company-specific configuration
    config = get_company_rounding_config(company_code, target_currency)
    
    # Apply overrides if provided
    decimal_places = override_precision if override_precision is not None else config["decimal_places"]
    rounding_method = override_method.value if override_method is not None else config["rounding_method"].value
    
    # Validate decimal places
    if decimal_places < 0:
        logger.warning(f"Invalid decimal places {decimal_places} for company {company_code}, using 0")
        decimal_places = 0
    
    # Create quantize pattern
    quantize_pattern = Decimal(f'0.{"0" * decimal_places}')
    
    # Apply rounding
    rounded_amount = amount.quantize(quantize_pattern, rounding=rounding_method)
    
    # Log the rounding operation
    logger.debug(f"Company rounding: {amount} → {rounded_amount} "
                f"(company: {company_code}, method: {rounding_method}, precision: {decimal_places})")
    
    return rounded_amount

def round_vca_amount(amount: Union[float, Decimal]) -> Decimal:
    """
    Apply VCA-specific rounding (standard rounding to 2 decimal places).
    
    Args:
        amount: Amount to round
        
    Returns:
        Decimal: Amount rounded to 2 decimal places using standard rounding
        
    Example:
        >>> round_vca_amount(10.118)
        Decimal('10.12')
    """
    return apply_company_rounding(amount, "VCA")

def round_vcp_amount(amount: Union[float, Decimal]) -> Decimal:
    """
    Apply VCP-specific rounding (standard rounding to 2 decimal places).
    
    Args:
        amount: Amount to round
        
    Returns:
        Decimal: Amount rounded to 2 decimal places using standard rounding
        
    Example:
        >>> round_vcp_amount(5.678)
        Decimal('5.68')
    """
    return apply_company_rounding(amount, "VCP")

def round_vct_amount(amount: Union[float, Decimal]) -> Decimal:
    """
    Apply VCT-specific rounding (round to nearest integer).
    
    Args:
        amount: Amount to round
        
    Returns:
        Decimal: Amount rounded to nearest integer
        
    Example:
        >>> round_vct_amount(99.9)
        Decimal('100')
    """
    return apply_company_rounding(amount, "VCT")

def get_rounding_examples(company_code: str) -> list:
    """
    Get example rounding calculations for a specific company.
    
    Args:
        company_code: Company code to get examples for
        
    Returns:
        list: List of dictionaries with input, output, and description
    """
    config = get_company_rounding_config(company_code)
    
    if company_code.upper() == "VCA":
        return [
            {"input": 10.118, "output": float(apply_company_rounding(10.118, "VCA")), 
             "description": "10.118 → 10.12 (standard rounding to 2 decimals)"},
            {"input": 10.119, "output": float(apply_company_rounding(10.119, "VCA")), 
             "description": "10.119 → 10.12 (standard rounding to 2 decimals)"},
            {"input": 10.115, "output": float(apply_company_rounding(10.115, "VCA")), 
             "description": "10.115 → 10.12 (standard rounding to 2 decimals)"}
        ]
    elif company_code.upper() == "VCP":
        return [
            {"input": 5.678, "output": float(apply_company_rounding(5.678, "VCP")), 
             "description": "5.678 → 5.68 (standard rounding to 2 decimals)"},
            {"input": 5.679, "output": float(apply_company_rounding(5.679, "VCP")), 
             "description": "5.679 → 5.68 (standard rounding to 2 decimals)"}
        ]
    elif company_code.upper() == "VCT":
        return [
            {"input": 99.9, "output": float(apply_company_rounding(99.9, "VCT")), 
             "description": "99.9 → 100 (round to nearest integer)"},
            {"input": 99.1, "output": float(apply_company_rounding(99.1, "VCT")), 
             "description": "99.1 → 99 (round to nearest integer)"},
            {"input": 100.5, "output": float(apply_company_rounding(100.5, "VCT")), 
             "description": "100.5 → 101 (round to nearest integer)"}
        ]
    else:
        # Standard rounding examples
        decimal_places = config["decimal_places"]
        return [
            {"input": 10.125, "output": float(apply_company_rounding(10.125, company_code)), 
             "description": f"10.125 → {float(apply_company_rounding(10.125, company_code))} (standard rounding to {decimal_places} decimals)"}
        ]

def validate_rounding_requirements():
    """
    Validate that the rounding implementation meets the business requirements.
    
    Returns:
        tuple: (is_valid, validation_report)
    """
    validation_report = []
    is_valid = True
    
    # Test VCA requirements: Standard rounding to 2 decimals
    test_cases_vca = [
        (10.118, 10.12),  # Round up 
        (10.119, 10.12),  # Round up
        (10.115, 10.12),  # Round up (half-up)
        (10.111, 10.11)   # Round down
    ]
    
    for input_val, expected in test_cases_vca:
        result = float(apply_company_rounding(input_val, "VCA"))
        if result != expected:
            is_valid = False
            validation_report.append(f"VCA FAIL: {input_val} → {result}, expected {expected}")
        else:
            validation_report.append(f"VCA PASS: {input_val} → {result}")
    
    # Test VCP requirements: Standard rounding to 2 decimals  
    test_cases_vcp = [
        (5.678, 5.68),   # Round up
        (5.679, 5.68),   # Round down
        (5.675, 5.68)    # Round up (half-up)
    ]
    
    for input_val, expected in test_cases_vcp:
        result = float(apply_company_rounding(input_val, "VCP"))
        if result != expected:
            is_valid = False
            validation_report.append(f"VCP FAIL: {input_val} → {result}, expected {expected}")
        else:
            validation_report.append(f"VCP PASS: {input_val} → {result}")
    
    # Test VCT requirements: Round to nearest integer
    test_cases_vct = [
        (99.9, 100),  # Round up
        (99.1, 99),   # Round down
        (100.9, 101), # Round up
        (99.0, 99)    # No change
    ]
    
    for input_val, expected in test_cases_vct:
        result = float(apply_company_rounding(input_val, "VCT"))
        if result != expected:
            is_valid = False
            validation_report.append(f"VCT FAIL: {input_val} → {result}, expected {expected}")
        else:
            validation_report.append(f"VCT PASS: {input_val} → {result}")
    
    return is_valid, validation_report

# Example usage and testing
if __name__ == "__main__":
    # Configure logging for standalone execution
    import logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Company-Specific Currency Rounding Examples:")
    print("=" * 50)
    
    # Test each company's rounding
    companies = ["VCA", "VCP", "VCT", "VCG"]
    
    for company in companies:
        print(f"\n{company} Examples:")
        examples = get_rounding_examples(company)
        for example in examples:
            print(f"  {example['description']}")
    
    print("\nRequirements Validation:")
    print("-" * 30)
    is_valid, report = validate_rounding_requirements()
    
    for line in report:
        print(f"  {line}")
    
    print(f"\nOverall validation: {'PASS' if is_valid else 'FAIL'}")