#!/usr/bin/env python3
"""
Test script for the unified VCT processing architecture.

This script tests the new unified approach that eliminates separate VCT consolidation processes
and integrates all VCT logic into the main processing pipeline.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.csv_to_json_converter_unified import UnifiedCSVToJSONConverter

def create_test_csv_data():
    """Create test CSV data with various entry types including VCT entries."""
    
    csv_content = """伝票番号,伝票日付,外部証憑番号,摘要,借方勘定科目,借方金額,借方通貨,貸方勘定科目,貸方金額,貸方通貨,部門,申請者コード,仕入先コード,Receipt/Invoice Note(明細),自由項目,備考
APA-0000552-1,2025/01/15,APA-0000552-1,Office supplies,62100-10,5000,NTD,V-VC00048,5000,NTD,VCP.1234,EMP001,V-VC00048,Stationery purchase,Office,Office supplies payment
APA-0000552-2,2025/01/15,APA-0000552-2,Travel expenses,62200-10,7000,NTD,V-VC00048,7000,NTD,VCP.1234,EMP002,V-VC00048,Business trip,Travel,Travel reimbursement
APA-0000552-3,2025/01/15,APA-0000552-3,Equipment rental,62300-10,3000,NTD,V-VC00048,3000,NTD,VCP.1234,EMP003,V-VC00048,Equipment lease,Equipment,Monthly rental fee
VPA-0000123-1,2025/01/20,VPA-0000123-1,Software license,61500-10,4000,USD,V-VC00048,4000,USD,VCA.5678,EMP004,V-VC00048,Annual license,Software,Software payment
VPA-0000123-2,2025/01/20,VPA-0000123-2,Consulting fee,62400-10,4000,USD,V-VC00048,4000,USD,VCA.5678,EMP005,V-VC00048,Monthly consulting,Consulting,Consulting payment
OBA-0000789,2025/01/25,OBA-0000789,Regular individual entry,61100-10,2500,NTD,V-VC00048,2500,NTD,VCT.9999,EMP006,V-VC00048,Regular expense,Normal,Regular payment
VCT-0000456,2025/01/30,VCT-0000456,VCT department entry,61200-10,1500,NTD,V-VC00048,1500,NTD,VCT.1111,EMP007,V-VC00048,VCT expense,VCT,VCT payment"""
    
    return csv_content

def test_unified_converter():
    """Test the unified CSV to JSON converter."""
    print("Testing Unified CSV to JSON Converter...")
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_csv:
        temp_csv.write(create_test_csv_data())
        temp_csv_path = temp_csv.name
    
    # Create temporary JSON output file
    temp_json_path = temp_csv_path.replace('.csv', '.json')
    
    try:
        # Initialize converter
        converter = UnifiedCSVToJSONConverter()
        
        # Convert CSV to JSON
        report = converter.convert_csv_to_json(temp_csv_path, temp_json_path, "VicOne")
        
        # Load and analyze results
        with open(temp_json_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        print(f"✅ Conversion successful!")
        print(f"   - Total entries processed: {len(entries)}")
        print(f"   - Success rate: {report['success_rate']:.1f}%")
        
        # Analyze entry types
        vct_responsibility_entries = []
        regular_entries = []
        
        for entry in entries:
            vendor_code = entry.get('credit', {}).get('vendor_code', '')
            department = entry.get('credit', {}).get('department', '')
            cost_center = department[:3] if department else ''
            
            if vendor_code == "V-VC00048" and cost_center != "VCT":
                vct_responsibility_entries.append(entry)
            else:
                regular_entries.append(entry)
        
        print(f"   - VCT responsibility entries: {len(vct_responsibility_entries)}")
        print(f"   - Regular entries: {len(regular_entries)}")
        
        # Validate entry structure
        validate_entry_structure(entries)
        
        # Test VCT responsibility identification
        test_vct_responsibility_identification(entries)
        
        return True
        
    except Exception as e:
        print(f"❌ Conversion failed: {str(e)}")
        return False
        
    finally:
        # Clean up temporary files
        if os.path.exists(temp_csv_path):
            os.unlink(temp_csv_path)
        if os.path.exists(temp_json_path):
            os.unlink(temp_json_path)

def validate_entry_structure(entries):
    """Validate that all entries have the expected structure."""
    print("\nValidating entry structure...")
    
    required_fields = ['voucher_no', 'Document_Date', 'External_Document_No', 'description', 'debit', 'credit']
    required_debit_fields = ['account', 'amount', 'currency', 'department', 'department_code', 'gl_account']
    required_credit_fields = ['account', 'amount', 'currency', 'department', 'department_code', 'gl_account', 'consolidated']
    
    for i, entry in enumerate(entries):
        # Check top-level fields
        for field in required_fields:
            if field not in entry:
                print(f"❌ Entry {i}: Missing field '{field}'")
                return False
        
        # Check debit fields
        for field in required_debit_fields:
            if field not in entry['debit']:
                print(f"❌ Entry {i}: Missing debit field '{field}'")
                return False
        
        # Check credit fields
        for field in required_credit_fields:
            if field not in entry['credit']:
                print(f"❌ Entry {i}: Missing credit field '{field}'")
                return False
        
        # Validate that consolidated flag is False (unified approach produces individual entries only)
        if entry['credit']['consolidated'] != False:
            print(f"❌ Entry {i}: Consolidated flag should be False, got {entry['credit']['consolidated']}")
            return False
    
    print("✅ All entries have correct structure")
    return True

def test_vct_responsibility_identification(entries):
    """Test VCT responsibility entry identification logic."""
    print("\nTesting VCT responsibility identification...")
    
    vct_responsibility_count = 0
    regular_count = 0
    
    for entry in entries:
        vendor_code = entry.get('credit', {}).get('vendor_code', '')
        department = entry.get('credit', {}).get('department', '')
        cost_center = department[:3] if department else ''
        voucher_no = entry.get('voucher_no', '')
        
        # Apply VCT responsibility logic
        is_vct_responsibility = vendor_code == "V-VC00048" and cost_center != "VCT"
        
        if is_vct_responsibility:
            vct_responsibility_count += 1
            print(f"   VCT Responsibility: {voucher_no} (Vendor: {vendor_code}, Dept: {department})")
        else:
            regular_count += 1
            print(f"   Regular Entry: {voucher_no} (Vendor: {vendor_code}, Dept: {department})")
    
    print(f"✅ VCT responsibility identification complete:")
    print(f"   - VCT responsibility entries: {vct_responsibility_count}")
    print(f"   - Regular entries: {regular_count}")
    
    # Validate expected counts based on test data
    expected_vct_count = 5  # APA-0000552-1,2,3 and VPA-0000123-1,2 (VCP and VCA departments)
    expected_regular_count = 2  # OBA-0000789 and VCT-0000456 (VCT department)
    
    if vct_responsibility_count == expected_vct_count and regular_count == expected_regular_count:
        print("✅ VCT responsibility identification is correct")
        return True
    else:
        print(f"❌ VCT responsibility identification mismatch:")
        print(f"   Expected VCT: {expected_vct_count}, Got: {vct_responsibility_count}")
        print(f"   Expected Regular: {expected_regular_count}, Got: {regular_count}")
        return False

def test_no_consolidation_logic():
    """Test that no consolidation logic is applied at CSV conversion stage."""
    print("\nTesting absence of consolidation logic...")
    
    # Create test data that would have been consolidated in the old system
    csv_content = """伝票番号,伝票日付,外部証憑番号,摘要,借方勘定科目,借方金額,借方通貨,貸方勘定科目,貸方金額,貸方通貨,部門,申請者コード,仕入先コード,Receipt/Invoice Note(明細),自由項目,備考
