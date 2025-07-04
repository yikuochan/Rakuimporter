#!/usr/bin/env python3
"""
Currency Conversion Analysis Tool

A flexible command-line tool to analyze currency conversions and rounding operations
from ERP API integration log files. Generates comprehensive reports for finance team review.

Usage:
    python analyze_currency_conversions.py <log_file_path> [options]

Examples:
    python analyze_currency_conversions.py Data/Logs/erp_api_integration.log
    python analyze_currency_conversions.py Data/Logs/erp_api_integration-vct-pr1-2-0529.log --output-dir reports/
    python analyze_currency_conversions.py Data/Logs/your-log-file.log --excel-only
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from currency_conversion_report_generator import CurrencyConversionAnalyzer

def validate_log_file(file_path):
    """Validate that the log file exists and is readable."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ Error: Log file not found: {file_path}")
        print(f"   Please check the file path and try again.")
        return False
    
    if not path.is_file():
        print(f"❌ Error: Path is not a file: {file_path}")
        return False
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            # Try to read first few lines to validate file format
            first_lines = [f.readline() for _ in range(3)]
            if not any(first_lines):
                print(f"❌ Error: Log file appears to be empty: {file_path}")
                return False
    except Exception as e:
        print(f"❌ Error: Cannot read log file: {file_path}")
        print(f"   {str(e)}")
        return False
    
    return True

def create_output_directory(output_dir):
    """Create output directory if it doesn't exist."""
    path = Path(output_dir)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ Error: Cannot create output directory: {output_dir}")
        print(f"   {str(e)}")
        return False

def generate_report_names(log_file_path, output_dir, timestamp):
    """Generate appropriate report names based on input file."""
    log_file = Path(log_file_path)
    base_name = log_file.stem  # filename without extension
    
    # Clean up the base name for report files
    if base_name.startswith('erp_api_integration'):
        if base_name == 'erp_api_integration':
            report_prefix = 'currency_conversion_report'
        else:
            # Extract meaningful part from names like 'erp_api_integration-vct-pr1-2-0529'
            parts = base_name.split('-')[1:]  # Remove 'erp_api_integration' part
            if parts:
                report_prefix = f"currency_conversion_{'_'.join(parts)}"
            else:
                report_prefix = 'currency_conversion_report'
    else:
        report_prefix = f"currency_conversion_{base_name}"
    
    excel_path = Path(output_dir) / f"{report_prefix}_{timestamp}.xlsx"
    json_path = Path(output_dir) / f"{report_prefix}_summary_{timestamp}.json"
    
    return excel_path, json_path

