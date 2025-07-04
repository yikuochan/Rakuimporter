# Currency Conversion Analysis Tools

This folder contains all tools and reports for analyzing currency conversions and rounding operations from ERP API integration logs.

## 📁 Folder Contents

### 🔧 Analysis Tools
- **`analyze_currency_conversions.py`** - Main flexible command-line tool (RECOMMENDED)
- **`currency_conversion_report_generator.py`** - Core analysis engine
- **`run_currency_analysis.py`** - Quick analysis script (now with CLI args)
- **`analyze_vct_conversions.py`** - VCT-specific analysis script (now with CLI args)

### 📚 Documentation
- **`USAGE_GUIDE.md`** - Complete usage guide for the new flexible tool
- **`CURRENCY_CONVERSION_REPORT_GUIDE.md`** - Detailed report analysis guide
- **`FINANCE_TEAM_DELIVERABLES.md`** - Executive summary for finance team
- **`README.md`** - This file

### 📊 Sample Reports
- **`vct_currency_conversion_report_20250701_170150.xlsx`** - Comprehensive Excel report (41 conversions)
- **`currency_conversion_report_20250701_170058.xlsx`** - Basic Excel report (1 conversion)
- **`vct_currency_conversion_summary_20250701_170150.json`** - JSON summary (VCT data)
- **`currency_conversion_summary_20250701_170058.json`** - JSON summary (basic data)

## 🚀 Quick Start

### Main Tool (Recommended)
```bash
cd Tools/currency_analysis
python analyze_currency_conversions.py ../../Data/Logs/erp_api_integration.log
```

### Alternative Tools
```bash
# VCT-specific analysis
python analyze_vct_conversions.py ../../Data/Logs/erp_api_integration-vct-pr1-2-0529.log

# Quick analysis
python run_currency_analysis.py ../../Data/Logs/erp_api_integration.log
```

### Save Reports to Custom Directory
```bash
# All tools now support --output-dir
python analyze_currency_conversions.py ../../Data/Logs/your-log-file.log --output-dir ../finance_reports/
python analyze_vct_conversions.py ../../Data/Logs/your-log-file.log --output-dir ../finance_reports/
python run_currency_analysis.py ../../Data/Logs/your-log-file.log --output-dir ../finance_reports/
```

## 📋 Available Options

| Option | Description |
|--------|-------------|
| `--output-dir` | Specify output directory for reports |
| `--excel-only` | Generate only Excel report |
| `--json-only` | Generate only JSON summary |
| `--quiet` | Suppress detailed output |
| `--help` | Show help message |

## 📊 What You Get

Each analysis generates:

### Excel Report (Multi-sheet)
1. **Summary** - Voucher-level aggregations
2. **Conversion Details** - Individual conversion records
3. **Currency Transformations** - All currency code changes
4. **Exchange Rates** - Rate usage summary

### JSON Summary
- Machine-readable data for automation
- Key metrics and rounding analysis
- Structured data for further processing

## 🎯 For Finance Team

### Quick Analysis Commands
```bash
# Current working directory analysis
cd Tools/currency_analysis

# Analyze main log file
python analyze_currency_conversions.py ../../Data/Logs/erp_api_integration.log

# Analyze comprehensive VCT data
python analyze_currency_conversions.py ../../Data/Logs/erp_api_integration-vct-pr1-2-0529.log

# Generate reports in finance folder
mkdir -p ../../finance_reports
python analyze_currency_conversions.py ../../Data/Logs/erp_api_integration-vct-pr1-2-0529.log --output-dir ../../finance_reports/
```

### Key Findings from Sample Analysis
- **41 currency conversions** across 3 vouchers
- **514 currency transformations** processed
- **Currency pairs**: RMB→NTD (25), JPY→NTD (10), USD→NTD (6)
- **✅ Positive**: Minimal rounding impact (0.0 total difference)
- **✅ Clean**: All conversions processed successfully

## 🔍 Understanding the Reports

### Excel Report Sheets
1. **Summary Sheet**: Start here for overview
2. **Conversion Details**: Individual transaction analysis
3. **Currency Transformations**: Track all currency code changes
4. **Exchange Rates**: Verify rates against official sources

### Key Metrics to Review
- **Exchange Rates**: Verify against official sources
- **Rounding Impact**: Monitor cumulative effects
- **Currency Pairs**: Ensure all expected conversions are captured
- **Voucher Totals**: Review aggregated amounts per voucher

## 📋 Exchange Rate Verification

**Current Rates Observed**:
- **USD/NTD**: 32.33 - Verify against official rates
- **RMB/NTD**: 4.45 - Confirm rate source
- **JPY/NTD**: Various rates - Check consistency

## 📞 Support

For questions about:
- **Tool Usage**: See `USAGE_GUIDE.md`
- **Report Analysis**: See `CURRENCY_CONVERSION_REPORT_GUIDE.md`
- **Finance Summary**: See `FINANCE_TEAM_DELIVERABLES.md`
- **Technical Issues**: Contact ERP integration team

## 🔄 Integration

These tools integrate with the existing ERP system:
- Parse standard ERP API integration logs
- Generate Business Central compatible reports
- Support multiple voucher types (VCA, VCP, VCT)
- Handle multiple currency pairs and exchange rates

---

**Last Updated**: July 1, 2025  
**Analysis Coverage**: Lines 78-135+ from ERP API integration logs  
**Report Generation**: Automated with timestamped outputs