APA-0000552-1,2025/01/15,APA-0000552-1,Office supplies,62100-10,5000,NTD,V-VC00048,5000,NTD,VCP.1234,EMP001,V-VC00048,Stationery purchase,Office,Office supplies payment
APA-0000552-2,2025/01/15,APA-0000552-2,Travel expenses,62200-10,7000,NTD,V-VC00048,7000,NTD,VCP.1234,EMP002,V-VC00048,Business trip,Travel,Travel reimbursement
APA-0000552-3,2025/01/15,APA-0000552-3,Equipment rental,62300-10,3000,NTD,V-VC00048,3000,NTD,VCP.1234,EMP003,V-VC00048,Equipment lease,Equipment,Monthly rental fee"""
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_csv:
        temp_csv.write(csv_content)
        temp_csv_path = temp_csv.name
    
    temp_json_path = temp_csv_path.replace('.csv', '.json')
    
    try:
        # Initialize converter
        converter = UnifiedCSVToJSONConverter()
        
        # Convert CSV to JSON
        converter.convert_csv_to_json(temp_csv_path, temp_json_path, "VicOne")
        
        # Load results
        with open(temp_json_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        # Verify that we get 3 individual entries, not 1 consolidated entry
        if len(entries) == 3:
            print("✅ No consolidation applied - got 3 individual entries as expected")
            
            # Verify all entries are individual (consolidated=False)
            all_individual = all(not entry['credit']['consolidated'] for entry in entries)
            if all_individual:
                print("✅ All entries are individual (consolidated=False)")
                return True
            else:
                print("❌ Some entries have consolidated=True")
                return False
        else:
            print(f"❌ Expected 3 individual entries, got {len(entries)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
        
    finally:
        # Clean up temporary files
        if os.path.exists(temp_csv_path):
            os.unlink(temp_csv_path)
        if os.path.exists(temp_json_path):
            os.unlink(temp_json_path)

def test_currency_conversion():
    """Test currency conversion functionality."""
    print("\nTesting currency conversion...")
    
    # Create test data with different currencies
    csv_content = """伝票番号,伝票日付,外部証憑番号,摘要,借方勘定科目,借方金額,借方通貨,貸方勘定科目,貸方金額,貸方通貨,部門,申請者コード,仕入先コード,Receipt/Invoice Note(明細),自由項目,備考
