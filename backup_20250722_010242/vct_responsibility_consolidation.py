#!/usr/bin/env python3
"""
VCT Responsibility Entry Consolidation Module

This module provides functionality to process VCT responsibility entries for V-VC00048 vendor mappings.
Based on GitHub Issue #35, V-VC00048 entries should be processed individually (not consolidated)
to create separate debit+credit pairs for each entry for easier auditing.

This creates:
- Individual debit+credit pairs for each V-VC00048 entry
- Each pair gets its own unique document number
- Maintains audit trail with individual entries
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
    
    UPDATED REQUIREMENT: V-VC00048 entries with non-VCT cost centers now require VCT responsibility entries
    to record the expense responsibility in VCT company. Only V-VC00048 entries with VCT cost center
    are excluded to prevent duplicate processing.
    
    Args:
        entries: List of all journal entries
        
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary mapping voucher numbers to lists of entries requiring VCT responsibility
    """
    vct_candidates = {}
    
    for entry in entries:
        # Check if this entry requires VCT responsibility entries
        original_vendor_code = entry.get('credit', {}).get('vendor_code', '')
        department = entry.get('credit', {}).get('department', '')
        cost_center = department[:3] if department else ''
        voucher_no = entry.get('voucher_no', 'Unknown')
        
        # CRITICAL FIX: Only include V-VC00048 entries with non-VCT cost centers
        # VCT cost center entries should NOT get VCT responsibility processing to avoid duplication
        if original_vendor_code == "V-VC00048":
            if cost_center == "VCT":
                logger.info(f"Excluding V-VC00048 entry with VCT cost center from VCT responsibility processing - Voucher: {voucher_no} (no duplicate processing needed)")
                continue
            elif cost_center and cost_center in ["VCA", "VCP", "VCG", "VCJ"]:
                logger.info(f"Including V-VC00048 entry with non-VCT cost center ({cost_center}) for VCT responsibility processing - Voucher: {voucher_no}")
                if voucher_no not in vct_candidates:
                    vct_candidates[voucher_no] = []
                vct_candidates[voucher_no].append(entry)
            else:
                logger.info(f"Excluding V-VC00048 entry with unknown cost center '{cost_center}' from VCT responsibility processing - Voucher: {voucher_no}")
                continue
        
        # Process other vendor codes that require VCT responsibility entries if needed
        # (This is for future extensibility)
        
    return vct_candidates

