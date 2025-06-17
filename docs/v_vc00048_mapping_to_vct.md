# V-VC00048 Mapping to VCT for Non-VCT Cost Centers

## Overview

This document describes the implementation of the requirement to map vendor code V-VC00048 to VCT for non-VCT cost centers. This feature ensures that when overseas employees use the company credit card (vendor V-VC00048), the payment is made to VCT, regardless of the individual account.

## Implementation Details

### Vendor Code Mapping

When processing journal entries, if a credit line has the vendor code V-VC00048 and the cost center is not VCT, the vendor code is changed to VCT. This mapping is implemented in the `create_journal_line` function in `core/process_japan_exports.py`:

```python
# Determine Account_No based on the account type
if entry_data.get("gl_account", "") == "Vendor":
    account_no = entry_data.get("vendor_code", "")
    
    # Handle V-VC00048 mapping for non-VCT cost centers
    if account_no == "V-VC00048":
        # Extract cost center from department code (first 3 characters)
        department = entry_data.get("department", "")
        cost_center = department[:3] if department else ""
        
        # If cost center is not VCT, change vendor code to VCT
        if cost_center and cost_center != "VCT":
            logger.info(f"Mapping vendor V-VC00048 to VCT for non-VCT cost center {cost_center} - Voucher: {entry.get('voucher_no', 'Unknown')}")
            account_no = "VCT"
else:
    account_no = entry_data.get("account", "")
```

### VCT Responsibility Entries

In addition to mapping the vendor code, the system also creates additional debit and credit lines in VCT to record the responsibility of expense for V-VC00048 vendor. This is implemented in the `create_vct_responsibility_entries` function in `core/process_japan_exports.py`.

When processing entries in the `process_entries` function, if the vendor code is V-VC00048 and the cost center is not VCT, the `create_vct_responsibility_entries` function is called:

```python
# Check if this was a V-VC00048 mapping to VCT for non-VCT cost center
original_vendor_code = entry.get('credit', {}).get('vendor_code', '')
department = entry.get('credit', {}).get('department', '')
cost_center = department[:3] if department else ''

if original_vendor_code == "V-VC00048" and cost_center and cost_center != "VCT":
    logger.info(f"Creating VCT responsibility entries for mapped vendor V-VC00048 - Voucher: {entry_voucher_no}")
    vct_success, vct_failure = create_vct_responsibility_entries(entry, access_token, rate_limiter, max_retries)
    success_count += vct_success
    failure_count += vct_failure
```

The `create_vct_responsibility_entries` function creates two additional journal lines:

1. **Debit Line**:
   - Account Type: G/L Account
   - Account No: 18600-10
   - Shortcut_Dimension_1_Code: VCT
   - Shortcut_Dimension_2_Code: VCT.9999
   - ShortcutDimCode3: Original cost center (e.g., VCP, VCA)

2. **Credit Line**:
   - Account Type: Vendor
   - Account No: V-VC00048
   - Shortcut_Dimension_1_Code: VCT
   - Shortcut_Dimension_2_Code: VCT.9999
   - ShortcutDimCode3: Empty

## Testing

The implementation is tested in `tests/test_v_vc00048_mapping.py`. The tests verify:

1. V-VC00048 is mapped to VCT for non-VCT cost centers
2. V-VC00048 is not mapped for VCT cost centers
3. Other vendors are not mapped
4. VCT responsibility entries are created correctly

## Example

### Before Mapping

Original entry with V-VC00048 vendor code and non-VCT cost center:

```
Entry:
- voucher_no: TEST-001
- debit:
  - amount: 1000.0
  - department: VCP.1234
  - gl_account: G/L Account
  - account: 12345-67
- credit:
  - amount: 1000.0
  - department: VCP.1234
  - gl_account: Vendor
  - vendor_code: V-VC00048
```

### After Mapping

1. **Original Entry (with mapped vendor code)**:

```
Entry:
- voucher_no: TEST-001
- debit:
  - amount: 1000.0
  - department: VCP.1234
  - gl_account: G/L Account
  - account: 12345-67
- credit:
  - amount: 1000.0
  - department: VCP.1234
  - gl_account: Vendor
  - vendor_code: VCT  # Changed from V-VC00048 to VCT
```

2. **Additional VCT Responsibility Entries**:

   a. **Debit Line**:

```
Journal Line:
- Journal_Template_Name: PURCHASES
- Journal_Batch_Name: PURCHASE
- Document_Type: Invoice
- Document_No: TEST-001
- Account_Type: G/L Account
- Account_No: 18600-10
- Shortcut_Dimension_1_Code: VCT
- Shortcut_Dimension_2_Code: VCT.9999
- ShortcutDimCode3: VCP
- Amount: 1000.0
```

   b. **Credit Line**:

```
Journal Line:
- Journal_Template_Name: PURCHASES
- Journal_Batch_Name: PURCHASE
- Document_Type: Invoice
- Document_No: TEST-001
- Account_Type: Vendor
- Account_No: V-VC00048
- Shortcut_Dimension_1_Code: VCT
- Shortcut_Dimension_2_Code: VCT.9999
- ShortcutDimCode3: ""
- Amount: -1000.0
