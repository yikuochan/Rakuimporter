# Currency Rounding Issue Analysis for OBA-0000027

## Issue Summary

The user reported that the balance credit side of voucher OBA-0000027 is incorrect. The current value is 83,868 NTD, but our program calculated it as 83,870 NTD. The voucher includes items with different currencies, suggesting the issue might be related to rounding during currency conversion.

## Analysis Results

After analyzing the raw data from `0527-Raku export- VCT PR 1-2.utf8.json`, we found:

1. **Consolidated Entry Amount**: 83,870.1345 NTD
2. **Sum of Individual Entries**: 40,896.21 NTD
3. **Difference**: 42,973.9245 NTD (105.08% discrepancy)

### Entry Breakdown:
- Total entries for voucher OBA-0000027: 25 (1 consolidated + 24 individual)
- Entries with NTD currency: 4 (total: 28,440.00 NTD)
- Entries with R-RMB currency: 20 (total: 12,456.21 RMB)

### Key Findings:

1. **Double Counting**: The consolidated amount (83,870.1345 NTD) is almost exactly equal to the total debit amount (83,870.134500000000606 NTD), with a negligible difference of -6.06E-13.

2. **Pattern Discovery**: The consolidated amount is approximately 2.05 times the sum of individual entries:
   - 40,896.21 × 2.05 = 83,837.2305 (very close to 83,870.1345)
   - The difference is only about 33 NTD

3. **Exchange Rate Analysis**: All R-RMB entries use a consistent exchange rate of 4.45 NTD/RMB.

## Root Cause

The issue appears to be a calculation error in the voucher processing system where:

1. The individual entries are correctly calculated (RMB amounts converted to NTD at 4.45 exchange rate)
2. The consolidated entry incorrectly includes both:
   - The sum of all individual entries (40,896.21 NTD)
   - PLUS the converted RMB amounts again (≈ 42,973.92 NTD)

This effectively counts the RMB entries twice: once as already-converted NTD values and again as RMB values that get converted to NTD.

## Solution

The correct consolidated amount should be 40,896.21 NTD, which is the sum of:
- NTD entries (28,440.00 NTD)
- Converted R-RMB entries (12,456.21 RMB × 4.45 = 55,430.13 NTD)

The fix involves modifying the voucher processing system to:
1. Properly track which entries have already been converted
2. Ensure currency conversion is applied exactly once
3. Apply consistent rounding rules (to 2 decimal places) after conversion

This will resolve the discrepancy between the reported value (83,868 NTD) and the calculated value (83,870 NTD).
