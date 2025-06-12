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

## Code Changes

### 1. Updated `transform_currency_code` function:
```python
def transform_currency_code(company_code: str, currency_code: str) -> str:
    """
    Legacy function for backward compatibility.
    Transform currency code based on company code according to business rules.
    
    Args:
        company_code: The company code (e.g., VCT, VCP, etc.)
        currency_code: The original currency code from the JSON
        
    Returns:
        str: The transformed currency code (empty string if it matches the rule,
             or R-prefixed version for specific currencies)
    """
    # Define the mapping of company codes to their respective "home" currencies
    # Updated to align with currency_converter.py
    company_currency_map = {
        "VCT": "NTD",
        "VCP": "PHP",  # Removed "R-" prefix
        "VCA": "USD",  # Removed "R-" prefix
        "VCG": "EUR",  # Removed "R-" prefix
        "VCJ": "JPY"
    }
    
    # Handle "R-" prefix in currency codes
    normalized_currency = currency_code
    if currency_code and currency_code.startswith("R-"):
        normalized_currency = currency_code[2:]  # Remove "R-" prefix
        logger.info(f"Normalized currency code by removing R- prefix: {currency_code} -> {normalized_currency}")
    
    # Special case for XEU with VCG (treat XEU as EUR)
    if company_code == "VCG" and (normalized_currency == "XEU"):
        logger.info(f"Transforming currency code for company {company_code}: {currency_code} -> 'R-EUR'")
        return "R-EUR"
    
    # If the company code exists in our mapping and the currency matches the home currency
    if company_code in company_currency_map and normalized_currency == company_currency_map[company_code]:
        logger.info(f"Transforming currency code for company {company_code}: {currency_code} -> ''")
        # Always return empty string when currency matches home currency, regardless of which currency it is
        return ""
    
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
    
    return currency_code
```

### 2. Updated `transform_currency` function:
```python
def transform_currency(company_code: str, currency_code: str, amount: float) -> Tuple[str, float]:
    """
    Transform currency code based on company code and convert amount according to business rules.
    
    Args:
        company_code: The company code (e.g., VCT, VCP, etc.)
        currency_code: The original currency code from the JSON
        amount: The amount to convert
        
    Returns:
        Tuple[str, float]: The transformed currency code and converted amount
    """
    # Define the mapping of company codes to their respective "home" currencies
    # Updated to align with currency_converter.py
    company_currency_map = {
        "VCT": "NTD",
        "VCP": "PHP",  # Removed "R-" prefix
        "VCA": "USD",  # Removed "R-" prefix
        "VCG": "EUR",  # Removed "R-" prefix
        "VCJ": "JPY"
    }
    
    # Handle "R-" prefix in currency codes
    normalized_currency = currency_code
    if currency_code and currency_code.startswith("R-"):
        normalized_currency = currency_code[2:]  # Remove "R-" prefix
        logger.info(f"Normalized currency code by removing R- prefix: {currency_code} -> {normalized_currency}")
    
    # Special case for XEU with VCG (treat XEU as EUR)
    if company_code == "VCG" and (normalized_currency == "XEU"):
        logger.info(f"Transforming currency code for company {company_code}: {currency_code} -> 'R-EUR'")
        return "R-EUR", amount
    
    # If the company code exists in our mapping
    if company_code in company_currency_map:
        target_currency = company_currency_map[company_code]
        
        # If the currency already matches the target (home currency)
        if normalized_currency == target_currency:
            logger.info(f"Transforming currency code for company {company_code}: {currency_code} -> ''")
            # Always return empty string when currency matches home currency, regardless of which currency it is
            return "", amount
        
        # If we have a different currency, convert the amount to the target currency
        elif normalized_currency:
            try:
                # Convert amount to target currency, passing company_code
                converted_amount = convert_amount(amount, normalized_currency, target_currency, company_code=company_code)
                logger.info(f"Converted {amount} {currency_code} to {converted_amount:.2f} {target_currency} for company {company_code}")
                
                # After conversion, the currency is now the home currency, so return empty string
                return "", converted_amount
            except Exception as e:
                logger.warning(f"Failed to convert {amount} from {currency_code} to {target_currency}: {str(e)}")
                # Return original currency code and amount if conversion fails
                return currency_code, amount
    
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
    
    # If company code not in mapping or other issues, return original values
    return currency_code, amount
```

### 3. Updated `create_journal_line` function (relevant part):
```python
# Apply transform_currency_code to the original currency
# This will handle all special cases consistently with our updated logic
transformed_currency = transform_currency_code(company_code, currency_to_use)
logger.info(
    f"Applied transform_currency_code for debit line - Voucher: {entry.get('voucher_no', 'Unknown')}, "
    f"Company: {company_code}, Original Currency: {currency_to_use}, Transformed Currency: {transformed_currency}"
)
```

## How to Verify
You can verify these changes by running the script with the `--dry-run` option on both VCT and VCA data:

```bash
python process_japan_exports.py --dry-run Test-VPA-0000087.json  # For VCT data
python process_japan_exports.py --dry-run "Raku export-VCA.json"  # For VCA data
```

The logs will show that for both companies, when the currency matches their home currency, it's being transformed to an empty string.
