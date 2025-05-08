# OAuth Token Helper

This utility helps with acquiring OAuth tokens from Microsoft Azure AD for integration with Microsoft Business Central API. It handles token acquisition and SSL certificate validation issues.

## Features

- OAuth 2.0 token acquisition using client credentials flow
- SSL certificate validation handling
- Detailed logging of token acquisition process
- Helper methods for using tokens in API requests

## Usage

```python
from oauth_token_helper import OAuthTokenHelper

# Initialize with your credentials
helper = OAuthTokenHelper(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret",
    scope="https://api.businesscentral.dynamics.com/.default"
)

# Acquire a token
token_data = helper.acquire_token()

if token_data:
    # Use the token for API requests
    auth_header = helper.get_token_header()
    # Make API requests with the auth_header
```

## SSL Certificate Issues

If you encounter SSL certificate validation issues, you can temporarily disable SSL verification for development purposes:

```python
token_data = helper.acquire_token(verify_ssl=False)
```

**Note:** Disabling SSL verification is not recommended for production environments.

## Logging

The helper logs all token acquisition attempts and results to both a file and the console. Log files are named with the current date (e.g., `oauth_token_20250508.log`).

## Related Issues

This utility was created to address [Issue #16](https://github.com/yikuochan/Rakuimporter/issues/16) regarding OAuth token acquisition and SSL certificate validation problems.