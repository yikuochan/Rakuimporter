# Document_No Assignment Fix

## Issue Description

There was an issue with voucher numbers being incorrectly converted in the BC API payload:

1. Voucher numbers VPA-0000119, VPA-0000120, VPA-0000121, VPA-0000124 were all being converted to the same Document_No VPA-0000119 in the BC API payload.
2. Similarly, VPA-0000122 and VPA-0000123 were both being converted to VPA-0000122 in the BC API payload.

This issue was causing confusion and data integrity problems, as multiple different vouchers were being recorded with the same Document_No in the Business Central system.

## Root Cause Analysis

After examining the code and logs, the root cause was identified:

1. The code was correctly setting the Document_No field in the API request payload to match the voucher_no.
2. However, the BC API was not maintaining this Document_No uniqueness when processing multiple entries with the same External_Document_No value.
3. Since many entries shared the same External_Document_No (e.g., "20250402"), the BC API was grouping them together and using the first Document_No it encountered for all of them.

## Solution

The solution was to ensure that each entry has a unique External_Document_No by prefixing it with the voucher_no:

1. Modified the `process_entries` function in `process_japan_exports.py` to set the External_Document_No to include the voucher_no as a prefix.
2. For example, if the original External_Document_No was "20250402" and the voucher_no was "VPA-0000120", the new External_Document_No would be "VPA-0000120-20250402".
3. This ensures that each entry has a unique External_Document_No, which prevents the BC API from grouping different vouchers together.

## Code Changes

The following changes were made to `process_japan_exports.py`:

1. Added code to modify the External_Document_No in the debit and credit lines to include the voucher_no as a prefix.
2. This was done in all places where journal lines are created and posted to the API.

## Testing

A new test file `test_document_no_fix.py` was created to verify the fix:

1. Tests that `create_journal_line` correctly sets the Document_No to match the voucher_no.
2. Tests that `process_entries` maintains the correct Document_No for each entry when posting to the API.
3. Tests that the External_Document_No is properly formatted to include the voucher_no.

All tests passed, confirming that the fix works correctly.

## Verification

To verify the fix in production:

1. Process a batch of entries with different voucher numbers but the same External_Document_No.
2. Check the BC API logs to confirm that each entry maintains its correct Document_No.
3. Verify in the Business Central system that each voucher is recorded with its correct Document_No.
