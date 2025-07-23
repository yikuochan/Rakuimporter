#!/usr/bin/env python3
"""
CSV Line Break Fixer

This script fixes line break issues in CSV files where multi-line text within quoted fields
causes parsing problems. It reads the CSV properly and replaces embedded line breaks with spaces.
"""

import csv
import sys
import os
import argparse
from typing import List, Dict, Any

def fix_csv_line_breaks(input_file: str, output_file: str = None, delimiter: str = ',', 
                       encoding: str = 'utf-8', replace_with: str = ' ') -> bool:
    """
    Fix line break issues in CSV files by replacing embedded newlines in fields.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output CSV file (defaults to input_file with .fixed suffix)
        delimiter: CSV delimiter (default: ',')
        encoding: File encoding (default: 'utf-8')
        replace_with: What to replace line breaks with (default: ' ')
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return False
    
    # Generate output filename if not provided
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}.fixed{ext}"
    
    try:
        # Read the CSV file
        rows = []
        with open(input_file, 'r', encoding=encoding, newline='') as infile:
            # Use csv.reader to properly handle quoted fields with line breaks
            reader = csv.reader(infile, delimiter=delimiter)
            
            for row_num, row in enumerate(reader, 1):
                # Process each field in the row
                fixed_row = []
                for field in row:
                    # Replace line breaks with the specified replacement
                    fixed_field = field.replace('\n', replace_with).replace('\r', replace_with)
                    # Also clean up any double spaces that might result
                    fixed_field = ' '.join(fixed_field.split())
                    fixed_row.append(fixed_field)
                
                rows.append(fixed_row)
                
                # Progress indicator for large files
                if row_num % 100 == 0:
                    print(f"Processed {row_num} rows...")
        
        print(f"Successfully read {len(rows)} rows from '{input_file}'")
        
        # Write the fixed CSV file
        with open(output_file, 'w', encoding=encoding, newline='') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            writer.writerows(rows)
        
        print(f"Fixed CSV written to '{output_file}'")
        
        # Verify the output
        with open(output_file, 'r', encoding=encoding) as verify_file:
            verify_content = verify_file.read()
            line_count = verify_content.count('\n')
            print(f"Verification: Output file has {line_count} lines")
        
        return True
        
    except Exception as e:
        print(f"Error processing CSV file: {str(e)}")
        return False

def analyze_csv_issues(input_file: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """
    Analyze CSV file for line break issues and provide statistics.
    
    Args:
        input_file: Path to the CSV file to analyze
        encoding: File encoding (default: 'utf-8')
        
    Returns:
        Dict with analysis results
    """
    if not os.path.exists(input_file):
        return {"error": f"File '{input_file}' not found"}
    
    try:
        analysis = {
            "total_rows": 0,
            "fields_with_line_breaks": 0,
            "affected_rows": 0,
            "max_field_lines": 0,
            "problematic_fields": []
        }
        
        with open(input_file, 'r', encoding=encoding, newline='') as infile:
            reader = csv.reader(infile)
            
            for row_num, row in enumerate(reader, 1):
                analysis["total_rows"] += 1
                row_has_issues = False
                
                for field_num, field in enumerate(row):
                    if '\n' in field or '\r' in field:
                        analysis["fields_with_line_breaks"] += 1
                        row_has_issues = True
                        
                        # Count lines in this field
                        field_lines = field.count('\n') + 1
                        analysis["max_field_lines"] = max(analysis["max_field_lines"], field_lines)
                        
                        # Store example of problematic field
                        if len(analysis["problematic_fields"]) < 5:  # Limit examples
                            analysis["problematic_fields"].append({
                                "row": row_num,
                                "field": field_num,
                                "content_preview": field[:100] + "..." if len(field) > 100 else field,
                                "line_count": field_lines
                            })
                
                if row_has_issues:
                    analysis["affected_rows"] += 1
        
        return analysis
        
    except Exception as e:
        return {"error": f"Error analyzing file: {str(e)}"}

def main():
    """Main function to handle command line arguments and execute the fix."""
    parser = argparse.ArgumentParser(description='Fix line break issues in CSV files')
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('-o', '--output', help='Output CSV file path (default: input_file.fixed.csv)')
    parser.add_argument('-d', '--delimiter', default=',', help='CSV delimiter (default: comma)')
    parser.add_argument('-e', '--encoding', default='utf-8', help='File encoding (default: utf-8)')
    parser.add_argument('-r', '--replace-with', default=' ', help='Replace line breaks with (default: space)')
    parser.add_argument('-a', '--analyze', action='store_true', help='Analyze file for issues before fixing')
    parser.add_argument('--dry-run', action='store_true', help='Analyze only, do not create fixed file')
    
    args = parser.parse_args()
    
    print(f"CSV Line Break Fixer")
    print(f"Input file: {args.input_file}")
    
    # Analyze the file first if requested
    if args.analyze or args.dry_run:
        print("\nAnalyzing CSV file for line break issues...")
        analysis = analyze_csv_issues(args.input_file, args.encoding)
        
        if "error" in analysis:
            print(f"Analysis failed: {analysis['error']}")
            sys.exit(1)
        
        print(f"\nAnalysis Results:")
        print(f"- Total rows: {analysis['total_rows']}")
        print(f"- Rows with line break issues: {analysis['affected_rows']}")
        print(f"- Fields with line breaks: {analysis['fields_with_line_breaks']}")
        print(f"- Maximum lines in a single field: {analysis['max_field_lines']}")
        
        if analysis['problematic_fields']:
            print(f"\nExamples of problematic fields:")
            for i, field in enumerate(analysis['problematic_fields'], 1):
                print(f"  {i}. Row {field['row']}, Field {field['field']} ({field['line_count']} lines):")
                print(f"     Preview: {repr(field['content_preview'])}")
        
        if args.dry_run:
            print("\nDry run completed. No files were modified.")
            sys.exit(0)
    
    # Fix the file
    print(f"\nFixing line breaks in CSV file...")
    success = fix_csv_line_breaks(
        args.input_file, 
        args.output, 
        args.delimiter, 
        args.encoding, 
        args.replace_with
    )
    
    if success:
        print("✅ CSV line break fix completed successfully!")
        sys.exit(0)
    else:
        print("❌ CSV line break fix failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
