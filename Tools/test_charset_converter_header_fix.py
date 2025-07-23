#!/usr/bin/env python3
"""
Test script to verify that the charset converter header fix works correctly.
This script tests the charset converter with VCT files to ensure proper header structure.
"""

import os
import sys
import subprocess
import tempfile
import csv

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_charset_converter_header_fix():
    """Test that the charset converter produces the correct header structure."""
    
    print("Testing charset converter header fix...")
    
    # Expected header structure for VCT CSV template (2 header lines, 21 columns each)
    expected_header_line_1 = [
        "勘定奉行：伝票区切", "G/L Account", "仕訳日", "申請日", "仕訳データ生成日", "伝票No.", 
        "借方：勘定科目：会計連携項目", "借方：補助科目：会計連携項目", "", "", "換算前額", "単位", 
        "借方：負担部門：会計連携項目", "申請者CD/支払先CD", "支払先CD", "摘要", "フリー２(明細)", 
        "Receipt/Invoice Note(明細)", "Receipt/Invoice No.(明細)", "借方：負担部門コード", "備考"
    ]
    
    expected_header_line_2 = [
        "", "Vendor", "仕訳日", "申請日", "仕訳データ生成日", "伝票No.", "", "", 
        "貸方：勘定科目：会計連携項目", "貸方：補助科目：会計連携項目", "換算前額", "単位", 
        "借方：負担部門：会計連携項目", "申請者CD/支払先CD", "支払先CD", "摘要", "フリー２(明細)", 
        "Receipt/Invoice Note(明細)", "Receipt/Invoice No.(明細)", "借方：負担部門コード", "備考"
    ]
    
    # Test files to check
    test_files = [
        "examples/0623/Raku export-VCT PR.csv",
        "examples/0721/VCT-0721.csv"  # If it exists
    ]
    
    results = []
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            print(f"Skipping {test_file} - file not found")
            continue
            
        print(f"\nTesting {test_file}...")
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.utf8.csv', delete=False) as temp_file:
            temp_output = temp_file.name
        
        try:
            # Run charset converter
            cmd = [
                sys.executable, 
                "core/charset_converter.py", 
                test_file, 
                temp_output, 
                "--japanese"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
            
            if result.returncode != 0:
                print(f"❌ Charset converter failed for {test_file}")
                print(f"Error: {result.stderr}")
                results.append(False)
                continue
            
            # Read the converted file and check both header lines
            with open(temp_output, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                actual_header_line_1 = next(reader)
                actual_header_line_2 = next(reader)
            
            # Compare first header line
            if len(actual_header_line_1) != len(expected_header_line_1):
                print(f"❌ Header line 1 count mismatch for {test_file}")
                print(f"Expected {len(expected_header_line_1)} columns, got {len(actual_header_line_1)}")
                print(f"Expected: {expected_header_line_1}")
                print(f"Actual:   {actual_header_line_1}")
                results.append(False)
                continue
            
            # Compare second header line
            if len(actual_header_line_2) != len(expected_header_line_2):
                print(f"❌ Header line 2 count mismatch for {test_file}")
                print(f"Expected {len(expected_header_line_2)} columns, got {len(actual_header_line_2)}")
                print(f"Expected: {expected_header_line_2}")
                print(f"Actual:   {actual_header_line_2}")
                results.append(False)
                continue
            
            # Check each header in line 1
            headers_match = True
            for i, (expected, actual) in enumerate(zip(expected_header_line_1, actual_header_line_1)):
                if expected != actual:
                    print(f"❌ Header line 1 mismatch at position {i} for {test_file}")
                    print(f"Expected: '{expected}'")
                    print(f"Actual:   '{actual}'")
                    headers_match = False
            
            # Check each header in line 2
            for i, (expected, actual) in enumerate(zip(expected_header_line_2, actual_header_line_2)):
                if expected != actual:
                    print(f"❌ Header line 2 mismatch at position {i} for {test_file}")
                    print(f"Expected: '{expected}'")
                    print(f"Actual:   '{actual}'")
                    headers_match = False
            
            if headers_match:
                print(f"✅ Both header lines match correctly for {test_file}")
                results.append(True)
            else:
                results.append(False)
                
        except Exception as e:
            print(f"❌ Error testing {test_file}: {str(e)}")
            results.append(False)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_output):
                os.unlink(temp_output)
    
    # Summary
    print(f"\n{'='*50}")
    print("CHARSET CONVERTER HEADER FIX TEST SUMMARY")
    print(f"{'='*50}")
    
    if all(results):
        print("✅ All tests passed! Header structure is now consistent.")
        return True
    else:
        print("❌ Some tests failed. Header consistency issues remain.")
        return False

def test_specific_file_conversion():
    """Test conversion of the specific file mentioned in the issue."""
    
    print("\nTesting specific file conversion...")
    
    test_file = "examples/0623/Raku export-VCT PR.csv"
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found")
        return False
    
    # Create output file
    output_file = "examples/0623/test_header_fix_verification.utf8.csv"
    
    try:
        # Run charset converter
        cmd = [
            sys.executable, 
            "core/charset_converter.py", 
            test_file, 
            output_file, 
            "--japanese"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        if result.returncode != 0:
            print(f"❌ Charset converter failed")
            print(f"Error: {result.stderr}")
            return False
        
        # Read and verify the output
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            print("❌ Output file has insufficient content")
            return False
        
        # Check header line
        header_line = lines[0].strip()
        header_columns = header_line.split(',')
        
        print(f"✅ Conversion successful")
        print(f"Header column count: {len(header_columns)}")
        print(f"First few columns: {header_columns[:5]}")
        print(f"Output saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during conversion: {str(e)}")
        return False

if __name__ == "__main__":
    print("Charset Converter Header Fix Test")
    print("=" * 50)
    
    # Test 1: Header structure consistency
    test1_passed = test_charset_converter_header_fix()
    
    # Test 2: Specific file conversion
    test2_passed = test_specific_file_conversion()
    
    print(f"\n{'='*50}")
    print("FINAL RESULTS")
    print(f"{'='*50}")
    print(f"Header structure test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"File conversion test:  {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The charset converter header fix is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the issues above.")
        sys.exit(1)
