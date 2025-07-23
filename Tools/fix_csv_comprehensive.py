#!/usr/bin/env python3
"""
Comprehensive CSV Fixer

This script addresses both encoding and line break issues in CSV files.
It first converts the file to UTF-8 if needed, then fixes line break issues.
"""

import csv
import sys
import os
import argparse
import chardet
from pathlib import Path
from typing import List, Dict, Any

def detect_and_convert_encoding(input_file: str, temp_file: str = None) -> str:
    """
    Detect encoding and convert to UTF-8 if needed.
    
    Args:
        input_file: Path to the input file
        temp_file: Path for temporary UTF-8 file (optional)
        
    Returns:
        str: Path to UTF-8 file (either original if already UTF-8, or converted file)
    """
    # Generate temp filename if not provided
    if temp_file is None:
        base, ext = os.path.splitext(input_file)
        temp_file = f"{base}.temp_utf8{ext}"
    
    # First, detect the encoding
    with open(input_file, 'rb') as f:
        raw_data = f.read(10000)  # Read first 10KB for detection
    
    result = chardet.detect(raw_data)
    detected_encoding = result['encoding']
    confidence = result['confidence']
    
    print(f"Detected encoding: {detected_encoding} with confidence: {confidence:.2%}")
    
    # If confidence is low, try with more data
    if confidence < 0.7:
        with open(input_file, 'rb') as f:
            raw_data = f.read()  # Read entire file
        result = chardet.detect(raw_data)
        detected_encoding = result['encoding']
        confidence = result['confidence']
        print(f"Re-detected encoding: {detected_encoding} with confidence: {confidence:.2%}")
    
    # If already UTF-8, return original file
    if detected_encoding and detected_encoding.lower() in ['utf-8', 'ascii']:
        print("File is already in UTF-8 or ASCII encoding")
        return input_file
    
    # Try to convert to UTF-8
    encodings_to_try = []
    if detected_encoding:
        encodings_to_try.append(detected_encoding)
    
    # Add common encodings as fallback
    encodings_to_try.extend(['shift_jis', 'cp932', 'euc_jp', 'iso-2022-jp', 
                            'windows-1252', 'windows-1254', 'iso-8859-1', 'gb2312', 'big5'])
    
    for encoding in encodings_to_try:
        try:
            print(f"Trying to convert from {encoding} to UTF-8...")
            with open(input_file, 'r', encoding=encoding, errors='replace') as f_in:
                content = f_in.read()
            
            # Check quality of conversion
            replacement_chars = content.count('�')
            total_chars = len(content) if len(content) > 0 else 1
            quality = 100 - (replacement_chars / total_chars * 100)
            
            print(f"Conversion quality: {quality:.1f}%")
            
            if quality > 80:  # Accept if quality is good enough
                with open(temp_file, 'w', encoding='utf-8') as f_out:
                    f_out.write(content)
                print(f"Successfully converted to UTF-8: {temp_file}")
                return temp_file
                
        except Exception as e:
            print(f"Failed to convert using {encoding}: {e}")
            continue
    
    print("Warning: Could not convert to UTF-8 with good quality. Using original file.")
    return input_file

