"""
Environment Configuration Utility

This module provides utilities for loading and accessing environment variables
for sensitive configuration data such as API keys, passwords, etc.

Usage:
    from utils.env_config import get_env_var

    api_key = get_env_var("API_KEY")
    password = get_env_var("DB_PASSWORD", required=True)
    debug_mode = get_env_var("DEBUG_MODE", default="False", as_type=bool)
"""

import os
import sys
from typing import Any, Optional, Type, TypeVar, Union, cast

# Try to import dotenv, but don't fail if it's not installed
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file if it exists
except ImportError:
    # If dotenv is not installed, print a helpful message
    print("Note: python-dotenv is not installed. Using only system environment variables.")
    print("To use .env files, install python-dotenv: pip install python-dotenv")

T = TypeVar('T')

def get_env_var(
    name: str, 
    default: Optional[str] = None, 
    required: bool = False,
    as_type: Type[T] = str
) -> Union[T, None]:
    """
    Get an environment variable with type conversion and validation.
    
    Args:
        name: Name of the environment variable
        default: Default value if not found (None if not specified)
        required: If True, raises an error when the variable is not found
        as_type: Type to convert the value to (str, int, float, bool)
        
    Returns:
        The environment variable value converted to the specified type,
        or the default value if not found and not required.
        
    Raises:
        ValueError: If the variable is required but not found
    """
    value = os.environ.get(name)
    
    if value is None:
        if required:
            raise ValueError(f"Required environment variable '{name}' is not set")
        return default if default is None else _convert_value(default, as_type)
    
    return _convert_value(value, as_type)

def _convert_value(value: str, as_type: Type[T]) -> T:
    """Convert a string value to the specified type."""
    if as_type == bool:
        return cast(T, value.lower() in ('true', 'yes', '1', 'y'))
    elif as_type == int:
        return cast(T, int(value))
    elif as_type == float:
        return cast(T, float(value))
    else:
        return cast(T, value)
