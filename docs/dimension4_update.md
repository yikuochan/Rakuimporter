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

## Previous Logic (May 23, 2025)

The previous update used applicant_code (申請者CD/支払先CD) for ShortcutDimCode4:

```python
# Always use applicant_code (申請者CD/支払先CD) for ShortcutDimCode4
shortcut_dim_code4 = entry_data.get("applicant_code", "")
```

This meant:
- ShortcutDimCode4 was always set to the value of applicant_code
- If applicant_code was empty or not present, ShortcutDimCode4 would be an empty string ("")

## Current Logic (May 23, 2025 - Updated)

The latest update differentiates between vendor payments and employee payments:

```python
# Determine ShortcutDimCode4 based on account type and source of account_no
if entry_data.get("gl_account", "") == "Vendor":
    # For Vendor accounts, check the source of account_no
    if entry_data.get("vendor_code") and entry_data.get("account") == entry_data.get("vendor_code"):
        # If account_no comes from column O (支払先CD), set ShortcutDimCode4 to empty
        shortcut_dim_code4 = ""
    else:
        # If account_no comes from column N (申請者CD/支払先CD), use applicant_code
        shortcut_dim_code4 = entry_data.get("applicant_code", "")
else:
    # For non-Vendor accounts, keep using applicant_code
    shortcut_dim_code4 = entry_data.get("applicant_code", "")
```

This means:
- For vendor accounts where account_no comes from column O (支払先CD), ShortcutDimCode4 is set to an empty string ("")
- For vendor accounts where account_no comes from column N (申請者CD/支払先CD), ShortcutDimCode4 uses the applicant_code value
- For non-vendor accounts, ShortcutDimCode4 continues to use the applicant_code value

## Data Flow

1. In the CSV file, column N "申請者CD/支払先CD" contains the applicant code/payment destination code
2. During CSV to JSON conversion (`csv_to_json_converter.py`), this column is mapped to the `applicant_code` field in both debit and credit sections
3. When creating journal lines in `process_japan_exports.py`, the `applicant_code` value is now always used for ShortcutDimCode4

## Testing

A dedicated test file `test_shortcut_dim_code4.py` has been created to verify the updated logic:

```python
def test_shortcut_dim_code4_pay_to_vendor(self):
    """Test ShortcutDimCode4 is empty when account_no comes from vendor_code (column O)"""
    # Test debit line
    debit_line = create_journal_line(self.vendor_entry_pay_to_vendor, "debit")
    self.assertEqual(debit_line["ShortcutDimCode4"], "", 
                     "ShortcutDimCode4 should be empty for vendor payment (from column O)")

def test_shortcut_dim_code4_pay_to_employee(self):
    """Test ShortcutDimCode4 uses applicant_code when account_no comes from applicant_code (column N)"""
    # Test debit line
    debit_line = create_journal_line(self.vendor_entry_pay_to_employee, "debit")
    self.assertEqual(debit_line["ShortcutDimCode4"], "EMPLOYEE456", 
                     "ShortcutDimCode4 should use applicant_code for employee payment (from column N)")

def test_shortcut_dim_code4_non_vendor(self):
    """Test ShortcutDimCode4 uses applicant_code for non-vendor account types"""
    # Test debit line
    debit_line = create_journal_line(self.non_vendor_entry, "debit")
    self.assertEqual(debit_line["ShortcutDimCode4"], "EMPLOYEE456", 
                     "ShortcutDimCode4 should use applicant_code for non-vendor account types")
```

## Verification

The changes have been verified by:
1. Running the dedicated test file: `python test_shortcut_dim_code4.py`
2. All tests pass, confirming that the new logic is working correctly for all scenarios:
   - Vendor payments (account_no from column O): ShortcutDimCode4 is empty
   - Employee payments (account_no from column N): ShortcutDimCode4 uses applicant_code
   - Non-vendor accounts: ShortcutDimCode4 uses applicant_code

## Implementation Dates

- Initial update (vendor_code): May 22, 2025
- Latest update (applicant_code): May 23, 2025
