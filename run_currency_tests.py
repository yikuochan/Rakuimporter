#!/usr/bin/env python3
"""
Run Currency Transformation Tests

This script runs all the tests related to currency transformations:
1. Unit tests for the transform_currency_code function
2. Verification of currency transformations in the JSON file

Usage:
    python run_currency_tests.py [input_json_file]

Example:
    python run_currency_tests.py Raku-export-1.json
"""

import argparse
import os
import subprocess
import sys
import time


def run_unit_tests():
    """Run the unit tests for currency transformation."""
    print("\n" + "="*80)
    print("Running unit tests for currency transformation...")
    print("="*80)
    
    # Get the current directory
    current_dir = os.getcwd()
    
    # Run the test from the current directory to maintain correct relative paths
    result = subprocess.run(
        ["python", "unittest/test_currency_transformation.py"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    if result.returncode != 0:
        print("Unit tests failed!")
        return False
    
    print("Unit tests passed successfully!")
    return True


def run_verification(input_file):
    """Run the verification script on the input file."""
    print("\n" + "="*80)
    print(f"Running currency transformation verification on {input_file}...")
    print("="*80)
    
    result = subprocess.run(
        ["python", "verify_currency_transformations.py", input_file],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    if result.returncode != 0:
        print("Verification failed!")
        return False
    
    print("Verification completed successfully!")
    return True


def main():
    """Main function to run all currency transformation tests."""
    parser = argparse.ArgumentParser(description='Run all currency transformation tests')
    parser.add_argument('input_file', nargs='?', default="Raku-export-1.json", help='Input JSON file path')
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    # Run unit tests
    if not run_unit_tests():
        sys.exit(1)
    
    # Run verification
    if not run_verification(args.input_file):
        sys.exit(1)
    
    # Print summary
    print("\n" + "="*80)
    print("All currency transformation tests passed successfully!")
    print("="*80)
    
    # Print report file location
    report_file = "currency_modification_report.md"
    if os.path.exists(report_file):
        print(f"\nCurrency modification report generated: {report_file}")
    
    # Print transformed file location
    base_name, ext = os.path.splitext(args.input_file)
    transformed_file = f"{base_name}.transformed{ext}"
    if os.path.exists(transformed_file):
        print(f"Transformed JSON file generated: {transformed_file}")


if __name__ == "__main__":
    main()
