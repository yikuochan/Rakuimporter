# Power Importer - ERP Integration System

This repository contains a system for processing CSV files from Japanese sources, converting them to structured JSON, and integrating with Microsoft Dynamics Business Central ERP.

## System Overview

The Power Importer system processes financial data through the following pipeline:

1. **Character Set Conversion**: Converts CSV files from various encodings (e.g., Shift-JIS) to UTF-8
2. **CSV to JSON Transformation**: Converts UTF-8 CSV files to structured JSON format
3. **ERP Integration**: Posts the JSON data to Microsoft Dynamics Business Central as journal entries

### High-Level Data Flow

```
Incoming CSV Files --> [charset_converter.py] --UTF-8 CSV--> [csv_to_json_converter.py] --Structured JSON--> [process_japan_exports.py] --Authenticated API Calls--> [ERP System (Microsoft Dynamics BC)]
                                                                                                                                        ^
                                                                                                                                        |
                                                                                                                              [oauth_token_helper.py] --OAuth Token-->
```

## Setup Instructions

### Python Environment Setup

1. **Create a virtual environment**:
   ```bash
   # Create a virtual environment
   python -m venv venv
   
   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit the .env file with your actual values
   # Required variables:
   # - ERP_CLIENT_ID: Azure AD client ID
   # - ERP_CLIENT_SECRET: Azure AD client secret
   # - ERP_TOKEN_URL: OAuth token endpoint URL
   # - ERP_API_URL: Business Central API base URL
   # - ERP_SCOPE: API scope (usually https://api.businesscentral.dynamics.com/.default)
   ```

## Key Components

### 1. charset_converter.py

Converts files from non-UTF-8 encodings (like Shift-JIS or other Japanese encodings) to UTF-8 format.

#### Usage

```bash
python charset_converter.py input_file [output_file] [--encoding encoding] [--force] [--japanese]
```

#### Arguments

- `input_file`: Path to the file you want to convert
- `output_file` (optional): Path where the converted file will be saved
- `--encoding`: Manually specify the source encoding
- `--force`: Force conversion even if validation fails
- `--japanese`: Optimize for Japanese text detection

#### Example

```bash
python charset_converter.py "Raku export.csv" "Raku export-utf8.csv"
```

### 2. csv_to_json_converter.py

Converts UTF-8 encoded CSV files to a structured JSON format, handling two-line headers, debit/credit pairs, and applying business rules.

#### Usage

```bash
python csv_to_json_converter.py -i INPUT_FILE -o OUTPUT_FILE [--max-desc-length LENGTH] [--no-fix-line-breaks] [--line-break-replacement CHAR]
```

#### Arguments

- `-i, --input`: Input CSV file path
- `-o, --output`: Output JSON file path
- `--max-desc-length`: Maximum length for description field (default: 100)
- `--no-fix-line-breaks`: Disable fixing line breaks in CSV fields
- `--line-break-replacement`: Character to replace line breaks with (default: space)

#### Example

```bash
python csv_to_json_converter.py -i "Raku export-utf8.csv" -o "Raku export.json"
```

### 3. process_japan_exports.py

Processes structured JSON data and posts it to Microsoft Dynamics Business Central as journal entries.

#### Usage

```bash
python process_japan_exports.py INPUT_JSON_FILE [--report REPORT_FILE] [--unbalanced-report REPORT_FILE] [--balance-tolerance TOLERANCE] [--skip-unbalanced] [--dry-run]
```

#### Arguments

- `input_file`: Path to the input JSON file
- `--report`: Generate currency modification report to specified file path
- `--unbalanced-report`: Generate unbalanced entries report to specified file path
- `--balance-tolerance`: Acceptable difference between debit and credit amounts
- `--skip-unbalanced`: Skip unbalanced entries instead of posting them
- `--dry-run`: Generate report only without posting to API

#### Example

```bash
python process_japan_exports.py "Raku export.json"
```

### 4. oauth_token_helper.py

Handles OAuth 2.0 authentication with Microsoft Azure AD for accessing the Business Central API.

### 5. exchange_rate_api.py

Manages currency exchange rate calculations and retrieval from the Business Central API.

## Complete Workflow Example

```bash
# 1. Convert CSV from original encoding to UTF-8
python charset_converter.py "Raku export.csv" "Raku export-utf8.csv"

# 2. Convert UTF-8 CSV to structured JSON
python csv_to_json_converter.py -i "Raku export-utf8.csv" -o "Raku export.json"

# 3. Process JSON and post to ERP
python process_japan_exports.py "Raku export.json"
```

