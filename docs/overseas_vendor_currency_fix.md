# Overseas Vendor Currency Fix

## Issue Description

When processing overseas vendors (vendor codes starting with V-VC) in the VCT company, there was an issue with currency code handling:

1. For overseas vendors, we correctly preserved the original currency and amount without conversion.
2. However, when the original currency was NTD (Taiwan Dollar) for items saving to VCT company, we needed to set the currency code to empty string ("") instead of "NTD".

This was causing API errors (400 Bad Request) when trying to post journal lines with:
- Currency_Code: "NTD"
- Account_Type: "Vendor"
- Account_No: "V-VC00048"
- Shortcut_Dimension_1_Code: "VCT"

## Root Cause

In Business Central, the home currency for a company should be represented as an empty string in API requests. For VCT company, the home currency is NTD.

The issue was in the `create_journal_line` function in `process_japan_exports.py`. While we had special handling for overseas vendors to preserve their original currency and amount, we weren't applying the special rule for NTD currency in VCT company.

## Fix Implementation

1. Modified the `create_journal_line` function in `process_japan_exports.py` to add a special case for overseas vendors with NTD currency in VCT company:

```python
# Special handling for overseas vendors (V-VC prefix)
if entry_type == "credit" and entry_data.get("gl_account") == "Vendor" and entry_data.get("vendor_code", "").startswith("V-VC"):
    # Keep original currency and amount for overseas vendors
    vendor_code = entry_data.get("vendor_code", "")
    logger.info(f"Overseas vendor detected ({vendor_code}): Keeping original currency {currency_to_use} and amount {original_amount}")
    
    # Special case: For VCT company and NTD currency, set currency code to empty string
    if company_code == "VCT" and currency_to_use == "NTD":
        logger.info(f"Overseas vendor with NTD currency in VCT company: Setting currency code to empty string")
        transformed_currency = ""
    else:
        # Apply transform_currency_code to non-NTD currencies for overseas vendors
        transformed_currency = transform_currency_code(company_code, currency_to_use)
        logger.info(f"Applied transform_currency_code for overseas vendor: {transformed_currency}")
        
    converted_amount = original_amount  # Keep the original sign (negative for credit)
```

2. Created a test script (`test_overseas_vendor_currency.py`) to verify the fix with three test cases:
   - Overseas vendor with NTD currency in VCT company (should have empty currency code)
   - Overseas vendor with USD currency in VCT company (should have R-USD currency code)
   - Overseas vendor with NTD currency in VCA company (should have R-NTD currency code)

## Testing

The fix was tested with the following scenarios:

1. **Test Case 1**: Overseas vendor with NTD currency in VCT company
   - Expected: Currency_Code = ""
   - Result: ✅ Currency_Code is empty

2. **Test Case 2**: Overseas vendor with USD currency in VCT company
   - Expected: Currency_Code = "R-USD"
   - Result: ✅ Currency_Code is "R-USD"

3. **Test Case 3**: Overseas vendor with NTD currency in VCA company
   - Expected: Currency_Code = "R-NTD"
   - Result: ✅ Currency_Code is "R-NTD"

## Summary

This fix ensures that:
1. For overseas vendors (V-VC prefix), we preserve the original currency and amount without conversion.
2. For overseas vendors in VCT company with NTD currency, we set the currency code to empty string.
3. For overseas vendors with non-home currencies, we apply the standard currency code transformation rules.

This change maintains the existing behavior for all other cases while fixing the specific issue with NTD currency for overseas vendors in VCT company.
