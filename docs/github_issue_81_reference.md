# GitHub Issue #81: V-VC00048 Intercompany Code Fix

This document references GitHub issue #81 which documents the fix for the intercompany code logic for V-VC00048 vendor credit lines with VCT cost center.

## Issue Link

[Issue #81: Fix intercompany code logic for V-VC00048 vendor credit lines with VCT cost center](https://github.com/yikuochan/Rakuimporter/issues/81)

## Summary

The issue was that the intercompany code (ShortcutDimCode3) was incorrectly being set to "VCT" for V-VC00048 vendor credit lines regardless of the cost center. This caused issues in the Business Central system when the cost center was VCT.

According to the business rules, the intercompany code should be:
1. Empty for any vendor with VCT cost center (including V-VC00048)
2. "VCT" for any vendor with non-VCT cost center (including V-VC00048)

## Fix

The fix was to remove the special case for V-VC00048 vendor code and maintain the original logic, which only sets the intercompany code to "VCT" when the cost center is not "VCT", regardless of the vendor code.

## Related Files

- `core/process_japan_exports.py`: Contains the main logic fix
- `docs/v_vc00048_intercompany_code_enhancement.md`: Detailed documentation of the issue and fix
- `tests/test_v_vc00048_intercompany.py`: Test cases to verify the fix

## Branch

The changes have been committed to the `v-vc00048-intercompany-enhancement` branch.
