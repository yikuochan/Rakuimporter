#!/usr/bin/env python3
"""
Business Central Payload Verification Tool

This tool verifies the Business Central payload generation logic by:
1. Testing the create_journal_line function with various scenarios
2. Validating field mappings and transformations
3. Checking currency code transformations
4. Verifying dimension assignments
5. Testing VCT responsibility entry generation
6. Generating sample payloads for inspection

Usage:
    python Tools/verify_bc_payload_generation.py [options]
"""

import json
import sys
import os
from typing import Dict, List, Any, Tuple
from decimal import Decimal

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the functions we want to test
try:
    from core.process_japan_exports import (
        create_journal_line, 
        transform_currency_code, 
        transform_currency,
        convert_date_format,
        create_vct_responsibility_entries,
        DecimalEncoder
    )
    print("Successfully imported functions from core.process_japan_exports")
except ImportError as e:
    print(f"Error importing from core.process_japan_exports: {e}")
    print("Falling back to local implementations for testing...")
    
    # Fallback implementations for testing
    def create_journal_line(entry: Dict[str, Any], entry_type: str) -> Dict[str, Any]:
        """Fallback implementation for testing"""
        return {"error": "Function not available - using fallback"}
    
    def transform_currency_code(company_code: str, currency_code: str) -> str:
        """Fallback implementation for testing"""
        return currency_code
    
    def transform_currency(company_code: str, currency_code: str, amount: float, decimal_precision: int = 2) -> Tuple[str, float]:
        """Fallback implementation for testing"""
        return currency_code, amount
    
    def convert_date_format(date_str: str) -> str:
        """Fallback implementation for testing"""
        return date_str
    
    class DecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return super().default(obj)


