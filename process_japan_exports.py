#!/usr/bin/env python3
"""
process_japan_exports.py - Convert and process files from Japan team

This script automates the workflow of:
1. Converting files from unknown-8bit charset to UTF-8
2. Processing the converted files with csv_to_json_converter.py

Usage:
    python process_japan_exports.py file1.csv [file2.csv ...]
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def process_file(file_path):
    """
    Process a single file by:
    1. Converting it to UTF-8
    2. Processing the converted file with csv_to_json_converter.py
    
    Args:
        file_path (str): Path to the file to process
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    file_path = Path(file_path)
    
    # Check if file exists
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist.")
        return False
    
    # Step 1: Convert to UTF-8
    utf8_file_path = file_path.with_name(f"{file_path.stem}_utf8{file_path.suffix}")
    json_file_path = file_path.with_name(f"{file_path.stem}_journal_data.json")
    
    print(f"Converting {file_path} to UTF-8...")
    try:
        # Activate the virtual environment if it exists
        venv_activate = ""
        if os.path.exists("charset_converter_env"):
            if os.name == 'nt':  # Windows
                venv_activate = "charset_converter_env\\Scripts\\activate && "
            else:  # Unix/Linux/Mac
                venv_activate = "source charset_converter_env/bin/activate && "
        
        # Run charset_converter.py
        cmd = f"{venv_activate}python charset_converter.py \"{file_path}\""
        result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)
        print(result.stdout)
        
        if not utf8_file_path.exists():
            print(f"Error: Failed to create UTF-8 file '{utf8_file_path}'.")
            if result.stderr:
                print(f"Error details: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error converting file: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False
    
    # Step 2: Process with csv_to_json_converter.py
    print(f"Processing {utf8_file_path} to JSON...")
    try:
        cmd = f"python csv_to_json_converter.py -i \"{utf8_file_path}\" -o \"{json_file_path}\""
        result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)
        print(result.stdout)
        
        if not json_file_path.exists():
            print(f"Error: Failed to create JSON file '{json_file_path}'.")
            if result.stderr:
                print(f"Error details: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error processing file: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False
    
    print(f"Successfully processed {file_path} to {json_file_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Convert and process files from Japan team')
    parser.add_argument('files', nargs='+', help='CSV files to process')
    
    args = parser.parse_args()
    
    success_count = 0
    failure_count = 0
    
    for file_path in args.files:
        print(f"\nProcessing file: {file_path}")
        print("-" * 50)
        
        if process_file(file_path):
            success_count += 1
        else:
            failure_count += 1
        
        print("-" * 50)
    
    print(f"\nSummary: {success_count} files processed successfully, {failure_count} files failed.")
    
    if failure_count > 0:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())