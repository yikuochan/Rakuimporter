# External_Document_No Counter Initialization Fix

## Issue Summary
Fixed the External_Document_No uniqueness counter initialization to ensure duplicate External_Document_No values start from `-1` instead of `-2`.

## Problem Description
When the system encountered duplicate External_Document_No values, the uniqueness counter was incorrectly initialized, causing the sequence to start from `-2` instead of the expected `-1`.

### Example of the Issue:
- Original External_Document_No: `20250522`
- First duplicate should be: `20250522-1` 
- But was generating: `20250522-2`

## Root Cause Analysis
The issue was found in two files where counter initialization was incorrect:

1. **csv_to_json_converter.py**: Counter was initialized to `1` instead of `0`
2. **process_japan_exports.py**: Counter for VCT responsibility entries was initialized to `0` instead of `-1`

## Solution Implemented

### Changes Made:

#### 1. csv_to_json_converter.py (Line ~240)
```python
# BEFORE:
external_doc_no_counter[original_external_doc_no] = 1

# AFTER:
external_doc_no_counter[original_external_doc_no] = 0
```

#### 2. process_japan_exports.py (Line ~1050)
```python
# BEFORE:
used_doc_numbers[original_doc_no] = 0

# AFTER:
used_doc_numbers[original_doc_no] = -1
```

## Testing Evidence
Based on the debug logs in `examples/0623/debug/`, the fix ensures:
- First occurrence: `20250522` (original)
- Second occurrence: `20250522-1` (not `20250522-2`)
- Third occurrence: `20250522-2`

## Files Modified
- `core/csv_to_json_converter.py`
- `core/process_japan_exports.py`

## Commit Information
- **Commit Hash**: b2a9374
- **Branch**: fix/external-document-no-starts-from-minus-1 → main
- **Date**: June 24, 2025

## Impact
- ✅ External_Document_No duplicates now correctly start from `-1`
- ✅ Maintains proper sequential numbering for duplicate entries
- ✅ No breaking changes to existing functionality
- ✅ Consistent behavior across both CSV conversion and API processing

## Related Issues
This fix addresses the user-reported issue where External_Document_No uniqueness was starting from `-2` instead of `-1`.