## Security Best Practices

This project follows security best practices for handling sensitive data:

- **No hard-coded secrets**: Sensitive data like API keys, passwords, or credentials are never hard-coded in the source code.
- **Environment variables**: All sensitive configuration is loaded from environment variables.
- **Dotenv support**: For local development, you can use a `.env` file (which is not committed to version control).

### Using Environment Variables

1. Copy the `.env.example` file to create your own `.env` file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file to add your sensitive data:
   ```
   ERP_CLIENT_ID=your_client_id
   ERP_CLIENT_SECRET=your_client_secret
   ERP_TOKEN_URL=https://login.microsoftonline.com/your_tenant_id/oauth2/v2.0/token
   ERP_API_URL=https://api.businesscentral.dynamics.com/v2.0/your_tenant_id/your_environment/api/v2.0
   ERP_SCOPE=https://api.businesscentral.dynamics.com/.default
   ```

3. In your code, use the `env_config.py` utility to access these values:
   ```python
   from env_config import get_env_var
   
   # Get a required value (raises error if not set)
   client_id = get_env_var("ERP_CLIENT_ID", required=True)
   
   # Get a value with a default
   api_url = get_env_var("ERP_API_URL", default="https://api.businesscentral.dynamics.com")
   ```

## Error Handling and Recovery

### Common Error Scenarios

1. **Encoding Detection Failures**:
   ```bash
   # Manually specify encoding
   python charset_converter.py input.csv output_utf8.csv --encoding shift_jis
   
   # Force conversion despite validation issues
   python charset_converter.py input.csv output_utf8.csv --encoding shift_jis --force
   ```

2. **CSV Parsing Errors**:
   - Ensure the CSV has the expected two-line header
   - Check for line break issues in fields
   - Manually inspect the CSV in a text editor

3. **Unbalanced Entries**:
   ```bash
   # Adjust tolerance for small differences
   python process_japan_exports.py data.json --balance-tolerance 0.05
   
   # Skip unbalanced entries
   python process_japan_exports.py data.json --skip-unbalanced
   ```

4. **API Authentication Issues**:
   - Verify ERP_CLIENT_ID and ERP_CLIENT_SECRET in .env
   - Check that the token URL is correct
   - Ensure the application has proper permissions in Azure AD

## Output Format

The JSON output from the csv_to_json_converter.py script is an array of journal entries, where each entry contains:

- Common fields (voucher number, dates, description, etc.)
- Debit information (account, amount, department, etc.)
- Credit information (account, amount, department, etc.)

Example:
```json
[
  {
    "voucher_no": "VPA-0000065",
    "transaction_date": "2025/03/10",
    "application_date": "2025/03/10",
    "journal_generation_date": "2025/03/20",
    "description": "VPA-0000065   飲食費(社内会議等)・10% Lunch Meeting with HR and RD Managers",
    "note": "",
    "receipt_invoice": "",
    "debit": {
      "marker": "",
      "gl_account_type": "G/L Account",
      "account": "73300-14",
      "main_account_code": "73300",
      "sub_account_code": "73300-14",
      "account_name": "飲食費(社内会議等)・10%",
      "amount": 785.0,
      "currency": "NTD",
      "department": "VCT.1692G",
      "applicant_code": "10017",
      "vendor_code": "",
      "description": "Lunch Meeting with HR and RD Managers",
      "department_code": "VCT.1692"
    },
    "credit": {
      "marker": "",
      "gl_account_type": "Vendor",
      "account": "32200-10",
      "main_account_code": "32200",
      "sub_account_code": "32200-10",
      "account_name": "未払金",
      "amount": 785.0,
      "currency": "NTD",
      "department": "VCT.1692G",
      "applicant_code": "10017",
      "vendor_code": "V0001",
      "description": "",
      "department_code": "VCT.9999"
    }
  }
]
```

## For More Information

For detailed technical documentation, refer to the `Design Document TOI.md` file in this repository, which provides comprehensive information about:

- System architecture and component interactions
- Data validation strategies
- Rate limiting implementation
- Exchange rate handling
- Consolidated entries logic
- Authentication and authorization
- Error handling and logging
- Monitoring recommendations

## Requirements

- Python 3.8+
- Required packages (see requirements.txt):
  - chardet
  - python-dotenv
  - requests
  - pandas (optional, for some utilities)
