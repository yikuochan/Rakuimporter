# Enhancement: Add R- Prefix to NTD, JPY, and PHP as Non-Home Currencies

## Problem
Previously, only specific currencies (USD, RMB, EUR/XEU) were getting the "R-" prefix when used as non-home currencies. However, there was a requirement to extend this behavior to include NTD, JPY, and PHP as well.

## Requirement
When NTD, JPY, and PHP are used as non-home currencies, they should be prefixed with "R-" in the BC API payload:
- NTD becomes "R-NTD" (when not used with VCT)
- JPY becomes "R-JPY" (when not used with VCJ)
- PHP becomes "R-PHP" (when not used with VCP)

## Solution
Modified the currency handling logic in `process_japan_exports.py` to add "R-" prefix to these currencies when they are not the home currency of the company:

1. Updated `transform_currency_code` function to add "R-" prefix to NTD, JPY, and PHP when they are used as non-home currencies
2. Updated `transform_currency` function to maintain consistency with the same logic
3. Added unit tests to verify the new behavior

## Changes Made

### 1. Updated `transform_currency_code` function:
```python
# For non-home currencies, apply special rules
if normalized_currency == "USD":
    logger.info(f"Adding R- prefix to USD: {currency_code} -> 'R-USD'")
    return "R-USD"
elif normalized_currency == "RMB":
    logger.info(f"Adding R- prefix to RMB: {currency_code} -> 'R-RMB'")
    return "R-RMB"
elif normalized_currency == "XEU" or normalized_currency == "EUR":
    logger.info(f"Adding R- prefix to {normalized_currency}: {currency_code} -> 'R-EUR'")
    return "R-EUR"
elif normalized_currency == "NTD":
    logger.info(f"Adding R- prefix to NTD: {currency_code} -> 'R-NTD'")
    return "R-NTD"
elif normalized_currency == "JPY":
    logger.info(f"Adding R- prefix to JPY: {currency_code} -> 'R-JPY'")
    return "R-JPY"
elif normalized_currency == "PHP":
    logger.info(f"Adding R- prefix to PHP: {currency_code} -> 'R-PHP'")
    return "R-PHP"
```

### 2. Updated `transform_currency` function:
```python
# For non-home currencies, apply special rules
if normalized_currency == "USD":
    logger.info(f"Adding R- prefix to USD: {currency_code} -> 'R-USD'")
    return "R-USD", amount
elif normalized_currency == "RMB":
    logger.info(f"Adding R- prefix to RMB: {currency_code} -> 'R-RMB'")
    return "R-RMB", amount
elif normalized_currency == "XEU" or normalized_currency == "EUR":
    logger.info(f"Adding R- prefix to {normalized_currency}: {currency_code} -> 'R-EUR'")
    return "R-EUR", amount
elif normalized_currency == "NTD":
    logger.info(f"Adding R- prefix to NTD: {currency_code} -> 'R-NTD'")
    return "R-NTD", amount
elif normalized_currency == "JPY":
    logger.info(f"Adding R- prefix to JPY: {currency_code} -> 'R-JPY'")
    return "R-JPY", amount
elif normalized_currency == "PHP":
    logger.info(f"Adding R- prefix to PHP: {currency_code} -> 'R-PHP'")
    return "R-PHP", amount
```

### 3. Added unit tests:
```python
# Test new requirements for NTD, JPY, and PHP as non-home currencies
self.assertEqual(transform_currency_code("VCA", "NTD"), "R-NTD")  # NTD is not home currency for VCA
self.assertEqual(transform_currency_code("VCT", "JPY"), "R-JPY")  # JPY is not home currency for VCT
self.assertEqual(transform_currency_code("VCJ", "PHP"), "R-PHP")  # PHP is not home currency for VCJ
```

## Verification
The changes have been verified by:
1. Running unit tests: `python -m unittest test_currency_handling.py`
2. Running the script with sample data: `python process_japan_exports.py --dry-run --sample-payload=sample_vca_output.json "Raku export-VCA.json"`
3. Checking the currency modification report to confirm that NTD, JPY, and PHP are now being transformed with the "R-" prefix when used as non-home currencies.
