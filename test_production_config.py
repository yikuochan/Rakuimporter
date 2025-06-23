#!/usr/bin/env python3
"""
Test script to verify that the configuration is correctly pointing to production endpoints.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.config import config
from core.exchange_rate_api import ExchangeRateAPI
from utils.env_config import get_env_var

def test_configuration():
    """Test that configuration is correctly loading production endpoints."""
    print("=== Testing Production Configuration ===\n")
    
    # Test 1: Check environment variables
    print("1. Environment Variables:")
    bc_environment = get_env_var("BC_ENVIRONMENT", default="Not Set")
    erp_api_url_base = get_env_var("ERP_API_URL_BASE", default="Not Set")
    
    print(f"   BC_ENVIRONMENT: {bc_environment}")
    print(f"   ERP_API_URL_BASE: {erp_api_url_base}")
    
    # Check if URLs contain "Production"
    if "Production" in erp_api_url_base:
        print("   ✅ ERP_API_URL_BASE correctly points to Production")
    else:
        print("   ❌ ERP_API_URL_BASE does NOT point to Production")
    
    print()
    
    # Test 2: Check config class
    print("2. Config Class:")
    config_api_url = config.get("ERP_API_URL_BASE")
    print(f"   Config ERP_API_URL_BASE: {config_api_url}")
    
    if "Production" in config_api_url:
        print("   ✅ Config correctly points to Production")
    else:
        print("   ❌ Config does NOT point to Production")
    
    print()
    
    # Test 3: Check ExchangeRateAPI
    print("3. Exchange Rate API:")
    try:
        exchange_api = ExchangeRateAPI()
        print(f"   Exchange API base_url: {exchange_api.base_url}")
        
        if "Production" in exchange_api.base_url:
            print("   ✅ Exchange Rate API correctly points to Production")
        else:
            print("   ❌ Exchange Rate API does NOT point to Production")
    except Exception as e:
        print(f"   ❌ Error initializing Exchange Rate API: {e}")
    
    print()
    
    # Test 4: Check API URL generation
    print("4. API URL Generation:")
    try:
        api_url_vct = config.get_api_url("VCT")
        print(f"   API URL for VCT: {api_url_vct}")
        
        if "Production" in api_url_vct:
            print("   ✅ Generated API URL correctly points to Production")
        else:
            print("   ❌ Generated API URL does NOT point to Production")
    except Exception as e:
        print(f"   ❌ Error generating API URL: {e}")
    
    print()
    
    # Summary
    print("=== Summary ===")
    production_checks = [
        "Production" in erp_api_url_base,
        "Production" in config_api_url,
        "Production" in exchange_api.base_url if 'exchange_api' in locals() else False,
        "Production" in api_url_vct if 'api_url_vct' in locals() else False
    ]
    
    passed_checks = sum(production_checks)
    total_checks = len(production_checks)
    
    print(f"Production endpoint checks: {passed_checks}/{total_checks} passed")
    
    if passed_checks == total_checks:
        print("🎉 All configuration correctly points to Production!")
        return True
    else:
        print("⚠️  Some configuration still points to Staging!")
        return False

if __name__ == "__main__":
    success = test_configuration()
    sys.exit(0 if success else 1)
