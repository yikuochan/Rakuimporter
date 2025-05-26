# Rate Limiting Implementation for Business Central API

## Overview

This document describes the rate limiting functionality implemented in the `process_japan_exports.py` script to prevent exceeding Business Central API limits. The implementation includes configurable delays between API calls, exponential backoff for failed requests, and retry logic for transient errors.

## Problem Statement

When making multiple API calls to Business Central in rapid succession, we may encounter rate limiting issues that can cause:

1. API calls to fail with 429 (Too Many Requests) status codes
2. Inconsistent responses from the API
3. Document number duplication issues

## Solution

A comprehensive rate limiting mechanism has been implemented with the following features:

### 1. RateLimiter Class

The `RateLimiter` class manages the timing of API calls with the following capabilities:

- **Configurable base delay**: Sets the minimum time between API calls
- **Exponential backoff**: Automatically increases delay after failed requests
- **Maximum delay cap**: Prevents excessive delays after multiple failures
- **Success tracking**: Resets the backoff after successful requests

```python
class RateLimiter:
    def __init__(self, base_delay=1.0, max_delay=10.0, backoff_factor=2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.last_request_time = 0
        self.consecutive_failures = 0
    
    def wait_before_request(self):
        """Wait appropriate time before making a request."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # Calculate delay based on consecutive failures (exponential backoff)
        if self.consecutive_failures > 0:
            delay = min(self.base_delay * (self.backoff_factor ** (self.consecutive_failures - 1)), self.max_delay)
        else:
            delay = self.base_delay
            
        # If not enough time has passed since last request, wait
        if elapsed < delay:
            wait_time = delay - elapsed
            logger.info(f"Rate limiting: Waiting {wait_time:.2f} seconds before next API call")
            time.sleep(wait_time)
        
        # Update last request time
        self.last_request_time = time.time()
    
    def record_success(self):
        """Record a successful API call."""
        self.consecutive_failures = 0
    
    def record_failure(self):
        """Record a failed API call."""
        self.consecutive_failures += 1
        logger.info(f"Rate limiting: Recorded failure. Consecutive failures: {self.consecutive_failures}")
```

### 2. Enhanced post_journal_line Function

The `post_journal_line` function has been updated to use the rate limiter and implement retry logic:

- Waits before making each request based on the rate limiter's rules
- Detects rate limit responses (HTTP 429) and backs off accordingly
- Retries failed requests with exponential backoff
- Gives up after a configurable maximum number of retries

### 3. Command-Line Configuration

The following command-line arguments have been added to allow fine-tuning of the rate limiting behavior:

```
--base-delay SECONDS     Base delay between API calls in seconds (default: 5.0)
--max-delay SECONDS      Maximum delay between API calls in seconds (default: 10.0)
--backoff-factor FACTOR  Factor to increase delay on failures (default: 2.0)
--max-retries COUNT      Maximum number of retry attempts for failed API calls (default: 3)
```

## Usage

### Basic Usage

To use the default rate limiting settings:

```bash
python process_japan_exports.py input_file.json
```

### Custom Rate Limiting

To customize the rate limiting behavior:

```bash
python process_japan_exports.py input_file.json --base-delay 2.0 --max-delay 20.0 --backoff-factor 3.0 --max-retries 5
```

## Recommended Settings

The optimal settings depend on the specific API limits of your Business Central instance. Here are some recommendations:

- For normal operation: `--base-delay 5.0 --max-retries 3`
- For high-volume processing: `--base-delay 2.0 --max-delay 15.0 --max-retries 5`
- For very strict API limits: `--base-delay 3.0 --max-delay 30.0 --backoff-factor 3.0 --max-retries 5`

## Testing

A comprehensive test suite (`test_rate_limiter.py`) has been created to verify the rate limiting functionality:

- Tests that appropriate delays are added between requests
- Verifies that exponential backoff increases delay after failures
- Confirms that the consecutive failures counter resets after success
- Tests retry logic for rate-limited responses
- Verifies that the system gives up after max retries

To run the tests:

```bash
python test_rate_limiter.py
```

## Troubleshooting

If you encounter API rate limiting issues despite these measures:

1. Increase the `base-delay` parameter to add more time between requests
2. Increase the `max-retries` parameter to allow more retry attempts
3. Check the logs for "Rate limit hit" warnings and adjust settings accordingly
4. Consider breaking up large batches of entries into smaller groups

## Conclusion

This rate limiting implementation helps ensure reliable communication with the Business Central API by:

1. Preventing API rate limit violations
2. Handling transient errors gracefully
3. Providing configurable parameters to adapt to different API environments
4. Logging detailed information about rate limiting decisions

These improvements should help address the document number duplication issues by ensuring that API calls are properly spaced out and that the system can recover from transient failures.
