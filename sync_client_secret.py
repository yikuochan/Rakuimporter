#!/usr/bin/env python3
"""
Script to synchronize the client secret in the .env file with the one in the environment variables.
"""

import os
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("sync_client_secret.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("sync_client_secret")

def sync_client_secret():
    """
    Synchronize the client secret in the .env file with the one in the environment variables.
    
    Returns:
        bool: True if the synchronization was successful, False otherwise
    """
    # Check if .env file exists
    if not os.path.exists('.env'):
        logger.error(".env file not found")
        return False
    
    # Get client secret from environment variables
    bc_client_secret = os.environ.get('BC_CLIENT_SECRET')
    erp_client_secret = os.environ.get('ERP_CLIENT_SECRET')
    
    if not bc_client_secret or not erp_client_secret:
        logger.error("Client secret not found in environment variables")
        return False
    
    # Check if they match
    if bc_client_secret != erp_client_secret:
        logger.warning("BC_CLIENT_SECRET and ERP_CLIENT_SECRET do not match")
        logger.warning(f"BC_CLIENT_SECRET: {bc_client_secret[:5]}...{bc_client_secret[-5:]}")
        logger.warning(f"ERP_CLIENT_SECRET: {erp_client_secret[:5]}...{erp_client_secret[-5:]}")
        return False
    
    try:
        # Read the current .env file
        with open('.env', 'r') as f:
            env_content = f.read()
        
        # Make a backup of the original .env file
        with open('.env.backup', 'w') as f:
            f.write(env_content)
        
        logger.info("Created backup of .env file as .env.backup")
        
        # Check if the client secret in the .env file matches the one in the environment variables
        env_bc_secret_match = re.search(r'BC_CLIENT_SECRET=(.+)', env_content)
        env_erp_secret_match = re.search(r'ERP_CLIENT_SECRET=(.+)', env_content)
        
        if env_bc_secret_match and env_erp_secret_match:
            env_bc_secret = env_bc_secret_match.group(1)
            env_erp_secret = env_erp_secret_match.group(1)
            
            if env_bc_secret == bc_client_secret and env_erp_secret == erp_client_secret:
                logger.info("Client secrets in .env file already match environment variables")
                return True
        
        # Update the client secret values
        updated_content = re.sub(
            r'(ERP_CLIENT_SECRET=).*',
            f'\\1{erp_client_secret}',
            env_content
        )
        
        updated_content = re.sub(
            r'(BC_CLIENT_SECRET=).*',
            f'\\1{bc_client_secret}',
            updated_content
        )
        
        # Write the updated content back to the .env file
        with open('.env', 'w') as f:
            f.write(updated_content)
        
        logger.info("Updated client secret in .env file to match environment variables")
        logger.info(f"New client secret (masked): {bc_client_secret[:5]}...{bc_client_secret[-5:]}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating .env file: {str(e)}")
        return False

def main():
    """
    Main function to run the script.
    """
    logger.info("Starting client secret synchronization")
    
    # Synchronize the client secret
    success = sync_client_secret()
    
    if success:
        logger.info("Client secret synchronized successfully")
    else:
        logger.error("Failed to synchronize client secret")
    
    logger.info("Synchronization completed")

if __name__ == "__main__":
    main()
