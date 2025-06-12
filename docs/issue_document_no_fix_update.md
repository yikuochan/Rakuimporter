# External_Document_No Handling Update

## Issue Description

Previously, the system was modifying the External_Document_No field by prefixing it with the voucher_no to ensure uniqueness. For example, if the original External_Document_No was "20250402" and the voucher_no was "VPA-0000120", the modified External_Document_No would be "VPA-0000120-20250402".

However, it was determined that uniqueness of the External_Document_No field is not actually required by the Business Central API. The requirement has been updated to use the original External_Document_No value from the JSON file without any modification.

## Changes Made

The following changes were implemented:

1. Modified the `process_entries` function in `process_japan_exports.py` to remove the code that adds the voucher_no prefix to the External_Document_No.
2. Updated the tests in `test_document_no_fix.py` and `test_document_no_fix_with_real_data.py` to reflect this change.

### Code Changes

In `process_japan_exports.py`, removed the following lines:

```python
# Set External_Document_No to include the voucher_no to ensure uniqueness
if "External_Document_No" in debit_line:
    debit_line["External_Document_No"] = f"{voucher_no}-{debit_line['External_Document_No']}"
```

And similar lines for credit lines.

### Test Updates

1. Updated `test_document_no_fix.py` to expect the original External_Document_No values without the voucher_no prefix.
2. Updated `test_document_no_fix_with_real_data.py` to remove the check that verifies if External_Document_No values start with the Document_No.

## Testing

All tests have been updated and are passing:

1. `test_document_no_fix.py`
2. `test_document_no_fix_with_real_data.py`
3. `unittest/test_document_no_assignment.py`
4. `unittest/test_multiple_vouchers_same_vendor.py`

## Verification

The changes have been verified to work correctly with the test data. The system now uses the original External_Document_No values from the JSON file without any modification.
