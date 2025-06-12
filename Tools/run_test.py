#!/usr/bin/env python3
"""
Simple script to run the test_process_japan_exports.py test
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the test module
sys.path.append('unittest')
from test_process_japan_exports import TestERPIntegration

if __name__ == "__main__":
    # Create a test suite with just the test_create_journal_line_debit_vct_1342g test
    suite = unittest.TestSuite()
    suite.addTest(TestERPIntegration("test_create_journal_line_debit_vct_1342g"))
    
    # Run the test
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print the result
    if result.wasSuccessful():
        print("\nTest passed successfully!")
        sys.exit(0)
    else:
        print("\nTest failed!")
        sys.exit(1)
