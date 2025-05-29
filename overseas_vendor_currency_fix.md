# Overseas Vendor Currency Fix

## Issue Description

For VCT vendors with V-VC prefix (overseas vendors), the system was incorrectly converting the currency and amount to NTD (home currency) for credit entries. According to the requirement, for these overseas vendors, we should preserve the original currency code and amount without conversion, regardless of whether it's a regular or consolidated billing case.

Example: For voucher APA-0000404, when generating the JSON file and BC payload, the currency and amount of the consolidated item should be R-USD and 375.59, not NTD and the converted amount 12143.

## Implementation Details

### Changes Made

1. Modified the `create_journal_line` function in `process_japan_exports.py` to add special handling for overseas vendors (those with vendor codes starting with "V-VC").

2. For credit entries with vendor accounts that have the V-VC prefix, we now preserve the original currency and amount without conversion.

3. For all other vendors, we continue to use the existing currency transformation logic.

### Code Changes

```python
# Special handling for overseas vendors (V-VC prefix)
# As per requirement: For VCT vendors with V-VC prefix (overseas vendors),
# we must preserve the original currency and amount without conversion
if entry_type == "credit" and entry_data.get("gl_account") == "Vendor" and entry_data.get("vendor_code", "").startswith("V-VC"):
    # Keep original currency and amount for overseas vendors
    vendor_code = entry_data.get("vendor_code", "")
    logger.info(f"Overseas vendor detected ({vendor_code}): Keeping original currency {currency_to_use} and amount {original_amount}")
    transformed_currency = currency_to_use
    converted_amount = original_amount  # Keep the original sign (negative for credit)
else:
    # For non-overseas vendors, use the existing transformation logic
    transformed_currency, converted_amount = transform_currency(
        company_code, 
        currency_to_use, 
        abs(original_amount)
    )
    # Apply sign based on entry type
    converted_amount = -converted_amount if entry_type == "credit" else converted_amount
```

## Testing

A test script `test_overseas_vendor_currency.py` was created to verify the changes:

1. For overseas vendors (V-VC prefix), the test confirms that the original currency (R-USD) and amount (375.59) are preserved.
2. For regular vendors (non-V-VC prefix), the test confirms that the currency is transformed to empty string (home currency) and the amount is converted to NTD.

The test was run successfully, confirming that the implementation meets the requirements.

## Example

### Before Fix:
For vendor V-VC00048 (APA-0000404):
- Credit entry in JSON file: Currency = "NTD", Amount = 12142.8247
- BC payload: Currency_Code = "", Amount = -12142.8247

### After Fix:
For vendor V-VC00048 (APA-0000404):
- Credit entry in JSON file: Currency = "R-USD", Amount = 375.59
- BC payload: Currency_Code = "R-USD", Amount = -375.59

## Affected Files

- `process_japan_exports.py`: Modified to add special handling for overseas vendors.
- `csv_to_json_converter.py`: Updated to preserve original currency and amount for overseas vendors during consolidation.
- `test_overseas_vendor_currency.py`: Created to test the changes.

## Next Steps

1. Deploy the changes to the production environment.
2. Monitor the system to ensure that overseas vendor transactions are processed correctly.
3. Update documentation to reflect the new behavior for overseas vendors.
