import requests
import json
from oauth_token_helper import OAuthTokenHelper
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_oauth_token")

def test_token_acquisition():
    """
    Test OAuth token acquisition and make a simple API request
    to verify the token works.
    """
    # VicOne app credentials
    tenant_id = "6b83c27c-aa6d-475a-9933-5c34bb008d73"
    client_id = "5d0ad744-0ae3-4712-b057-2cac7afb52f8"
    client_secret = "YOUR_CLIENT_SECRET_HERE"  # Replace with actual secret
    scope = "https://api.businesscentral.dynamics.com/.default"
    
    # Create the helper
    helper = OAuthTokenHelper(tenant_id, client_id, client_secret, scope)
    
    # Try to acquire a token
    logger.info("Testing token acquisition...")
    token_data = helper.acquire_token()
    
    if not token_data:
        logger.error("Failed to acquire token. Test failed.")
        return False
    
    logger.info("Token acquired successfully!")
    logger.info(f"Token type: {token_data.get('token_type')}")
    logger.info(f"Expires in: {token_data.get('expires_in')} seconds")
    
    # Get the authorization header
    auth_header = helper.get_token_header()
    if not auth_header:
        logger.error("Failed to get authorization header. Test failed.")
        return False
    
    # Test making an API request
    try:
        logger.info("Testing API request with the acquired token...")
        
        # Example API endpoint - replace with an actual Business Central endpoint
        api_url = "https://api.businesscentral.dynamics.com/v2.0/YOUR_COMPANY/api/v2.0/companies"
        
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json"
        }
        
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            logger.info("API request successful!")
            logger.info(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            logger.error(f"API request failed with status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error making API request: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_token_acquisition()
    if success:
        logger.info("All tests passed successfully!")
    else:
        logger.error("Tests failed. Check the logs for details.")
