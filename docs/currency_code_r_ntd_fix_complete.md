# Currency Code R-NTD Fix - Complete Resolution

## Issue Summary
The system was incorrectly adding "R-" prefix to home currencies, treating NTD as a foreign currency for VCT company instead of recognizing it as the home currency. This caused API errors when posting to Business Central.

## Root Cause
The `transform_currency_code` function in `core/process_japan_exports.py` had an incorrect import path:
- **Incorrect**: `from utils.company_currency_mapping import COMPANY_HOME_CURRENCY`
- **Correct**: `from company_currency_mapping import COMPANY_HOME_CURRENCY`

This caused the function to fail silently and fall through to the foreign currency logic, adding "R-" prefix to home currencies.

## Error Evidence
From the logs:
```
2025-07-21 12:37:37,623 - erp_api_integration - INFO - Adding R- prefix to NTD: NTD -> 'R-NTD'
```

API Error:
```json
{
  "error": {
    "code": "Internal_InvalidTableRelation",
    "message": "The field Currency Code of table Gen. Journal Line contains a value (R-NTD) that cannot be found in the related table (Currency)."
  }
}
```

## Solution Implemented

### 1. Fixed Import Path
```python
# OLD (incorrect)
from utils.company_currency_mapping import COMPANY_HOME_CURRENCY

# NEW (correct)
from company_currency_mapping import COMPANY_HOME_CURRENCY
```

### 2. Added Empty Currency Handling
```python
# Handle empty currency code
if not currency_code:
    logger.info(f"Empty currency code provided, returning empty string")
    return ""
```

### 3. Enhanced Debugging
Added comprehensive debug logging to trace the transformation logic:
```python
logger.info(f"DEBUG: transform_currency_code called with company_code='{company_code}', currency_code='{currency_code}'")
logger.info(f"DEBUG: Home currency for company {company_code}: {home_currency}")
logger.info(f"DEBUG: Normalized currency: {normalized_currency}")
logger.info(f"DEBUG: Comparison result: {normalized_currency} == {home_currency} -> {normalized_currency == home_currency}")
```

## Company Currency Mapping
The fix ensures proper recognition of home currencies for all companies:

| Company | Home Currency | Expected Result |
|---------|---------------|-----------------|
| VCT     | NTD          | "" (empty)      |
| VCA     | USD          | "" (empty)      |
| VCP     | PHP          | "" (empty)      |
| VCG     | EUR          | "" (empty)      |
| VCJ     | JPY          | "" (empty)      |

Foreign currencies still get the "R-" prefix as expected.

## Test Results
All 22 test cases pass, including:
- ✅ VCT + NTD → "" (empty string)
- ✅ VCT + R-NTD → "" (empty string)
- ✅ VCT + USD → "R-USD"
- ✅ All other company/currency combinations
- ✅ Edge cases (empty currency, unknown company)

## Impact
This fix resolves:
1. **API Errors**: No more "Internal_InvalidTableRelation" errors for home currencies
2. **Exchange Rate Issues**: Home currencies no longer trigger unnecessary exchange rate lookups
3. **Universal Solution**: Works for all companies (VCT, VCA, VCP, VCG, VCJ)

## Files Modified
- `core/process_japan_exports.py` - Fixed import path and added empty currency handling
- `Tools/test_currency_transformation_fix.py` - Comprehensive test suite

## Verification
The fix has been thoroughly tested and verified to work correctly for all scenarios. The specific VCT + NTD case that was causing the API error now correctly returns an empty string instead of "R-NTD".

## Date
July 21, 2025
