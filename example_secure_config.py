"""
Example script demonstrating how to use environment variables for sensitive data.

This script shows how to use the env_config module to securely load configuration
values from environment variables instead of hard-coding them in your scripts.

To run this example:
1. Copy .env.example to .env
2. Edit .env to add your actual values
3. Run this script: python example_secure_config.py
"""

from env_config import get_env_var
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Example: Loading API credentials from environment variables
    api_key = get_env_var("ERP_API_KEY", default="demo_key")
    api_secret = get_env_var("ERP_API_SECRET", default="demo_secret")
    
    # Example: Loading database configuration
    db_config = {
        "host": get_env_var("DB_HOST", default="localhost"),
        "port": get_env_var("DB_PORT", default="5432", as_type=int),
        "database": get_env_var("DB_NAME", default="erp_database"),
        "user": get_env_var("DB_USER", default="user"),
        "password": get_env_var("DB_PASSWORD", default="password"),
    }
    
    # Example: Loading application configuration
    debug_mode = get_env_var("DEBUG_MODE", default="False", as_type=bool)
    log_level = get_env_var("LOG_LEVEL", default="INFO")
    
    # Display the loaded configuration (NEVER log actual secrets in production!)
    if debug_mode:
        logger.info("Debug mode is enabled")
        logger.info(f"API Key: {api_key}")  # In production, don't log actual secrets
        logger.info(f"Database: {db_config['database']} on {db_config['host']}:{db_config['port']}")
    else:
        logger.info("Debug mode is disabled")
        logger.info("Configuration loaded successfully")
    
    # Example: Using the configuration values
    logger.info("Simulating API connection...")
    simulate_api_connection(api_key, api_secret)
    
    logger.info("Simulating database connection...")
    simulate_db_connection(db_config)

def simulate_api_connection(api_key, api_secret):
    """Simulate connecting to an API with credentials."""
    # In a real application, you would use these credentials to authenticate
    # with an actual API service
    logger.info("API connection successful (simulation)")

def simulate_db_connection(db_config):
    """Simulate connecting to a database with configuration."""
    # In a real application, you would use these settings to establish
    # a connection to an actual database
    logger.info(f"Database connection successful (simulation) to {db_config['database']}")

if __name__ == "__main__":
    main()
