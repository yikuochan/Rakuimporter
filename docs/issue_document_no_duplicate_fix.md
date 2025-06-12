# Document_No Duplication Issue Fix

## Issue Description

When processing journal entries with different voucher numbers, the system was incorrectly assigning the same Document_No to multiple journal entries in the Business Central (BC) payload. This issue was observed with vouchers like VPA-0000119, VPA-0000120, VPA-0000121, and VPA-0000122, where the system was generating multiple journal line items with the same Document_No, even though they should have had unique Document_No values matching their respective voucher numbers.

## Root Cause Analysis

The issue was in the `process_japan_exports.py` file. When a journal line was created with the correct Document_No and then passed to the `post_journal_line` function, the function was modifying the original object. This meant that when the next journal line was created, it would inherit any modifications made to the previous journal line object.

Specifically, in the `process_entries` function, the journal line objects were being passed directly to the `post_journal_line` function without creating a deep copy first:

```python
# Process debit line
debit_line = create_journal_line(entry, "debit")
# Ensure Document_No matches the voucher_no
debit_line["Document_No"] = entry_voucher_no
# Use the original External_Document_No without modification
logger.info(f"Posting debit line for voucher {entry_voucher_no} with Document_No: {debit_line['Document_No']}")
debit_success, debit_response = post_journal_line(debit_line, access_token)
```

If the `post_journal_line` function or any other code that processes the journal line object modifies it, those modifications would persist and affect subsequent journal lines.

## Solution

The solution is to create a deep copy of the journal line object before passing it to the `post_journal_line` function. This ensures that each journal line is independent and modifications made during API calls don't affect subsequent journal lines.

The fix involves adding a deep copy operation using `json.loads(json.dumps(journal_line))` before passing the journal line to the `post_journal_line` function:

```python
# Process debit line
debit_line = create_journal_line(entry, "debit")
# Ensure Document_No matches the voucher_no
debit_line["Document_No"] = entry_voucher_no
# Use the original External_Document_No without modification
logger.info(f"Posting debit line for voucher {entry_voucher_no} with Document_No: {debit_line['Document_No']}")
# Create a deep copy of the debit line to prevent any reference issues
debit_line_copy = json.loads(json.dumps(debit_line))
debit_success, debit_response = post_journal_line(debit_line_copy, access_token)
```

This change has been implemented in multiple places in the `process_entries` function where journal lines are passed to the `post_journal_line` function.

## Testing

Two test files were created to verify the fix:

1. `test_document_no_fix.py` - A unit test with synthetic data that verifies the Document_No is correctly assigned for each journal line.

2. `test_document_no_fix_with_real_data.py` - A test that uses real data from the 05-Raku export-utf8-fixed.json file to verify the fix works with the actual data that was causing the issue.

3. `test_document_no_duplicate_fix.py` - A more comprehensive test that specifically tests the deep copy functionality to ensure that modifications made to one journal line don't affect subsequent journal lines.

All tests have passed successfully, confirming that each journal line now has the correct Document_No matching its voucher_no, and that modifications made during API calls don't affect subsequent journal lines.

## Implementation Details

The fix has been implemented in the `process_entries` function in `process_japan_exports.py`. The following changes were made:

1. Added deep copy operations for all journal line objects before passing them to the `post_journal_line` function.

2. Added comments to explain the purpose of the deep copy operations.

3. Ensured that all journal lines have the correct Document_No matching their respective voucher numbers.

## Verification

The fix has been verified with both synthetic test data and real data from the 05-Raku export-utf8-fixed.json file. The tests confirm that each journal line now has the correct Document_No matching its voucher_no, and that modifications made during API calls don't affect subsequent journal lines.

## Conclusion

The Document_No duplication issue has been fixed by creating deep copies of journal line objects before passing them to the `post_journal_line` function. This ensures that each journal line is independent and modifications made during API calls don't affect subsequent journal lines.
