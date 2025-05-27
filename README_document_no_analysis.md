# Document_No Discrepancy Analysis Tool

This tool analyzes Business Central API log files to identify discrepancies between Document_No values in request and response payloads. It helps identify cases where the Document_No sent in the request is different from the Document_No returned in the response.

## Background

Business Central API sometimes returns a different Document_No in the response compared to what was sent in the request. For example, sending a request with Document_No "OBA-0000024" might result in a response with Document_No "OBA-0000022". This can cause tracking and reconciliation issues.

## Features

- Parses Business Central API log files to extract request and response pairs
- Identifies discrepancies in Document_No values
- Generates detailed reports with statistics and affected items
- Outputs both human-readable Markdown reports and machine-readable JSON data

## Usage

```bash
python analyze_document_no_discrepancies.py <log_file_path> [output_report_path]
```

### Arguments

- `log_file_path`: Path to the Business Central API log file to analyze
- `output_report_path` (optional): Path where the report will be saved (default: document_no_discrepancy_report.md)

### Example

```bash
python analyze_document_no_discrepancies.py erp_api_integration.log bc_discrepancy_report.md
```

## Output

The script generates two output files:

1. A Markdown report (e.g., `bc_discrepancy_report.md`) containing:
   - Summary statistics
   - Affected Document_No prefixes
   - Detailed list of discrepancies

2. A JSON file (e.g., `bc_discrepancy_report.json`) containing the raw discrepancy data for further analysis

## Example Report

```markdown
# Document_No Discrepancy Analysis Report
Generated on: 2025-05-27 08:48:21

## Summary Statistics
- Total API requests analyzed: 2
- Total discrepancies found: 1
- Discrepancy percentage: 50.00%

## Affected Document_No Prefixes
- OBA-0000024: 1 occurrences

## Detailed Discrepancies
### Discrepancy 1
- Timestamp: 2025-05-24 09:30:02,208
- External Document No: 2025/04/13
- Request Document No: OBA-0000024
- Response Document No: OBA-0000022
```

## Requirements

- Python 3.6 or higher
- No external dependencies required

## How It Works

1. The script parses the log file to extract request and response JSON payloads
2. It matches each request with its corresponding response based on timestamps and External_Document_No
3. It compares the Document_No values in each request-response pair
4. It generates a report with statistics and details of the discrepancies found

## Troubleshooting

If the script doesn't find any discrepancies:
- Verify that the log file contains both request and response entries
- Check that the log format matches what the script expects
- Ensure that there are actual discrepancies in the Document_No values

## Limitations

- The script assumes a specific log format with "Request body for journal line" and "API response body" markers
- It relies on timestamps and External_Document_No to match requests with responses
- Very large log files may require significant memory to process
