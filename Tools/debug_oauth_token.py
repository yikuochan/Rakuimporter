#!/usr/bin/env python3
"""
Debug OAuth Token Helper

This script helps debug issues with obtaining OAuth tokens for the Business Central API.
It provides detailed error information and suggestions for fixing common problems.
"""

import sys
import json
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"oauth_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("oauth_debug")

def load_env_variables():
    """Load environment variables and return them as a dictionary."""
    # Print the current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if .env file exists
    env_file = os.path.join(os.getcwd(), '.env')
    env_vars = {}
    missing_vars = []
    
    if os.path.exists(env_file):
        print(f".env file found at: {env_file}")
        # Manually parse the .env file
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
                print("First few lines of .env file:")
                line_count = 0
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Print masked values for secrets
                            if line_count < 10:  # Only print first 10 non-comment lines
                                if "SECRET" in key.upper():
                                    print(f"{key}=***MASKED***")
                                else:
                                    print(f"{key}={value}")
                                line_count += 1
                            
                            # Store the value in env_vars
                            env_vars[key] = value
        except Exception as e:
            print(f"Error reading .env file: {str(e)}")
    else:
        print(f".env file not found at: {env_file}")
        # Fall back to load_dotenv if file not found
        load_dotenv()
    
    # Required variables
    required_vars = [
        "BC_CLIENT_ID",
        "BC_CLIENT_SECRET",
        "BC_TENANT_ID"
    ]
    
    # Optional variables with defaults
    optional_vars = {
        "BC_SCOPE": "https://api.businesscentral.dynamics.com/.default",
        "BC_VERIFY_SSL": "True"
    }
    
    # Check required variables
    for var in required_vars:
        # First check our manually parsed values
        value = env_vars.get(var)
        # If not found, try os.getenv as fallback
        if value is None:
            value = os.getenv(var)
            if value:
                env_vars[var] = value
        
        print(f"Using environment variable {var}: {value[:10]}{'...' if value and len(value) > 10 else ''}")
        if value is None or value.strip() == "":
            missing_vars.append(var)
    
    # Check optional variables
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        env_vars[var] = value
    
    # Convert boolean string to actual boolean
    if "BC_VERIFY_SSL" in env_vars:
        env_vars["BC_VERIFY_SSL"] = env_vars["BC_VERIFY_SSL"].lower() == "true"
    
    return env_vars, missing_vars

def test_token_acquisition(env_vars):
    """Test token acquisition with the provided environment variables."""
    tenant_id = env_vars.get("BC_TENANT_ID")
    client_id = env_vars.get("BC_CLIENT_ID")
    client_secret = env_vars.get("BC_CLIENT_SECRET")
    scope = env_vars.get("BC_SCOPE")
    verify_ssl = env_vars.get("BC_VERIFY_SSL", True)
    
    logger.info(f"Testing token acquisition with:")
    logger.info(f"  Tenant ID: {tenant_id}")
    logger.info(f"  Client ID: {client_id}")
    logger.info(f"  Scope: {scope}")
    logger.info(f"  Verify SSL: {verify_ssl}")
    
    # Construct the token URL
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    # Prepare the request data
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': scope
    }
    
    try:
        # Make the request
        logger.info(f"Making request to: {token_url}")
        response = requests.post(token_url, data=data, verify=verify_ssl)
        
        # Check if the request was successful
        if response.status_code == 200:
            token_data = response.json()
            logger.info("Token acquisition successful!")
            logger.info(f"Token expires in: {token_data.get('expires_in')} seconds")
            logger.info(f"Token type: {token_data.get('token_type')}")
            
            # Only show the first few characters of the token for security
            token = token_data.get('access_token', '')
            if token:
                visible_part = token[:10] + "..." + token[-5:]
                logger.info(f"Access token: {visible_part}")
            
            return True, token_data
        else:
            # Log the error
            logger.error(f"Token acquisition failed with status code: {response.status_code}")
            try:
                error_data = response.json()
                logger.error(f"Error response: {json.dumps(error_data, indent=2)}")
                
                # Provide specific guidance based on error codes
                error_code = error_data.get("error")
                if error_code == "invalid_client":
                    logger.error("GUIDANCE: The client credentials (client ID or client secret) are incorrect.")
                    logger.error("1. Double-check your BC_CLIENT_ID and BC_CLIENT_SECRET in the .env file.")
                    logger.error("2. Ensure you're using the correct credentials for this tenant.")
                    logger.error("3. Check if the client secret has expired and needs to be renewed.")
                
                elif error_code == "unauthorized_client":
                    logger.error("GUIDANCE: The application is not authorized to request a token.")
                    logger.error("1. Verify that the application is registered in the correct Azure AD tenant.")
                    logger.error("2. Check if the application has the necessary API permissions.")
                    logger.error("3. Ensure the BC_TENANT_ID in your .env file is correct.")
                
                elif error_code == "invalid_request":
                    logger.error("GUIDANCE: The request is malformed.")
                    logger.error("1. Check if the scope format is correct (should be 'https://api.businesscentral.dynamics.com/.default').")
                    logger.error("2. Verify all required parameters are included in the request.")
                
                elif error_code == "invalid_scope":
                    logger.error("GUIDANCE: The requested scope is invalid or unknown.")
                    logger.error("1. Check the BC_SCOPE value in your .env file.")
                    logger.error("2. The correct format is typically 'https://api.businesscentral.dynamics.com/.default'.")
                
                else:
                    logger.error("GUIDANCE: An unknown error occurred. Check the error details above.")
                
            except ValueError:
                logger.error(f"Error response (non-JSON): {response.text}")
            
            return False, None
    
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL Error: {str(e)}")
        logger.error("GUIDANCE: SSL verification failed.")
        logger.error("1. If you're using a self-signed certificate or testing environment, set BC_VERIFY_SSL=False in your .env file.")
        logger.error("2. Otherwise, ensure your system's CA certificates are up to date.")
        return False, None
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection Error: {str(e)}")
        logger.error("GUIDANCE: Could not connect to the token endpoint.")
        logger.error("1. Check your internet connection.")
        logger.error("2. Verify that the tenant ID is correct.")
        logger.error("3. Ensure there are no network restrictions blocking access to login.microsoftonline.com.")
        return False, None
    
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        logger.error("GUIDANCE: An unexpected error occurred during token acquisition.")
        logger.error("1. Check the error details above.")
        logger.error("2. Verify all environment variables are set correctly.")
        return False, None

