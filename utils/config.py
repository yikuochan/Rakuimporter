"""
Configuration Module

This module provides centralized configuration management for the Power Importer.
It loads configuration from environment variables with sensible defaults.
"""

import os
from typing import Any, Dict, Optional, Union, cast

# Import environment variable utility
from .env_config import get_env_var

# Default configuration values
DEFAULT_CONFIG = {
    # API Configuration
    "ERP_TOKEN_URL": "https://login.microsoftonline.com/6b83c27c-aa6d-475a-9933-5c34bb008d73/oauth2/v2.0/token",
    "ERP_API_URL_BASE": "https://api.businesscentral.dynamics.com/v2.0/6b83c27c-aa6d-475a-9933-5c34bb008d73/Production/ODataV4/Company",
    "ERP_API_ENDPOINT": "PurchaseJournals",
    "ERP_SCOPE": "https://api.businesscentral.dynamics.com/.default",
    "ERP_VERIFY_SSL": True,
    
    # Business Central Configuration
    "BC_TENANT_ID": "6b83c27c-aa6d-475a-9933-5c34bb008d73",
    "BC_SCOPE": "https://api.businesscentral.dynamics.com/.default",
    "BC_VERIFY_SSL": True,
    "BC_COMPANY": "VCJ",
    
    # Journal Entry Configuration
    "JOURNAL_TEMPLATE_NAME": "PURCHASES",
    "JOURNAL_BATCH_NAME": "PURCHASE",
    "DOCUMENT_TYPE": "Invoice",
    
    # Exchange Rate Configuration
    "USE_EXCHANGE_RATE_API": True,
    
    # Rate Limiting Configuration
    "API_BASE_DELAY": 5.0,
    "API_MAX_DELAY": 10.0,
    "API_BACKOFF_FACTOR": 2.0,
    "API_MAX_RETRIES": 3,
    
    # Balance Tolerance Configuration
    "BALANCE_TOLERANCE": 0.01,
    
    # Logging Configuration
    "LOG_LEVEL": "INFO",
    "LOG_FILE": "erp_api_integration.log",
}


class Config:
    """Configuration class for Power Importer."""
    
    def __init__(self):
        """Initialize configuration with default values."""
        self._config = DEFAULT_CONFIG.copy()
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # API Configuration
        self._config["ERP_TOKEN_URL"] = get_env_var("ERP_TOKEN_URL", default=self._config["ERP_TOKEN_URL"])
        self._config["ERP_API_URL_BASE"] = get_env_var("ERP_API_URL_BASE", default=self._config["ERP_API_URL_BASE"])
        self._config["ERP_API_ENDPOINT"] = get_env_var("ERP_API_ENDPOINT", default=self._config["ERP_API_ENDPOINT"])
        self._config["ERP_SCOPE"] = get_env_var("ERP_SCOPE", default=self._config["ERP_SCOPE"])
        self._config["ERP_VERIFY_SSL"] = get_env_var("ERP_VERIFY_SSL", default=str(self._config["ERP_VERIFY_SSL"]), as_type=bool)
        
        # Business Central Configuration
        self._config["BC_TENANT_ID"] = get_env_var("BC_TENANT_ID", default=self._config["BC_TENANT_ID"])
        self._config["BC_CLIENT_ID"] = get_env_var("BC_CLIENT_ID", required=True)
        self._config["BC_CLIENT_SECRET"] = get_env_var("BC_CLIENT_SECRET", required=True)
        self._config["BC_SCOPE"] = get_env_var("BC_SCOPE", default=self._config["BC_SCOPE"])
        self._config["BC_VERIFY_SSL"] = get_env_var("BC_VERIFY_SSL", default=str(self._config["BC_VERIFY_SSL"]), as_type=bool)
        self._config["BC_COMPANY"] = get_env_var("BC_COMPANY", default=self._config["BC_COMPANY"])
        
        # Journal Entry Configuration
        self._config["JOURNAL_TEMPLATE_NAME"] = get_env_var("JOURNAL_TEMPLATE_NAME", default=self._config["JOURNAL_TEMPLATE_NAME"])
        self._config["JOURNAL_BATCH_NAME"] = get_env_var("JOURNAL_BATCH_NAME", default=self._config["JOURNAL_BATCH_NAME"])
        self._config["DOCUMENT_TYPE"] = get_env_var("DOCUMENT_TYPE", default=self._config["DOCUMENT_TYPE"])
        
        # Exchange Rate Configuration
        self._config["USE_EXCHANGE_RATE_API"] = get_env_var("USE_EXCHANGE_RATE_API", default=str(self._config["USE_EXCHANGE_RATE_API"]), as_type=bool)
        
        # Rate Limiting Configuration
        self._config["API_BASE_DELAY"] = get_env_var("API_BASE_DELAY", default=str(self._config["API_BASE_DELAY"]), as_type=float)
        self._config["API_MAX_DELAY"] = get_env_var("API_MAX_DELAY", default=str(self._config["API_MAX_DELAY"]), as_type=float)
        self._config["API_BACKOFF_FACTOR"] = get_env_var("API_BACKOFF_FACTOR", default=str(self._config["API_BACKOFF_FACTOR"]), as_type=float)
        self._config["API_MAX_RETRIES"] = get_env_var("API_MAX_RETRIES", default=str(self._config["API_MAX_RETRIES"]), as_type=int)
        
        # Balance Tolerance Configuration
        self._config["BALANCE_TOLERANCE"] = get_env_var("BALANCE_TOLERANCE", default=str(self._config["BALANCE_TOLERANCE"]), as_type=float)
        
        # Logging Configuration
        self._config["LOG_LEVEL"] = get_env_var("LOG_LEVEL", default=self._config["LOG_LEVEL"])
        self._config["LOG_FILE"] = get_env_var("LOG_FILE", default=self._config["LOG_FILE"])
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: Default value if key is not found
            
        Returns:
            The configuration value or default
        """
        return self._config.get(key, default)
    
    def get_api_url(self, company_code: str = None) -> str:
        """
        Get the API URL for a specific company.
        
        Args:
            company_code: The company code (e.g., VCT, VCP, etc.)
            
        Returns:
            The API URL for the company
        """
        base_url = self._config["ERP_API_URL_BASE"]
        endpoint = self._config["ERP_API_ENDPOINT"]
        
        if company_code:
            return f"{base_url}('{company_code}')/PurchaseJournals"
        else:
            # Use default company from configuration
            company = self._config["BC_COMPANY"]
            return f"{base_url}('{company}')/PurchaseJournals"
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Get the configuration as a dictionary.
        
        Returns:
            The configuration dictionary
        """
        return self._config.copy()


# Create a singleton instance
config = Config()
