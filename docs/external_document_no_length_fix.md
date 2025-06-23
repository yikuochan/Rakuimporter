# External_Document_No Length Limit Fix

## Issue Description

The Business Central API has a 35-character limit for the `External_Document_No` field. When importing data with longer external document numbers, the API would return a 400 Bad Request error with the message:

```
The length of the string is 45, but it must be a maximum of 35 characters. Value: 'Phone, including two China travel roaming fee'
```

## Root Cause

The system was not validating or truncating the `External_Document_No` field before sending it to the Business Central API. Long descriptions from the CSV data (particularly from the "Receipt/Invoice Note(明細)" column) were being used directly as external document numbers without length validation.

## Solution

Implemented automatic truncation of `External_Document_No` fields to 35 characters in two key locations:

### 1. CSV to JSON Converter (`core/csv_to_json_converter.py`)

Added truncation logic in the `convert_csv_to_json` function:

```python
# Truncate External_Document_No to 35 characters if needed
if len(external_doc_no) > 35:
    original_length = len(external_doc_no)
    external_doc_no = external_doc_no[:35]
    logger.warning(f"Truncated External_Document_No from {original_length} to 35 characters: '{entry.get('External_Document_No', '')}' -> '{external_doc_no}'")
```

### 2. Process Japan Exports (`core/process_japan_exports.py`)

Added truncation logic in the `create_journal_line` function:

```python
# Truncate External_Document_No to 35 characters if needed
external_doc_no = entry.get('External_Document_No', '')
if len(external_doc_no) > 35:
    original_length = len(external_doc_no)
    external_doc_no = external_doc_no[:35]
    logger.warning(f"Truncated External_Document_No from {original_length} to 35 characters: '{entry.get('External_Document_No', '')}' -> '{external_doc_no}'")
```

## Implementation Details

- **Truncation Method**: Simple string slicing (`[:35]`) to take the first 35 characters
- **Logging**: Warning messages are logged when truncation occurs, showing both original and truncated values
- **Preservation**: Original data in CSV/JSON files remains unchanged; truncation only affects API calls
- **Performance**: Minimal performance impact as truncation only occurs when needed

## Testing

Created comprehensive test suite (`tests/test_external_document_no_length_fix.py`) covering:

1. **Truncation in CSV converter**: Verifies long external document numbers are truncated during CSV to JSON conversion
2. **Truncation in process exports**: Verifies truncation occurs when creating journal lines
3. **No truncation when within limit**: Ensures short external document numbers are not modified
4. **Exactly 35 characters**: Verifies that 35-character strings are not truncated

## Verification

The fix was verified with the problematic file `examples/0623/Raku export-VCT GE.utf8.csv`:

### Before Fix
```
HTTP error: 400 Client Error: Bad Request
Error message: The length of the string is 45, but it must be a maximum of 35 characters. Value: 'Phone, including two China travel roaming fee'
```

### After Fix
```
2025-06-23 12:09:18,302 - csv_converter - WARNING - Truncated External_Document_No from 45 to 35 characters: 'Phone, including two China travel roaming fee' -> 'Phone, including two China travel r'
```

API calls now succeed with the truncated external document numbers.

## Impact

- **Positive**: Eliminates External_Document_No length errors, allowing successful data import
- **Minimal**: Only affects display/reference value; no impact on financial data integrity
- **Transparent**: Clear logging shows when and how truncation occurs
- **Backward Compatible**: Existing short external document numbers remain unchanged

## Files Modified

1. `core/csv_to_json_converter.py` - Added truncation in CSV conversion
2. `core/process_japan_exports.py` - Added truncation in journal line creation
3. `tests/test_external_document_no_length_fix.py` - Comprehensive test coverage

## Future Considerations

- Consider implementing configurable truncation length if Business Central limits change
- Evaluate alternative approaches like abbreviation or smart truncation algorithms
- Monitor for any business impact from truncated external document numbers
