# VicOne ERP API Integration

This project provides a Python script for integrating with the VicOne ERP API. The script processes JSON files containing journal entries and posts them to the ERP API.

## Features

- **JSON Parsing**: Reads journal entries from a JSON file
- **Field Mapping**: Maps fields according to specified rules
- **API Integration**: Authenticates and posts journal lines to the ERP API
- **Error Handling**: Comprehensive error handling and logging

## Requirements

- Python 3.6+
- `requests` library

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yikuochan/Rakuimporter.git
   cd Rakuimporter
   ```

2. Install the required dependencies:
   ```bash
   pip install requests
   ```

## Usage

Run the script with the input JSON file:

```bash
python process_japan_exports.py <input_json_file>
```

Example:
```bash
python process_japan_exports.py jp-test-Evelyn\ Raku\ export_journal_data.json
```

## Input Format

The input JSON file should contain an array of journal entries, each with the following structure:

```json
{
  "voucher_no": "VPA-0000087",
  "transaction_date": "1114/03/26",
  "application_date": "2025/03/25",
  "journal_generation_date": "2025/04/22",
  "description": "VPA-0000087   Telephone, Mobile Phone Call March mobile fee",
  "note": "",
  "receipt_invoice": "",
  "debit": {
    "marker": "*",
    "gl_account": "G/L Account",
    "account": "72700-10",
    "sub_account": "",
    "amount": 599.0,
    "currency": "台湾ドル",
    "department": "VCT.1342G",
    "applicant_code": "10055",
    "vendor_code": "",
    "free_field": "March mobile fee",
    "department_code": "VCT.1342G"
  },
  "credit": {
    "marker": "",
    "gl_account": "Vendor",
    "account": "32200-10",
    "sub_account": "32200-10",
    "amount": 599.0,
    "currency": "台湾ドル",
    "department": "VCT.1342G",
    "applicant_code": "10055",
    "vendor_code": "",
    "free_field": "March mobile fee",
    "department_code": "VCT.1342G"
  }
}
```

## Field Mapping

For each entry in the input JSON, the script generates two journal lines (debit and credit) with the following mapping:

- `Journal_Template_Name`: `"PURCHASES"` (fixed)
- `Journal_Batch_Name`: `"PURCHASE"` (fixed)
- `Document_Type`: `"Invoice"` (fixed)
- `External_Document_No`: from top-level `voucher_no`
- `Account_Type`: from `debit.gl_account` or `credit.gl_account`
- `Account_No`: from `debit.account` or `credit.account`
- `Description`: from top-level `description`
- `Currency_Code`: from `debit.currency` or `credit.currency`
- `Amount`: 
  - Debit line: `debit.amount` (positive)
  - Credit line: `-credit.amount` (negative)
- `Shortcut_Dimension_1_Code`: first 3 characters of `debit.department` or `credit.department`
- `Shortcut_Dimension_2_Code`: from `debit.department` or `credit.department`
- `ShortcutDimCode4`: 
  - If `vendor_code` is provided and not empty, use `vendor_code`
  - Otherwise, use `applicant_code`
- All other shortcut dimension codes: empty string

## API Configuration

The script uses the following API configuration:

- **Token URL**: `https://login.microsoftonline.com/6b83c27c-aa6d-475a-9933-5c34bb008d73/oauth2/v2.0/token`
- **API URL**: `https://api.businesscentral.dynamics.com/v2.0/6b83c27c-aa6d-475a-9933-5c34bb008d73/Staging/ODataV4/Company('VCT')/PurchaseJournals`
- **Client ID**: `5d0ad744`
- **Scope**: `https://api.businesscentral.dynamics.com/.default`

## Logging

The script logs information to both the console and a file (`erp_api_integration.log`). The log includes:

- Entry processing status
- API request and response details
- Error information
- Summary of successful and failed operations

## Error Handling

The script includes robust error handling:

- Validates input file existence
- Handles JSON parsing errors
- Manages API authentication failures
- Captures and logs API response errors
- Provides detailed logging for troubleshooting

## License

This project is licensed under the MIT License - see the LICENSE file for details.