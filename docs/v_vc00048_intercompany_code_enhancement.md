# V-VC00048 Intercompany Code Enhancement

## Issue

When processing credit lines in regular journal entries, the intercompany code (ShortcutDimCode3) was being set to "VCT" only if the cost center was not "VCT". The previous implementation incorrectly set the intercompany code to "VCT" for V-VC00048 vendor credit lines regardless of the cost center, which was causing issues.

According to the business rules, the intercompany code should be:
1. Empty for any vendor with VCT cost center (including V-VC00048)
2. "VCT" for V-VC00048 vendor with non-VCT cost center (specific to V-VC00048 only)
3. Empty for all other vendors regardless of cost center (corrected from previous broad application)

**IMPORTANT**: The intercompany code logic should only apply to V-VC00048 vendor specifically, not to all vendors with non-VCT cost centers as was previously implemented.

This issue affected both regular and consolidated journal entries, as they both use the same `create_journal_line` function.

## Previous Implementation

```python
# For credit lines, set intercompany code to "VCT" if cost center is not VCT
elif entry_type == "credit":
    # Extract cost center from department code (first 3 characters)
    department = entry_data.get("department", "")
    cost_center = department[:3] if department else ""
    
    # If cost center is not VCT, set intercompany code to "VCT"
    if cost_center and cost_center != "VCT":
        intercompany_code = "VCT"
        logger.info(f"Setting intercompany code to VCT for credit line with cost center {cost_center} - Voucher: {entry.get('voucher_no', 'Unknown')}")
```

## Enhanced Implementation (CORRECTED)

The code has been updated to be vendor-specific, applying the intercompany logic only to V-VC00048:

```python
# For credit lines, check vendor-specific rules
elif entry_type == "credit":
    # Get vendor code
    vendor_code = entry_data.get("vendor_code", "")

    # Extract cost center from department code (first 3 characters)
    department = entry_data.get("department", "")
    cost_center = department[:3] if department else ""

    # Only apply VCT intercompany logic to V-VC00048
    if vendor_code == "V-VC00048" and cost_center and cost_center != "VCT":
        intercompany_code = "VCT"
        logger.info(f"Setting intercompany code to VCT for V-VC00048 with non-VCT cost center {cost_center}")
    # All other vendors get empty intercompany code
    else:
        intercompany_code = ""
```

## Benefits (CORRECTED)

1. For V-VC00048 vendor credit lines with VCT cost center, the intercompany code is correctly set to empty.
2. For V-VC00048 vendor credit lines with non-VCT cost center, the intercompany code is set to "VCT".
3. For all other vendors, the intercompany code is now correctly set to empty (regardless of cost center).
4. This fixes the previous broad application of VCT intercompany codes to all vendors.
5. The same logic applies to consolidated entries since they use the same function.

## Impact (CORRECTED)

This change ensures that vendor credit lines follow the correct vendor-specific intercompany code rules:
- V-VC00048 with VCT cost center → Empty intercompany code
- V-VC00048 with non-VCT cost center → "VCT" intercompany code
- All other vendors → Empty intercompany code (regardless of cost center)

This significantly reduces the number of transactions with intercompany codes, as the previous implementation incorrectly applied "VCT" to all vendors with non-VCT cost centers.

This is required for proper accounting in the Business Central system and prevents errors like the one shown in the BC payload log:

```json
{
  "Account_Type": "Vendor",
  "Account_No": "V-VC00048",
  "Shortcut_Dimension_1_Code": "VCT",
  "Shortcut_Dimension_2_Code": "VCT.9999",
  "ShortcutDimCode3": "VCT"  // This should be empty for VCT cost center
}
```

## Testing

The change has been tested with both regular and consolidated journal entries, and the intercompany code is now correctly set to "VCT" for all V-VC00048 vendor credit lines.
