#!/usr/bin/env python3
"""
Simple script to test authentication with the Business Central API.
"""

import os
import sys
import logging
from oauth_token_helper import OAuthTokenHelper
from env_config import get_env_var

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_auth")

def test_authentication():
    """
    Test authentication with the Business Central API.
    """
    # Get credentials from environment variables
    tenant_id = get_env_var("BC_TENANT_ID", default="6b83c27c-aa6d-475a-9933-5c34bb008d73")
    client_id = get_env_var("BC_CLIENT_ID", required=True)
    client_secret = get_env_var("BC_CLIENT_SECRET", required=True)
    scope = get_env_var("BC_SCOPE", default="https://api.businesscentral.dynamics.com/.default")
    
    print(f"Using tenant ID: {tenant_id}")
    print(f"Using client ID: {client_id}")
    print(f"Using client secret: {client_secret[:5]}...{client_secret[-5:]}")
    print(f"Using scope: {scope}")
    
    # Initialize OAuth helper
    oauth_helper = OAuthTokenHelper(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope
    )
    
    # Try to acquire a token
    print("\nAttempting to acquire token...")
    token_data = oauth_helper.acquire_token(verify_ssl=True)
    
    if token_data:
        print("\nAuthentication successful!")
        print(f"Token type: {token_data.get('token_type')}")
        print(f"Expires in: {token_data.get('expires_in')} seconds")
        return True
    else:
        print("\nAuthentication failed!")
        return False

def main():
    """
    Main function to run the test.
    """
    print("Starting authentication test")
    
    # Test authentication
    success = test_authentication()
    
    if success:
        print("\nTest completed successfully")
        sys.exit(0)
    else:
        print("\nTest failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
