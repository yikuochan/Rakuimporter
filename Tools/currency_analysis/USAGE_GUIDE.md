# Currency Conversion Analysis Tool - Usage Guide

## Quick Start

The new `analyze_currency_conversions.py` script allows you to analyze any ERP API integration log file by specifying it as a command-line argument.

## Basic Usage

```bash
# Analyze any log file
python analyze_currency_conversions.py <path_to_log_file>
```

## Examples

### 1. Analyze the main log file
```bash
python analyze_currency_conversions.py Data/Logs/erp_api_integration.log
```

### 2. Analyze the VCT log file with more conversion data
```bash
python analyze_currency_conversions.py Data/Logs/erp_api_integration-vct-pr1-2-0529.log
```

### 3. Save reports to a specific directory
```bash
python analyze_currency_conversions.py Data/Logs/erp_api_integration-vct-pr1-2-0529.log --output-dir reports/
```

### 4. Generate only Excel report (skip JSON)
```bash
python analyze_currency_conversions.py Data/Logs/your-log-file.log --excel-only
```

### 5. Generate only JSON summary (skip Excel)
```bash
python analyze_currency_conversions.py Data/Logs/your-log-file.log --json-only
```

### 6. Quiet mode (minimal output)
```bash
python analyze_currency_conversions.py Data/Logs/your-log-file.log --quiet
```

## Available Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output-dir` | `-o` | Specify output directory for reports |
| `--excel-only` | | Generate only Excel report |
| `--json-only` | | Generate only JSON summary |
| `--quiet` | `-q` | Suppress detailed output |
| `--help` | `-h` | Show help message |

## Output Files

The script automatically generates meaningful file names based on your input log file:

### Input: `erp_api_integration.log`
- Excel: `currency_conversion_report_YYYYMMDD_HHMMSS.xlsx`
- JSON: `currency_conversion_report_summary_YYYYMMDD_HHMMSS.json`

### Input: `erp_api_integration-vct-pr1-2-0529.log`
- Excel: `currency_conversion_vct_pr1_2_0529_YYYYMMDD_HHMMSS.xlsx`
- JSON: `currency_conversion_vct_pr1_2_0529_summary_YYYYMMDD_HHMMSS.json`

## Available Log Files

You can analyze any of these log files in your `Data/Logs/` directory:

```bash
# List available log files
ls Data/Logs/*.log

# Common files to analyze:
Data/Logs/erp_api_integration.log                    # Main log file
Data/Logs/erp_api_integration-vct-pr1-2-0529.log    # VCT with many conversions
Data/Logs/erp_api_integration-vca-0527.log          # VCA log file
Data/Logs/erp_api_integration-vcp-0527.log          # VCP log file
```

## What the Script Does

1. **Validates** the log file exists and is readable
2. **Parses** currency conversions, transformations, and API responses
3. **Analyzes** exchange rates, rounding impacts, and validation results
4. **Generates** comprehensive Excel reports with multiple sheets:
   - Summary: Voucher-level aggregations
   - Conversion Details: Individual conversion records
   - Validation: Comparison with API responses
   - Currency Transformations: All currency code changes
   - Exchange Rates: Rate usage summary
5. **Creates** JSON summaries for automation
6. **Provides** detailed analysis output with emojis for easy reading

## Error Handling

The script includes comprehensive error handling:

- ❌ **File not found**: Clear error message with path verification
- ❌ **Empty files**: Detects and reports empty log files
- ❌ **Permission issues**: Reports file access problems
- ❌ **Invalid arguments**: Validates command-line options
- ⚠️ **No data found**: Warns if no conversions are detected

## Sample Output

```
🚀 Starting currency conversion analysis...
📁 Log file: Data/Logs/erp_api_integration-vct-pr1-2-0529.log
📂 Output directory: reports
🔍 Parsing log file...

============================================================
📊 CURRENCY CONVERSION ANALYSIS SUMMARY
============================================================
📁 Log file analyzed: Data/Logs/erp_api_integration-vct-pr1-2-0529.log
📈 Total conversions found: 41
🔄 Total currency transformations: 514
📋 Vouchers processed: 3

========================================
💱 CURRENCY PAIRS PROCESSED
========================================
  RMB → NTD: 25 conversions
  JPY → NTD: 10 conversions
  USD → NTD: 6 conversions

✅ ANALYSIS COMPLETED SUCCESSFULLY
📋 Excel Report: reports/currency_conversion_vct_pr1_2_0529_20250701_171253.xlsx
📋 JSON Summary: reports/currency_conversion_vct_pr1_2_0529_summary_20250701_171253.json
```

## For Finance Team

### Quick Analysis
```bash
# Analyze the main log file for current data
python analyze_currency_conversions.py Data/Logs/erp_api_integration.log

# Analyze historical data with more conversions
python analyze_currency_conversions.py Data/Logs/erp_api_integration-vct-pr1-2-0529.log
```

### Organized Reports
```bash
# Create reports in a dedicated directory
mkdir finance_reports
python analyze_currency_conversions.py Data/Logs/your-log-file.log --output-dir finance_reports/
```

### Quick Summary Only
```bash
# Generate just JSON summary for quick review
python analyze_currency_conversions.py Data/Logs/your-log-file.log --json-only --quiet
```

## Troubleshooting

### Common Issues

1. **"Log file not found"**
   - Check the file path is correct
   - Use `ls Data/Logs/` to see available files

2. **"No conversions found"**
   - Verify you're using the correct log file
   - Some log files may only contain transformations, not conversions

3. **Permission errors**
   - Ensure you have read access to the log file
   - Check write permissions for the output directory

### Getting Help

```bash
# Show all available options
python analyze_currency_conversions.py --help
```

## Integration with Existing Tools

The new script uses the same analysis engine as the previous tools:
- `currency_conversion_report_generator.py` - Core analysis engine
- `run_currency_analysis.py` - Original fixed-file script
- `analyze_vct_conversions.py` - VCT-specific script

All generate the same comprehensive reports, but the new script offers maximum flexibility for file selection.
