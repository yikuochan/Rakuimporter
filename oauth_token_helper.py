import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"oauth_token_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("oauth_token_helper")

class OAuthTokenHelper:
    """
    Helper class for acquiring OAuth tokens from Microsoft Azure AD
    and handling SSL certificate validation.
    """
    
    def __init__(self, tenant_id, client_id, client_secret, scope):
        """
        Initialize the OAuth token helper with the required credentials.
        
        Args:
            tenant_id (str): The Azure AD tenant ID
            client_id (str): The client ID (application ID)
            client_secret (str): The client secret
            scope (str): The requested scope
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        self.token = None
        self.token_expiry = None
    
    def acquire_token(self, verify_ssl=True):
        """
        Acquire an OAuth token from Microsoft Azure AD.
        
        Args:
            verify_ssl (bool): Whether to verify SSL certificates
            
        Returns:
            dict: The token response or None if acquisition failed
        """
        try:
            logger.info(f"Acquiring token for client ID: {self.client_id}")
            
            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': self.scope
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(
                self.token_url,
                data=payload,
                headers=headers,
                verify=verify_ssl
            )
            
            if response.status_code == 200:
                token_data = response.json()
                logger.info("Token acquired successfully")
                self.token = token_data
                return token_data
            else:
                logger.error(f"Failed to acquire token. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.SSLError as ssl_err:
            logger.error(f"SSL Certificate Error: {str(ssl_err)}")
            logger.info("Try setting verify_ssl=False if you're in a development environment")
            return None
            
        except Exception as e:
            logger.error(f"Error acquiring token: {str(e)}")
            return None
    
    def get_token_header(self):
        """
        Get the Authorization header value for API requests.
        
        Returns:
            str: The Authorization header value or None if no token is available
        """
        if self.token and 'access_token' in self.token:
            return f"Bearer {self.token['access_token']}"
        return None


def main():
    """
    Example usage of the OAuthTokenHelper class.
    """
    # VicOne app credentials
    tenant_id = "6b83c27c-aa6d-475a-9933-5c34bb008d73"
    client_id = "5d0ad744-0ae3-4712-b057-2cac7afb52f8"
    client_secret = "YOUR_CLIENT_SECRET_HERE"  # Replace with actual secret
    scope = "https://api.businesscentral.dynamics.com/.default"
    
    # Create the helper
    helper = OAuthTokenHelper(tenant_id, client_id, client_secret, scope)
    
    # Try to acquire a token with SSL verification
    logger.info("Attempting to acquire token with SSL verification...")
    token_data = helper.acquire_token(verify_ssl=True)
    
    if token_data:
        logger.info("Token acquired successfully with SSL verification")
        logger.info(f"Token type: {token_data.get('token_type')}")
        logger.info(f"Expires in: {token_data.get('expires_in')} seconds")
    else:
        # If SSL verification fails, try without it (for development only)
        logger.warning("Attempting to acquire token without SSL verification (DEVELOPMENT ONLY)...")
        token_data = helper.acquire_token(verify_ssl=False)
        
        if token_data:
            logger.info("Token acquired successfully without SSL verification")
            logger.info(f"Token type: {token_data.get('token_type')}")
            logger.info(f"Expires in: {token_data.get('expires_in')} seconds")
        else:
            logger.error("Failed to acquire token with and without SSL verification")


if __name__ == "__main__":
    main()