def create_consolidated_vct_responsibility_entries(voucher_entries: List[Dict[str, Any]], 
                                                 access_token: str, rate_limiter, 
                                                 used_doc_numbers: Dict[str, int] = None, 
                                                 external_doc_no_counter: Dict[str, int] = None,
                                                 max_retries: int = 3) -> Tuple[int, int]:
    """
    Create VCT responsibility entries as individual debit+credit pairs.
    
    IMPORTANT: Based on GitHub Issue #35, V-VC00048 entries are NOT consolidated.
    They are created as individual debit/credit pairs for easier auditing.
    
    For V-VC00048:
    - Creates individual debit/credit pairs for each entry
    - Each pair gets its own unique document number (APA-0000552-1, APA-0000552-2, etc.)
    
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
    
    # Check if this is V-VC00048 - these should use individual approach (separate debit+credit pairs)
    is_v_vc00048 = all(entry.get('credit', {}).get('vendor_code', '') == 'V-VC00048' for entry in voucher_entries)
    
    if is_v_vc00048:
        logger.info(f"Creating individual VCT responsibility entries for V-VC00048 voucher {voucher_no} with {len(voucher_entries)} entries (individual debit+credit pairs)")
    else:
        logger.info(f"Creating individual VCT responsibility entries for voucher {voucher_no} with {len(voucher_entries)} entries")
    
    # Initialize counter if needed
    if voucher_no not in used_doc_numbers:
        used_doc_numbers[voucher_no] = 0
        logger.info(f"Initializing counter for document number {voucher_no}")
    
    success_count = 0
    failure_count = 0
    
    # Process each entry individually (create separate debit+credit pairs)
    for i, entry in enumerate(voucher_entries):
        # Increment counter for each individual pair
        used_doc_numbers[voucher_no] += 1
        individual_doc_no = f"{voucher_no}-{used_doc_numbers[voucher_no]}"
        
        logger.info(f"Creating individual VCT responsibility pair {i+1}/{len(voucher_entries)} with document number {individual_doc_no}")
        
        # Create individual debit+credit pair
        pair_success, pair_failure = _create_individual_vct_responsibility_pair(
            entry, individual_doc_no, access_token, rate_limiter, external_doc_no_counter, max_retries
        )
        
        success_count += pair_success
        failure_count += pair_failure
    
    logger.info(f"Completed individual VCT responsibility entries for voucher {voucher_no} - Success: {success_count}, Failure: {failure_count}")
    
    return success_count, failure_count

def _create_individual_vct_responsibility_pair(entry: Dict[str, Any], 
                                              document_no: str,
                                              access_token: str, 
                                              rate_limiter, 
                                              external_doc_no_counter: Dict[str, int],
                                              max_retries: int = 3) -> Tuple[int, int]:
    """
    Create an individual debit/credit pair for V-VC00048 VCT responsibility.
    
    Args:
        entry: Single entry requiring VCT responsibility
        document_no: Document number to use for this pair
        access_token: OAuth2 access token
        rate_limiter: RateLimiter instance
        external_doc_no_counter: Dictionary to track External Document Number uniqueness
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple[int, int]: Count of successful and failed entries
    """
    success_count = 0
    failure_count = 0
    
    # Import post_journal_line function
    from core.process_japan_exports import post_journal_line
    
    # Fixed values for journal entries
    JOURNAL_TEMPLATE_NAME = "PURCHASES"
    JOURNAL_BATCH_NAME = "PURCHASE"
    DOCUMENT_TYPE = "Invoice"
    
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
    original_external_doc_no = entry.get('External_Document_No', entry.get('voucher_no', 'Unknown'))
    document_date = entry.get('Document_Date', '')
    
    # Generate unique External Document Number for debit line
    unique_external_doc_no_debit = generate_unique_external_doc_no(original_external_doc_no, external_doc_no_counter)
    
    # Create debit line
    debit_line = {
        "Journal_Template_Name": JOURNAL_TEMPLATE_NAME,
        "Journal_Batch_Name": JOURNAL_BATCH_NAME,
        "Document_Type": DOCUMENT_TYPE,
        "External_Document_No": unique_external_doc_no_debit,
        "Document_No": document_no,
        "Document_Date": convert_date_format(document_date),
        "Account_Type": "G/L Account",
        "Account_No": "18600-10",
        "Description": vct_description,
        "Currency_Code": currency,
        "Amount": amount,
        "Shortcut_Dimension_1_Code": "VCT",
        "Shortcut_Dimension_2_Code": "VCT.9999",
        "ShortcutDimCode3": cost_center,
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
    
    logger.info(f"Creating individual debit line - Amount: {amount}, Cost Center: {cost_center}, Doc No: {document_no}")
    
    # Post debit line
    debit_line_copy = json.loads(json.dumps(debit_line, cls=DecimalEncoder))
    debit_success, debit_response = post_journal_line(debit_line_copy, access_token, rate_limiter, max_retries)
    
    if debit_success:
        logger.info(f"Successfully posted VCT responsibility debit line for document {document_no}")
        success_count += 1
    else:
        logger.error(f"Failed to post VCT responsibility debit line for document {document_no}")
        failure_count += 1
    
    # Generate unique External Document Number for credit line
    unique_external_doc_no_credit = generate_unique_external_doc_no(original_external_doc_no, external_doc_no_counter)
    
    # Create credit line
    credit_line = {
        "Journal_Template_Name": JOURNAL_TEMPLATE_NAME,
        "Journal_Batch_Name": JOURNAL_BATCH_NAME,
        "Document_Type": DOCUMENT_TYPE,
        "External_Document_No": unique_external_doc_no_credit,
        "Document_No": document_no,
        "Document_Date": convert_date_format(document_date),
        "Account_Type": "Vendor",
        "Account_No": "V-VC00048",
        "Description": original_description,
        "Currency_Code": currency,
        "Amount": -amount,
        "Shortcut_Dimension_1_Code": "VCT",
        "Shortcut_Dimension_2_Code": "VCT.9999",
        "ShortcutDimCode3": "",
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
    
    logger.info(f"Creating individual credit line - Amount: {-amount}, Doc No: {document_no}")
    
    # Post credit line
    credit_line_copy = json.loads(json.dumps(credit_line, cls=DecimalEncoder))
    credit_success, credit_response = post_journal_line(credit_line_copy, access_token, rate_limiter, max_retries)
    
    if credit_success:
        logger.info(f"Successfully posted VCT responsibility credit line for document {document_no}")
        success_count += 1
    else:
        logger.error(f"Failed to post VCT responsibility credit line for document {document_no}")
        failure_count += 1
    
    return success_count, failure_count
