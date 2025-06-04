#!/usr/bin/env python3
"""
Debug script to print out the client secret being used by the application.
This helps diagnose authentication issues with the Business Central API.
"""

import logging
import os
from env_config import get_env_var
from oauth_token_helper import OAuthTokenHelper

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("client_secret_debug.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("debug_client_secret")

def debug_env_variables():
    """
    Print out environment variables related to authentication.
    """
    logger.info("=== Environment Variables ===")
    
    # Check if .env file exists
    env_file_exists = os.path.exists('.env')
    logger.info(f".env file exists: {env_file_exists}")
    
    # Print out client ID and secret from environment variables
    client_id = get_env_var("BC_CLIENT_ID", default="Not set")
    client_secret = get_env_var("BC_CLIENT_SECRET", default="Not set")
    
    # Mask the secret for security, but show enough to verify
    masked_secret = "Not set" if client_secret == "Not set" else f"{client_secret[:5]}...{client_secret[-5:]}"
    
    logger.info(f"BC_CLIENT_ID: {client_id}")
    logger.info(f"BC_CLIENT_SECRET (masked): {masked_secret}")
    
    # Check alternative environment variables that might be used
    alt_client_id = get_env_var("ERP_CLIENT_ID", default="Not set")
    alt_client_secret = get_env_var("ERP_CLIENT_SECRET", default="Not set")
    
    # Mask the secret for security, but show enough to verify
    alt_masked_secret = "Not set" if alt_client_secret == "Not set" else f"{alt_client_secret[:5]}...{alt_client_secret[-5:]}"
    
    logger.info(f"ERP_CLIENT_ID: {alt_client_id}")
    logger.info(f"ERP_CLIENT_SECRET (masked): {alt_masked_secret}")
    
    # Check if the client ID and secret match between BC and ERP variables
    if client_id != "Not set" and alt_client_id != "Not set":
        logger.info(f"Client IDs match: {client_id == alt_client_id}")
    
    if client_secret != "Not set" and alt_client_secret != "Not set":
        logger.info(f"Client secrets match: {client_secret == alt_client_secret}")

def test_token_acquisition():
    """
    Test acquiring a token with the current client secret.
    """
    logger.info("\n=== Testing Token Acquisition ===")
    
    # Get credentials from environment variables
    tenant_id = get_env_var("BC_TENANT_ID", default="6b83c27c-aa6d-475a-9933-5c34bb008d73")
    client_id = get_env_var("BC_CLIENT_ID", required=True)
    client_secret = get_env_var("BC_CLIENT_SECRET", required=True)
    scope = get_env_var("BC_SCOPE", default="https://api.businesscentral.dynamics.com/.default")
    
    # Print the full client secret for debugging (be careful with this in production!)
    logger.info(f"Using client secret: {client_secret}")
    
    # Initialize OAuth helper
    oauth_helper = OAuthTokenHelper(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope
    )
    
    # Try to acquire a token
    token_data = oauth_helper.acquire_token(verify_ssl=True)
    
    if token_data:
        logger.info("Token acquired successfully!")
        logger.info(f"Token type: {token_data.get('token_type')}")
        logger.info(f"Expires in: {token_data.get('expires_in')} seconds")
    else:
        logger.error("Failed to acquire token")
        
        # Try with alternative credentials
        logger.info("\nTrying with ERP credentials...")
        alt_tenant_id = get_env_var("ERP_TOKEN_URL", "").split("/")[3] if get_env_var("ERP_TOKEN_URL", "") else tenant_id
        alt_client_id = get_env_var("ERP_CLIENT_ID", default=client_id)
        alt_client_secret = get_env_var("ERP_CLIENT_SECRET", default=client_secret)
        alt_scope = get_env_var("ERP_SCOPE", default=scope)
        
        # Print the full alternative client secret for debugging
        logger.info(f"Using alternative client secret: {alt_client_secret}")
        
        # Initialize OAuth helper with alternative credentials
        alt_oauth_helper = OAuthTokenHelper(
            tenant_id=alt_tenant_id,
            client_id=alt_client_id,
            client_secret=alt_client_secret,
            scope=alt_scope
        )
        
        # Try to acquire a token with alternative credentials
        alt_token_data = alt_oauth_helper.acquire_token(verify_ssl=True)
        
        if alt_token_data:
            logger.info("Token acquired successfully with alternative credentials!")
            logger.info(f"Token type: {alt_token_data.get('token_type')}")
            logger.info(f"Expires in: {alt_token_data.get('expires_in')} seconds")
        else:
            logger.error("Failed to acquire token with alternative credentials")

def main():
    """
    Main function to run the debug script.
    """
    logger.info("Starting client secret debug script")
    
    # Debug environment variables
    debug_env_variables()
    
    # Test token acquisition
    test_token_acquisition()
    
    logger.info("Debug script completed")

if __name__ == "__main__":
    main()
