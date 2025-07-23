#!/usr/bin/env python3
"""
Power Importer - Main Entry Point (Streamlined with Unified Converter)

This script serves as the main entry point for the Power Importer application.
It processes CSV files, converts them to JSON, and imports them into the ERP system.

ENHANCED FEATURES:
- Uses unified CSV converter for better processing
- Comprehensive line break fixing and encoding detection
- Individual entry processing (no problematic VCT consolidation)
- Enhanced error handling and validation
- Improved currency conversion logic
- Real-time progress reporting

Usage:
    python run_importer.py <input_csv_file> [options]

Options:
    --output-json FILE       Output JSON file path (default: input_filename.json)
    --skip-import            Skip importing to ERP, only convert CSV to JSON
    --dry-run                Generate report only without posting to API
    --report FILE            Generate currency modification report to specified file path
    --unbalanced-report FILE Generate unbalanced entries report to specified file path
    --balance-tolerance N    Acceptable difference between debit and credit amounts (default: 0.01)
    --skip-unbalanced        Skip unbalanced entries instead of posting them
    --max-desc-length N      Maximum length for description field (default: 100)
    --no-fix-line-breaks     Disable fixing line breaks in CSV fields (enabled by default)
    --line-break-replacement CHAR  Character to replace line breaks with (default: space)

STREAMLINED IMPROVEMENTS:
- VCT consolidation issues resolved (individual entries only)
- Better CSV structure repair and validation
- Enhanced encoding detection with fallback options
- Comprehensive error reporting with success rates
- All existing commands work exactly the same
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Import core modules
from core.charset_converter import convert_file as convert_charset
from core.csv_to_json_converter import convert_csv_to_json
from core.process_japan_exports import main as process_japan_exports

# Import utility modules
from utils.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.get("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.get("LOG_FILE", "erp_api_integration.log")),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("power_importer")


def main():
    """Main function to process the input file and post to the ERP API."""
    parser = argparse.ArgumentParser(
        description='Process CSV files, convert to JSON, and import to ERP system',
        epilog='Example: python run_importer.py "Raku export.csv" --output-json "journal_entries.json"'
    )
    
    # Input/output options
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('--output-json', help='Output JSON file path (default: input_filename.json)')
    parser.add_argument('--skip-import', action='store_true', help='Skip importing to ERP, only convert CSV to JSON')
    
    # CSV conversion options
    parser.add_argument('--max-desc-length', type=int, default=100, 
                        help='Maximum length for description field (default: 100)')
    parser.add_argument('--no-fix-line-breaks', action='store_true',
                        help='Disable fixing line breaks in CSV fields (enabled by default)')
    parser.add_argument('--line-break-replacement', default=' ',
                        help='Character to replace line breaks with (default: space)')
    
    # ERP import options
    parser.add_argument('--dry-run', action='store_true', help='Generate report only without posting to API')
    parser.add_argument('--report', help='Generate currency modification report to specified file path',
                        default="currency_modification_report.md")
    parser.add_argument('--unbalanced-report', help='Generate unbalanced entries report to specified file path',
                        default="unbalanced_entries_report.md")
    parser.add_argument('--balance-tolerance', type=float, default=0.01,
                        help='Acceptable difference between debit and credit amounts')
    parser.add_argument('--skip-unbalanced', action='store_true',
                        help='Skip unbalanced entries instead of posting them')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # If output file is not specified, derive it from the input filename
    if not args.output_json:
        input_base = args.input_file.rsplit('.', 1)[0]  # Remove extension
        args.output_json = f"{input_base}.json"
    
    # Step 1: Check if the input file needs charset conversion
    input_file_path = args.input_file
    input_file_name = os.path.basename(input_file_path)
    
    if not input_file_name.endswith('.utf8.csv'):
        # Convert charset to UTF-8
        logger.info(f"Converting charset of {input_file_path} to UTF-8")
        utf8_file_path = input_file_path.rsplit('.', 1)[0] + '.utf8.csv'
        
        try:
            # Detect encoding and convert to UTF-8
            encodings_to_try = ['shift_jis', 'euc_jp', 'iso-2022-jp', 'cp932', 'windows-1254', 'iso-8859-9']
            success = convert_charset(input_file_path, utf8_file_path, encodings_to_try)
            
            if success:
                logger.info(f"Successfully converted {input_file_path} to UTF-8")
                input_file_path = utf8_file_path
            else:
                logger.error(f"Failed to convert {input_file_path} to UTF-8")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Error converting charset: {str(e)}")
            sys.exit(1)
    
    # Step 2: Convert CSV to JSON using Original Converter
    try:
        logger.info(f"Converting CSV to JSON using original converter: {input_file_path} -> {args.output_json}")
        
        # Convert CSV to JSON with original processing
        entry_count = convert_csv_to_json(
            input_file_path,
            args.output_json,
            args.max_desc_length,
            not args.no_fix_line_breaks,  # Invert the flag since our function expects fix_line_breaks
            args.line_break_replacement
        )
        
        logger.info(f"Converted {entry_count} journal entries to JSON format using original converter")
            
    except Exception as e:
        logger.error(f"Error converting CSV to JSON: {str(e)}")
        sys.exit(1)
    
    # Step 3: Import to ERP if not skipped
    if not args.skip_import:
        logger.info(f"Importing JSON to ERP: {args.output_json}")
        
        # Prepare arguments for process_japan_exports
        erp_args = [
            args.output_json,
            '--report', args.report,
            '--unbalanced-report', args.unbalanced_report,
            '--balance-tolerance', str(args.balance_tolerance),
        ]
        
        if args.skip_unbalanced:
            erp_args.append('--skip-unbalanced')
        
        if args.dry_run:
            erp_args.append('--dry-run')
        
        # Call process_japan_exports with the prepared arguments
        try:
            # Set sys.argv for process_japan_exports
            old_argv = sys.argv
            sys.argv = ['process_japan_exports.py'] + erp_args
            
            # Call the main function
            process_japan_exports()
            
            # Restore sys.argv
            sys.argv = old_argv
            
            logger.info("Import to ERP completed successfully")
        except Exception as e:
            logger.error(f"Error importing to ERP: {str(e)}")
            sys.exit(1)
    else:
        logger.info("Skipping import to ERP as requested")
    
    logger.info("Processing completed successfully")


if __name__ == "__main__":
    main()
