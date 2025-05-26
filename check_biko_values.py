#!/usr/bin/env python3
"""
Script to check the Remarks (備考) column values in the CSV file.
This will help us understand if there's a line break issue affecting the values.
"""

import csv
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("biko_checker")

def check_biko_values(csv_file_path):
    """Check the Remarks (備考) column values in the CSV file"""
    try:
        # Open the CSV file with proper encoding
        with open(csv_file_path, 'r', encoding='utf-8', newline='') as file:
            # Create a CSV reader
            reader = csv.reader(file)
            
            # Read the header row to find the index of the Remarks (備考) column
            header = next(reader)
            biko_index = header.index('Remarks') if 'Remarks' in header else (header.index('備考') if '備考' in header else -1)
            
            if biko_index == -1:
                logger.error("Could not find 'Remarks' or '備考' column in the CSV file")
                return
            
            logger.info(f"Found 'Remarks' (備考) column at index {biko_index}")
            
            # Skip the second header row
            next(reader)
            
            # Read the data rows and check the 備考 column values
            row_count = 0
            non_empty_count = 0
            biko_values = []
            
            for row in reader:
                row_count += 1
                
                # Skip empty rows
                if not any(row):
                    continue
                
                # Check if the row has enough columns
                if len(row) > biko_index:
                    biko_value = row[biko_index]
                    
                    # Check if the Remarks (備考) value is not empty
                    if biko_value:
                        non_empty_count += 1
                        biko_values.append(biko_value)
                        
                        # Log the first 10 non-empty values
                        if non_empty_count <= 10:
                            logger.info(f"Row {row_count}: Remarks (備考) = '{biko_value}'")
            
            # Log summary
            logger.info(f"Total rows: {row_count}")
            logger.info(f"Rows with non-empty Remarks (備考) values: {non_empty_count}")
            logger.info(f"Percentage of rows with non-empty Remarks (備考) values: {non_empty_count / row_count * 100:.2f}%")
            
            # Check for unique values
            unique_values = set(biko_values)
            logger.info(f"Number of unique Remarks (備考) values: {len(unique_values)}")
            
            # Log the top 10 most common values
            from collections import Counter
            counter = Counter(biko_values)
            logger.info("Top 10 most common Remarks (備考) values:")
            for value, count in counter.most_common(10):
                logger.info(f"  '{value}': {count} occurrences")
            
    except Exception as e:
        logger.error(f"Error checking Remarks (備考) values: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        csv_file_path = sys.argv[1]
        logger.info(f"Checking Remarks (備考) values in: {csv_file_path}")
        check_biko_values(csv_file_path)
    else:
        logger.error("No CSV file provided. Usage: python check_biko_values.py <csv_file_path>")
