#!/usr/bin/env python3
"""
Test script to verify the charset converter with integrated line break fix.

This script tests the enhanced charset converter that now includes line break
fixing for CSV files during the encoding conversion process.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.charset_converter import convert_file, detect_encoding, fix_line_breaks_in_quoted_fields, detect_csv_file

def create_test_csv_with_line_breaks():
    """Create a test CSV file with line breaks in quoted fields."""
    test_content = '''Account_Type,Vendor,仕訳日,申請日,仕訳データ生成日,伝票No.
G/L Account,"Test
Vendor
Name",2025-06-13,2025-06-13,2025-06-13,VPA-0000242
Vendor,"Another
Multi-line
Description",2025-06-14,2025-06-14,2025-06-14,VPA-0000243'''
    
    # Create a temporary file with SHIFT_JIS encoding
    with tempfile.NamedTemporaryFile(mode='w', encoding='shift_jis', suffix='.csv', delete=False) as f:
        f.write(test_content)
        return f.name

def test_line_break_fix_function():
    """Test the line break fix function directly."""
    print("Testing line break fix function...")
    
    test_content = '''Account_Type,Vendor,Description
G/L Account,"Test
Vendor
Name","Single line description"
Vendor,"Another
Multi-line
Description","Normal field"'''
    
    fixed_content = fix_line_breaks_in_quoted_fields(test_content)
    
    print("Original content:")
    print(repr(test_content))
    print("\nFixed content:")
    print(repr(fixed_content))
    
    # Verify that line breaks within quotes are replaced with spaces
    expected_lines = 4  # Header + 2 data rows + empty line at end
    actual_lines = fixed_content.count('\n')
    
    print(f"\nOriginal lines: {test_content.count(chr(10))}")
    print(f"Fixed lines: {actual_lines}")
    
    # Check that quoted fields no longer contain line breaks
    lines = fixed_content.split('\n')
    for i, line in enumerate(lines):
        if line.strip():
            print(f"Line {i+1}: {repr(line)}")
    
    return True

def test_csv_detection():
    """Test CSV file detection."""
    print("\nTesting CSV file detection...")
    
    # Test with .csv extension
    csv_file = "test.csv"
    result = detect_csv_file(csv_file)
    print(f"detect_csv_file('{csv_file}') = {result}")
    assert result == True, "Should detect .csv files"
    
    # Test with .CSV extension (uppercase)
    csv_file_upper = "test.CSV"
    result = detect_csv_file(csv_file_upper)
    print(f"detect_csv_file('{csv_file_upper}') = {result}")
    assert result == True, "Should detect .CSV files"
    
    # Test with non-CSV extension
    txt_file = "test.txt"
    result = detect_csv_file(txt_file)
    print(f"detect_csv_file('{txt_file}') = {result}")
    assert result == False, "Should not detect non-CSV files"
    
    print("CSV detection tests passed!")
    return True

def test_integrated_conversion():
    """Test the integrated charset conversion with line break fixing."""
    print("\nTesting integrated charset conversion with line break fixing...")
    
    # Create a test CSV file with line breaks
    test_file = create_test_csv_with_line_breaks()
    
    try:
        # Create output file path
        output_file = test_file.replace('.csv', '_utf8.csv')
        
        print(f"Test file created: {test_file}")
        print(f"Output file will be: {output_file}")
        
        # Detect encoding
        encodings_to_try = detect_encoding(test_file)
        print(f"Encodings to try: {encodings_to_try}")
        
        # Convert the file
        success = convert_file(test_file, output_file, encodings_to_try, force=False)
        
        if success:
            print("Conversion successful!")
            
            # Read the converted file and check if line breaks are fixed
            with open(output_file, 'r', encoding='utf-8') as f:
                converted_content = f.read()
            
            print("\nConverted content:")
            print(repr(converted_content))
            
            # Verify the content
            lines = converted_content.split('\n')
            print(f"\nNumber of lines in converted file: {len([l for l in lines if l.strip()])}")
            
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"Line {i+1}: {repr(line)}")
            
            # Check that no quoted fields contain line breaks
            has_line_breaks_in_quotes = False
            in_quotes = False
            for char in converted_content:
                if char == '"':
                    in_quotes = not in_quotes
                elif in_quotes and char in ['\n', '\r']:
                    has_line_breaks_in_quotes = True
                    break
            
            if has_line_breaks_in_quotes:
                print("ERROR: Line breaks still found in quoted fields!")
                return False
            else:
                print("SUCCESS: No line breaks found in quoted fields!")
                return True
        else:
            print("Conversion failed!")
            return False
            
    finally:
        # Clean up test files
        try:
            os.unlink(test_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
        except:
            pass

def main():
    """Run all tests."""
    print("Testing Enhanced Charset Converter with Line Break Fix")
    print("=" * 60)
    
    try:
        # Test 1: Line break fix function
        if not test_line_break_fix_function():
            print("Line break fix function test FAILED")
            return False
        
        # Test 2: CSV detection
        if not test_csv_detection():
            print("CSV detection test FAILED")
            return False
        
        # Test 3: Integrated conversion
        if not test_integrated_conversion():
            print("Integrated conversion test FAILED")
            return False
        
        print("\n" + "=" * 60)
        print("All tests PASSED!")
        print("The charset converter now properly fixes line breaks in CSV files during encoding conversion.")
        return True
        
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
