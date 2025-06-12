# Fix Currency Handling for Company VCA

## Problem
When generating the BC payload for company VCA, the system was not applying the same logic as for other companies like VCT. Specifically:
- For company VCT, when the currency of the original line item is NTD (its home currency), the currency field is set to empty
- For company VCA, when the currency is USD (its home currency), the system was incorrectly setting it to "R-USD" instead of empty

## Solution
Modified the currency handling logic in `process_japan_exports.py` to ensure consistent behavior across all companies:

1. Updated `transform_currency_code` function to always return an empty string when the currency matches the home currency of any company
2. Updated `transform_currency` function to be consistent with `transform_currency_code`
3. Simplified `create_journal_line` function to use the updated `transform_currency_code` function consistently

## Changes Made
The changes ensure that for all companies, when the currency matches their home currency, it returns an empty string:
- VCT with NTD currency → returns empty string
- VCA with USD currency → returns empty string (previously returned "R-USD")
- VCJ with JPY currency → returns empty string
- VCG with EUR currency → returns empty string (previously returned "R-EUR")
- VCP with PHP currency → returns empty string

The special case handling for USD, RMB, and XEU/EUR now only applies when these currencies are NOT the home currency of the company.

## Testing
Tested with both VCT and VCA data to confirm the solution works correctly.
