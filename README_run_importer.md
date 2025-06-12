# How to Use run_importer.py

`run_importer.py` is the main entry point for the Power Importer application. It provides a complete workflow for processing CSV files, converting them to JSON, and importing them into the ERP system.

## Basic Usage

```bash
python run_importer.py <input_csv_file> [options]
```

## Command-line Options

| Option | Description |
|--------|-------------|
| `--output-json FILE` | Output JSON file path (default: input_filename.json) |
| `--skip-import` | Skip importing to ERP, only convert CSV to JSON |
| `--dry-run` | Generate report only without posting to API |
| `--report FILE` | Generate currency modification report to specified file path (default: currency_modification_report.md) |
| `--unbalanced-report FILE` | Generate unbalanced entries report to specified file path (default: unbalanced_entries_report.md) |
| `--balance-tolerance N` | Acceptable difference between debit and credit amounts (default: 0.01) |
| `--skip-unbalanced` | Skip unbalanced entries instead of posting them |
| `--max-desc-length N` | Maximum length for description field (default: 100) |
| `--no-fix-line-breaks` | Disable fixing line breaks in CSV fields (enabled by default) |
| `--line-break-replacement CHAR` | Character to replace line breaks with (default: space) |

## Examples

### Basic Example: Full Process (CSV to ERP)

```bash
python run_importer.py "examples/0527-Raku export- VCA.csv"
```

This will:
1. Convert the CSV file to UTF-8 encoding
2. Convert the UTF-8 CSV to JSON
3. Import the JSON data into the ERP system

### Convert CSV to JSON Only

```bash
python run_importer.py "examples/0527-Raku export- VCA.csv" --skip-import
```

This will:
1. Convert the CSV file to UTF-8 encoding
2. Convert the UTF-8 CSV to JSON
3. Skip the ERP import step

### Specify Output JSON File

```bash
python run_importer.py "examples/0527-Raku export- VCA.csv" --output-json "custom_output.json"
```

### Generate Reports Without Posting to API

```bash
python run_importer.py "examples/0527-Raku export- VCA.csv" --dry-run --report "currency_report.md" --unbalanced-report "balance_issues.md"
```

### Skip Unbalanced Entries

```bash
python run_importer.py "examples/0527-Raku export- VCA.csv" --skip-unbalanced
```

### Customize Description Field Handling

```bash
python run_importer.py "examples/0527-Raku export- VCA.csv" --max-desc-length 150 --no-fix-line-breaks
```

## Workflow Steps

1. **Charset Conversion**: The script first checks if the input file needs charset conversion. If the file doesn't end with `.utf8.csv`, it attempts to convert it from various Japanese encodings (shift_jis, euc_jp, etc.) to UTF-8.

2. **CSV to JSON Conversion**: The UTF-8 CSV file is then converted to JSON format using the `core.csv_to_json_converter` module.

3. **ERP Import**: Unless `--skip-import` is specified, the JSON data is imported into the ERP system using the `core.process_japan_exports` module.

## Environment Variables

The script uses environment variables for configuration, which can be set in the `.env` file:

- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FILE`: Log file path (default: erp_api_integration.log)
- `ERP_TOKEN_URL`: OAuth token URL
- `ERP_API_URL`: ERP API endpoint URL
- `ERP_CLIENT_ID`: Client ID for OAuth authentication
- `ERP_CLIENT_SECRET`: Client secret for OAuth authentication
- `ERP_SCOPE`: OAuth scope

## Running process_japan_exports.py Directly

If you already have a JSON file and want to import it directly without going through the CSV conversion steps:

```bash
python -m core.process_japan_exports "examples/0527-Raku export- VCA.utf8.json"
```

Note the `-m` flag which is needed because the script is now in the `core` module.

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**: Ensure that all required environment variables are set in your `.env` file, especially `ERP_CLIENT_ID` and `ERP_CLIENT_SECRET`.

2. **Encoding Issues**: If you encounter encoding problems with CSV files, try specifying a different encoding in the charset conversion step.

3. **Unbalanced Entries**: Use the `--balance-tolerance` option to adjust the acceptable difference between debit and credit amounts, or use `--skip-unbalanced` to skip unbalanced entries.

4. **API Rate Limiting**: The script includes rate limiting and retry logic to handle API rate limits. If you encounter persistent rate limiting issues, adjust the delay parameters in the `process_japan_exports.py` script.

### Logs

Check the log file (default: `erp_api_integration.log`) for detailed information about the execution process, including any errors or warnings.
