#!/usr/bin/env python3
"""
VCT Responsibility Entry Consolidation Module

This module provides functionality to consolidate VCT responsibility entries for V-VC00048 vendor mappings.
Instead of creating individual debit+credit pairs for each entry, it creates:
- Multiple individual debit lines (preserving original entry details)
- Single consolidated credit line (with total amount)

This reduces API calls and document numbers while maintaining audit trail.
"""

import json
import logging
from typing import Dict, List, Any, Tuple
from decimal import Decimal

# Get logger
logger = logging.getLogger("erp_api_integration")

# Custom JSON encoder to handle Decimal objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def extract_description_from_entry(entry: Dict[str, Any]) -> str:
    """
    Extract description from entry following the same logic as the main processing.
    
    Args:
        entry: The journal entry data
        
    Returns:
        str: The extracted description
    """
    # Get the credit data
    credit_data = entry.get('credit', {})
    
    # First check the main description field
    description = entry.get("description", "")
    
    # If no main description, check credit_description field
    if not description and "credit_description" in entry:
        description = entry.get("credit_description", "")
    
    # If still no description, check Remarks and 備考 fields
    if not description:
        description = credit_data.get("Remarks", "") or credit_data.get("備考", "")
    
    # If still no description, check Receipt/Invoice Note(明細) and free_field
    if not description:
        if credit_data.get("Receipt/Invoice Note(明細)"):
            description = credit_data.get("Receipt/Invoice Note(明細)")
        elif credit_data.get("free_field"):
            description = credit_data.get("free_field")
    
    return description

def convert_date_format(date_str):
    """
    Convert date from YYYY/MM/DD to YYYY-MM-DD format
    
    Args:
        date_str (str): Date string in YYYY/MM/DD format
        
    Returns:
        str: Date string in YYYY-MM-DD format
    """
    if not date_str:
        return ""
    
    try:
        # Split by / and rejoin with -
        parts = date_str.split('/')
        if len(parts) == 3:
            return f"{parts[0]}-{parts[1]}-{parts[2]}"
        return date_str  # Return original if not in expected format
    except Exception as e:
        logger.warning(f"Failed to convert date format for {date_str}: {str(e)}")
        return date_str  # Return original on error

def generate_unique_external_doc_no(original_external_doc_no: str, external_doc_no_counter: Dict[str, int]) -> str:
    """
    Generate a unique External Document Number following the same logic as Issue #72.
    
    Args:
        original_external_doc_no: The original External Document Number
        external_doc_no_counter: Dictionary to track External Document Number uniqueness
        
    Returns:
        str: Unique External Document Number
    """
    if external_doc_no_counter is None:
        logger.warning("external_doc_no_counter is None, returning original External Document Number")
        return original_external_doc_no
    
    # Make External_Document_No unique if it's a duplicate
    if original_external_doc_no in external_doc_no_counter:
        external_doc_no_counter[original_external_doc_no] += 1
        unique_external_doc_no = f"{original_external_doc_no}-{external_doc_no_counter[original_external_doc_no]}"
        logger.info(f"Made VCT responsibility External_Document_No unique: {original_external_doc_no} -> {unique_external_doc_no}")
        return unique_external_doc_no
    else:
        external_doc_no_counter[original_external_doc_no] = 0
        logger.info(f"First occurrence of External_Document_No for VCT responsibility: {original_external_doc_no}")
        return original_external_doc_no

