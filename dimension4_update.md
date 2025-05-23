# DIMENSION4 Logic Update

## Overview

This document describes the update to the DIMENSION4 (ShortcutDimCode4) logic in the `process_japan_exports.py` script. The change ensures that ShortcutDimCode4 always references the value from column N "申請者CD/支払先CD" (applicant code/payment destination code) for both credit and debit lines.

## Previous Logic

Previously, the ShortcutDimCode4 value was determined using the following logic:

```python
# Determine ShortcutDimCode4 (empty if vendor_code present, otherwise use applicant_code)
shortcut_dim_code4 = "" if entry_data.get("vendor_code") else entry_data.get("applicant_code", "")
```

This meant:
- If a vendor_code was present, ShortcutDimCode4 was set to an empty string ("")
- If no vendor_code was present, ShortcutDimCode4 was set to the value of applicant_code

## Intermediate Logic

The logic was updated to always use the vendor_code (支払先CD) for ShortcutDimCode4:

```python
# Always use vendor_code (支払先CD) for ShortcutDimCode4
shortcut_dim_code4 = entry_data.get("vendor_code", "")
```

This meant:
- ShortcutDimCode4 is always set to the value of vendor_code
- If vendor_code is empty or not present, ShortcutDimCode4 will be an empty string ("")

## Current Logic

The latest update now uses applicant_code (申請者CD/支払先CD) for ShortcutDimCode4:

```python
# Always use applicant_code (申請者CD/支払先CD) for ShortcutDimCode4
shortcut_dim_code4 = entry_data.get("applicant_code", "")
```

This means:
- ShortcutDimCode4 is always set to the value of applicant_code
- If applicant_code is empty or not present, ShortcutDimCode4 will be an empty string ("")

## Data Flow

1. In the CSV file, column N "申請者CD/支払先CD" contains the applicant code/payment destination code
2. During CSV to JSON conversion (`csv_to_json_converter.py`), this column is mapped to the `applicant_code` field in both debit and credit sections
3. When creating journal lines in `process_japan_exports.py`, the `applicant_code` value is now always used for ShortcutDimCode4

## Testing

A new test case has been added to `test_currency_handling.py` to verify the updated logic:

```python
def test_shortcut_dim_code4_logic(self):
    """Test that ShortcutDimCode4 always uses applicant_code for both debit and credit lines"""
    # Test cases verify that:
    # 1. When applicant_code is present, it's used for ShortcutDimCode4
    # 2. When applicant_code is empty, ShortcutDimCode4 is also empty
```

## Verification

The changes have been verified by:
1. Running unit tests: `python -m unittest test_currency_handling.py`
2. All tests pass, confirming that the new logic is working correctly

## Implementation Dates

- Initial update (vendor_code): May 22, 2025
- Latest update (applicant_code): May 23, 2025
