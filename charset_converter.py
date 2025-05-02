#!/usr/bin/env python3
"""
charset_converter.py - Convert files from unknown-8bit charset to UTF-8

This script is designed to convert CSV files exported by the Japan team
with charset=unknown-8bit to charset=utf-8 for proper processing.

Usage:
    python charset_converter.py input_file [output_file]
    
    If output_file is not specified, it will create a file with the same name
    as input_file but with "_utf8" appended before the extension.
"""

import os
import sys
import argparse
import chardet
from pathlib import Path

def detect_encoding(file_path):
    """
    Detect the encoding of a file using chardet
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Detected encoding
    """
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
    
    # If still not confident, try some common Japanese encodings
    if confidence < 0.7:
        common_jp_encodings = ['shift_jis', 'euc_jp', 'iso-2022-jp', 'cp932']
        print("Low confidence. Will try common Japanese encodings during conversion.")
        return common_jp_encodings
    
    return [encoding]

def convert_file(input_file, output_file, encodings_to_try):
    """
    Convert a file from the detected encoding to UTF-8
    
    Args:
        input_file (str): Path to the input file
        output_file (str): Path to the output file
        encodings_to_try (list): List of encodings to try
        
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    for encoding in encodings_to_try:
        try:
            print(f"Trying to read with encoding: {encoding}")
            with open(input_file, 'r', encoding=encoding, errors='replace') as f_in:
                content = f_in.read()
                
            with open(output_file, 'w', encoding='utf-8') as f_out:
                f_out.write(content)
                
            print(f"Successfully converted {input_file} from {encoding} to UTF-8")
            print(f"Output saved to {output_file}")
            return True
        except UnicodeError as e:
            print(f"Failed to convert using {encoding}: {e}")
    
    print(f"Failed to convert {input_file} to UTF-8 after trying all encodings")
    return False

def main():
    parser = argparse.ArgumentParser(description='Convert files from unknown-8bit charset to UTF-8')
    parser.add_argument('input_file', help='Path to the input file')
    parser.add_argument('output_file', nargs='?', help='Path to the output file (optional)')
    
    args = parser.parse_args()
    
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
    
    # Detect encoding
    encodings_to_try = detect_encoding(input_file)
    
    # Convert file
    success = convert_file(input_file, output_file, encodings_to_try)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()