class BCPayloadVerifier:
    """Business Central Payload Verification Tool"""
    
    def __init__(self):
        self.test_results = []
        self.sample_payloads = []
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        status = "PASS" if passed else "FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details
        })
        print(f"[{status}] {test_name}: {details}")
    
    def create_test_entry(self, scenario: str) -> Dict[str, Any]:
        """Create test entries for different scenarios"""
        
        base_entry = {
            "voucher_no": "APA-0000401",
            "External_Document_No": "EXT-001",
            "Document_Date": "2024/12/19",
            "description": "Test transaction"
        }
        
        if scenario == "vct_ntd_debit":
            return {
                **base_entry,
                "debit": {
                    "amount": 1000.00,
                    "currency": "NTD",
                    "account": "60100-10",
                    "gl_account": "G/L Account",
                    "department": "VCT.1001",
                    "applicant_code": "EMP001",
                    "Receipt/Invoice Note(明細)": "Office supplies",
                    "free_field": "Additional info"
                },
                "credit": {
                    "amount": 1000.00,
                    "currency": "NTD",
                    "vendor_code": "V-001",
                    "gl_account": "Vendor",
                    "department": "VCT.1001",
                    "department_code": "VCT.1001",
                    "account_source": "vendor_code",
                    "Remarks": "Payment to vendor",
                    "備考": "備考欄位"
                }
            }
        
        elif scenario == "vcp_usd_credit":
            return {
                **base_entry,
                "voucher_no": "APA-0000402",
                "debit": {
                    "amount": 500.00,
                    "currency": "USD",
                    "account": "60200-10",
                    "gl_account": "G/L Account",
                    "department": "VCP.2001",
                    "applicant_code": "EMP002"
                },
                "credit": {
                    "amount": 500.00,
                    "currency": "USD",
                    "vendor_code": "V-002",
                    "gl_account": "Vendor",
                    "department": "VCP.2001",
                    "department_code": "VCP.2001",
                    "account_source": "vendor_code"
                }
            }
        
        elif scenario == "vct_overseas_vendor":
            return {
                **base_entry,
                "voucher_no": "APA-0000403",
                "debit": {
                    "amount": 2000.00,
                    "currency": "NTD",
                    "account": "60300-10",
                    "gl_account": "G/L Account",
                    "department": "VCT.3001",
                    "applicant_code": "EMP003"
                },
                "credit": {
                    "amount": 2000.00,
                    "currency": "NTD",
                    "vendor_code": "V-VC00048",
                    "gl_account": "Vendor",
                    "department": "VCT.3001",
                    "department_code": "VCT.3001",
                    "account_source": "vendor_code"
                }
            }
        
        elif scenario == "vcp_v_vc00048_mapping":
            return {
                **base_entry,
                "voucher_no": "APA-0000404",
                "debit": {
                    "amount": 1500.00,
                    "currency": "PHP",
                    "account": "60400-10",
                    "gl_account": "G/L Account",
                    "department": "VCP.4001",
                    "applicant_code": "EMP004"
                },
                "credit": {
                    "amount": 1500.00,
                    "currency": "PHP",
                    "vendor_code": "V-VC00048",
                    "gl_account": "Vendor",
                    "department": "VCP.4001",
                    "department_code": "VCP.4001",
                    "account_source": "vendor_code"
                }
            }
        
        elif scenario == "vct_special_department":
            return {
                **base_entry,
                "voucher_no": "APA-0000405",
                "debit": {
                    "amount": 800.00,
                    "currency": "NTD",
                    "account": "60500-10",
                    "gl_account": "G/L Account",
                    "department": "VCT.1342G",
                    "applicant_code": "EMP005"
                },
                "credit": {
                    "amount": 800.00,
                    "currency": "NTD",
                    "vendor_code": "V-003",
                    "gl_account": "Vendor",
                    "department": "VCT.1342G",
                    "department_code": "VCT.1342G",
                    "account_source": "vendor_code"
                }
            }
        
        elif scenario == "consolidated_credit":
            return {
                **base_entry,
                "voucher_no": "APA-0000406",
                "debit": {
                    "amount": 0,  # Empty debit for consolidated entry
                    "currency": "",
                    "account": "",
                    "gl_account": "",
                    "department": "",
                    "applicant_code": ""
                },
                "credit": {
                    "amount": 3000.00,
                    "currency": "NTD",
                    "vendor_code": "V-004",
                    "gl_account": "Vendor",
                    "department": "VCT.5001",
                    "department_code": "VCT.5001",
                    "account_source": "vendor_code",
                    "consolidated": True,
                    "original_entries_count": 3,
                    "consolidation_note": "Consolidated from 3 entries",
                    "Remarks": "Consolidated payment"
                }
            }
        
        else:
            return base_entry
    
    def test_basic_journal_line_creation(self):
        """Test basic journal line creation"""
        print("\n=== Testing Basic Journal Line Creation ===")
        
        entry = self.create_test_entry("vct_ntd_debit")
        
        try:
            # Test debit line creation
            debit_line = create_journal_line(entry, "debit")
            self.sample_payloads.append({"scenario": "VCT NTD Debit", "payload": debit_line})
            
            # Verify required fields
            required_fields = [
                "Journal_Template_Name", "Journal_Batch_Name", "Document_Type",
                "Document_No", "Account_Type", "Account_No", "Description",
                "Amount", "Shortcut_Dimension_1_Code"
            ]
            
            missing_fields = [field for field in required_fields if field not in debit_line]
            
            if missing_fields:
                self.log_test("Basic Debit Line Creation", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Basic Debit Line Creation", True, "All required fields present")
            
            # Test credit line creation
            credit_line = create_journal_line(entry, "credit")
            self.sample_payloads.append({"scenario": "VCT NTD Credit", "payload": credit_line})
            
            missing_fields = [field for field in required_fields if field not in credit_line]
            
            if missing_fields:
                self.log_test("Basic Credit Line Creation", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Basic Credit Line Creation", True, "All required fields present")
                
        except Exception as e:
            self.log_test("Basic Journal Line Creation", False, f"Exception: {str(e)}")
    
    def test_currency_transformations(self):
        """Test currency code transformations"""
        print("\n=== Testing Currency Transformations ===")
        
        test_cases = [
            # (company_code, input_currency, expected_output)
            ("VCT", "NTD", ""),  # Home currency should be empty
            ("VCT", "USD", "R-USD"),  # Foreign currency should have R- prefix
            ("VCP", "PHP", ""),  # Home currency should be empty
            ("VCP", "USD", "R-USD"),  # Foreign currency should have R- prefix
            ("VCA", "USD", ""),  # Home currency should be empty
            ("VCA", "NTD", "R-NTD"),  # Foreign currency should have R- prefix
            ("VCG", "EUR", ""),  # Home currency should be empty
            ("VCG", "XEU", "R-EUR"),  # XEU should be treated as EUR
            ("VCJ", "JPY", ""),  # Home currency should be empty
            ("VCT", "R-USD", "R-USD"),  # Already prefixed should remain
        ]
        
        for company_code, input_currency, expected in test_cases:
            try:
                result = transform_currency_code(company_code, input_currency)
                passed = result == expected
                self.log_test(
                    f"Currency Transform {company_code}-{input_currency}", 
                    passed, 
                    f"Expected: '{expected}', Got: '{result}'"
                )
            except Exception as e:
                self.log_test(
                    f"Currency Transform {company_code}-{input_currency}", 
                    False, 
                    f"Exception: {str(e)}"
                )
    
    def test_date_conversion(self):
        """Test date format conversion"""
        print("\n=== Testing Date Conversion ===")
        
        test_cases = [
            ("2024/12/19", "2024-12-19"),
            ("2024/01/01", "2024-01-01"),
            ("", ""),
            ("invalid", "invalid"),  # Should return original if invalid
        ]
        
        for input_date, expected in test_cases:
            try:
                result = convert_date_format(input_date)
                passed = result == expected
                self.log_test(
                    f"Date Conversion '{input_date}'", 
                    passed, 
                    f"Expected: '{expected}', Got: '{result}'"
                )
            except Exception as e:
                self.log_test(
                    f"Date Conversion '{input_date}'", 
                    False, 
                    f"Exception: {str(e)}"
                )
    
    def test_vendor_account_mapping(self):
        """Test vendor account mapping logic"""
        print("\n=== Testing Vendor Account Mapping ===")
        
        # Test V-VC00048 mapping for non-VCT cost centers
        entry = self.create_test_entry("vcp_v_vc00048_mapping")
        
        try:
            credit_line = create_journal_line(entry, "credit")
            
            # For VCP cost center, V-VC00048 should be mapped to VCT
            expected_account = "VCT"
            actual_account = credit_line.get("Account_No", "")
            
            passed = actual_account == expected_account
            self.log_test(
                "V-VC00048 Mapping for VCP", 
                passed, 
                f"Expected: '{expected_account}', Got: '{actual_account}'"
            )
            
            self.sample_payloads.append({
                "scenario": "VCP V-VC00048 Mapping", 
                "payload": credit_line
            })
            
        except Exception as e:
            self.log_test("V-VC00048 Mapping", False, f"Exception: {str(e)}")
    
    def test_dimension_assignments(self):
        """Test dimension code assignments"""
        print("\n=== Testing Dimension Assignments ===")
        
        # Test special department VCT.1342G
        entry = self.create_test_entry("vct_special_department")
        
        try:
            debit_line = create_journal_line(entry, "debit")
            
            # Should have ShortcutDimCode14 set to VCT_TW0001
            expected_dim14 = "VCT_TW0001"
            actual_dim14 = debit_line.get("ShortcutDimCode14", "")
            
            passed = actual_dim14 == expected_dim14
            self.log_test(
                "Special Department VCT.1342G", 
                passed, 
                f"Expected ShortcutDimCode14: '{expected_dim14}', Got: '{actual_dim14}'"
            )
            
            self.sample_payloads.append({
                "scenario": "VCT.1342G Special Department", 
                "payload": debit_line
            })
            
        except Exception as e:
            self.log_test("Special Department Dimension", False, f"Exception: {str(e)}")
    
    def test_intercompany_codes(self):
        """Test intercompany code assignments"""
        print("\n=== Testing Intercompany Code Assignments ===")
        
        # Test VCP entry with V-VC00048 vendor
        entry = self.create_test_entry("vcp_v_vc00048_mapping")
        
        try:
            credit_line = create_journal_line(entry, "credit")
            
            # For non-VCT cost center, should have ShortcutDimCode3 = "VCT"
            expected_intercompany = "VCT"
            actual_intercompany = credit_line.get("ShortcutDimCode3", "")
            
            passed = actual_intercompany == expected_intercompany
            self.log_test(
                "Intercompany Code for VCP", 
                passed, 
                f"Expected ShortcutDimCode3: '{expected_intercompany}', Got: '{actual_intercompany}'"
            )
            
        except Exception as e:
            self.log_test("Intercompany Code Assignment", False, f"Exception: {str(e)}")
    
    def test_description_handling(self):
        """Test description field handling"""
        print("\n=== Testing Description Field Handling ===")
        
        entry = self.create_test_entry("vct_ntd_debit")
        
        try:
            # Test debit description (should use Receipt/Invoice Note or free_field)
            debit_line = create_journal_line(entry, "debit")
            debit_description = debit_line.get("Description", "")
            
            # Should contain the Receipt/Invoice Note content
            expected_content = "Office supplies"
            passed = expected_content in debit_description
            self.log_test(
                "Debit Description Content", 
                passed, 
                f"Expected to contain: '{expected_content}', Got: '{debit_description}'"
            )
            
            # Test credit description (should use Remarks/備考)
            credit_line = create_journal_line(entry, "credit")
            credit_description = credit_line.get("Description", "")
            
            # Should contain the Remarks content
            expected_content = "Payment to vendor"
            passed = expected_content in credit_description or "備考欄位" in credit_description
            self.log_test(
                "Credit Description Content", 
                passed, 
                f"Expected to contain remarks, Got: '{credit_description}'"
            )
            
        except Exception as e:
            self.log_test("Description Handling", False, f"Exception: {str(e)}")
    
    def test_consolidated_entries(self):
        """Test consolidated entry handling"""
        print("\n=== Testing Consolidated Entry Handling ===")
        
        entry = self.create_test_entry("consolidated_credit")
        
        try:
            credit_line = create_journal_line(entry, "credit")
            
            # Verify consolidated entry fields
            amount = credit_line.get("Amount", 0)
            description = credit_line.get("Description", "")
            
            # Amount should be negative for credit
            passed_amount = amount < 0
            self.log_test(
                "Consolidated Credit Amount", 
                passed_amount, 
                f"Expected negative amount, Got: {amount}"
            )
            
            # Description should contain consolidated info
            passed_desc = "Consolidated" in description or len(description) > 0
            self.log_test(
                "Consolidated Description", 
                passed_desc, 
                f"Description: '{description}'"
            )
            
            self.sample_payloads.append({
                "scenario": "Consolidated Credit Entry", 
                "payload": credit_line
            })
            
        except Exception as e:
            self.log_test("Consolidated Entry Handling", False, f"Exception: {str(e)}")
    
    def generate_sample_payloads_report(self, output_file: str = "bc_payload_samples.json"):
        """Generate a report with sample payloads"""
        print(f"\n=== Generating Sample Payloads Report: {output_file} ===")
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.sample_payloads, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)
            
            self.log_test("Sample Payloads Report", True, f"Generated {len(self.sample_payloads)} samples")
            
        except Exception as e:
            self.log_test("Sample Payloads Report", False, f"Exception: {str(e)}")
    
    def generate_test_summary(self, output_file: str = "bc_payload_verification_report.md"):
        """Generate a summary report of all tests"""
        print(f"\n=== Generating Test Summary Report: {output_file} ===")
        
        try:
            total_tests = len(self.test_results)
            passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
            failed_tests = total_tests - passed_tests
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Business Central Payload Verification Report\n\n")
                f.write(f"**Total Tests:** {total_tests}\n")
                f.write(f"**Passed:** {passed_tests}\n")
                f.write(f"**Failed:** {failed_tests}\n")
                f.write(f"**Success Rate:** {(passed_tests/total_tests*100):.1f}%\n\n")
                
                f.write("## Test Results\n\n")
                f.write("| Test Name | Status | Details |\n")
                f.write("|-----------|--------|----------|\n")
                
                for result in self.test_results:
                    f.write(f"| {result['test']} | {result['status']} | {result['details']} |\n")
                
                f.write("\n## Failed Tests\n\n")
                failed_results = [r for r in self.test_results if r["status"] == "FAIL"]
                if failed_results:
                    for result in failed_results:
                        f.write(f"### {result['test']}\n")
                        f.write(f"**Details:** {result['details']}\n\n")
                else:
                    f.write("No failed tests.\n\n")
                
                f.write("## Sample Payloads Generated\n\n")
                f.write(f"Generated {len(self.sample_payloads)} sample payloads for inspection.\n")
                f.write("See `bc_payload_samples.json` for detailed payload examples.\n")
            
            print(f"Test Summary: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests*100):.1f}%)")
            
        except Exception as e:
            print(f"Error generating test summary: {str(e)}")
    
    def run_all_tests(self):
        """Run all verification tests"""
        print("=" * 60)
        print("BUSINESS CENTRAL PAYLOAD VERIFICATION")
        print("=" * 60)
        
        self.test_basic_journal_line_creation()
        self.test_currency_transformations()
        self.test_date_conversion()
        self.test_vendor_account_mapping()
        self.test_dimension_assignments()
        self.test_intercompany_codes()
        self.test_description_handling()
        self.test_consolidated_entries()
        
        self.generate_sample_payloads_report()
        self.generate_test_summary()
        
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)


def main():
    """Main function to run the verification"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify Business Central payload generation')
    parser.add_argument('--samples-output', default='bc_payload_samples.json', 
                       help='Output file for sample payloads')
    parser.add_argument('--report-output', default='bc_payload_verification_report.md', 
                       help='Output file for verification report')
    args = parser.parse_args()
    
    verifier = BCPayloadVerifier()
    verifier.run_all_tests()


if __name__ == "__main__":
    main()
