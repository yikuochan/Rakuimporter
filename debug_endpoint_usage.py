#!/usr/bin/env python3
"""
Debug Endpoint Usage Script

This script adds temporary debug logging to help verify that all API calls
are going to the correct production endpoints during actual operations.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.config import config
from utils.env_config import get_env_var

def setup_debug_logging():
    """Set up debug logging to track endpoint usage."""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Set up debug logger
    debug_logger = logging.getLogger("endpoint_debug")
    debug_logger.setLevel(logging.DEBUG)
    
    # Create file handler for debug logs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_file = logs_dir / f"endpoint_debug_{timestamp}.log"
    
    file_handler = logging.FileHandler(debug_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Create console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    debug_logger.addHandler(file_handler)
    debug_logger.addHandler(console_handler)
    
    return debug_logger, debug_file

def log_configuration_state(logger):
    """Log current configuration state for debugging."""
    logger.info("=" * 60)
    logger.info("CONFIGURATION STATE DEBUG")
    logger.info("=" * 60)
    
    # Log environment variables
    logger.info("Environment Variables:")
    logger.info(f"  BC_ENVIRONMENT: {get_env_var('BC_ENVIRONMENT', 'Not Set')}")
    logger.info(f"  BC_TENANT_ID: {get_env_var('BC_TENANT_ID', 'Not Set')}")
    logger.info(f"  BC_COMPANY: {get_env_var('BC_COMPANY', 'Not Set')}")
    
    # Log configuration values
    logger.info("Configuration Values:")
    logger.info(f"  BC_ENVIRONMENT: {config.get('BC_ENVIRONMENT')}")
    logger.info(f"  BC_TENANT_ID: {config.get('BC_TENANT_ID')}")
    logger.info(f"  BC_COMPANY: {config.get('BC_COMPANY')}")
    logger.info(f"  ERP_API_URL_BASE: {config.get('ERP_API_URL_BASE')}")
    
    # Log generated URLs
    logger.info("Generated URLs:")
    logger.info(f"  Default Company URL: {config.get_api_url()}")
    logger.info(f"  VCT Company URL: {config.get_api_url('VCT')}")
    logger.info(f"  VCP Company URL: {config.get_api_url('VCP')}")
    logger.info(f"  VCA Company URL: {config.get_api_url('VCA')}")
    
    # Log Exchange Rate API if available
    try:
        from core.exchange_rate_api import ExchangeRateAPI
        exchange_api = ExchangeRateAPI()
        logger.info(f"  Exchange Rate API URL: {exchange_api.base_url}")
    except Exception as e:
        logger.warning(f"  Exchange Rate API: Error loading - {e}")
    
    logger.info("=" * 60)

def create_endpoint_monitor():
    """Create a monitoring function that can be used to track API calls."""
    
    def monitor_api_call(url, method="GET", company=None, description="API Call"):
        """Monitor and log API calls."""
        logger = logging.getLogger("endpoint_debug")
        
        # Determine environment from URL
        if "api.businesscentral.dynamics.com" in url:
            if "/Production/" in url:
                environment = "Production"
                status = "✅ CORRECT"
            elif "/Staging/" in url:
                environment = "Staging"
                status = "❌ INCORRECT"
            else:
                environment = "Unknown"
                status = "⚠️  UNKNOWN"
        else:
            environment = "External"
            status = "ℹ️  EXTERNAL"
        
        # Log the API call
        logger.info(f"{status} {description}")
        logger.info(f"  Method: {method}")
        logger.info(f"  URL: {url}")
        logger.info(f"  Environment: {environment}")
        if company:
            logger.info(f"  Company: {company}")
        logger.info("-" * 40)
        
        # Return status for programmatic use
        return {
            "url": url,
            "method": method,
            "environment": environment,
            "is_production": environment == "Production",
            "company": company,
            "description": description
        }
    
    return monitor_api_call

def test_endpoint_monitoring():
    """Test the endpoint monitoring functionality."""
    logger, debug_file = setup_debug_logging()
    monitor = create_endpoint_monitor()
    
    logger.info("Testing Endpoint Monitoring Functionality")
    logger.info("=" * 60)
    
    # Test various URL patterns
    test_urls = [
        {
            "url": config.get_api_url("VCT"),
            "method": "POST",
            "company": "VCT",
            "description": "VCT Journal Entry"
        },
        {
            "url": config.get_api_url("VCP"),
            "method": "POST", 
            "company": "VCP",
            "description": "VCP Journal Entry"
        },
        {
            "url": config.get_api_url("VCA"),
            "method": "POST",
            "company": "VCA", 
            "description": "VCA Journal Entry"
        },
        {
            "url": "https://api.businesscentral.dynamics.com/v2.0/6b83c27c-aa6d-475a-9933-5c34bb008d73/Staging/ODataV4/Company('VCT')/PurchaseJournals",
            "method": "POST",
            "company": "VCT",
            "description": "STAGING URL (Should be flagged as incorrect)"
        }
    ]
    
    # Test Exchange Rate API URL if available
    try:
        from core.exchange_rate_api import ExchangeRateAPI
        exchange_api = ExchangeRateAPI()
        test_urls.append({
            "url": f"{exchange_api.base_url}/Company('VCT')/Currencies",
            "method": "GET",
            "company": "VCT",
            "description": "Exchange Rate API Call"
        })
    except:
        pass
    
    # Monitor all test URLs
    results = []
    for test_case in test_urls:
        result = monitor(**test_case)
        results.append(result)
    
    # Summary
    logger.info("=" * 60)
    logger.info("MONITORING TEST SUMMARY")
    logger.info("=" * 60)
    
    production_calls = [r for r in results if r["is_production"]]
    non_production_calls = [r for r in results if not r["is_production"] and "businesscentral" in r["url"]]
    
    logger.info(f"Total API calls monitored: {len(results)}")
    logger.info(f"Production calls: {len(production_calls)}")
    logger.info(f"Non-production calls: {len(non_production_calls)}")
    
    if non_production_calls:
        logger.warning("NON-PRODUCTION CALLS DETECTED:")
        for call in non_production_calls:
            logger.warning(f"  - {call['description']}: {call['url']}")
    else:
        logger.info("✅ All Business Central API calls are going to Production!")
    
    logger.info(f"Debug log saved to: {debug_file}")
    
    return len(non_production_calls) == 0

def create_integration_test():
    """Create an integration test that simulates actual workflow."""
    
    def run_integration_test():
        """Run integration test with endpoint monitoring."""
        logger, debug_file = setup_debug_logging()
        monitor = create_endpoint_monitor()
        
        logger.info("INTEGRATION TEST: Simulating Full Workflow")
        logger.info("=" * 60)
        
        # Log current configuration
        log_configuration_state(logger)
        
        # Simulate the workflow steps
        companies = ["VCT", "VCP", "VCA"]
        all_production = True
        
        for company in companies:
            logger.info(f"Processing company: {company}")
            
            # Simulate getting exchange rate
            try:
                from core.exchange_rate_api import ExchangeRateAPI
                exchange_api = ExchangeRateAPI()
                exchange_url = f"{exchange_api.base_url}/Company('{company}')/Currencies"
                result = monitor(exchange_url, "GET", company, f"{company} Exchange Rate Lookup")
                if not result["is_production"]:
                    all_production = False
            except Exception as e:
                logger.warning(f"Exchange Rate API test failed for {company}: {e}")
            
            # Simulate posting journal entry
            journal_url = config.get_api_url(company)
            result = monitor(journal_url, "POST", company, f"{company} Journal Entry Post")
            if not result["is_production"]:
                all_production = False
        
        # Final assessment
        logger.info("=" * 60)
        logger.info("INTEGRATION TEST RESULTS")
        logger.info("=" * 60)
        
        if all_production:
            logger.info("🎉 SUCCESS: All API calls in workflow use Production endpoints!")
        else:
            logger.error("❌ FAILURE: Some API calls are not using Production endpoints!")
        
        logger.info(f"Full debug log available at: {debug_file}")
        
        return all_production
    
    return run_integration_test

def main():
    """Main function to run endpoint debugging."""
    print("Debug Endpoint Usage Tool")
    print("=" * 40)
    print()
    print("This tool helps verify that all API calls are going to production endpoints.")
    print()
    
    # Test basic monitoring
    print("1. Testing endpoint monitoring...")
    monitoring_success = test_endpoint_monitoring()
    
    print()
    print("2. Running integration test...")
    integration_test = create_integration_test()
    integration_success = integration_test()
    
    print()
    print("=" * 40)
    print("FINAL RESULTS")
    print("=" * 40)
    
    if monitoring_success and integration_success:
        print("✅ All tests passed! Endpoints are correctly configured for Production.")
        return True
    else:
        print("❌ Some tests failed. Please review the debug logs.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
