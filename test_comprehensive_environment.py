#!/usr/bin/env python3
"""
Comprehensive Environment Configuration Test Suite

This script provides thorough testing of environment configuration to ensure
all components correctly use production endpoints as specified in BC_ENVIRONMENT.
"""

import os
import sys
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.config import config
from utils.env_config import get_env_var

# Test results tracking
test_results = []

def log_test_result(test_name: str, passed: bool, message: str = ""):
    """Log test result for summary."""
    test_results.append({
        'name': test_name,
        'passed': passed,
        'message': message
    })
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"   {status}: {test_name}")
    if message:
        print(f"      {message}")

def test_environment_variable_loading():
    """Test 1: Environment Variable Loading"""
    print("1. Testing Environment Variable Loading")
    
    # Test BC_ENVIRONMENT loading
    bc_env = get_env_var("BC_ENVIRONMENT", default="Not Set")
    log_test_result(
        "BC_ENVIRONMENT variable loading",
        bc_env == "Production",
        f"Expected: Production, Got: {bc_env}"
    )
    
    # Test ERP_API_URL_BASE loading
    erp_url = get_env_var("ERP_API_URL_BASE")
    if erp_url:
        log_test_result(
            "ERP_API_URL_BASE contains Production",
            "Production" in erp_url,
            f"URL: {erp_url}"
        )
    else:
        log_test_result(
            "ERP_API_URL_BASE dynamic construction",
            True,
            "URL will be constructed dynamically from BC_ENVIRONMENT"
        )
    
    print()

def test_config_class_integration():
    """Test 2: Config Class Integration"""
    print("2. Testing Config Class Integration")
    
    # Test BC_ENVIRONMENT in config
    config_env = config.get("BC_ENVIRONMENT")
    log_test_result(
        "Config BC_ENVIRONMENT",
        config_env == "Production",
        f"Expected: Production, Got: {config_env}"
    )
    
    # Test ERP_API_URL_BASE construction
    erp_base_url = config.get("ERP_API_URL_BASE")
    log_test_result(
        "Config ERP_API_URL_BASE contains Production",
        "Production" in erp_base_url,
        f"URL: {erp_base_url}"
    )
    
    # Test tenant ID consistency
    tenant_id = config.get("BC_TENANT_ID")
    expected_tenant = "6b83c27c-aa6d-475a-9933-5c34bb008d73"
    log_test_result(
        "Tenant ID consistency",
        tenant_id == expected_tenant,
        f"Expected: {expected_tenant}, Got: {tenant_id}"
    )
    
    print()

def test_api_url_generation():
    """Test 3: API URL Generation"""
    print("3. Testing API URL Generation")
    
    # Test default company URL
    default_url = config.get_api_url()
    log_test_result(
        "Default company URL contains Production",
        "Production" in default_url,
        f"URL: {default_url}"
    )
    
    # Test specific company URLs
    companies = ["VCT", "VCP", "VCA"]
    for company in companies:
        company_url = config.get_api_url(company)
        log_test_result(
            f"{company} company URL contains Production",
            "Production" in company_url,
            f"URL: {company_url}"
        )
    
    print()

def test_exchange_rate_api():
    """Test 4: Exchange Rate API Configuration"""
    print("4. Testing Exchange Rate API Configuration")
    
    try:
        from core.exchange_rate_api import ExchangeRateAPI
        
        # Test ExchangeRateAPI initialization
        exchange_api = ExchangeRateAPI()
        log_test_result(
            "Exchange Rate API base_url contains Production",
            "Production" in exchange_api.base_url,
            f"URL: {exchange_api.base_url}"
        )
        
        # Test tenant ID consistency
        log_test_result(
            "Exchange Rate API tenant ID consistency",
            exchange_api.tenant_id == config.get("BC_TENANT_ID"),
            f"API: {exchange_api.tenant_id}, Config: {config.get('BC_TENANT_ID')}"
        )
        
    except Exception as e:
        log_test_result(
            "Exchange Rate API initialization",
            False,
            f"Error: {str(e)}"
        )
    
    print()

def test_environment_switching():
    """Test 5: Environment Switching Behavior"""
    print("5. Testing Environment Switching Behavior")
    
    # Test with different environment values
    test_environments = ["Production", "Staging", "Development"]
    
    # Save current environment variables that are required
    required_vars = {
        "BC_CLIENT_ID": get_env_var("BC_CLIENT_ID"),
        "BC_CLIENT_SECRET": get_env_var("BC_CLIENT_SECRET"),
        "BC_TENANT_ID": get_env_var("BC_TENANT_ID", default="6b83c27c-aa6d-475a-9933-5c34bb008d73")
    }
    
    for test_env in test_environments:
        # Create environment with required vars plus test environment
        test_env_vars = required_vars.copy()
        test_env_vars["BC_ENVIRONMENT"] = test_env
        
        with patch.dict(os.environ, test_env_vars, clear=True):
            # Import fresh modules to avoid singleton caching
            import importlib
            import sys
            
            # Remove cached modules to force reload
            modules_to_reload = [
                'utils.config',
                'utils.env_config'
            ]
            for module in modules_to_reload:
                if module in sys.modules:
                    del sys.modules[module]
            
            # Import fresh config
            from utils.config import Config
            test_config = Config()
            
            erp_url = test_config.get("ERP_API_URL_BASE")
            log_test_result(
                f"Environment switching to {test_env}",
                test_env in erp_url,
                f"URL contains {test_env}: {erp_url}"
            )
    
    print()

