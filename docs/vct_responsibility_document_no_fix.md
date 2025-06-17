# VCT Responsibility Document Number Fix

## Issue Description

When processing consolidated debit lines with VCT responsibility entries, duplicate document numbers were being generated. This was causing issues in Business Central, as document numbers must be unique.

The issue was specifically observed with document numbers like "APA-0000401" and "APA-0000451", where multiple debit lines were created with the same document number.

## Root Cause Analysis

The root cause was identified in the `create_vct_responsibility_entries` function in `core/process_japan_exports.py`. When creating VCT responsibility entries, the function was not modifying the document number to add a suffix, which resulted in duplicate document numbers.

The issue was particularly visible in the log file:

```
2025-06-17 12:23:23,055 - erp_api_integration - INFO - Posting debit line for voucher APA-0000401 with Document_No: APA-0000401
2025-06-17 12:23:29,000 - erp_api_integration - INFO - Posting VCT responsibility debit line for voucher APA-0000401
2025-06-17 12:23:29,000 - erp_api_integration - INFO - Document No: APA-0000401
```

As shown above, both the original debit line and the VCT responsibility debit line were using the same document number "APA-0000401".

## Solution

The solution was to modify the `create_vct_responsibility_entries` function to use the same document number suffix logic that was already being used for regular debit lines. This ensures that each VCT responsibility entry gets a unique document number.

The following changes were made:

1. Updated the `create_vct_responsibility_entries` function signature to accept a `used_doc_numbers` dictionary parameter:

```python
def create_vct_responsibility_entries(entry: Dict[str, Any], access_token: str, rate_limiter: RateLimiter, 
                                     used_doc_numbers: Dict[str, int] = None, max_retries: int = 3) -> Tuple[int, int]:
```

2. Added logic to check if the document number has been used before and append a suffix if needed:

```python
# Check if this document number has been used before and append a suffix if needed
original_doc_no = voucher_no

# Log the document number being processed
logger.info(f"Processing document number for VCT responsibility entry: {original_doc_no}")

# Always check if this document number is in the tracking dictionary
if original_doc_no not in used_doc_numbers:
    used_doc_numbers[original_doc_no] = 0
    logger.info(f"Initializing counter for document number {original_doc_no}")

# Always increment for VCT responsibility entries
used_doc_numbers[original_doc_no] += 1
modified_doc_no = f"{original_doc_no}-{used_doc_numbers[original_doc_no]}"
logger.info(f"Using modified document number {modified_doc_no} for VCT responsibility entry")
```

3. Updated the document number in both debit and credit lines:

```python
debit_line["Document_No"] = modified_doc_no
credit_line["Document_No"] = modified_doc_no
```

4. Updated all calls to `create_vct_responsibility_entries` to pass the `used_doc_numbers` dictionary:

```python
vct_success, vct_failure = create_vct_responsibility_entries(entry, access_token, rate_limiter, used_doc_numbers, max_retries)
```

## Testing

The fix was tested using the `tests/test_vct_responsibility_document_no_fix.py` test file, which verifies that document numbers are modified only for VCT responsibility entries. The test ensures that:

1. Document numbers for VCT responsibility entries are modified with suffixes like "-1", "-2", etc.
2. Document numbers for non-VCT responsibility entries are not modified.
3. Document numbers for VCT cost center entries are not modified.

## Expected Behavior

After the fix, the log file should show different document numbers for the original debit line and the VCT responsibility debit line:

```
2025-06-17 12:23:23,055 - erp_api_integration - INFO - Posting debit line for voucher APA-0000401 with Document_No: APA-0000401
2025-06-17 12:23:29,000 - erp_api_integration - INFO - Posting VCT responsibility debit line for voucher APA-0000401
2025-06-17 12:23:29,000 - erp_api_integration - INFO - Document No: APA-0000401-1
```

This ensures that each document number is unique, preventing conflicts in the Business Central system.
