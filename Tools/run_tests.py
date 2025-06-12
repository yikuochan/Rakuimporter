#!/usr/bin/env python3
"""
Simple script to run specific tests for process_japan_exports.py
"""

import unittest
from unittest.mock import patch
import sys
import os

# Add the current directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the test module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unittest'))
from test_process_japan_exports import TestERPIntegration

if __name__ == "__main__":
    # Create a test suite with just the tests we want to run
    suite = unittest.TestSuite()
    
    # Add the specific test cases we're interested in
    suite.addTest(TestERPIntegration('test_create_journal_line_debit'))
    suite.addTest(TestERPIntegration('test_create_journal_line_credit_vendor'))
    suite.addTest(TestERPIntegration('test_create_journal_line_missing_fields_handled_gracefully'))
    
    # Run the tests
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    
    # Exit with non-zero status if tests failed
    sys.exit(not result.wasSuccessful())
