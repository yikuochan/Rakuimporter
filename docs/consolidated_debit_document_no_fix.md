# Consolidated Debit Document Number Duplication Fix

## Issue Description

When processing multiple entries with consolidated credit in the `process_entries` function, multiple debit lines can have the same document number, which causes problems in the Business Central system. For example, if there are multiple debit entries with the same document number APA-0000501, the system would try to create multiple journal entries with the same document number, leading to potential conflicts or errors.

## Root Cause Analysis

In the `process_entries` function in `core/process_japan_exports.py`, when creating debit lines for consolidated entries, the document number was always set to the original voucher number without checking if that document number had been used before:

```python
# Process all debit lines
for i, entry in enumerate(valid_entries):
    debit_line = create_journal_line(entry, "debit")
    # Ensure Document_No matches the entry's voucher_no
    entry_voucher_no = entry.get('voucher_no', voucher_no)
    debit_line["Document_No"] = entry_voucher_no
    # ... other code ...
```

This caused issues when multiple debit lines were created with the same document number, as the Business Central system expects unique document numbers for each journal entry.

## Solution

The solution is to track document numbers that have been used and append a suffix (-1, -2, etc.) to duplicate document numbers. This ensures that each debit line has a unique document number.

The fix involves:

1. Adding a `used_doc_numbers` dictionary to the `process_entries` function to track used document numbers
2. Checking if a document number has been used before and appending a suffix if needed
3. Ensuring that only debit lines after the first one get a suffix

Here's the key part of the implementation:

```python
# Check if this document number has been used before for debit lines
# and append a suffix if needed
original_doc_no = entry_voucher_no
if i > 0:  # First entry uses original document number
    if original_doc_no in used_doc_numbers:
        # Increment the count for this document number
        used_doc_numbers[original_doc_no] += 1
        # Append the suffix to the document number
        modified_doc_no = f"{original_doc_no}-{used_doc_numbers[original_doc_no]}"
        logger.info(f"Document number {original_doc_no} has been used before for debit line. Using {modified_doc_no} instead.")
        debit_line["Document_No"] = modified_doc_no
    else:
        # First time seeing this document number
        used_doc_numbers[original_doc_no] = 0
        debit_line["Document_No"] = original_doc_no
else:
    # First entry uses original document number
    if original_doc_no not in used_doc_numbers:
        used_doc_numbers[original_doc_no] = 0
    debit_line["Document_No"] = original_doc_no
```

## Implementation Details

The fix has been implemented in the following files:

1. `core/process_japan_exports.py`:
   - Added `used_doc_numbers` dictionary to the `process_entries` function
   - Added logic to check for duplicate document numbers and append a suffix if needed
   - Added logging to track document number modifications

2. `tests/test_consolidated_debit_document_no_fix.py`:
   - Added unit tests to verify the document number duplication fix works correctly
   - Tests include checking that document numbers are modified correctly for multiple entries

## Example

For example, if there are multiple debit entries with the same document number APA-0000501:

- First debit entry: APA-0000501 (unchanged)
- Second debit entry: APA-0000501-1
- Third debit entry: APA-0000501-2
- And so on...

This ensures that each debit line has a unique document number, preventing conflicts in the Business Central system.

## Testing

The fix has been tested with unit tests that verify:

1. The first debit line with a given document number uses the original document number
2. Subsequent debit lines with the same document number have a suffix appended
3. The suffix increments correctly for multiple debit lines
4. Document numbers are tracked separately for different voucher numbers

All tests have passed successfully, confirming that the document number duplication fix works correctly.

## Conclusion

The consolidated debit document number duplication fix ensures that each debit line has a unique document number, preventing conflicts in the Business Central system. This is particularly important for consolidated entries where multiple debit lines can have the same document number.
