# V-VC00048 Vendor Mapping to VCT for Non-VCT Cost Centers

## Implementation Summary

This feature implements the requirement to map the vendor code V-VC00048 to VCT when used with non-VCT cost centers, as specified in [GitHub issue #78](https://github.com/yikuochan/Rakuimporter/issues/78).

### Changes Made

1. Modified the `create_journal_line` function in `process_japan_exports.py` to:
   - Check if the account number is V-VC00048
   - Extract the cost center from the department code (first 3 characters)
   - If the cost center is not VCT, change the vendor code to VCT

2. Added a new function `create_vct_responsibility_entries` that:
   - Creates additional debit and credit lines in VCT to record the responsibility of expense
   - Uses fixed account numbers (18600-10 for debit, V-VC00048 for credit)
   - Uses fixed department code (VCT.9999)
   - Preserves the original currency and amount
   - Adds the original cost center as a prefix to the description

3. Updated the `process_entries` function to:
   - Check for V-VC00048 vendor code regardless of whether credit line posting succeeds or fails
   - Call the `create_vct_responsibility_entries` function when needed

### Bug Fix

Fixed an issue where VCT responsibility entries were not being created when the credit line posting failed. The code now checks for V-VC00048 vendor code and creates VCT responsibility entries regardless of whether the credit line posting succeeds or fails.

### Testing

The implementation was tested with a sample file containing V-VC00048 vendor entries with non-VCT cost centers. The test confirmed that:

1. The vendor code is correctly mapped to VCT for non-VCT cost centers
2. Additional responsibility entries are created in VCT
3. The original transaction details are preserved
4. VCT responsibility entries are created even when credit line posting fails

### Usage

No changes to the command-line interface are required. The feature works automatically when processing files with V-VC00048 vendor entries.

Example:
```
python process_japan_exports.py input_file.json
