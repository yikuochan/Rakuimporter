#!/usr/bin/env python3
"""
charset_converter.py - Convert files from various charsets to UTF-8

This script is designed to convert files with various encodings (such as
unknown-8bit, Windows-1254, SHIFT_JIS, etc.) to UTF-8 for proper processing.

Usage:
    python charset_converter.py input_file [output_file] [options]
    
    If output_file is not specified, it will create a file with the same name
    as input_file but with "_utf8" appended before the extension.

Options:
    -e, --encoding ENCODING  Source encoding to try first
    -f, --force              Force conversion even if validation fails
    --japanese               Optimize for Japanese text (try Japanese encodings first)
    --list-encodings         List all available encodings and exit
"""

import os
import sys
import argparse
import chardet
from pathlib import Path

def detect_encoding(file_path, user_encoding=None):
    """
    Detect the encoding of a file using chardet or use user-specified encoding
    
    Args:
        file_path (str): Path to the file
        user_encoding (str, optional): User-specified encoding to try first
        
    Returns:
        list: List of encodings to try
    """
    encodings_to_try = []
    
    # If user specified an encoding, add it first
    if user_encoding:
        print(f"User specified encoding: {user_encoding}")
        encodings_to_try.append(user_encoding)
    
    # Read a sample of the file to detect encoding
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # Read first 10000 bytes for detection
    
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    confidence = result['confidence']
    
    print(f"Detected encoding: {encoding} with confidence: {confidence:.2%}")
    
    # If confidence is low or encoding is None, try with more data
    if confidence < 0.7 or encoding is None:
        with open(file_path, 'rb') as f:
            raw_data = f.read()  # Read the entire file
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
        print(f"Re-detected encoding: {encoding} with confidence: {confidence:.2%}")
    
    # Add detected encoding if not already in the list
    if encoding and encoding not in encodings_to_try:
        encodings_to_try.append(encoding)
    
    # If still not confident or no encoding detected, add common encodings
    if confidence < 0.7 or not encoding:
        # Common Japanese encodings
        common_jp_encodings = ['shift_jis', 'euc_jp', 'iso-2022-jp', 'cp932']
        
        # Common Turkish and other encodings
        common_other_encodings = ['windows-1254', 'iso-8859-9', 'windows-1252', 'iso-8859-1']
        
        # Additional common encodings
        additional_encodings = ['utf-16', 'utf-16-le', 'utf-16-be', 'gb2312', 'gbk', 'big5']
        
        print("Low confidence. Will try common encodings during conversion.")
        
        # Add all encodings that aren't already in the list
        for enc in common_jp_encodings + common_other_encodings + additional_encodings:
            if enc not in encodings_to_try:
                encodings_to_try.append(enc)
    
    return encodings_to_try

def is_valid_conversion(text, encoding):
    """
    Check if the conversion seems valid by looking for common signs of encoding issues
    
    Args:
        text (str): Converted text
        encoding (str): Encoding used for conversion
        
    Returns:
        bool: True if the conversion seems valid, False otherwise
    """
    # Count the number of replacement characters (�) which indicate conversion issues
    replacement_char_count = text.count('�')
    
    # Count the number of characters that are likely encoding artifacts
    encoding_artifact_chars = '�����������������������������������������������������������'
    artifact_count = sum(text.count(c) for c in encoding_artifact_chars)
    
    # Calculate the percentage of problematic characters
    total_chars = len(text) if len(text) > 0 else 1
    problem_percentage = (replacement_char_count + artifact_count) / total_chars * 100
    
    # For Japanese encodings, check for presence of Japanese characters
    if encoding.lower() in ['shift_jis', 'euc_jp', 'iso-2022-jp', 'cp932']:
        # Check if there are Japanese characters in the text
        # This is a simple heuristic - if we have Japanese encodings but no Japanese-looking text,
        # it might be a wrong encoding
        has_japanese_chars = any(ord(c) > 0x3000 for c in text[:1000])
        if not has_japanese_chars:
            print(f"Warning: No Japanese characters found when using {encoding}")
            return False
    
    # If more than 10% of characters are problematic, consider the conversion invalid
    if problem_percentage > 10:
        print(f"Warning: Conversion quality is poor ({problem_percentage:.1f}% problematic characters)")
        return False
    
    return True

