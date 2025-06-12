#!/usr/bin/env python3
"""
Test script to verify the rate limiting functionality in process_japan_exports.py.

This test ensures that the RateLimiter class correctly spaces out API calls and
implements exponential backoff for failed requests.
"""

import unittest
import time
from unittest.mock import patch, MagicMock
import logging
import sys

# Import the RateLimiter class from process_japan_exports.py
from process_japan_exports import RateLimiter, post_journal_line

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRateLimiter(unittest.TestCase):
    """Test cases for the RateLimiter class in process_japan_exports.py."""

    def setUp(self):
        """Set up test data."""
        # Create a RateLimiter instance with test settings (smaller delays for faster tests)
        self.rate_limiter = RateLimiter(base_delay=0.1, max_delay=1.0, backoff_factor=2.0)
        
        # Create a sample journal line for testing
        self.journal_line = {
            "Journal_Template_Name": "PURCHASES",
            "Journal_Batch_Name": "PURCHASE",
            "Document_Type": "Invoice",
            "External_Document_No": "TEST-001",
            "Document_No": "VPA-0000123",
            "Document_Date": "2025-05-23",
            "Account_Type": "G/L Account",
            "Account_No": "72600-30",
            "Description": "VPA-0000123 - Test Description",
            "Currency_Code": "R-USD",
            "Amount": 100.00,
            "Shortcut_Dimension_1_Code": "VCA",
            "Shortcut_Dimension_2_Code": "VCA.1342G"
        }
        
        # Mock access token
        self.access_token = "fake_token"

    def test_wait_before_request(self):
        """Test that wait_before_request adds appropriate delay between requests."""
        # Record start time
        start_time = time.time()
        
        # First request should not wait (no previous request)
        self.rate_limiter.wait_before_request()
        first_request_time = time.time() - start_time
        
        # Second request should wait at least base_delay
        self.rate_limiter.wait_before_request()
        second_request_time = time.time() - start_time - first_request_time
        
        # Check that the second request waited at least base_delay
        self.assertGreaterEqual(second_request_time, self.rate_limiter.base_delay)
        
        # Third request should also wait at least base_delay
        self.rate_limiter.wait_before_request()
        third_request_time = time.time() - start_time - first_request_time - second_request_time
        
        # Check that the third request waited at least base_delay
        self.assertGreaterEqual(third_request_time, self.rate_limiter.base_delay)
        
        logger.info(f"First request time: {first_request_time:.4f}s")
        logger.info(f"Second request time: {second_request_time:.4f}s")
        logger.info(f"Third request time: {third_request_time:.4f}s")

    def test_exponential_backoff(self):
        """Test that exponential backoff increases delay after failures."""
        # Record start time
        start_time = time.time()
        
        # First request (no failures yet)
        self.rate_limiter.wait_before_request()
        first_request_time = time.time() - start_time
        
        # Record a failure
        self.rate_limiter.record_failure()
        
        # Second request (after 1 failure)
        self.rate_limiter.wait_before_request()
        second_request_time = time.time() - start_time - first_request_time
        
        # Record another failure
        self.rate_limiter.record_failure()
        
        # Third request (after 2 failures)
        self.rate_limiter.wait_before_request()
        third_request_time = time.time() - start_time - first_request_time - second_request_time
        
        # Check that delays increase with failures
        # After 1 failure: delay = base_delay * (backoff_factor^0) = base_delay
        # After 2 failures: delay = base_delay * (backoff_factor^1) = base_delay * backoff_factor
        expected_second_delay = self.rate_limiter.base_delay
        expected_third_delay = self.rate_limiter.base_delay * self.rate_limiter.backoff_factor
        
        self.assertGreaterEqual(second_request_time, expected_second_delay)
        self.assertGreaterEqual(third_request_time, expected_third_delay)
        
        logger.info(f"First request time: {first_request_time:.4f}s")
        logger.info(f"Second request time (after 1 failure): {second_request_time:.4f}s")
        logger.info(f"Third request time (after 2 failures): {third_request_time:.4f}s")
        logger.info(f"Expected second delay: {expected_second_delay:.4f}s")
        logger.info(f"Expected third delay: {expected_third_delay:.4f}s")

    def test_reset_after_success(self):
        """Test that consecutive failures counter resets after a success."""
        # Record failures
        self.rate_limiter.record_failure()
        self.rate_limiter.record_failure()
        self.assertEqual(self.rate_limiter.consecutive_failures, 2)
        
        # Record success
        self.rate_limiter.record_success()
        self.assertEqual(self.rate_limiter.consecutive_failures, 0)

    @patch('process_japan_exports.requests.post')
    def test_post_journal_line_with_rate_limiting(self, mock_post):
        """Test that post_journal_line uses rate limiting."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        # Create a rate limiter with a significant delay for testing
        rate_limiter = RateLimiter(base_delay=0.2, max_delay=1.0, backoff_factor=2.0)
        
        # Record start time
        start_time = time.time()
        
        # Make first API call
        success1, _ = post_journal_line(self.journal_line, self.access_token, rate_limiter)
        first_call_time = time.time() - start_time
        
        # Make second API call
        success2, _ = post_journal_line(self.journal_line, self.access_token, rate_limiter)
        second_call_time = time.time() - start_time - first_call_time
        
        # Check that both calls were successful
        self.assertTrue(success1)
        self.assertTrue(success2)
        
        # Check that the second call waited at least base_delay
        self.assertGreaterEqual(second_call_time, rate_limiter.base_delay)
        
        logger.info(f"First API call time: {first_call_time:.4f}s")
        logger.info(f"Second API call time: {second_call_time:.4f}s")

    @patch('process_japan_exports.requests.post')
    def test_retry_on_rate_limit(self, mock_post):
        """Test that post_journal_line retries on rate limit (429) responses."""
        # Set up mock responses
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {"success": True}
        
        # First call returns rate limit, second call succeeds
        mock_post.side_effect = [rate_limit_response, success_response]
        
        # Create a rate limiter with a small delay for testing
        rate_limiter = RateLimiter(base_delay=0.1, max_delay=0.5, backoff_factor=2.0)
        
        # Make API call (should retry once)
        success, _ = post_journal_line(self.journal_line, self.access_token, rate_limiter, max_retries=3)
        
        # Check that the call was eventually successful
        self.assertTrue(success)
        
        # Check that post was called twice (initial + retry)
        self.assertEqual(mock_post.call_count, 2)
        
        # Check that consecutive_failures was incremented
        self.assertEqual(rate_limiter.consecutive_failures, 0)  # Reset after success

    @patch('process_japan_exports.requests.post')
    def test_max_retries_exceeded(self, mock_post):
        """Test that post_journal_line gives up after max_retries."""
        # Set up mock response that always returns rate limit
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        mock_post.return_value = rate_limit_response
        
        # Create a rate limiter with a small delay for testing
        rate_limiter = RateLimiter(base_delay=0.1, max_delay=0.5, backoff_factor=2.0)
        
        # Make API call with max_retries=2
        success, response = post_journal_line(self.journal_line, self.access_token, rate_limiter, max_retries=2)
        
        # Check that the call failed
        self.assertFalse(success)
        
        # Check that post was called 3 times (initial + 2 retries)
        self.assertEqual(mock_post.call_count, 3)
        
        # Check that the error message mentions max retries
        self.assertIn("Failed after 2 attempts", response.get("error", ""))
        
        # Check that consecutive_failures was incremented for each failure
        self.assertEqual(rate_limiter.consecutive_failures, 3)

if __name__ == '__main__':
    unittest.main()
