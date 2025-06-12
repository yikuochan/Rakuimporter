# VCT Responsibility Intercompany Code Fix

## Issue

When processing VCT responsibility entries for vendor V-VC00048 with non-VCT cost centers, the system was setting `ShortcutDimCode3` (intercompany code) to "VCT" for the credit line. This was causing an error in the Business Central API:

```
VCT is not an available Code for that dimension. CorrelationId: cc41028d-35a0-4b72-a2e9-1810057704cc.
```

The error occurred because "VCT" is not a valid code for the intercompany dimension in the credit line context.

## Root Cause

In the `create_vct_responsibility_entries` function in `core/process_japan_exports.py`, the credit line was being created with:

```python
credit_line = {
    # ... other fields ...
    "ShortcutDimCode3": "VCT",  # Set intercompany code to VCT for credit line
    # ... other fields ...
}
```

This was causing the API to reject the request because "VCT" is not a valid intercompany code for credit lines.

## Fix

The fix was to leave the `ShortcutDimCode3` field empty for the credit line in VCT responsibility entries, while keeping it set to the original cost center for the debit line:

```python
# For debit line
debit_line = {
    # ... other fields ...
    "ShortcutDimCode3": original_cost_center,  # Set intercompany code to original cost center
    # ... other fields ...
}

# For credit line
credit_line = {
    # ... other fields ...
    "ShortcutDimCode3": "",  # Leave intercompany code empty for credit line
    # ... other fields ...
}
```

This change ensures that:
1. The debit line correctly records the original cost center as the intercompany code
2. The credit line has an empty intercompany code, which is accepted by the Business Central API

## Implementation

The fix was implemented in the `create_vct_responsibility_entries` function in `core/process_japan_exports.py`. The log message was also updated to reflect the change:

```python
logger.info(f"Setting intercompany code to empty for VCT responsibility credit line - Voucher: {voucher_no}")
```

This fix applies to both regular and consolidated VCT responsibility entries, as they both use the same function to create the journal lines.

## Testing

The fix was tested by running the importer with real data, and the error no longer occurs. The VCT responsibility credit lines are now successfully posted to the Business Central API.