def collect_vct_responsibility_candidates(entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Collect entries that require VCT responsibility entries, grouped by voucher number.
    
    Args:
        entries: List of all journal entries
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary mapping voucher numbers to lists of V-VC00048 entries
    """
    vct_candidates = {}
    
    for entry in entries:
        # Check if this entry requires VCT responsibility entries
        original_vendor_code = entry.get('credit', {}).get('vendor_code', '')
        department = entry.get('credit', {}).get('department', '')
        cost_center = department[:3] if department else ''
        
        # Check if this is a V-VC00048 entry that needs VCT responsibility processing
        # Exclude consolidated entries as they are results of processing, not sources
        is_consolidated = entry.get('credit', {}).get('consolidated', False)
        
        if original_vendor_code == "V-VC00048" and cost_center and cost_center != "VCT":
            voucher_no = entry.get('voucher_no', 'Unknown')
            
            if is_consolidated:
                logger.info(f"Excluding consolidated V-VC00048 entry from VCT responsibility - Voucher: {voucher_no}, Amount: {entry.get('credit', {}).get('amount', 0)}")
            else:
                if voucher_no not in vct_candidates:
                    vct_candidates[voucher_no] = []
                
                vct_candidates[voucher_no].append(entry)
                logger.info(f"Collected VCT responsibility candidate - Voucher: {voucher_no}, Cost Center: {cost_center}, Amount: {entry.get('credit', {}).get('amount', 0)}")
    
    return vct_candidates

def create_consolidated_vct_responsibility_entries(voucher_entries: List[Dict[str, Any]], 
                                                 access_token: str, rate_limiter, 
                                                 used_doc_numbers: Dict[str, int] = None, 
                                                 external_doc_no_counter: Dict[str, int] = None,
                                                 max_retries: int = 3) -> Tuple[int, int]:
    """
    Create consolidated VCT responsibility entries following the existing document numbering logic.
    
    Creates:
    - Individual debit lines for each original entry (preserving amounts and cost centers)
    - Single consolidated credit line with total amount
    - All entries use the same document number (single increment)
    - Ensures External Document Number uniqueness across the entire system
    
    Args:
        voucher_entries: List of entries for the same voucher requiring VCT responsibility entries
        access_token: OAuth2 access token
        rate_limiter: RateLimiter instance for managing API call timing
        used_doc_numbers: Dictionary to track used document numbers and their counters
        external_doc_no_counter: Dictionary to track External Document Number uniqueness
        max_retries: Maximum number of retry attempts for failed API calls
    
    Returns:
        Tuple[int, int]: Count of successful and failed entries
    """
    if not voucher_entries:
        return 0, 0
    
    # Initialize used_doc_numbers if not provided
    if used_doc_numbers is None:
        used_doc_numbers = {}
        logger.warning("used_doc_numbers was None, initializing new dictionary. This may cause document number gaps.")
    
    voucher_no = voucher_entries[0].get('voucher_no', 'Unknown')
    logger.info(f"Creating consolidated VCT responsibility entries for voucher {voucher_no} with {len(voucher_entries)} entries")
    
    # CRITICAL: Follow existing document numbering logic from PR #87 and Issue #91
    # Initialize counter to 0 (will be incremented to 1, as fixed in Issue #91)
    if voucher_no not in used_doc_numbers:
        used_doc_numbers[voucher_no] = 0
        logger.info(f"Initializing counter for document number {voucher_no}")
    
    # Increment ONCE for the entire consolidated group
    used_doc_numbers[voucher_no] += 1
    consolidated_doc_no = f"{voucher_no}-{used_doc_numbers[voucher_no]}"
    
    logger.info(f"Using consolidated document number {consolidated_doc_no} for all VCT responsibility entries in voucher {voucher_no}")
    
    success_count = 0
    failure_count = 0
    
    # Import post_journal_line function
    from core.process_japan_exports import post_journal_line
    
    # Fixed values for journal entries
    JOURNAL_TEMPLATE_NAME = "PURCHASES"
    JOURNAL_BATCH_NAME = "PURCHASE"
    DOCUMENT_TYPE = "Invoice"
    
    # Step 1: Create individual debit lines (preserving original entry details)
    for entry in voucher_entries:
        credit_data = entry.get('credit', {})
        amount = credit_data.get('amount', 0)
        currency = credit_data.get('currency', '')
        department = credit_data.get('department', '')
        cost_center = department[:3] if department else ''
        
        # Extract description from entry
        original_description = extract_description_from_entry(entry)
        vct_description = f"{department} {original_description}"
        
        # Ensure description is not too long
        if len(vct_description) > 100:
            vct_description = vct_description[:100]
            logger.warning(f"Truncated VCT responsibility description to 100 characters: {vct_description}")
        
        # Get external document number and document date
        original_external_doc_no = entry.get('External_Document_No', voucher_no)
        document_date = entry.get('Document_Date', '')
        
        # Generate unique External Document Number for VCT responsibility debit line
        unique_external_doc_no = generate_unique_external_doc_no(original_external_doc_no, external_doc_no_counter)
        
        debit_line = {
            "Journal_Template_Name": JOURNAL_TEMPLATE_NAME,
            "Journal_Batch_Name": JOURNAL_BATCH_NAME,
            "Document_Type": DOCUMENT_TYPE,
            "External_Document_No": unique_external_doc_no,  # Use unique External Document Number
            "Document_No": consolidated_doc_no,  # Same doc number for all
            "Document_Date": convert_date_format(document_date),
            "Account_Type": "G/L Account",
            "Account_No": "18600-10",  # Fixed account number
            "Description": vct_description,
            "Currency_Code": currency,
            "Amount": amount,
            "Shortcut_Dimension_1_Code": "VCT",
            "Shortcut_Dimension_2_Code": "VCT.9999",  # Fixed department code
            "ShortcutDimCode3": cost_center,  # Original cost center as intercompany code
            "ShortcutDimCode4": "",
            "ShortcutDimCode5": "",
            "ShortcutDimCode6": "",
            "ShortcutDimCode7": "",
            "ShortcutDimCode8": "",
            "ShortcutDimCode9": "",
            "ShortcutDimCode10": "",
            "ShortcutDimCode11": "",
            "ShortcutDimCode12": "",
            "ShortcutDimCode13": "",
            "ShortcutDimCode14": "",
            "ShortcutDimCode15": ""
        }
        
        logger.info(f"Creating individual debit line - Amount: {amount}, Cost Center: {cost_center}, Doc No: {consolidated_doc_no}")
        
        # Post individual debit line
        debit_line_copy = json.loads(json.dumps(debit_line, cls=DecimalEncoder))
        debit_success, debit_response = post_journal_line(debit_line_copy, access_token, rate_limiter, max_retries)
        
        if debit_success:
            logger.info(f"Successfully posted VCT responsibility debit line for voucher {voucher_no}")
            success_count += 1
        else:
            logger.error(f"Failed to post VCT responsibility debit line for voucher {voucher_no}")
            failure_count += 1
    
    # Step 2: Create single consolidated credit line
    total_amount = sum(entry.get('credit', {}).get('amount', 0) for entry in voucher_entries)
    template_entry = voucher_entries[0]  # Use first entry as template
    template_credit = template_entry.get('credit', {})
    
    # Use the description from the first entry as template
    original_description = extract_description_from_entry(template_entry)
    
    # Generate unique External Document Number for VCT responsibility credit line
    original_external_doc_no = template_entry.get('External_Document_No', voucher_no)
    unique_external_doc_no = generate_unique_external_doc_no(original_external_doc_no, external_doc_no_counter)
    
    credit_line = {
        "Journal_Template_Name": JOURNAL_TEMPLATE_NAME,
        "Journal_Batch_Name": JOURNAL_BATCH_NAME,
        "Document_Type": DOCUMENT_TYPE,
        "External_Document_No": unique_external_doc_no,  # Use unique External Document Number
        "Document_No": consolidated_doc_no,  # Same doc number
        "Document_Date": convert_date_format(template_entry.get('Document_Date', '')),
        "Account_Type": "Vendor",
        "Account_No": "V-VC00048",  # Fixed vendor code
        "Description": original_description,  # Use original description without department prefix
        "Currency_Code": template_credit.get('currency', ''),
        "Amount": -total_amount,  # Consolidated negative amount
        "Shortcut_Dimension_1_Code": "VCT",
        "Shortcut_Dimension_2_Code": "VCT.9999",  # Fixed department code
        "ShortcutDimCode3": "",  # Empty intercompany code for credit line
        "ShortcutDimCode4": "",
        "ShortcutDimCode5": "",
        "ShortcutDimCode6": "",
        "ShortcutDimCode7": "",
        "ShortcutDimCode8": "",
        "ShortcutDimCode9": "",
        "ShortcutDimCode10": "",
        "ShortcutDimCode11": "",
        "ShortcutDimCode12": "",
        "ShortcutDimCode13": "",
        "ShortcutDimCode14": "",
        "ShortcutDimCode15": ""
    }
    
    logger.info(f"Creating consolidated credit line - Total Amount: {-total_amount}, Doc No: {consolidated_doc_no}")
    
    # Post consolidated credit line
    credit_line_copy = json.loads(json.dumps(credit_line, cls=DecimalEncoder))
    credit_success, credit_response = post_journal_line(credit_line_copy, access_token, rate_limiter, max_retries)
    
    if credit_success:
        logger.info(f"Successfully posted consolidated VCT responsibility credit line for voucher {voucher_no}")
        success_count += 1
    else:
        logger.error(f"Failed to post consolidated VCT responsibility credit line for voucher {voucher_no}")
        failure_count += 1
    
    logger.info(f"Completed consolidated VCT responsibility entries for voucher {voucher_no} - Success: {success_count}, Failure: {failure_count}")
    
    return success_count, failure_count
