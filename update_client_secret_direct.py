#!/usr/bin/env python3
"""
Script to directly update the client secret in the .env file.

This script reads the current .env file, updates the client secret values with the provided value,
and writes the updated content back to the .env file.
"""

import os
import re
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("update_client_secret")

def update_env_file(new_client_secret):
    """
    Update the client secret in the .env file.
    
    Args:
        new_client_secret (str): The new client secret to use
    
    Returns:
        bool: True if the update was successful, False otherwise
    """
    # Check if .env file exists
    if not os.path.exists('.env'):
        logger.error(".env file not found")
        return False
    
    try:
        # Read the current .env file
        with open('.env', 'r') as f:
            env_content = f.read()
        
        # Make a backup of the original .env file
        with open('.env.backup', 'w') as f:
            f.write(env_content)
        
        logger.info("Created backup of .env file as .env.backup")
        
        # Update the client secret values
        updated_content = re.sub(
            r'(ERP_CLIENT_SECRET=).*',
            f'\\1{new_client_secret}',
            env_content
        )
        
        updated_content = re.sub(
            r'(BC_CLIENT_SECRET=).*',
            f'\\1{new_client_secret}',
            updated_content
        )
        
        # Write the updated content back to the .env file
        with open('.env', 'w') as f:
            f.write(updated_content)
        
        logger.info("Updated client secret in .env file")
        return True
        
    except Exception as e:
        logger.error(f"Error updating .env file: {str(e)}")
        return False

def main():
    """
    Main function to run the script.
    """
    logger.info("Starting client secret update script")
    
    # Check if client secret is provided as command line argument
    if len(sys.argv) < 2:
        logger.error("No client secret provided")
        print("Usage: python update_client_secret_direct.py <new_client_secret>")
        return
    
    new_client_secret = sys.argv[1]
    
    # Update the .env file
    success = update_env_file(new_client_secret)
    
    if success:
        logger.info("Client secret updated successfully")
        logger.info("Please restart any running applications to pick up the new client secret")
    else:
        logger.error("Failed to update client secret")
    
    logger.info("Update script completed")

if __name__ == "__main__":
    main()
