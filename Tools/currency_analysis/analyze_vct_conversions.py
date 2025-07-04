#!/usr/bin/env python3
"""
Analyze the VCT log file with more currency conversions
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
        print(f"Error: Log file not found: {file_path}")
        print(f"Please check the file path and try again.")
        return False
    
    if not path.is_file():
        print(f"Error: Path is not a file: {file_path}")
        return False
    
    return True

def create_output_directory(output_dir):
    """Create output directory if it doesn't exist."""
    path = Path(output_dir)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error: Cannot create output directory: {output_dir}")
        print(f"   {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Analyze VCT currency conversions from ERP API integration logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ../../Data/Logs/erp_api_integration-vct-pr1-2-0529.log
  %(prog)s ../../Data/Logs/your-log-file.log --output-dir ../finance_reports/
        """
    )
    
    parser.add_argument('log_file', 
                       help='Path to the ERP API integration log file to analyze')
    
    parser.add_argument('--output-dir', '-o', 
                       default='.', 
                       help='Output directory for generated reports (default: current directory)')
    
    args = parser.parse_args()
    
    # Validate log file
    if not validate_log_file(args.log_file):
        sys.exit(1)
    
    # Create output directory
    if not create_output_directory(args.output_dir):
        sys.exit(1)
    
    log_file = args.log_file
    
    print("=== Currency Conversion Analysis - VCT PR1-2 Log ===")
    print(f"Analyzing log file: {log_file}")
    print()
    
    # Initialize analyzer
    analyzer = CurrencyConversionAnalyzer(log_file)
    
    # Parse log file
    analyzer.parse_log_file()
    
    if not analyzer.conversion_data:
        print("No currency conversions found in the log file.")
        return
    
    # Generate reports
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Generate Excel report
    excel_path = Path(args.output_dir) / f'vct_currency_conversion_report_{timestamp}.xlsx'
    analyzer.generate_excel_report(excel_path)
    
    # Generate JSON summary
    json_path = Path(args.output_dir) / f'vct_currency_conversion_summary_{timestamp}.json'
    analyzer.generate_json_summary(json_path)
    
    # Print detailed analysis
    print("=== ANALYSIS RESULTS ===")
    print(f"Total conversions found: {len(analyzer.conversion_data)}")
    print(f"Total currency transformations: {len(analyzer.currency_transformations)}")
    print(f"Vouchers processed: {len(analyzer.voucher_summaries)}")
    print()
    
    # Show first 10 conversion details
    print("=== CURRENCY CONVERSIONS FOUND (First 10) ===")
    for i, conv in enumerate(analyzer.conversion_data[:10], 1):
        print(f"{i}. Voucher: {conv['voucher_number']}")
        print(f"   {conv['original_amount']} {conv['from_currency']} → {conv['converted_amount']} {conv['to_currency']}")
        print(f"   Exchange Rate: {conv['exchange_rate']}")
        if conv['rounding_difference']:
            print(f"   Rounding Difference: {conv['rounding_difference']}")
        print(f"   Timestamp: {conv['timestamp']}")
        print()
    
    if len(analyzer.conversion_data) > 10:
        print(f"... and {len(analyzer.conversion_data) - 10} more conversions")
        print()
    
    
    # Show rounding summary
    rounding_summary = analyzer._get_rounding_summary()
    print("=== ROUNDING IMPACT SUMMARY ===")
    print(f"Total rounding impact: {rounding_summary['total_rounding_impact']}")
    print(f"Max single rounding difference: {rounding_summary['max_single_rounding']}")
    print(f"Conversions with rounding: {rounding_summary['conversions_with_rounding']}")
    print()
    
    # Show currency pairs
    currency_pairs = set()
    for conv in analyzer.conversion_data:
        currency_pairs.add(f"{conv['from_currency']} → {conv['to_currency']}")
    
    print("=== CURRENCY PAIRS PROCESSED ===")
    for pair in sorted(currency_pairs):
        count = sum(1 for conv in analyzer.conversion_data 
                   if f"{conv['from_currency']} → {conv['to_currency']}" == pair)
        print(f"  {pair}: {count} conversions")
    print()
    
    # Show voucher summary
    print("=== VOUCHER SUMMARY (First 10) ===")
    for i, (voucher, summary) in enumerate(list(analyzer.voucher_summaries.items())[:10], 1):
        print(f"{i}. {voucher}:")
        print(f"   Conversions: {len(summary['conversions'])}")
        print(f"   Total Original: {summary['total_original_amount']}")
        print(f"   Total Converted: {summary['total_converted_amount']}")
        print(f"   Rounding Impact: {summary['total_rounding_difference']}")
        print()
    
    if len(analyzer.voucher_summaries) > 10:
        print(f"... and {len(analyzer.voucher_summaries) - 10} more vouchers")
        print()
    
    print("=== REPORTS GENERATED ===")
    print(f"Excel Report: {excel_path}")
    print(f"JSON Summary: {json_path}")
    print()
    print("The Excel report contains multiple sheets:")
    print("  - Summary: Voucher-level aggregations")
    print("  - Conversion Details: Individual conversion records")
    print("  - Currency Transformations: All currency code changes")
    print("  - Exchange Rates: Rate usage summary")
    print()
    print("This report is ready for finance team review!")

if __name__ == '__main__':
    main()