def replace_csv_headers_if_needed(content, quality_score):
    """
    Replace CSV headers with proper Japanese headers if conversion quality is poor.
    VCT CSV template has 2 header lines that need to be replaced.
    
    Args:
        content (str): CSV content
        quality_score (float): Quality score of the conversion
        
    Returns:
        str: Content with replaced headers if needed
    """
    # Always check for corrupted headers, regardless of quality score
    # Quality score might be 100% but headers can still be corrupted
    
    lines = content.split('\n')
    if not lines:
        return content
    
    # Check if this is a CSV file by looking at the first line
    first_line = lines[0].strip()
    if ',' not in first_line:
        return content
    
    # Define the correct Japanese headers for VCT CSV template (2 header lines)
    # Header line 1: Main headers
    header_line_1 = [
        "勘定奉行：伝票区切", "G/L Account", "仕訳日", "申請日", "仕訳データ生成日", "伝票No.", 
        "借方：勘定科目：会計連携項目", "借方：補助科目：会計連携項目", "", "", "換算前額", "単位", 
        "借方：負担部門：会計連携項目", "申請者CD/支払先CD", "支払先CD", "摘要", "フリー２(明細)", 
        "Receipt/Invoice Note(明細)", "Receipt/Invoice No.(明細)", "借方：負担部門コード", "備考"
    ]
    
    # Header line 2: Secondary headers (for vendor entries)
    header_line_2 = [
        "", "Vendor", "仕訳日", "申請日", "仕訳データ生成日", "伝票No.", "", "", 
        "貸方：勘定科目：会計連携項目", "貸方：補助科目：会計連携項目", "換算前額", "単位", 
        "借方：負担部門：会計連携項目", "申請者CD/支払先CD", "支払先CD", "摘要", "フリー２(明細)", 
        "Receipt/Invoice Note(明細)", "Receipt/Invoice No.(明細)", "借方：負担部門コード", "備考"
    ]
    
    # Check if we need to replace headers (look for corrupted characters or non-Japanese headers)
    needs_replacement = False
    
    # Check for corrupted UTF-8 characters in headers
    corrupted_chars = ['ä', 'ç', 'å', 'è', 'æ', 'ã', 'ª', '¥', '¨', '§', '©', '¡', '¿', '°', 'ň', 'ś', 'Ř', 'ű', 'Ú', 'ď', 'v', 'A', 'g', 'Ú', 'ˇ', 'Z', 'O', 'z', 'P', 'Ę', 'S', 'ĺ', 'F', '\\', 'ż', 'Ň', 'C', 'D', '/', 'x', 'Ľ', 'ć', 'E', 'v', 't', '[', 'Q', '(', 'ž', '×', ')', 'R', '[', 'h', 'ő', 'ł']
    if any(char in first_line for char in corrupted_chars):
        needs_replacement = True
        print(f"Detected corrupted headers due to encoding issues (quality: {quality_score:.1f}%)")
    
    # Check the second line too if it exists
    if len(lines) > 1:
        second_line = lines[1].strip()
        if any(char in second_line for char in corrupted_chars):
            needs_replacement = True
            print(f"Detected corrupted headers in second line due to encoding issues")
    
    # Check if headers are in English or other non-Japanese format
    english_indicators = ['voucher', 'document', 'date', 'account', 'amount', 'currency', 'department']
    if any(indicator in first_line.lower() for indicator in english_indicators):
        needs_replacement = True
        print(f"Detected English headers, replacing with Japanese format")
    
    if needs_replacement:
        print("Replacing CSV headers with correct Japanese format (2 header lines for VCT template)")
        
        # Replace the first two lines with correct Japanese headers
        new_lines = [
            ','.join(header_line_1),  # First header line
            ','.join(header_line_2)   # Second header line
        ]
        
        # Keep the rest of the content (data rows)
        if len(lines) > 2:
            # Keep data from line 3 onwards
            new_lines.extend(lines[2:])
        elif len(lines) > 1:
            # If there's only one data line after headers, keep it
            new_lines.extend(lines[1:])
        
        return '\n'.join(new_lines)
    
    return content

