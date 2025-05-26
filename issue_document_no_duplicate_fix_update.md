# External Document Number Uniqueness Implementation

## Issue Description

Business Central API requires the External Document Number field to be unique. Previously, the system was using the value from column S "Receipt/Invoice No.(明細)" in raw CSV files, or falling back to the transaction date if column S was empty. However, there was no mechanism to ensure uniqueness when the same value appeared multiple times, which could cause API errors or data inconsistencies.

## Requirements

1. The External Document Number value comes from column S "Receipt/Invoice No.(明細)" in raw CSV files
2. If column S is empty, use column C "仕訳日" (transaction date)
3. If both are empty, use "Empty-{timestamp in milliseconds}"
4. Uniqueness must be enforced across the entire file
5. Format for duplicates: add "-2", "-3", etc. suffix

## Solution Implemented

We've implemented a tracking system in the CSV to JSON converter that adds a numeric suffix to make duplicate External Document Numbers unique:

1. First occurrence: Use the original value (e.g., "2025/4/18")
2. Second occurrence: Add "-2" suffix (e.g., "2025/4/18-2")
3. Third occurrence: Add "-3" suffix (e.g., "2025/4/18-3")
4. And so on...

For consolidated entries, we add a "-consolidated" suffix to ensure they also have unique External Document Numbers.

### Code Changes

The following changes were made to `csv_to_json_converter.py`:

1. Added a tracking dictionary `external_doc_no_counter` to count occurrences of each External_Document_No value
2. Modified the logic to get External_Document_No from column S "Receipt/Invoice No.(明細)" or fall back to column C "仕訳日"
3. Added logic to generate "Empty-{timestamp in milliseconds}" for completely empty values
4. Added logic to make External_Document_No unique by adding suffixes to duplicates
5. Modified the `consolidate_entries` function to add "-consolidated" suffix to consolidated entries

### Example

For a CSV file with these entries:
- Entry 1: Receipt/Invoice No.(明細) = "2025/4/18"
- Entry 2: Receipt/Invoice No.(明細) = "2025/4/18"
- Entry 3: Receipt/Invoice No.(明細) = "2025/4/18"
- Entry 4: Receipt/Invoice No.(明細) = "" (empty), 仕訳日 = "2025/04/03"
- Entry 5: Receipt/Invoice No.(明細) = "" (empty), 仕訳日 = "2025/04/03"
- Entry 6: Receipt/Invoice No.(明細) = "" (empty), 仕訳日 = "" (empty)

The resulting External_Document_No values will be:
- Entry 1: "2025/4/18"
- Entry 2: "2025/4/18-2"
- Entry 3: "2025/4/18-3"
- Entry 4: "2025/04/03"
- Entry 5: "2025/04/03-2"
- Entry 6: "Empty-{timestamp in milliseconds}"

## Testing

A new test file `test_external_document_no_uniqueness.py` was created to verify the uniqueness logic:

1. Tests that duplicate External_Document_No values are made unique with appropriate suffixes
2. Tests that empty values fall back to transaction date or "Empty-" prefix
3. Tests that all External_Document_No values in the output are unique

All tests are passing, confirming that the implementation works correctly.

## Benefits

1. **API Compatibility**: Ensures that all entries have unique External Document Numbers as required by the Business Central API
2. **Data Integrity**: Prevents potential data loss or corruption due to duplicate External Document Numbers
3. **Traceability**: The original value is preserved as much as possible, with a simple suffix added only when needed
4. **Robustness**: Handles all edge cases, including completely empty values

## Usage

No changes are required to the usage of the CSV to JSON converter. The uniqueness logic is applied automatically during the conversion process.
