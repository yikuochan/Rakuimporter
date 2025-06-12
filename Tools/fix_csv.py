#!/usr/bin/env python3
"""
Script to fix CSV files with line breaks within fields.
This script reads a CSV file with line breaks in quoted fields,
replaces those line breaks with spaces, and outputs a cleaned CSV file.
"""

import csv
import sys
import os

def fix_csv_line_breaks(input_file, output_file, replacement=' '):
    """
    Fix CSV file by replacing line breaks within fields with the specified replacement character.
    
    Args:
        input_file (str): Path to the input CSV file
        output_file (str): Path to the output CSV file
        replacement (str): Character to replace line breaks with (default: space)
    """
    try:
        # Open the input file with proper newline handling
        with open(input_file, 'r', encoding='utf-8', newline='') as infile:
            # Create a CSV reader that can handle quoted fields with line breaks
            reader = csv.reader(infile, quotechar='"', delimiter=',', quoting=csv.QUOTE_MINIMAL)
            
            # Open the output file
            with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.writer(outfile, quotechar='"', delimiter=',', quoting=csv.QUOTE_MINIMAL)
                
                # Process each row
                for row in reader:
                    # Replace line breaks within each field
                    cleaned_row = [field.replace('\n', replacement).replace('\r', '') for field in row]
                    writer.writerow(cleaned_row)
                    
        print(f"Successfully processed {input_file} and saved cleaned data to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return False

def main():
    """Main function to handle command line arguments and execute the CSV fix."""
    if len(sys.argv) < 2:
        print("Usage: python fix_csv.py <input_csv_file> [output_csv_file] [replacement_char]")
        print("Example: python fix_csv.py input.csv output.csv '|'")
        return
    
    input_file = sys.argv[1]
    
    # Default output file name if not provided
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}-fixed.csv"
    
    # Default replacement character if not provided
    replacement = ' '
    if len(sys.argv) >= 4:
        replacement = sys.argv[3]
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return
    
    # Process the file
    fix_csv_line_breaks(input_file, output_file, replacement)

if __name__ == "__main__":
    main()
