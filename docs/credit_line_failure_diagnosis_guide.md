# Credit Line Posting Failure Diagnosis Guide

## Overview

This guide provides tools and methods to diagnose credit line posting failures in the ERP API integration, specifically focusing on the failure of voucher APA-0000401.

## Background

During the implementation of the V-VC00048 VCT responsibility entries feature, we observed that credit line posting for voucher APA-0000401 was failing. While our implementation ensures that VCT responsibility entries are created regardless of credit line posting success, it's important to understand why the credit line posting is failing in the first place.

## Enhanced Logging

We've enhanced the logging in `process_japan_exports.py` to provide more detailed information about API requests and responses:

1. **Detailed Request Logging**:
   - Full request payload is now logged before sending
   - Detailed information about journal line fields is logged
   - Headers (excluding authorization) are logged

2. **Detailed Error Response Logging**:
   - Complete error response is logged when a request fails
   - Error messages are extracted and logged separately
   - Error analysis is performed to categorize common issues

3. **Credit Line Failure Logging**:
   - Original entry data is logged when a credit line posting fails
   - Error analysis is performed on the response

## Diagnostic Tools

We've created two diagnostic tools to help investigate the credit line posting failure:

### 1. `test_apa_0000401_credit_failure.py`

This script extracts and processes only the APA-0000401 voucher from a JSON file with enhanced logging to diagnose the failure.

**Usage**:
```bash
python test_apa_0000401_credit_failure.py <input_json_file>
```

**Example**:
```bash
python test_apa_0000401_credit_failure.py 0604-Raku\ export-\ VCT\ credit\ card\ 1.utf8.json
```

**Features**:
- Extracts only the APA-0000401 voucher from the input file
- Logs the full entry data
- Logs detailed information about the debit and credit lines
- Logs the full request payload and response
- Performs error analysis on the response

### 2. `compare_vouchers.py`

This script compares a failing voucher (APA-0000401) with a successful voucher to identify differences that might be causing the failure.

**Usage**:
```bash
python compare_vouchers.py <input_json_file> --failing <failing_voucher> --success <successful_voucher>
```

**Example**:
```bash
python compare_vouchers.py 0604-Raku\ export-\ VCT\ credit\ card\ 1.utf8.json --failing APA-0000401 --success APA-0000402
```

**Features**:
- Extracts the failing and successful vouchers from the input file
- Compares metadata, debit line, and credit line fields
- Generates a markdown report of the differences
- Analyzes potential issues based on the differences
- Suggests next steps for investigation

## How to Use These Tools

1. **Run the Enhanced Process Script**:
   First, run the main process script with the enhanced logging to see if the error details are now captured:
   ```bash
   python process_japan_exports.py <input_json_file>
   ```

2. **Isolate the Failing Voucher**:
   Run the test script to isolate and process only the failing voucher:
   ```bash
   python test_apa_0000401_credit_failure.py <input_json_file>
   ```

3. **Compare with a Successful Voucher**:
   Identify a successful voucher from the same file and compare it with the failing one:
   ```bash
   python compare_vouchers.py <input_json_file> --failing APA-0000401 --success <successful_voucher>
   ```

4. **Analyze the Results**:
   - Check the log files for detailed error information
   - Review the comparison report for differences between the vouchers
   - Look for validation errors, missing fields, or invalid values

## Common Issues to Check

1. **Vendor Code Issues**:
   - Does the vendor code exist in the ERP system?
   - Are there any special validation rules for this vendor?

2. **Department Code Issues**:
   - Is the department code valid?
   - Are there any restrictions on which departments can be used with certain vendors?

3. **Currency Issues**:
   - Is the currency code valid?
   - Are there any restrictions on which currencies can be used with certain vendors or departments?

4. **Amount Issues**:
   - Is the amount within acceptable limits?
   - Are there any validation rules for minimum or maximum amounts?

5. **Description Issues**:
   - Is the description field properly formatted?
   - Are there any special characters that might be causing issues?

## Next Steps

After identifying the root cause of the credit line posting failure, consider the following options:

1. **Fix the Data**:
   - If the issue is with the input data, correct it and reprocess the voucher

2. **Update the Code**:
   - If the issue is with the code logic, update the code to handle the specific case

3. **Add Validation**:
   - Add validation checks to catch similar issues before attempting to post to the API

4. **Document the Issue**:
   - Document the issue and solution for future reference
