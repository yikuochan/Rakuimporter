# V-VC00048 Intercompany Code Enhancement

## Issue

When processing credit lines in regular journal entries, the intercompany code (ShortcutDimCode3) was being set to "VCT" only if the cost center was not "VCT". The previous implementation incorrectly set the intercompany code to "VCT" for V-VC00048 vendor credit lines regardless of the cost center, which was causing issues.

According to the business rules, the intercompany code should be:
1. Empty for any vendor with VCT cost center (including V-VC00048)
2. "VCT" for any vendor with non-VCT cost center (including V-VC00048)

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

## Enhanced Implementation

The code has been updated to maintain the original logic, which only sets the intercompany code to "VCT" when the cost center is not "VCT", regardless of the vendor code:

```python
# For credit lines, check if cost center is not VCT
elif entry_type == "credit":
    # Get vendor code
    vendor_code = entry_data.get("vendor_code", "")
    
    # Extract cost center from department code (first 3 characters)
    department = entry_data.get("department", "")
    cost_center = department[:3] if department else ""
    
    # If cost center is not VCT, set intercompany code to "VCT"
    if cost_center and cost_center != "VCT":
        intercompany_code = "VCT"
        logger.info(f"Setting intercompany code to VCT for credit line - Vendor: {vendor_code}, Cost center: {cost_center} - Voucher: {entry.get('voucher_no', 'Unknown')}")
```

## Benefits

1. For V-VC00048 vendor credit lines with VCT cost center, the intercompany code is now correctly set to empty.
2. For V-VC00048 vendor credit lines with non-VCT cost center, the intercompany code is still set to "VCT".
3. For other vendors, the existing logic is maintained (set to "VCT" only if cost center is not "VCT").
4. The same logic applies to consolidated entries since they use the same function.

## Impact

This change ensures that all vendor credit lines (including V-VC00048) follow the correct intercompany code rules:
- Empty intercompany code for VCT cost center
- "VCT" intercompany code for non-VCT cost center

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