def test_fallback_behavior():
    """Test 6: Fallback Behavior"""
    print("6. Testing Fallback Behavior")
    
    # Save current required environment variables
    required_vars = {
        "BC_CLIENT_ID": get_env_var("BC_CLIENT_ID"),
        "BC_CLIENT_SECRET": get_env_var("BC_CLIENT_SECRET"),
        "BC_TENANT_ID": get_env_var("BC_TENANT_ID", default="6b83c27c-aa6d-475a-9933-5c34bb008d73")
    }
    
    # Test behavior when BC_ENVIRONMENT is not set (but keep required vars)
    with patch.dict(os.environ, required_vars, clear=True):
        from utils.config import Config
        fallback_config = Config()
        
        bc_env = fallback_config.get("BC_ENVIRONMENT")
        log_test_result(
            "Fallback to Production when BC_ENVIRONMENT not set",
            bc_env == "Production",
            f"Fallback value: {bc_env}"
        )
        
        erp_url = fallback_config.get("ERP_API_URL_BASE")
        log_test_result(
            "Fallback ERP URL contains Production",
            "Production" in erp_url,
            f"Fallback URL: {erp_url}"
        )
    
    print()

def test_logging_verification():
    """Test 7: Logging Verification"""
    print("7. Testing Logging Configuration")
    
    # Test logging configuration
    log_level = config.get("LOG_LEVEL")
    log_file = config.get("LOG_FILE")
    
    log_test_result(
        "Log level configuration",
        log_level in ["DEBUG", "INFO", "WARNING", "ERROR"],
        f"Log level: {log_level}"
    )
    
    log_test_result(
        "Log file configuration",
        log_file is not None and len(log_file) > 0,
        f"Log file: {log_file}"
    )
    
    print()

def test_all_url_consistency():
    """Test 8: All URL Consistency Check"""
    print("8. Testing All URL Consistency")
    
    # Collect all URLs from configuration
    urls_to_check = {
        "ERP_API_URL_BASE": config.get("ERP_API_URL_BASE"),
        "ERP_TOKEN_URL": config.get("ERP_TOKEN_URL"),
        "Default Company URL": config.get_api_url(),
        "VCT Company URL": config.get_api_url("VCT"),
        "VCP Company URL": config.get_api_url("VCP"),
        "VCA Company URL": config.get_api_url("VCA"),
    }
    
    # Check Exchange Rate API if available
    try:
        from core.exchange_rate_api import ExchangeRateAPI
        exchange_api = ExchangeRateAPI()
        urls_to_check["Exchange Rate API URL"] = exchange_api.base_url
    except:
        pass
    
    # Verify all URLs point to correct environment
    environment = config.get("BC_ENVIRONMENT", "Production")
    
    for url_name, url_value in urls_to_check.items():
        if url_value and "api.businesscentral.dynamics.com" in url_value:
            log_test_result(
                f"{url_name} environment consistency",
                environment in url_value,
                f"URL: {url_value}"
            )
        else:
            log_test_result(
                f"{url_name} configuration",
                url_value is not None,
                f"Value: {url_value}"
            )
    
    print()

def test_security_configuration():
    """Test 9: Security Configuration"""
    print("9. Testing Security Configuration")
    
    # Test SSL verification settings
    bc_verify_ssl = config.get("BC_VERIFY_SSL")
    erp_verify_ssl = config.get("ERP_VERIFY_SSL")
    
    log_test_result(
        "BC SSL verification enabled",
        bc_verify_ssl is True,
        f"BC_VERIFY_SSL: {bc_verify_ssl}"
    )
    
    log_test_result(
        "ERP SSL verification enabled",
        erp_verify_ssl is True,
        f"ERP_VERIFY_SSL: {erp_verify_ssl}"
    )
    
    # Test that sensitive values are loaded
    client_id = config.get("BC_CLIENT_ID")
    client_secret = config.get("BC_CLIENT_SECRET")
    
    log_test_result(
        "Client ID configured",
        client_id is not None and len(client_id) > 0,
        "Client ID is set"
    )
    
    log_test_result(
        "Client Secret configured",
        client_secret is not None and len(client_secret) > 0,
        "Client Secret is set"
    )
    
    print()

def print_summary():
    """Print test summary."""
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = [t for t in test_results if t['passed']]
    failed_tests = [t for t in test_results if not t['passed']]
    
    print(f"Total Tests: {len(test_results)}")
    print(f"Passed: {len(passed_tests)}")
    print(f"Failed: {len(failed_tests)}")
    print()
    
    if failed_tests:
        print("FAILED TESTS:")
        for test in failed_tests:
            print(f"  ❌ {test['name']}")
            if test['message']:
                print(f"     {test['message']}")
        print()
    
    if len(passed_tests) == len(test_results):
        print("🎉 ALL TESTS PASSED! Environment configuration is correct.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the configuration.")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("COMPREHENSIVE ENVIRONMENT CONFIGURATION TEST")
    print("=" * 60)
    print()
    
    # Run all test functions
    test_environment_variable_loading()
    test_config_class_integration()
    test_api_url_generation()
    test_exchange_rate_api()
    test_environment_switching()
    test_fallback_behavior()
    test_logging_verification()
    test_all_url_consistency()
    test_security_configuration()
    
    # Print summary
    success = print_summary()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
