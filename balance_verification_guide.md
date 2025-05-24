# Balance Verification Guide

## Overview

This guide explains the balance verification feature added to the VicOne ERP API Integration Script. This feature verifies that debit and credit amounts balance after currency conversion before creating line items in Business Central (BC).

## Problem Statement

Users have reported that some entries in Business Central show unbalanced amounts, where the debit and credit amounts don't match. This can happen due to:

1. **Currency conversion issues** - When converting between currencies, rounding or exchange rate differences might cause small imbalances
2. **Inconsistent currency handling** - Different handling of currency codes between debit and credit lines
3. **Timing issues with exchange rates** - Exchange rates might be fetched at different times
4. **Consolidated entries** - When multiple debit entries are consolidated into a single credit entry, the total might not match exactly

## Solution

The balance verification feature checks that debit and credit amounts balance after all currency conversions are applied, before posting to Business Central. This ensures that only balanced entries are created in BC, preventing accounting issues.

## How It Works

1. For each entry or group of entries, the system:
   - Applies currency transformations to both debit and credit amounts
   - Calculates the total debit and credit amounts
   - Compares the totals and checks if they are within the specified tolerance

2. If the entry is balanced (difference ≤ tolerance):
   - The entry is processed normally
   - A log message is generated indicating the entry is balanced

3. If the entry is unbalanced (difference > tolerance):
   - A warning is logged with details about the imbalance
   - Depending on configuration, the entry is either:
     - Skipped (not posted to BC)
     - Posted anyway with a warning
   - The entry is added to an unbalanced entries report

## Usage

### Command Line Arguments

The following command line arguments have been added to control the balance verification feature:

```
--balance-tolerance FLOAT   Acceptable difference between debit and credit amounts (default: 0.01)
--skip-unbalanced          Skip unbalanced entries instead of posting them
--unbalanced-report FILE   Generate unbalanced entries report to specified file path
                          (default: unbalanced_entries_report.md)
```

### Example Usage

```bash
# Process entries with default tolerance (0.01) and generate report
python process_japan_exports.py input_file.json

# Process entries with higher tolerance (0.1)
python process_japan_exports.py input_file.json --balance-tolerance 0.1

# Skip unbalanced entries
python process_japan_exports.py input_file.json --skip-unbalanced

# Specify custom report file
python process_japan_exports.py input_file.json --unbalanced-report custom_report.md
```

## Unbalanced Entries Report

The system generates a report of all unbalanced entries in Markdown format. The report includes:

- Voucher number
- Vendor code
- Debit total
- Credit total
- Difference

Example report:

```markdown
# Unbalanced Entries Report

| Voucher No | Vendor Code | Debit Total | Credit Total | Difference |
|------------|-------------|-------------|--------------|------------|
| OBA-0000028 | 10055 | 202.37 | 200.37 | 2.00 |
| VPA-0000087 | 20033 | 150.00 | 152.50 | 2.50 |

Total unbalanced entries: 2

Note: This report includes entries where the difference between debit and credit amounts exceeds the tolerance of 0.01.
```

## Testing

A test file `test_balance_verification.py` has been created to verify the balance checking functionality. It includes tests for:

- Balanced single entries
- Unbalanced single entries
- Entries with currency conversion
- Multiple entries that balance in aggregate
- Multiple entries that are unbalanced in aggregate
- Different tolerance levels

To run the tests:

```bash
python test_balance_verification.py
```

## Best Practices

1. **Start with a small tolerance** - Begin with the default tolerance of 0.01 to catch most imbalances
2. **Review the unbalanced entries report** - Regularly check the report to identify patterns or systematic issues
3. **Adjust tolerance as needed** - If many entries are failing due to small rounding differences, consider increasing the tolerance
4. **Use skip-unbalanced in production** - In production environments, use the `--skip-unbalanced` flag to prevent unbalanced entries from being posted

## Troubleshooting

If you encounter issues with the balance verification feature:

1. **Check the logs** - Look for warning and error messages related to balance verification
2. **Review the unbalanced entries report** - Examine the specific entries that are unbalanced
3. **Test with higher tolerance** - Try increasing the tolerance to see if the issue is related to rounding
4. **Check exchange rates** - Verify that exchange rates are being correctly applied
5. **Examine currency conversion** - Look for issues in the currency conversion process

## Technical Details

The balance verification is implemented in the `verify_balanced_amounts` function in `process_japan_exports.py`. This function:

- Takes an entry or list of entries and a tolerance parameter
- Applies currency transformations to get the final amounts
- Calculates the total debit and credit amounts
- Returns a tuple of (is_balanced, difference, debit_total, credit_total)

The `process_entries` function has been modified to:

- Call `verify_balanced_amounts` before posting entries
- Log information about balanced and unbalanced entries
- Skip unbalanced entries if configured to do so
- Generate a report of unbalanced entries