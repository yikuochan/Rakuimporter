# General Journal CSV to JSON Converter

This Python script converts a General Journal CSV file from Raku export format to a structured JSON format.

## Features

- Handles multi-line headers in the CSV file
- Processes debit and credit pairs in the journal entries
- Extracts and organizes relevant accounting fields
- Converts numeric values where appropriate
- Preserves Japanese characters with proper UTF-8 encoding

## Usage

```bash
python3 csv_to_json_converter.py [-i INPUT_FILE] [-o OUTPUT_FILE]
```

### Command-line Arguments

- `-i, --input`: Input CSV file path (default: "Raku export.csv")
- `-o, --output`: Output JSON file path (default: "journal_entries.json")

### Examples

Use default file names:
```bash
python3 csv_to_json_converter.py
```

Specify input file:
```bash
python3 csv_to_json_converter.py -i my_export.csv
```

Specify both input and output files:
```bash
python3 csv_to_json_converter.py -i my_export.csv -o my_output.json
```

## Output Format

The JSON output is an array of journal entries, where each entry contains:

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

## Error Handling

The script includes error handling for common issues:

- If the input file doesn't exist, it will display an appropriate error message
- Other exceptions during processing are also caught and reported

## Requirements

- Python 3.x
- Standard libraries: csv, json, io