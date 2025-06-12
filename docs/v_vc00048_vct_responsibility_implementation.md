# V-VC00048 VCT Responsibility Implementation

## Overview

This document describes the implementation of the requirement to use the full department code instead of just the cost center (first 3 characters) in the description field for VCT responsibility entries.

## Issue Description

In the current implementation, when creating VCT responsibility entries for V-VC00048 vendor transactions, only the first 3 characters of the department code (the cost center) are used as a prefix in the description field. According to the new requirement, the full department code should be used instead.

Reference: [GitHub Issue #78](https://github.com/yikuochan/Rakuimporter/issues/78)

## Changes Made

### 1. Modified `create_vct_responsibility_entries` function

The function was updated to use the full department code instead of extracting just the first 3 characters:

**Before:**
```python
# Get the original cost center from the credit entry's department
original_department = entry.get('credit', {}).get('department', '')
original_cost_center = original_department[:3] if original_department else ''

# Create the description with cost center prefix
vct_description = f"{original_cost_center} {original_description}"
```

**After:**
```python
# Get the original department from the credit entry
original_department = entry.get('credit', {}).get('department', '')

# Create the description with department prefix
vct_description = f"{original_department} {original_description}"
```

### 2. Updated logging message

The logging message was also updated to reflect the change:

**Before:**
```python
logger.info(f"Creating VCT responsibility entries for voucher {voucher_no} - Original cost center: {original_cost_center}")
```

**After:**
```python
logger.info(f"Creating VCT responsibility entries for voucher {voucher_no} - Original department: {original_department}")
```

## Testing

A new test file `test_v_vc00048_vct_responsibility.py` was created to verify that:

1. The full department code is used in the description field
2. Description truncation still works correctly if the description is too long
3. Error handling for post failures works as expected

## Impact

This change ensures that the full department code is included in the description field for VCT responsibility entries, providing more detailed information about the transaction's origin. This will help with tracking and reporting, as users will be able to see the exact department associated with each transaction.

## Deployment Notes

1. The changes have been implemented in a new branch: `v-vc00048-vct-responsibility-fix`
2. No database changes are required
3. No configuration changes are required
4. The changes are backward compatible with existing data
