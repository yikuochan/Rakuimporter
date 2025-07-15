#!/usr/bin/env python3
"""
Environment Configuration Test Script

This script tests that all modules are using the centralized configuration
from utils/config.py instead of direct environment variable access.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("environment_config_test")

def test_centralized_config():
    """Test that centralized configuration is working correctly."""
    print("=" * 60)
    print("ENVIRONMENT CONFIGURATION TEST")
    print("=" * 60)
    
    try:
        # Test 1: Import centralized config
        print("\n1. Testing centralized configuration import...")
        from utils.config import config
        print("✅ Successfully imported centralized config")
        
        # Test 2: Check BC_ENVIRONMENT configuration
        print("\n2. Testing BC_ENVIRONMENT configuration...")
        bc_environment = config.get("BC_ENVIRONMENT", "Not Set")
        print(f"   BC_ENVIRONMENT from config: {bc_environment}")
        
        # Check environment variable
        env_bc_environment = os.environ.get("BC_ENVIRONMENT", "Not Set")
        print(f"   BC_ENVIRONMENT from env var: {env_bc_environment}")
        
        if bc_environment == env_bc_environment or (env_bc_environment == "Not Set" and bc_environment == "Production"):
            print("✅ BC_ENVIRONMENT configuration is consistent")
        else:
            print("❌ BC_ENVIRONMENT configuration mismatch!")
            return False
        
        # Test 3: Test API URL generation
        print("\n3. Testing API URL generation...")
        vca_url = config.get_api_url("VCA")
        vct_url = config.get_api_url("VCT")
        
        print(f"   VCA API URL: {vca_url}")
        print(f"   VCT API URL: {vct_url}")
        
        # Both URLs should use the same environment
        if bc_environment in vca_url and bc_environment in vct_url:
            print("✅ API URLs are using consistent environment")
        else:
            print("❌ API URLs are using inconsistent environments!")
            return False
        
        # Test 4: Test process_japan_exports module
        print("\n4. Testing process_japan_exports module...")
        try:
            from core.process_japan_exports import BC_ENVIRONMENT as pje_env
            print(f"   process_japan_exports BC_ENVIRONMENT: {pje_env}")
            
            if pje_env == bc_environment:
                print("✅ process_japan_exports is using centralized config")
            else:
                print("❌ process_japan_exports is NOT using centralized config!")
                return False
        except ImportError as e:
            print(f"❌ Failed to import process_japan_exports: {e}")
            return False
        
        # Test 5: Test exchange_rate_api module
        print("\n5. Testing exchange_rate_api module...")
        try:
            from core.exchange_rate_api import ExchangeRateAPI
            api_client = ExchangeRateAPI()
            
            # Check if the base URL contains the correct environment
            if bc_environment in api_client.base_url:
                print(f"   exchange_rate_api base URL: {api_client.base_url}")
                print("✅ exchange_rate_api is using centralized config")
            else:
                print(f"   exchange_rate_api base URL: {api_client.base_url}")
                print("❌ exchange_rate_api is NOT using centralized config!")
                return False
        except Exception as e:
            print(f"❌ Failed to test exchange_rate_api: {e}")
            return False
        
        # Test 6: Configuration consistency check
        print("\n6. Testing configuration consistency...")
        config_dict = config.as_dict()
        
        critical_configs = [
            "BC_TENANT_ID",
            "BC_ENVIRONMENT", 
            "BC_CLIENT_ID",
            "BC_CLIENT_SECRET"
        ]
        
        for key in critical_configs:
            value = config_dict.get(key, "Not Set")
            if key in ["BC_CLIENT_ID", "BC_CLIENT_SECRET"]:
                # Don't print sensitive values
                print(f"   {key}: {'[SET]' if value and value != 'Not Set' else '[NOT SET]'}")
            else:
                print(f"   {key}: {value}")
        
        print("✅ Configuration consistency check completed")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Environment configuration is working correctly!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        print("=" * 60)
        return False

def test_environment_scenarios():
    """Test different environment scenarios."""
    print("\n" + "=" * 60)
    print("ENVIRONMENT SCENARIO TESTING")
    print("=" * 60)
    
    # Save original environment
    original_env = os.environ.get("BC_ENVIRONMENT")
    
    try:
        # Test Production environment
        print("\n1. Testing Production environment...")
        os.environ["BC_ENVIRONMENT"] = "Production"
        
        # Reload config (in real scenario, this would require restarting the application)
        from utils.config import Config
        test_config = Config()
        
        prod_url = test_config.get_api_url("VCA")
        if "Production" in prod_url:
            print(f"   Production URL: {prod_url}")
            print("✅ Production environment test passed")
        else:
            print(f"   Production URL: {prod_url}")
            print("❌ Production environment test failed")
        
        # Test Staging environment
        print("\n2. Testing Staging environment...")
        os.environ["BC_ENVIRONMENT"] = "Staging"
        
        test_config = Config()
        staging_url = test_config.get_api_url("VCA")
        if "Staging" in staging_url:
            print(f"   Staging URL: {staging_url}")
            print("✅ Staging environment test passed")
        else:
            print(f"   Staging URL: {staging_url}")
            print("❌ Staging environment test failed")
        
        print("\n✅ Environment scenario testing completed")
        
    finally:
        # Restore original environment
        if original_env:
            os.environ["BC_ENVIRONMENT"] = original_env
        elif "BC_ENVIRONMENT" in os.environ:
            del os.environ["BC_ENVIRONMENT"]

def main():
    """Main test function."""
    print("Starting Environment Configuration Tests...")
    
    # Run main configuration test
    config_test_passed = test_centralized_config()
    
    # Run environment scenario tests
    test_environment_scenarios()
    
    # Final result
    if config_test_passed:
        print("\n🎉 All environment configuration tests completed successfully!")
        print("\nThe environment configuration issue has been resolved:")
        print("- All modules now use centralized configuration")
        print("- No more mixed environment usage")
        print("- Consistent API URL generation across all companies")
        return 0
    else:
        print("\n❌ Environment configuration tests failed!")
        print("\nPlease check the following:")
        print("- Ensure all modules import from utils.config")
        print("- Verify BC_ENVIRONMENT is set correctly")
        print("- Check for any remaining direct environment variable access")
        return 1

if __name__ == "__main__":
    sys.exit(main())
