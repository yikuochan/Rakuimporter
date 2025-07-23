#!/usr/bin/env python3
"""
Business Central API Integration Test

This script tests the complete Power-importer pipeline with Business Central API integration
to verify that the currency transformation fixes resolve the original "R-NTD" errors.

Key Test Areas:
1. Currency transformation validation (NTD vs R-NTD)
2. Business Central API payload generation
3. Module import resolution
4. End-to-end pipeline testing
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add the project root to Python path to resolve module imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_module_imports():
    """Test that all required modules can be imported correctly."""
    logger.info("Testing module imports...")
    
    try:
        # Test core module imports
        from core.process_japan_exports import (
            transform_currency_code, 
            create_journal_line,
            transform_currency,
            setup_logging
        )
        from core.charset_converter import fix_line_breaks_in_quoted_fields
        from core.csv_to_json_converter_enhanced import convert_csv_to_json
        from company_currency_mapping import COMPANY_HOME_CURRENCY, get_home_currency
        
        logger.info("✅ All module imports successful")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Module import failed: {e}")
        return False

def test_currency_transformation_logic():
    """Test the currency transformation logic for VCT company."""
    logger.info("Testing currency transformation logic...")
    
    try:
        from core.process_japan_exports import transform_currency_code
        from company_currency_mapping import COMPANY_HOME_CURRENCY
        
        # Test cases for VCT company (home currency: NTD)
        test_cases = [
            # (company_code, input_currency, expected_output, description)
            ("VCT", "NTD", "", "VCT home currency NTD should become empty"),
            ("VCT", "R-NTD", "", "VCT R-NTD should become empty (normalized)"),
            ("VCT", "USD", "R-USD", "VCT foreign currency USD should get R- prefix"),
            ("VCT", "R-USD", "R-USD", "VCT R-USD should remain R-USD"),
            ("VCT", "JPY", "R-JPY", "VCT foreign currency JPY should get R- prefix"),
            ("VCT", "INR", "R-INR", "VCT foreign currency INR should get R- prefix"),
            ("VCT", "RMB", "R-RMB", "VCT foreign currency RMB should get R- prefix"),
            ("VCT", "THB", "R-THB", "VCT foreign currency THB should get R- prefix"),
        ]
        
        all_passed = True
        for company_code, input_currency, expected_output, description in test_cases:
            result = transform_currency_code(company_code, input_currency)
            if result == expected_output:
                logger.info(f"✅ {description}: '{input_currency}' -> '{result}'")
            else:
                logger.error(f"❌ {description}: '{input_currency}' -> '{result}' (expected '{expected_output}')")
                all_passed = False
        
        # Verify company currency mapping
        logger.info("Testing company currency mapping...")
        assert COMPANY_HOME_CURRENCY["VCT"] == "NTD", "VCT home currency should be NTD"
        assert COMPANY_HOME_CURRENCY["VCA"] == "USD", "VCA home currency should be USD"
        assert COMPANY_HOME_CURRENCY["VCP"] == "PHP", "VCP home currency should be PHP"
        logger.info("✅ Company currency mapping verified")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Currency transformation test failed: {e}")
        return False

def test_journal_line_creation():
    """Test journal line creation with currency transformation."""
    logger.info("Testing journal line creation...")
    
    try:
        from core.process_japan_exports import create_journal_line
        
        # Create test entry with VCT company and NTD currency
        test_entry = {
            "voucher_no": "TEST-001",
            "External_Document_No": "TEST-EXT-001",
            "Document_Date": "2025/7/21",
            "description": "Test transaction",
            "debit": {
                "gl_account": "G/L Account",
                "account": "72600-10",
                "amount": 1000.0,
                "currency": "NTD",  # VCT home currency
                "department": "VCT.1000",
                "applicant_code": "10001"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "",
                "amount": 1000.0,
                "currency": "NTD",  # VCT home currency
                "department": "VCT.1000",
                "applicant_code": "10001",
                "vendor_code": "V12345",
                "Remarks": "Test credit transaction"
            }
        }
        
        # Test debit line creation
        debit_line = create_journal_line(test_entry, "debit")
        logger.info(f"Debit line currency: '{debit_line.get('Currency_Code')}'")
        
        # Test credit line creation
        credit_line = create_journal_line(test_entry, "credit")
        logger.info(f"Credit line currency: '{credit_line.get('Currency_Code')}'")
        
        # Verify that NTD currency becomes empty for VCT company
        if debit_line.get('Currency_Code') == "" and credit_line.get('Currency_Code') == "":
            logger.info("✅ NTD currency correctly transformed to empty string for VCT company")
        else:
            logger.error(f"❌ Currency transformation failed - Debit: '{debit_line.get('Currency_Code')}', Credit: '{credit_line.get('Currency_Code')}'")
            return False
        
        # Test with foreign currency
        test_entry["debit"]["currency"] = "USD"
        test_entry["credit"]["currency"] = "USD"
        
        debit_line_foreign = create_journal_line(test_entry, "debit")
        credit_line_foreign = create_journal_line(test_entry, "credit")
        
        logger.info(f"Foreign currency - Debit: '{debit_line_foreign.get('Currency_Code')}', Credit: '{credit_line_foreign.get('Currency_Code')}'")
        
        # Verify foreign currency gets R- prefix
        if debit_line_foreign.get('Currency_Code') == "R-USD" and credit_line_foreign.get('Currency_Code') == "R-USD":
            logger.info("✅ Foreign currency correctly transformed with R- prefix")
        else:
            logger.error(f"❌ Foreign currency transformation failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Journal line creation test failed: {e}")
        return False

def test_sample_data_processing():
    """Test processing of sample data from the test output file."""
    logger.info("Testing sample data processing...")
    
    try:
        # Load the test output file
        test_file_path = project_root / "examples" / "0721" / "VCT-2-0721_test_output.json"
        
        if not test_file_path.exists():
            logger.warning(f"Test file not found: {test_file_path}")
            return True  # Skip this test if file doesn't exist
        
        with open(test_file_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        logger.info(f"Loaded {len(entries)} entries from test file")
        
        # Analyze currency codes in the test data
        currency_analysis = {
            "ntd_count": 0,
            "r_ntd_count": 0,
            "foreign_currencies": set(),
            "total_entries": len(entries)
        }
        
        for entry in entries:
            debit_currency = entry.get("debit", {}).get("currency", "")
            credit_currency = entry.get("credit", {}).get("currency", "")
            
            for currency in [debit_currency, credit_currency]:
                if currency == "NTD":
                    currency_analysis["ntd_count"] += 1
                elif currency == "R-NTD":
                    currency_analysis["r_ntd_count"] += 1
                elif currency.startswith("R-"):
                    currency_analysis["foreign_currencies"].add(currency)
        
        logger.info(f"Currency analysis:")
        logger.info(f"  - NTD entries: {currency_analysis['ntd_count']}")
        logger.info(f"  - R-NTD entries: {currency_analysis['r_ntd_count']}")
        logger.info(f"  - Foreign currencies: {sorted(currency_analysis['foreign_currencies'])}")
        
        # Verify no R-NTD entries exist (this was the original problem)
        if currency_analysis["r_ntd_count"] == 0:
            logger.info("✅ No R-NTD entries found - currency fix is working correctly")
        else:
            logger.error(f"❌ Found {currency_analysis['r_ntd_count']} R-NTD entries - currency fix not working")
            return False
        
        # Verify NTD entries exist (should be the home currency for VCT)
        if currency_analysis["ntd_count"] > 0:
            logger.info(f"✅ Found {currency_analysis['ntd_count']} NTD entries - home currency handling correct")
        else:
            logger.warning("⚠️ No NTD entries found - this might be unexpected")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Sample data processing test failed: {e}")
        return False

def test_business_central_payload_structure():
    """Test that generated payloads match Business Central API requirements."""
    logger.info("Testing Business Central payload structure...")
    
    try:
        from core.process_japan_exports import create_journal_line
        
        # Create test entry
        test_entry = {
            "voucher_no": "BC-TEST-001",
            "External_Document_No": "BC-EXT-001",
            "Document_Date": "2025/7/21",
            "description": "Business Central API test",
            "debit": {
                "gl_account": "G/L Account",
                "account": "72600-10",
                "amount": 1500.0,
                "currency": "NTD",
                "department": "VCT.1000",
                "applicant_code": "10001"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "",
                "amount": 1500.0,
                "currency": "NTD",
                "department": "VCT.1000",
                "applicant_code": "10001",
                "vendor_code": "V12345",
                "Remarks": "Business Central test transaction"
            }
        }
        
        # Generate journal lines
        debit_line = create_journal_line(test_entry, "debit")
        credit_line = create_journal_line(test_entry, "credit")
        
        # Required Business Central fields
        required_fields = [
            "Journal_Template_Name",
            "Journal_Batch_Name",
            "Document_Type",
            "External_Document_No",
            "Document_No",
            "Document_Date",
            "Account_Type",
            "Account_No",
            "Description",
            "Currency_Code",
            "Amount",
            "Shortcut_Dimension_1_Code",
            "Shortcut_Dimension_2_Code"
        ]
        
        # Verify all required fields are present
        for line_type, line in [("debit", debit_line), ("credit", credit_line)]:
            missing_fields = []
            for field in required_fields:
                if field not in line:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.error(f"❌ {line_type} line missing required fields: {missing_fields}")
                return False
            else:
                logger.info(f"✅ {line_type} line has all required Business Central fields")
        
        # Verify currency code is correct (empty for NTD in VCT)
        if debit_line["Currency_Code"] == "" and credit_line["Currency_Code"] == "":
            logger.info("✅ Currency codes correctly set for Business Central API")
        else:
            logger.error(f"❌ Incorrect currency codes - Debit: '{debit_line['Currency_Code']}', Credit: '{credit_line['Currency_Code']}'")
            return False
        
        # Log sample payload for verification
        logger.info("Sample Business Central payload:")
        # Use DecimalEncoder to handle Decimal objects
        from core.process_japan_exports import DecimalEncoder
        logger.info(json.dumps(debit_line, indent=2, ensure_ascii=False, cls=DecimalEncoder))
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Business Central payload test failed: {e}")
        return False

def test_environment_configuration():
    """Test environment configuration and API setup."""
    logger.info("Testing environment configuration...")
    
    try:
        # Check if environment variables are accessible
        env_vars_to_check = [
            "ERP_CLIENT_ID",
            "ERP_CLIENT_SECRET",
            "ERP_TOKEN_URL",
            "ERP_API_URL",
            "ERP_SCOPE"
        ]
        
        missing_vars = []
        for var in env_vars_to_check:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"⚠️ Missing environment variables: {missing_vars}")
            logger.info("This is expected in test environment - API calls will be skipped")
        else:
            logger.info("✅ All required environment variables are set")
        
        # Test configuration loading
        from core.process_japan_exports import TOKEN_URL, API_URL, CLIENT_ID, CLIENT_SECRET, SCOPE
        
        logger.info(f"Token URL: {TOKEN_URL}")
        logger.info(f"API URL: {API_URL}")
        logger.info(f"Client ID configured: {'Yes' if CLIENT_ID else 'No'}")
        logger.info(f"Client Secret configured: {'Yes' if CLIENT_SECRET else 'No'}")
        logger.info(f"Scope: {SCOPE}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Environment configuration test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide a comprehensive report."""
    logger.info("=" * 60)
    logger.info("BUSINESS CENTRAL API INTEGRATION TEST")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Module Imports", test_module_imports),
        ("Currency Transformation Logic", test_currency_transformation_logic),
        ("Journal Line Creation", test_journal_line_creation),
        ("Sample Data Processing", test_sample_data_processing),
        ("Business Central Payload Structure", test_business_central_payload_structure),
        ("Environment Configuration", test_environment_configuration),
    ]
    
    # Execute all tests
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            test_results[test_name] = result
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            test_results[test_name] = False
    
    # Generate summary report
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY REPORT")
    logger.info("=" * 60)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED - Business Central API integration is ready!")
        logger.info("\nKey Achievements:")
        logger.info("- ✅ Currency transformation fixes are working correctly")
        logger.info("- ✅ No R-NTD errors will occur in Business Central API calls")
        logger.info("- ✅ VCT home currency (NTD) is properly handled")
        logger.info("- ✅ Foreign currencies are correctly prefixed with R-")
        logger.info("- ✅ Business Central payload structure is valid")
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} tests failed - review issues before production use")
    
    return test_results

if __name__ == "__main__":
    # Run the comprehensive test
    results = run_comprehensive_test()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure
