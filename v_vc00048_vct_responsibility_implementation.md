# V-VC00048 VCT Responsibility Implementation

## Overview

This document describes the implementation of Issue #78, which extends the existing functionality of mapping vendor code V-VC00048 to VCT for non-VCT cost centers. The enhancement adds additional debit and credit lines in VCT to record the responsibility of the expense.

## Background

Previously, when a journal entry had vendor code V-VC00048 with a non-VCT cost center (e.g., VCA), the vendor code was mapped to VCT in the credit line. This implementation extends that functionality by adding a new pair of debit and credit lines in VCT to record the responsibility of the expense.

## Implementation Details

### New Function: `create_vct_responsibility_entries`

A new helper function `create_vct_responsibility_entries` was added to `process_japan_exports.py`. This function:

1. Creates additional debit and credit lines in VCT for V-VC00048 vendor when the cost center is not VCT
2. Uses fixed account numbers and department codes as specified in the requirements
3. Prefixes the description with the original cost center code
4. Maintains the original currency and amount

```python
def create_vct_responsibility_entries(entry: Dict[str, Any], access_token: str, rate_limiter: RateLimiter, max_retries: int = 3) -> Tuple[int, int]:
    """
    Create additional debit and credit lines in VCT to record the responsibility of expense for V-VC00048 vendor.
    
    Args:
        entry: The original journal entry
        access_token: OAuth2 access token
        rate_limiter: RateLimiter instance for managing API call timing
        max_retries: Maximum number of retry attempts for failed API calls
    
    Returns:
        Tuple[int, int]: Count of successful and failed entries
    """
    # Implementation details...
```

### Modifications to `process_entries`

The `process_entries` function was modified to check if a V-VC00048 mapping occurred and, if so, call the new `create_vct_responsibility_entries` function to create the additional entries. This check is performed after successfully posting the credit line for both individual entries and consolidated entries.

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

## Testing

A new test file `test_v_vc00048_vct_responsibility.py` was created to verify the implementation. The tests cover:

1. Basic functionality of the `create_vct_responsibility_entries` function
2. Handling of consolidated entries
3. Verification of the format and content of the generated journal lines

## Format of Additional Entries

### Debit Line in VCT

- Account Type: G/L Account
- Account Number: 18600-10 (fixed)
- Description: [Original Cost Center] [Original Description]
- External Document Number: Same as original document number
- Document Number: Same as original voucher number
- Department Code: VCT.9999 (fixed)
- Currency Code: Same as original currency
- Amount: Same as original amount (positive for debit)

### Credit Line in VCT

- Account Type: Vendor
- Account Number: V-VC00048 (fixed)
- Description: [Original Cost Center] [Original Description]
- External Document Number: Same as original document number
- Document Number: Same as original voucher number
- Department Code: VCT.9999 (fixed)
- Currency Code: Same as original currency
- Amount: Same as original amount (negative for credit)

## Example

For a journal entry with:
- Voucher No: APA-0000401
- Cost Center: VCA
- Description: Events
- Currency: R-USD
- Amount: 7284.55

The additional entries created in VCT would be:

1. Debit Line:
   - Account: 18600-10
   - Description: VCA Events
   - Department: VCT.9999
   - Currency: R-USD
   - Amount: 7284.55

2. Credit Line:
   - Account: V-VC00048
   - Description: VCA Events
   - Department: VCT.9999
   - Currency: R-USD
   - Amount: -7284.55

## Conclusion

This implementation successfully extends the existing V-VC00048 mapping functionality to add additional VCT responsibility entries. The code has been tested and verified to work correctly with both individual and consolidated entries.