def fix_csv_structure(input_file: str, output_file: str, delimiter: str = ',') -> bool:
    """
    Fix CSV structure issues including line breaks and malformed headers.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output CSV file
        delimiter: CSV delimiter
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        rows = []
        header_fixed = False
        
        with open(input_file, 'r', encoding='utf-8', newline='') as infile:
            # Try to read as CSV first
            try:
                reader = csv.reader(infile, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, 1):
                    # Fix the first row (header) if it's malformed
                    if row_num == 1 and not header_fixed:
                        # Check if header looks malformed (too few fields or strange characters)
                        if len(row) < 10 or any('?' in field for field in row[:5]):
                            print("Detected malformed header, attempting to fix...")
                            # Create a proper header based on the pattern we see in the data
                            fixed_header = [
                                "Account_Type", "Vendor", "仕訳日", "申請日", "仕訳データ生成日", "伝票No.",
                                "借方：勘定科目：会計連携科目", "借方：補助科目：会計連携科目", 
                                "貸方：勘定科目：会計連携科目", "貸方：補助科目：会計連携科目",
                                "換算前額", "単位", "借方：負担部門：会計連携科目", "申請者CD/支払先CD", "支払先CD",
                                "摘要", "フォーム２(明細)", "Receipt/Invoice Note(明細)", 
                                "Receipt/Invoice No.(明細)", "借方：負担部門コード", "備考"
                            ]
                            rows.append(fixed_header)
                            header_fixed = True
                            print(f"Fixed header with {len(fixed_header)} fields")
                            continue
                    
                    # Process each field in the row to remove line breaks
                    fixed_row = []
                    for field in row:
                        # Replace line breaks with spaces and clean up
                        fixed_field = field.replace('\n', ' ').replace('\r', ' ')
                        # Clean up multiple spaces
                        fixed_field = ' '.join(fixed_field.split())
                        fixed_row.append(fixed_field)
                    
                    rows.append(fixed_row)
                    
                    if row_num % 100 == 0:
                        print(f"Processed {row_num} rows...")
                        
            except csv.Error as e:
                print(f"CSV parsing error: {e}")
                print("Attempting line-by-line processing...")
                
                # Fallback: process line by line
                infile.seek(0)
                lines = infile.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    # Remove line breaks and clean up
                    cleaned_line = line.replace('\n', ' ').replace('\r', ' ')
                    cleaned_line = ' '.join(cleaned_line.split())
                    
                    # Try to parse as CSV
                    try:
                        row = list(csv.reader([cleaned_line], delimiter=delimiter))[0]
                        rows.append(row)
                    except:
                        # If CSV parsing fails, just split by delimiter
                        row = cleaned_line.split(delimiter)
                        rows.append(row)
        
        print(f"Successfully processed {len(rows)} rows")
        
        # Write the fixed CSV
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            writer.writerows(rows)
        
        print(f"Fixed CSV written to '{output_file}'")
        
        # Verify the output
        with open(output_file, 'r', encoding='utf-8') as verify_file:
            verify_lines = verify_file.readlines()
            print(f"Verification: Output file has {len(verify_lines)} lines")
        
        return True
        
    except Exception as e:
        print(f"Error processing CSV file: {str(e)}")
        return False

def analyze_csv_issues(input_file: str) -> Dict[str, Any]:
    """
    Analyze CSV file for various issues.
    
    Args:
        input_file: Path to the CSV file to analyze
        
    Returns:
        Dict with analysis results
    """
    analysis = {
        "encoding_issues": False,
        "line_break_issues": 0,
        "total_lines": 0,
        "estimated_records": 0,
        "header_issues": False
    }
    
    try:
        # Check encoding
        with open(input_file, 'rb') as f:
            raw_data = f.read(1000)
        result = chardet.detect(raw_data)
        if result['encoding'] and result['encoding'].lower() not in ['utf-8', 'ascii']:
            analysis["encoding_issues"] = True
        
        # Count lines and analyze structure
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            analysis["total_lines"] = len(lines)
            
            # Count fields with line breaks
            line_break_count = 0
            for line in lines:
                if '\n' in line.strip() or '\r' in line.strip():
                    line_break_count += 1
            
            analysis["line_break_issues"] = line_break_count
            
            # Check header
            if lines:
                first_line = lines[0]
                if '?' in first_line or len(first_line.split(',')) < 10:
                    analysis["header_issues"] = True
        
        # Try to estimate actual records by parsing as CSV
        try:
            with open(input_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                analysis["estimated_records"] = sum(1 for _ in reader)
        except:
            analysis["estimated_records"] = analysis["total_lines"]
        
    except Exception as e:
        analysis["error"] = str(e)
    
    return analysis

def main():
    parser = argparse.ArgumentParser(description='Comprehensive CSV fixer for encoding and structure issues')
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('-o', '--output', help='Output CSV file path (default: input_file.fixed.csv)')
    parser.add_argument('-d', '--delimiter', default=',', help='CSV delimiter (default: comma)')
    parser.add_argument('-a', '--analyze', action='store_true', help='Analyze file issues before fixing')
    parser.add_argument('--keep-temp', action='store_true', help='Keep temporary UTF-8 file')
    
    args = parser.parse_args()
    
    input_file = args.input_file
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    
    # Generate output filename if not provided
    if args.output:
        output_file = args.output
    else:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}.fixed{ext}"
    
    print(f"Comprehensive CSV Fixer")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Analyze if requested
    if args.analyze:
        print("\nAnalyzing CSV file...")
        analysis = analyze_csv_issues(input_file)
        
        print(f"Analysis Results:")
        print(f"- Encoding issues: {'Yes' if analysis.get('encoding_issues') else 'No'}")
        print(f"- Total lines: {analysis.get('total_lines', 'Unknown')}")
        print(f"- Estimated records: {analysis.get('estimated_records', 'Unknown')}")
        print(f"- Line break issues: {analysis.get('line_break_issues', 0)}")
        print(f"- Header issues: {'Yes' if analysis.get('header_issues') else 'No'}")
    
    # Step 1: Handle encoding
    print("\nStep 1: Handling encoding...")
    utf8_file = detect_and_convert_encoding(input_file)
    
    # Step 2: Fix CSV structure
    print("\nStep 2: Fixing CSV structure...")
    success = fix_csv_structure(utf8_file, output_file, args.delimiter)
    
    # Clean up temporary file if created and not keeping it
    if utf8_file != input_file and not args.keep_temp:
        try:
            os.remove(utf8_file)
            print(f"Cleaned up temporary file: {utf8_file}")
        except:
            pass
    
    if success:
        print("\n✅ Comprehensive CSV fix completed successfully!")
        print(f"Fixed file: {output_file}")
    else:
        print("\n❌ CSV fix failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