def convert_file(input_file, output_file, encodings_to_try, force=False):
    """
    Convert a file from the detected encoding to UTF-8
    
    Args:
        input_file (str): Path to the input file
        output_file (str): Path to the output file
        encodings_to_try (list): List of encodings to try
        force (bool): Force conversion even if validation fails
        
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    # If force is True and we have a user-specified encoding (first in the list),
    # only try that encoding
    if force and encodings_to_try:
        forced_encoding = encodings_to_try[0]
        try:
            print(f"Forcing conversion with encoding: {forced_encoding}")
            with open(input_file, 'r', encoding=forced_encoding, errors='replace') as f_in:
                content = f_in.read()
            
            # Show a sample of the converted text (first 100 characters)
            sample = content[:100].replace('\n', ' ')
            print(f"Sample of converted text: \"{sample}...\"")
            
            # Calculate a quality score based on problematic characters
            replacement_char_count = content.count('�')
            artifact_chars = '�����������������������������������������������������������'
            artifact_count = sum(content.count(c) for c in artifact_chars)
            total_chars = len(content) if len(content) > 0 else 1
            quality_score = 100 - ((replacement_char_count + artifact_count) / total_chars * 100)
            
            print(f"Conversion quality score: {quality_score:.1f}%")
            print(f"Forcing conversion regardless of quality score due to --force option")
            
            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.write(content)
            
            print(f"Successfully converted {input_file} from {forced_encoding} to UTF-8")
            print(f"Output saved to {output_file}")
            return True
        except UnicodeError as e:
            print(f"Failed to convert using {forced_encoding}: {e}")
            print(f"Even with --force, the encoding {forced_encoding} could not be used due to errors.")
            print(f"Falling back to automatic detection.")
        except Exception as e:
            print(f"Error during conversion with {forced_encoding}: {str(e)}")
            print(f"Falling back to automatic detection.")
    
    # If not forcing or if forcing failed, proceed with normal detection
    best_encoding = None
    best_content = None
    best_quality_score = -1
    
    for encoding in encodings_to_try:
        try:
            print(f"Trying to read with encoding: {encoding}")
            with open(input_file, 'r', encoding=encoding, errors='replace') as f_in:
                content = f_in.read()
            
            # Show a sample of the converted text (first 100 characters)
            sample = content[:100].replace('\n', ' ')
            print(f"Sample of converted text: \"{sample}...\"")
            
            # Check if the conversion seems valid
            is_valid = is_valid_conversion(content, encoding)
            
            # Calculate a quality score based on problematic characters
            replacement_char_count = content.count('�')
            artifact_chars = '�����������������������������������������������������������'
            artifact_count = sum(content.count(c) for c in artifact_chars)
            total_chars = len(content) if len(content) > 0 else 1
            quality_score = 100 - ((replacement_char_count + artifact_count) / total_chars * 100)
            
            print(f"Conversion quality score: {quality_score:.1f}%")
            
            # If this is a valid conversion and it's better than what we've seen so far
            if is_valid and quality_score > best_quality_score:
                best_encoding = encoding
                best_content = content
                best_quality_score = quality_score
                
                # If we have a very good conversion, we can stop here
                if quality_score > 95:
                    break
            
        except UnicodeError as e:
            print(f"Failed to convert using {encoding}: {e}")
        except Exception as e:
            print(f"Error during conversion with {encoding}: {str(e)}")
    
    # If we found a usable encoding, write the output file
    if best_encoding:
        # Apply header replacement if needed for CSV files
        final_content = replace_csv_headers_if_needed(best_content, best_quality_score)
        
        with open(output_file, 'w', encoding='utf-8') as f_out:
            f_out.write(final_content)
        
        print(f"Successfully converted {input_file} from {best_encoding} to UTF-8")
        print(f"Output saved to {output_file}")
        return True
    else:
        print(f"Failed to convert {input_file} to UTF-8 after trying all encodings")
        return False

def main():
    parser = argparse.ArgumentParser(description='Convert files from various charsets to UTF-8')
    parser.add_argument('input_file', nargs='?', help='Path to the input file')
    parser.add_argument('output_file', nargs='?', help='Path to the output file (optional)')
    parser.add_argument('-e', '--encoding', help='Source encoding to try first (optional)')
    parser.add_argument('-f', '--force', action='store_true', help='Force conversion even if validation fails')
    parser.add_argument('--list-encodings', action='store_true', help='List all available encodings and exit')
    parser.add_argument('--japanese', action='store_true', help='Optimize for Japanese text (try Japanese encodings first)')
    
    args = parser.parse_args()
    
    # If --list-encodings is specified, print all available encodings and exit
    if args.list_encodings:
        import encodings
        print("Available encodings:")
        for encoding in sorted(set(encodings.aliases.aliases.values())):
            print(f"  {encoding}")
        sys.exit(0)
    
    # Check if input file is provided
    if not args.input_file:
        parser.error("input_file is required unless --list-encodings is specified")
    
    input_file = args.input_file
    
    # If output file is not specified, create one with _utf8 appended
    if args.output_file:
        output_file = args.output_file
    else:
        input_path = Path(input_file)
        output_file = str(input_path.with_name(f"{input_path.stem}_utf8{input_path.suffix}"))
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)
    
    # Detect encoding, considering user-specified encoding if provided
    encodings_to_try = detect_encoding(input_file, args.encoding)
    
    # If --japanese is specified, prioritize Japanese encodings
    if args.japanese:
        # Move Japanese encodings to the front of the list
        jp_encodings = ['shift_jis', 'euc_jp', 'iso-2022-jp', 'cp932']
        # Remove them from the list if they're already there
        encodings_to_try = [e for e in encodings_to_try if e.lower() not in [je.lower() for je in jp_encodings]]
        # Add them to the front (after any user-specified encoding)
        if args.encoding:
            encodings_to_try = [args.encoding] + jp_encodings + [e for e in encodings_to_try if e != args.encoding]
        else:
            encodings_to_try = jp_encodings + encodings_to_try
    
    # Convert file
    success = convert_file(input_file, output_file, encodings_to_try, args.force)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
