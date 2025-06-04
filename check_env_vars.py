#!/usr/bin/env python3
"""
Script to check environment variables and their sources.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("env_check.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("check_env_vars")

def check_env_file(file_path):
    """
    Check if an environment file exists and print its contents.
    
    Args:
        file_path (str): Path to the environment file
    """
    if os.path.exists(file_path):
        logger.info(f"Found environment file: {file_path}")
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Print the file content, masking sensitive information
            lines = content.split('\n')
            for line in lines:
                if line.strip() and not line.strip().startswith('#'):
                    if 'SECRET' in line or 'PASSWORD' in line or 'KEY' in line:
                        key, value = line.split('=', 1)
                        masked_value = value[:5] + '...' + value[-5:] if len(value) > 10 else '***'
                        logger.info(f"  {key}={masked_value}")
                    else:
                        logger.info(f"  {line}")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
    else:
        logger.info(f"Environment file not found: {file_path}")

def check_env_vars():
    """
    Check environment variables related to authentication.
    """
    logger.info("=== Environment Variables ===")
    
    # Check specific environment variables
    env_vars = [
        "BC_CLIENT_ID",
        "BC_CLIENT_SECRET",
        "BC_TENANT_ID",
        "ERP_CLIENT_ID",
        "ERP_CLIENT_SECRET",
        "ERP_TOKEN_URL"
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive information
            if 'SECRET' in var or 'PASSWORD' in var or 'KEY' in var:
                masked_value = value[:5] + '...' + value[-5:] if len(value) > 10 else '***'
                logger.info(f"{var}={masked_value}")
            else:
                logger.info(f"{var}={value}")
        else:
            logger.info(f"{var} is not set")

def check_python_path():
    """
    Check the Python path to see where modules might be loaded from.
    """
    logger.info("\n=== Python Path ===")
    for path in sys.path:
        logger.info(path)

def main():
    """
    Main function to run the checks.
    """
    logger.info("Starting environment variable check")
    
    # Check .env files
    logger.info("\n=== Checking .env Files ===")
    check_env_file('.env')
    check_env_file('.env.local')
    check_env_file('.env.development')
    check_env_file('.env.production')
    
    # Check environment variables
    check_env_vars()
    
    # Check Python path
    check_python_path()
    
    logger.info("\nEnvironment check completed")

if __name__ == "__main__":
    main()