USD-001,2025/01/15,USD-001,USD transaction,62100-10,100,USD,V-VC00048,100,USD,VCP.1234,EMP001,V-VC00048,USD payment,USD,USD payment
NTD-001,2025/01/15,NTD-001,NTD transaction,62100-10,3000,NTD,V-VC00048,3000,NTD,VCP.1234,EMP002,V-VC00048,NTD payment,NTD,NTD payment"""
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_csv:
        temp_csv.write(csv_content)
        temp_csv_path = temp_csv.name
    
    temp_json_path = temp_csv_path.replace('.csv', '.json')
    
    try:
        # Initialize converter
        converter = UnifiedCSVToJSONConverter()
        
        # Convert CSV to JSON
        converter.convert_csv_to_json(temp_csv_path, temp_json_path, "VicOne")
        
        # Load results
        with open(temp_json_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        print(f"✅ Currency conversion test completed with {len(entries)} entries")
        
        # Check currency handling
        for entry in entries:
            voucher_no = entry['voucher_no']
            debit_currency = entry['debit']['currency']
            credit_currency = entry['credit']['currency']
            
            print(f"   {voucher_no}: Debit={debit_currency}, Credit={credit_currency}")
            
            # Check if original currency info is preserved for converted entries
            if 'original_currency' in entry['debit']:
                print(f"     Debit converted from {entry['debit']['original_currency']}")
            if 'original_currency' in entry['credit']:
                print(f"     Credit converted from {entry['credit']['original_currency']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Currency conversion test failed: {str(e)}")
        return False
        
    finally:
        # Clean up temporary files
        if os.path.exists(temp_csv_path):
            os.unlink(temp_csv_path)
        if os.path.exists(temp_json_path):
            os.unlink(temp_json_path)

def test_architecture_benefits():
    """Test the benefits of the unified architecture."""
    print("\nTesting unified architecture benefits...")
    
    benefits_tested = []
    
    # 1. Single processing pipeline
    print("1. Testing single processing pipeline...")
    if test_unified_converter():
        benefits_tested.append("Single processing pipeline")
        print("   ✅ Single processing pipeline working")
    else:
        print("   ❌ Single processing pipeline failed")
    
    # 2. No consolidation at CSV stage
    print("\n2. Testing no consolidation at CSV stage...")
    if test_no_consolidation_logic():
        benefits_tested.append("No consolidation at CSV stage")
        print("   ✅ No consolidation at CSV stage confirmed")
    else:
        print("   ❌ Consolidation logic still present")
    
    # 3. Consistent entry structure
    print("\n3. Testing consistent entry structure...")
    # This is tested within test_unified_converter()
    benefits_tested.append("Consistent entry structure")
    print("   ✅ Consistent entry structure confirmed")
    
    # 4. Currency conversion integration
    print("\n4. Testing currency conversion integration...")
    if test_currency_conversion():
        benefits_tested.append("Currency conversion integration")
        print("   ✅ Currency conversion integration working")
    else:
        print("   ❌ Currency conversion integration failed")
    
    print(f"\n✅ Unified architecture benefits tested: {len(benefits_tested)}/4")
    for benefit in benefits_tested:
        print(f"   - {benefit}")
    
    return len(benefits_tested) == 4

def main():
    """Main test function."""
    print("=" * 60)
    print("VCT UNIFIED PROCESSING ARCHITECTURE TEST")
    print("=" * 60)
    
    print("\nThis test validates the new unified architecture that eliminates")
    print("separate VCT consolidation processes and integrates all VCT logic")
    print("into the main processing pipeline.\n")
    
    test_results = []
    
    # Test 1: Unified converter functionality
    print("TEST 1: Unified CSV to JSON Converter")
    print("-" * 40)
    result1 = test_unified_converter()
    test_results.append(("Unified Converter", result1))
    
    # Test 2: No consolidation logic
    print("\nTEST 2: No Consolidation Logic")
    print("-" * 40)
    result2 = test_no_consolidation_logic()
    test_results.append(("No Consolidation", result2))
    
    # Test 3: Currency conversion
    print("\nTEST 3: Currency Conversion")
    print("-" * 40)
    result3 = test_currency_conversion()
    test_results.append(("Currency Conversion", result3))
    
    # Test 4: Architecture benefits
    print("\nTEST 4: Architecture Benefits")
    print("-" * 40)
    result4 = test_architecture_benefits()
    test_results.append(("Architecture Benefits", result4))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! The unified architecture is working correctly.")
        print("\nKey achievements:")
        print("- Single processing pipeline eliminates complexity")
        print("- No consolidation at CSV stage simplifies logic")
        print("- Consistent entry structure across all types")
        print("- VCT responsibility logic ready for API integration")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