def print_analysis_summary(analyzer, log_file_path):
    """Print a comprehensive analysis summary."""
    print(f"\n{'='*60}")
    print(f"📊 CURRENCY CONVERSION ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"📁 Log file analyzed: {log_file_path}")
    print(f"📈 Total conversions found: {len(analyzer.conversion_data)}")
    print(f"🔄 Total currency transformations: {len(analyzer.currency_transformations)}")
    print(f"📋 Vouchers processed: {len(analyzer.voucher_summaries)}")
    
    if analyzer.conversion_data:
        print(f"\n{'='*40}")
        print(f"💱 CURRENCY PAIRS PROCESSED")
        print(f"{'='*40}")
        
        # Show currency pairs
        currency_pairs = {}
        for conv in analyzer.conversion_data:
            pair = f"{conv['from_currency']} → {conv['to_currency']}"
            currency_pairs[pair] = currency_pairs.get(pair, 0) + 1
        
        for pair, count in sorted(currency_pairs.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pair}: {count} conversions")
        
        print(f"\n{'='*40}")
        print(f"💰 SAMPLE CONVERSIONS")
        print(f"{'='*40}")
        
        # Show first 5 conversions
        for i, conv in enumerate(analyzer.conversion_data[:5], 1):
            print(f"  {i}. Voucher: {conv['voucher_number']}")
            print(f"     {conv['original_amount']} {conv['from_currency']} → {conv['converted_amount']} {conv['to_currency']}")
            print(f"     Exchange Rate: {conv['exchange_rate']}")
            if conv['rounding_difference']:
                print(f"     Rounding Difference: {conv['rounding_difference']}")
            print()
        
        if len(analyzer.conversion_data) > 5:
            print(f"     ... and {len(analyzer.conversion_data) - 5} more conversions")
    
    
    # Show rounding summary
    rounding_summary = analyzer._get_rounding_summary()
    print(f"\n{'='*40}")
    print(f"🔢 ROUNDING IMPACT SUMMARY")
    print(f"{'='*40}")
    print(f"  Total rounding impact: {rounding_summary['total_rounding_impact']}")
    print(f"  Max single rounding difference: {rounding_summary['max_single_rounding']}")
    print(f"  Conversions with rounding: {rounding_summary['conversions_with_rounding']}")

def main():
    parser = argparse.ArgumentParser(
        description='Analyze currency conversions and rounding from ERP API integration logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s Data/Logs/erp_api_integration.log
  %(prog)s Data/Logs/erp_api_integration-vct-pr1-2-0529.log --output-dir reports/
  %(prog)s Data/Logs/your-log-file.log --excel-only
  %(prog)s Data/Logs/your-log-file.log --json-only
        """
    )
    
    parser.add_argument('log_file', 
                       help='Path to the ERP API integration log file to analyze')
    
    parser.add_argument('--output-dir', '-o', 
                       default='.', 
                       help='Output directory for generated reports (default: current directory)')
    
    parser.add_argument('--excel-only', 
                       action='store_true', 
                       help='Generate only Excel report (skip JSON summary)')
    
    parser.add_argument('--json-only', 
                       action='store_true', 
                       help='Generate only JSON summary (skip Excel report)')
    
    parser.add_argument('--quiet', '-q', 
                       action='store_true', 
                       help='Suppress detailed output (show only essential information)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.excel_only and args.json_only:
        print("❌ Error: Cannot specify both --excel-only and --json-only")
        sys.exit(1)
    
    # Validate log file
    if not validate_log_file(args.log_file):
        sys.exit(1)
    
    # Create output directory
    if not create_output_directory(args.output_dir):
        sys.exit(1)
    
    if not args.quiet:
        print(f"🚀 Starting currency conversion analysis...")
        print(f"📁 Log file: {args.log_file}")
        print(f"📂 Output directory: {args.output_dir}")
    
    # Initialize analyzer
    try:
        analyzer = CurrencyConversionAnalyzer(args.log_file)
    except Exception as e:
        print(f"❌ Error: Failed to initialize analyzer: {str(e)}")
        sys.exit(1)
    
    # Parse log file
    try:
        if not args.quiet:
            print(f"🔍 Parsing log file...")
        analyzer.parse_log_file()
    except Exception as e:
        print(f"❌ Error: Failed to parse log file: {str(e)}")
        sys.exit(1)
    
    if not analyzer.conversion_data and not analyzer.currency_transformations:
        print(f"⚠️  No currency conversions or transformations found in the log file.")
        print(f"   Please verify that this is the correct log file.")
        sys.exit(0)
    
    # Generate timestamp for output files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_path, json_path = generate_report_names(args.log_file, args.output_dir, timestamp)
    
    # Generate reports
    reports_generated = []
    
    try:
        if not args.json_only:
            if not args.quiet:
                print(f"📊 Generating Excel report...")
            analyzer.generate_excel_report(excel_path)
            reports_generated.append(f"Excel Report: {excel_path}")
        
        if not args.excel_only:
            if not args.quiet:
                print(f"📄 Generating JSON summary...")
            analyzer.generate_json_summary(json_path)
            reports_generated.append(f"JSON Summary: {json_path}")
    
    except Exception as e:
        print(f"❌ Error: Failed to generate reports: {str(e)}")
        sys.exit(1)
    
    # Print analysis summary
    if not args.quiet:
        print_analysis_summary(analyzer, args.log_file)
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"✅ ANALYSIS COMPLETED SUCCESSFULLY")
    print(f"{'='*60}")
    
    for report in reports_generated:
        print(f"📋 {report}")
    
    if not args.excel_only and not args.json_only:
        print(f"\n📊 The Excel report contains multiple sheets:")
        print(f"   • Summary: Voucher-level aggregations")
        print(f"   • Conversion Details: Individual conversion records")
        print(f"   • Currency Transformations: All currency code changes")
        print(f"   • Exchange Rates: Rate usage summary")
    
    print(f"\n🎯 Reports are ready for finance team review!")

if __name__ == '__main__':
    main()