def test_api_access(token_data, env_vars):
    """Test API access with the acquired token."""
    if not token_data:
        logger.error("Cannot test API access without a valid token.")
        return False
    
    tenant_id = env_vars.get("BC_TENANT_ID")
    company = os.getenv("BC_COMPANY", "VCJ")
    verify_ssl = env_vars.get("BC_VERIFY_SSL", True)
    
    # Construct the API URL
    api_url = f"https://api.businesscentral.dynamics.com/v2.0/{tenant_id}/Production/ODataV4/Company('{company}')/CurrencyExchangeRates"
    
    # Prepare headers
    headers = {
        "Authorization": f"{token_data.get('token_type', 'Bearer')} {token_data.get('access_token')}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        # Make the request
        logger.info(f"Testing API access: {api_url}")
        response = requests.get(api_url, headers=headers, verify=verify_ssl)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            count = len(data.get("value", []))
            logger.info(f"API access successful! Retrieved {count} exchange rate records.")
            return True
        else:
            # Log the error
            logger.error(f"API access failed with status code: {response.status_code}")
            try:
                error_data = response.json()
                logger.error(f"Error response: {json.dumps(error_data, indent=2)}")
                
                # Provide specific guidance based on error codes
                if response.status_code == 401:
                    logger.error("GUIDANCE: Unauthorized. The token is invalid or expired.")
                    logger.error("1. Check if the token has the correct permissions.")
                    logger.error("2. Verify that the application has been granted access to Business Central.")
                
                elif response.status_code == 403:
                    logger.error("GUIDANCE: Forbidden. The token doesn't have permission to access this resource.")
                    logger.error("1. Check if the application has the necessary API permissions.")
                    logger.error("2. Verify that the user or application has access to the specified company.")
                
                elif response.status_code == 404:
                    logger.error("GUIDANCE: Not Found. The requested resource doesn't exist.")
                    logger.error(f"1. Check if the company '{company}' exists in your Business Central environment.")
                    logger.error("2. Verify that the API endpoint URL is correct.")
                
                else:
                    logger.error("GUIDANCE: An unknown error occurred. Check the error details above.")
                
            except ValueError:
                logger.error(f"Error response (non-JSON): {response.text}")
            
            return False
    
    except Exception as e:
        logger.error(f"Error testing API access: {str(e)}")
        return False

def main():
    """Main function to run the OAuth token debugging."""
    print("Business Central OAuth Token Debugging")
    print("=====================================")
    
    # Load environment variables
    env_vars, missing_vars = load_env_variables()
    
    # Check for missing variables
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file and try again.")
        return
    
    # Test token acquisition
    success, token_data = test_token_acquisition(env_vars)
    
    if success:
        print("\nToken acquisition successful! ✅")
        
        # Test API access
        print("\nTesting API access...")
        api_success = test_api_access(token_data, env_vars)
        
        if api_success:
            print("\nAPI access successful! ✅")
            print("\nYour Business Central API configuration is working correctly.")
        else:
            print("\nAPI access failed. ❌")
            print("Token was acquired successfully, but API access failed.")
            print("Check the log for details and guidance.")
    else:
        print("\nToken acquisition failed. ❌")
        print("Check the log for details and guidance.")
    
    print("\nDebug log has been saved for reference.")

if __name__ == "__main__":
    main()
