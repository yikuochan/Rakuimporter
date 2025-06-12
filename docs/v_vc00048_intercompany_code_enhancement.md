# V-VC00048 Intercompany Code Enhancement

## Issue

When processing credit lines in regular journal entries, the intercompany code (ShortcutDimCode3) was being set to "VCT" only if the cost center was not "VCT". However, for vendor code V-VC00048, we need to always set the intercompany code to "VCT" regardless of the cost center.

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

The code has been updated to specifically check for vendor code V-VC00048 and set the intercompany code to "VCT" regardless of the cost center:

```python
# For credit lines, check if vendor code is V-VC00048 or if cost center is not VCT
elif entry_type == "credit":
    # Get vendor code
    vendor_code = entry_data.get("vendor_code", "")
    
    # Extract cost center from department code (first 3 characters)
    department = entry_data.get("department", "")
    cost_center = department[:3] if department else ""
    
    # If vendor code is V-VC00048 or cost center is not VCT, set intercompany code to "VCT"
    if vendor_code == "V-VC00048" or (cost_center and cost_center != "VCT"):
        intercompany_code = "VCT"
        logger.info(f"Setting intercompany code to VCT for credit line - Vendor: {vendor_code}, Cost center: {cost_center} - Voucher: {entry.get('voucher_no', 'Unknown')}")
```

## Benefits

1. For V-VC00048 vendor credit lines, the intercompany code is now always set to "VCT", regardless of the cost center.
2. For other vendors, the existing logic is maintained (set to "VCT" only if cost center is not "VCT").
3. The same logic applies to consolidated entries since they use the same function.

## Impact

This change ensures that all V-VC00048 vendor credit lines have the correct intercompany code "VCT", which is required for proper accounting in the Business Central system.

## Testing

The change has been tested with both regular and consolidated journal entries, and the intercompany code is now correctly set to "VCT" for all V-VC00048 vendor credit lines.
