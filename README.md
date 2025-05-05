# Power Importer - CSV Processing Tools

This repository contains tools for processing CSV files from various sources, including files with Japanese character encodings.

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
   ERP_API_KEY=your_actual_api_key
   DB_PASSWORD=your_actual_password
   ```

3. In your code, use the `env_config.py` utility to access these values:
   ```python
   from env_config import get_env_var
   
   # Get a simple string value
   api_key = get_env_var("ERP_API_KEY")
   
   # Get a required value (raises error if not set)
   password = get_env_var("DB_PASSWORD", required=True)
   
   # Get a value with a default
   host = get_env_var("DB_HOST", default="localhost")
   
   # Get a value as a specific type
   debug = get_env_var("DEBUG_MODE", default="False", as_type=bool)
   port = get_env_var("DB_PORT", default="5432", as_type=int)
   ```

4. For production deployment, set actual environment variables in your environment instead of using a `.env` file.

## Tools Overview

1. **csv_to_json_converter.py** - Converts General Journal CSV files to structured JSON format
2. **charset_converter.py** - Converts files from non-UTF-8 encodings (like Shift-JIS) to UTF-8
3. **process_japan_exports.py** - Batch processes files from the Japan team (conversion + JSON processing)

## CSV to JSON Converter

The `csv_to_json_converter.py` script converts General Journal CSV files to a structured JSON format.

### Features

- Handles multi-line headers in the CSV file
- Processes debit and credit pairs in the journal entries
- Extracts and organizes relevant accounting fields
- Converts numeric values where appropriate
- Normalizes currency values ("台湾ドル" -> "NTD", "円" -> "JPY")
- Preserves Japanese characters with proper UTF-8 encoding

**Note:** This script expects input files to be in UTF-8 encoding. For files with other encodings, use the charset_converter.py script first.

### Usage

```bash
python csv_to_json_converter.py [-i INPUT_FILE] [-o OUTPUT_FILE]
```

#### Command-line Arguments

- `-i, --input`: Input CSV file path (default: "Raku export.csv")
- `-o, --output`: Output JSON file path (default: "journal_entries.json")

#### Examples

Use default file names:
```bash
python csv_to_json_converter.py
```

Specify input file:
```bash
python csv_to_json_converter.py -i my_export.csv
```

Specify both input and output files:
```bash
python csv_to_json_converter.py -i my_export.csv -o my_output.json
```

## Charset Converter

The `charset_converter.py` script converts files from non-UTF-8 encodings (like Shift-JIS or other Japanese encodings) to UTF-8 format.

### Features

- Automatic encoding detection using the `chardet` library
- Fallback to common Japanese encodings if detection confidence is low
- Handles various Japanese encodings (Shift-JIS, EUC-JP, ISO-2022-JP, CP932)
- Creates a new file with UTF-8 encoding, preserving the original file

### Requirements

- Python 3.x
- `chardet` library (install with `pip install chardet` in a virtual environment)

### Usage

```bash
python charset_converter.py input_file [output_file]
```

#### Arguments

- `input_file`: Path to the file you want to convert
- `output_file` (optional): Path where the converted file will be saved. If not specified, the script will create a file with the same name as the input file but with "_utf8" appended before the extension.

#### Examples

Convert a file and let the script name the output file:
```bash
python charset_converter.py "Evelyn Raku export.csv"
```
This will create a file named "Evelyn Raku export_utf8.csv"

## Batch Processing Script

The `process_japan_exports.py` script automates the workflow of:
1. Converting files from non-UTF-8 charset to UTF-8
2. Processing the converted files with csv_to_json_converter.py

### Usage

```bash
python process_japan_exports.py file1.csv [file2.csv ...]
```

#### Examples

Process a single file:
```bash
python process_japan_exports.py "Evelyn Raku export.csv"
```

Process multiple files:
```bash
python process_japan_exports.py "Evelyn Raku export.csv" "Raku export.csv"
```

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
      "gl_account": "G/L Account",
      "account": "",
      "sub_account": "73300-14",
      "amount": 785.0,
      "currency": "台湾ドル",
      "department": "VCT.1692G",
      "applicant_code": "10017",
      "vendor_code": "",
      "free_field": "Lunch Meeting with HR and RD Managers",
      "department_code": "VCT.1692"
    },
    "credit": {
      "marker": "",
      "gl_account": "Vendor",
      "account": "32200-10",
      "sub_account": "32200-10",
      "amount": 785.0,
      "currency": "台湾ドル",
      "department": "VCT.1692G",
      "applicant_code": "10017",
      "vendor_code": "",
      "free_field": "",
      "department_code": ""
    }
  },
  // More journal entries...
]
```

## Workflow for Processing Japan Team Files

1. **For a single file:**
   ```bash
   # Convert encoding
   python charset_converter.py "Japan_export.csv"
   
   # Process the converted file
   python csv_to_json_converter.py -i "Japan_export_utf8.csv" -o "japan_data.json"
   ```

2. **For batch processing:**
   ```bash
   # Process multiple files at once
   python process_japan_exports.py "Japan_export1.csv" "Japan_export2.csv"
   ```

## Error Handling

All scripts include error handling for common issues:

- If input files don't exist, they will display appropriate error messages
- The charset_converter.py script will try multiple encodings if the initial detection fails
- The process_japan_exports.py script provides a summary of successful and failed file processing
