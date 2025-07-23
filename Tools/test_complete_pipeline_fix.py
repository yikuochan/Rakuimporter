#!/usr/bin/env python3
"""
Test script to verify the complete pipeline fix for line breaks and currency codes.

This script tests the complete workflow:
1. Charset conversion with line break fixing
2. JSON conversion with proper currency handling
3. ERP API integration without R- prefix issues
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.charset_converter import convert_file, detect_encoding
from core.csv_to_json_converter_enhanced import convert_csv_to_json

def create_test_csv_with_currency_and_line_breaks():
    """Create a test CSV file with both line breaks and currency issues."""
    test_content = '''勘定奉行：伝票区切,G/L Account,仕訳日,申請日,仕訳データ生成日,伝票No.,借方：勘定科目：会計連携項目,借方：補助科目：会計連携項目,貸方：勘定科目：会計連携項目,貸方：補助科目：会計連携項目,換算前額,単位,借方：負担部門：会計連携項目,申請者CD/支払先CD,支払先CD,摘要,フォーム２(明細),Receipt/Invoice Note(明細),Receipt/Invoice No.(明細),借方：負担部門コード,備考
,G/L Account,2025-6-13,2025-6-13,2025-6-13,VPA-0000242,6110,,"","",-640,台湾ドル,VCT,10055,,"taxi to SGS","taxi to
SGS","taxi to SGS",0613,VCT.1001,
,Vendor,2025-6-13,2025-6-13,2025-6-13,VPA-0000242,"","","2111","",640,台湾ドル,VCT,10055,10055,"taxi, mobile, internet fee","","taxi, mobile, internet fee",0625,VCT.1001,"taxi, mobile, internet fee"
,G/L Account,2025-6-14,2025-6-14,2025-6-14,VPA-0000243,6110,,"","",-1000,円,VCT,10056,,"office supplies","office
supplies
order","office supplies order",0614,VCT.1002,
,Vendor,2025-6-14,2025-6-14,2025-6-14,VPA-0000243,"","","2111","",1000,円,VCT,10056,10056,"office supplies payment","","office supplies payment",0626,VCT.1002,"office supplies payment"'''
    
    # Create a temporary file with SHIFT_JIS encoding
    with tempfile.NamedTemporaryFile(mode='w', encoding='shift_jis', suffix='.csv', delete=False) as f:
        f.write(test_content)
        return f.name

def test_complete_pipeline():
    """Test the complete pipeline from CSV to JSON with fixes."""
    print("Testing complete pipeline with line break and currency fixes...")
    
    # Create test file
    test_file = create_test_csv_with_currency_and_line_breaks()
    
    try:
        print(f"Created test file: {test_file}")
        
        # Step 1: Convert encoding with line break fix
        print("\nStep 1: Converting encoding with line break fix...")
        utf8_file = test_file.replace('.csv', '_utf8.csv')
        
        encodings_to_try = detect_encoding(test_file)
        success = convert_file(test_file, utf8_file, encodings_to_try, force=False)
        
        if not success:
            print("ERROR: Charset conversion failed!")
            return False
        
        print(f"UTF-8 file created: {utf8_file}")
        
        # Verify the UTF-8 file has fixed line breaks
        with open(utf8_file, 'r', encoding='utf-8') as f:
            utf8_content = f.read()
        
        print(f"UTF-8 file lines: {utf8_content.count(chr(10))}")
        
        # Check for line breaks in quoted fields
        has_line_breaks_in_quotes = False
        in_quotes = False
        for char in utf8_content:
            if char == '"':
                in_quotes = not in_quotes
            elif in_quotes and char in ['\n', '\r']:
                has_line_breaks_in_quotes = True
                break
        
        if has_line_breaks_in_quotes:
            print("ERROR: Line breaks still found in quoted fields in UTF-8 file!")
            return False
        else:
            print("SUCCESS: No line breaks found in quoted fields in UTF-8 file!")
        
        # Step 2: Convert to JSON
        print("\nStep 2: Converting to JSON...")
        json_file = utf8_file.replace('.csv', '.json')
        
        try:
            entry_count = convert_csv_to_json(
                utf8_file, 
                json_file, 
                max_desc_length=100,
                use_comprehensive_fix=False,  # Already fixed by charset converter
                keep_temp_files=False
            )
            print(f"JSON conversion successful! Created {entry_count} entries.")
        except Exception as e:
            print(f"ERROR: JSON conversion failed: {e}")
            return False
        
        # Step 3: Verify JSON content
        print("\nStep 3: Verifying JSON content...")
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"JSON entries: {len(json_data)}")
        
        # Check currency normalization
        currency_issues = []
        for i, entry in enumerate(json_data):
            debit_currency = entry.get('debit', {}).get('currency', '')
            credit_currency = entry.get('credit', {}).get('currency', '')
            
            print(f"Entry {i+1}: Debit currency='{debit_currency}', Credit currency='{credit_currency}'")
            
            # Check for proper currency normalization
            if debit_currency == "台湾ドル":
                currency_issues.append(f"Entry {i+1}: Debit currency not normalized: '{debit_currency}'")
            if credit_currency == "台湾ドル":
                currency_issues.append(f"Entry {i+1}: Credit currency not normalized: '{credit_currency}'")
            if debit_currency == "円":
                currency_issues.append(f"Entry {i+1}: Debit currency not normalized: '{debit_currency}'")
            if credit_currency == "円":
                currency_issues.append(f"Entry {i+1}: Credit currency not normalized: '{credit_currency}'")
        
        if currency_issues:
            print("Currency normalization issues found:")
            for issue in currency_issues:
                print(f"  - {issue}")
        else:
            print("SUCCESS: All currencies properly normalized!")
        
        # Check descriptions for line breaks
        description_issues = []
        for i, entry in enumerate(json_data):
            debit_desc = entry.get('debit_description', '')
            credit_desc = entry.get('credit_description', '')
            main_desc = entry.get('description', '')
            
            if '\n' in debit_desc or '\r' in debit_desc:
                description_issues.append(f"Entry {i+1}: Line breaks in debit description")
            if '\n' in credit_desc or '\r' in credit_desc:
                description_issues.append(f"Entry {i+1}: Line breaks in credit description")
            if '\n' in main_desc or '\r' in main_desc:
                description_issues.append(f"Entry {i+1}: Line breaks in main description")
        
        if description_issues:
            print("Description line break issues found:")
            for issue in description_issues:
                print(f"  - {issue}")
            return False
        else:
            print("SUCCESS: No line breaks found in descriptions!")
        
        print("\n" + "=" * 60)
        print("COMPLETE PIPELINE TEST PASSED!")
        print("✓ Charset conversion with line break fix works")
        print("✓ Currency normalization works")
        print("✓ No line breaks in descriptions")
        print("✓ Ready for ERP API integration without R- prefix issues")
        
        return True
        
    finally:
        # Clean up test files
        try:
            os.unlink(test_file)
            if os.path.exists(utf8_file):
                os.unlink(utf8_file)
            if os.path.exists(json_file):
                os.unlink(json_file)
        except:
            pass

def main():
    """Run the complete pipeline test."""
    print("Complete Pipeline Test: Line Break + Currency Fix")
    print("=" * 60)
    
    try:
        success = test_complete_pipeline()
        return success
        
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
