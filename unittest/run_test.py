#!/usr/bin/env python3
"""
Simple script to run a specific test case for process_japan_exports.py
"""

import sys
import os
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.abspath('..'))

# Import the test module
from test_process_japan_exports import TestERPIntegration

if __name__ == '__main__':
    # Create a test suite with the tests we want to run
    suite = unittest.TestSuite()
    suite.addTest(TestERPIntegration('test_create_journal_line_debit_non_home_currency'))
    suite.addTest(TestERPIntegration('test_create_journal_line_debit_home_currency'))
    suite.addTest(TestERPIntegration('test_create_journal_line_credit_vendor'))
    
    # Run the test
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate status code
    sys.exit(not result.wasSuccessful())
