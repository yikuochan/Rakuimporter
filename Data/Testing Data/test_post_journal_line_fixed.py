#!/usr/bin/env python3
"""
Test script to verify that the post_journal_line function properly populates the description field.
"""

import json
import sys
import os
import logging
import types

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockRateLimiter:
    """Mock rate limiter for testing."""
    def wait_before_request(self):
        """Mock wait_before_request method."""
        pass
    
    def record_success(self):
        """Mock record_success method."""
        pass
    
    def record_failure(self):
        """Mock record_failure method."""
        pass

def test_post_journal_line():
    """Test that the post_journal_line function properly populates the description field."""
    # Import the functions from process_japan_exports
    from process_japan_exports import create_journal_line, post_journal_line
    
    # Load the JSON data for VPA-0000093
    try:
        with open('0526-Raku export- VCT GE.utf8.json', 'r', encoding='utf-8') as f:
            entries = json.load(f)
    except Exception as e:
        logger.error(f"Error loading input file: {str(e)}")
        sys.exit(1)
    
    # Find the entry for VPA-0000093
    vpa_0000093_entry = None
    for entry in entries:
        if entry.get('voucher_no') == 'VPA-0000093':
            vpa_0000093_entry = entry
            break
    
    if not vpa_0000093_entry:
        logger.error("Entry for VPA-0000093 not found in the JSON file.")
        sys.exit(1)
    
    # Create a test case with empty description
    logger.info("Testing with empty description:")
    empty_desc_entry = vpa_0000093_entry.copy()
    empty_desc_entry['description'] = ''
    empty_desc_entry['debit']['free_field'] = ''
    empty_desc_entry['credit']['free_field'] = ''
    
    # Create journal lines for the empty description entry
    empty_debit_line = create_journal_line(empty_desc_entry, "debit")
    empty_credit_line = create_journal_line(empty_desc_entry, "credit")
    
    # Print the description fields from the journal lines
    logger.info("Journal line descriptions (before post_journal_line):")
    logger.info(f"Debit line description: '{empty_debit_line['Description']}'")
    logger.info(f"Credit line description: '{empty_credit_line['Description']}'")
    
    # Create a mock access token
    mock_token = "mock_token"
    
    # Create a mock rate limiter
    mock_rate_limiter = MockRateLimiter()
    
    # Call the post_journal_line function with the empty description lines
    logger.info("\nTesting post_journal_line with empty debit line description:")
    debit_success, debit_response = post_journal_line(empty_debit_line, mock_token, mock_rate_limiter)
    
    logger.info("\nTesting post_journal_line with empty credit line description:")
    credit_success, credit_response = post_journal_line(empty_credit_line, mock_token, mock_rate_limiter)
    
    # Print the description fields after post_journal_line
    logger.info("\nJournal line descriptions (after post_journal_line):")
    logger.info(f"Debit line description: '{empty_debit_line['Description']}'")
    logger.info(f"Credit line description: '{empty_credit_line['Description']}'")
    
    # Check if the descriptions were properly populated
    if empty_debit_line['Description']:
        logger.info("\nFix successfully populated the empty debit line description field.")
    else:
        logger.error("\nFix FAILED to populate the empty debit line description field!")
    
    if empty_credit_line['Description']:
        logger.info("Fix successfully populated the empty credit line description field.")
    else:
        logger.error("Fix FAILED to populate the empty credit line description field!")
    
    # Create a sample payload with the updated journal lines
    updated_payload = {
        "debit_line": empty_debit_line,
        "credit_line": empty_credit_line
    }
    
    # Save the payload to a file
    output_file = 'bc-payload-vpa-0000093-post-journal-line.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(updated_payload, f, ensure_ascii=False, indent=2)
        logger.info(f"\nUpdated payload saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving payload: {str(e)}")

if __name__ == "__main__":
    test_post_journal_line()
