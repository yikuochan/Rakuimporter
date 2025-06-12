# Currency Prefix Fix for OBA-0000028

## Issue Description

When processing voucher OBA-0000028, the system encountered an error during currency conversion. The specific error was:

```
Failed to convert 177.99 from R-EUR to USD: unsupported format string passed to tuple.__format__
```

The issue occurred because:

1. The voucher OBA-0000028 had a currency code of "R-EUR" in the credit line
2. The company code was "VCA", which has a home currency of "USD"
3. When converting from "R-EUR" to "USD", the system:
   - Correctly normalized "R-EUR" to "EUR" for the exchange rate lookup
   - Successfully retrieved the exchange rate and converted the amount
   - But then tried to use the original "R-EUR" in a string formatting operation, causing the error

## Root Cause

In the `transform_currency` function, when handling currencies with an "R-" prefix, the function was:
1. Correctly removing the "R-" prefix to get the normalized currency code
2. Using this normalized code to look up the exchange rate
3. But when logging the conversion, it was using the original currency code with the "R-" prefix

This caused a formatting error when trying to log the conversion.

## Fix

The fix modifies the `transform_currency` function to consistently use the normalized currency code (without the "R-" prefix) throughout the entire conversion process:

```python
# Before:
logger.warning(f"Failed to convert {amount} from {currency_code} to {target_currency}: {str(e)}")

# After:
logger.warning(f"Failed to convert {amount} from {normalized_currency} to {target_currency}: {str(e)}")
```

Additionally, the function now correctly handles the return value from `convert_amount`, which was updated to return a tuple of (converted_amount, success).

## Testing

A new test file `test_currency_prefix_fix.py` was created to verify the fix:

1. `test_r_eur_to_usd_conversion`: Tests that "R-EUR" can be correctly converted to USD for company "VCA"
2. `test_normalized_currency_used_for_conversion`: Uses mocking to verify that the normalized currency "EUR" (without the "R-" prefix) is used for the conversion

Both tests pass, confirming that the fix works correctly.

## Impact

This fix ensures that vouchers with currency codes that have an "R-" prefix (like OBA-0000028) can be correctly processed and posted to the ERP API without errors.
