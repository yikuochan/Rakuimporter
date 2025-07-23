#!/usr/bin/env python3
"""
Script to apply the unified VCT solution to the current process.

This script demonstrates the practical steps to migrate from the current
fragmented VCT processing to the unified architecture.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def backup_current_system():
    """Backup current system files before applying changes."""
    print("Step 1: Backing up current system...")
    
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        "run_importer.py",
        "core/process_japan_exports.py",
        "core/csv_to_json_converter_enhanced.py",
        "core/vct_responsibility_consolidation.py"
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            shutil.copy2(file_path, f"{backup_dir}/{os.path.basename(file_path)}")
            print(f"  ✅ Backed up: {file_path}")
        else:
            print(f"  ⚠️  File not found: {file_path}")
    
    print(f"  📁 Backup created in: {backup_dir}")
    return backup_dir

def test_unified_converter():
    """Test the unified converter with sample data."""
    print("\nStep 2: Testing unified converter...")
    
    try:
        from core.csv_to_json_converter_unified import UnifiedCSVToJSONConverter
        
        # Create test CSV data
        test_csv_content = """伝票番号,伝票日付,外部証憑番号,摘要,借方勘定科目,借方金額,借方通貨,貸方勘定科目,貸方金額,貸方通貨,部門,申請者コード,仕入先コード,Receipt/Invoice Note(明細),自由項目,備考
APA-0000552-1,2025/01/15,APA-0000552-1,Office supplies,62100-10,5000,NTD,V-VC00048,5000,NTD,VCP.1234,EMP001,V-VC00048,Stationery purchase,Office,Office supplies payment
VCT-0000456,2025/01/30,VCT-0000456,VCT department entry,61200-10,1500,NTD,V-VC00048,1500,NTD,VCT.1111,EMP007,V-VC00048,VCT expense,VCT,VCT payment"""
        
        # Write test CSV
        test_csv_path = "test_unified_input.csv"
        with open(test_csv_path, 'w', encoding='utf-8') as f:
            f.write(test_csv_content)
        
        # Test conversion
        converter = UnifiedCSVToJSONConverter()
        test_json_path = "test_unified_output.json"
        
        report = converter.convert_csv_to_json(test_csv_path, test_json_path, "VicOne")
        
        # Analyze results
        with open(test_json_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        print(f"  ✅ Conversion successful!")
        print(f"  📊 Processed {len(entries)} entries")
        print(f"  📈 Success rate: {report['success_rate']:.1f}%")
        
        # Check VCT responsibility identification
        vct_responsibility_count = 0
        regular_count = 0
        
        for entry in entries:
            vendor_code = entry.get('credit', {}).get('vendor_code', '')
            department = entry.get('credit', {}).get('department', '')
            cost_center = department[:3] if department else ''
            
            if vendor_code == "V-VC00048" and cost_center != "VCT":
                vct_responsibility_count += 1
            else:
                regular_count += 1
        
        print(f"  🎯 VCT responsibility entries: {vct_responsibility_count}")
        print(f"  📝 Regular entries: {regular_count}")
        
        # Cleanup test files
        os.remove(test_csv_path)
        os.remove(test_json_path)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed: {str(e)}")
        return False

def show_current_vs_new_process():
    """Show comparison between current and new process."""
    print("\nStep 3: Process Comparison")
    print("=" * 50)
    
    print("\n🔴 CURRENT PROCESS (Fragmented):")
    print("  1. CSV → csv_to_json_converter_enhanced.py → JSON with consolidated entries")
    print("  2. JSON → vct_responsibility_consolidation.py → Processed VCT entries")
    print("  3. Processed entries → process_japan_exports.py → Business Central API")
    print("  ❌ Issues: Multiple paths, complex testing, maintenance burden")
    
    print("\n🟢 NEW PROCESS (Unified):")
    print("  1. CSV → csv_to_json_converter_unified.py → Individual entries")
    print("  2. Individual entries → process_japan_exports.py (with integrated VCT logic) → Business Central API")
    print("  ✅ Benefits: Single path, simplified testing, easier maintenance")

def create_updated_run_importer():
    """Create an updated version of run_importer.py using unified architecture."""
    print("\nStep 4: Creating updated run_importer.py...")
    
    # Read current run_importer.py to understand structure
    current_importer_path = "run_importer.py"
    
    if not os.path.exists(current_importer_path):
        print(f"  ⚠️  {current_importer_path} not found. Creating new one...")
    
    updated_importer_content = '''#!/usr/bin/env python3
"""
Updated run_importer.py using unified VCT processing architecture.

This version eliminates separate VCT consolidation processes and uses
a single unified pipeline for all entry types.
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.csv_to_json_converter_unified import UnifiedCSVToJSONConverter
from core.process_japan_exports import process_entries

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_importer_unified")

def main():
    """Main unified processing function."""
    
    if len(sys.argv) < 3:
        print("Usage: python run_importer.py <csv_file> <company_code>")
        print("Example: python run_importer.py Data/input.csv VicOne")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    company_code = sys.argv[2] if len(sys.argv) > 2 else "VicOne"
    
    # Generate output file name
    json_file = csv_file.replace('.csv', '_unified.json')
    
    try:
        logger.info("Starting unified VCT processing...")
        logger.info(f"Input CSV: {csv_file}")
        logger.info(f"Output JSON: {json_file}")
        logger.info(f"Company: {company_code}")
        
        # Step 1: Convert CSV to JSON using unified converter
        logger.info("Converting CSV to JSON with unified converter...")
        converter = UnifiedCSVToJSONConverter()
        report = converter.convert_csv_to_json(csv_file, json_file, company_code)
        
        logger.info(f"Conversion completed: {report['valid_entries_created']} entries")
        logger.info(f"Success rate: {report['success_rate']:.1f}%")
        
        # Step 2: Load entries for processing
        logger.info("Loading entries for API processing...")
        with open(json_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        # Step 3: Process entries with integrated VCT logic
        logger.info("Processing entries with integrated VCT logic...")
        
        # Analyze entry types before processing
        vct_responsibility_count = 0
        regular_count = 0
        
        for entry in entries:
            vendor_code = entry.get('credit', {}).get('vendor_code', '')
            department = entry.get('credit', {}).get('department', '')
            cost_center = department[:3] if department else ''
            
            if vendor_code == "V-VC00048" and cost_center != "VCT":
                vct_responsibility_count += 1
            else:
                regular_count += 1
        
        logger.info(f"Entry analysis:")
        logger.info(f"  - VCT responsibility entries: {vct_responsibility_count}")
        logger.info(f"  - Regular entries: {regular_count}")
        
        # Process all entries through unified pipeline
        success_count = process_entries(entries)
        
        logger.info(f"Processing completed successfully!")
        logger.info(f"Successfully processed: {success_count} entries")
        
        # Generate summary report
        summary = {
            "input_file": csv_file,
            "output_file": json_file,
            "company_code": company_code,
            "total_entries": len(entries),
            "vct_responsibility_entries": vct_responsibility_count,
            "regular_entries": regular_count,
            "successfully_processed": success_count,
            "conversion_report": report
        }
        
        # Save summary
        summary_file = json_file.replace('.json', '_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Summary report saved to: {summary_file}")
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    # Save updated importer
    updated_importer_path = "run_importer_unified.py"
    with open(updated_importer_path, 'w', encoding='utf-8') as f:
        f.write(updated_importer_content)
    
    print(f"  ✅ Created: {updated_importer_path}")
    print(f"  📝 Usage: python {updated_importer_path} your_file.csv VicOne")

def show_integration_steps():
    """Show the specific integration steps needed."""
    print("\nStep 5: Integration Steps Required")
    print("=" * 50)
    
    print("\n📋 IMMEDIATE ACTIONS:")
    print("  1. Test unified converter:")
    print("     python Tools/test_unified_processing.py")
    
    print("\n  2. Test with your CSV file:")
    print("     python core/csv_to_json_converter_unified.py your_file.csv test_output.json --company VicOne")
    
    print("\n  3. Use updated importer:")
    print("     python run_importer_unified.py your_file.csv VicOne")
    
    print("\n📋 INTEGRATION STEPS:")
    print("  1. Update process_japan_exports.py to include VCT logic:")
    print("     - Add is_vct_responsibility_entry() function")
    print("     - Add apply_vct_responsibility_rules() function")
    print("     - Integrate VCT logic into main processing loop")
    
    print("\n  2. Replace current run_importer.py:")
    print("     - Backup current version")
    print("     - Replace with run_importer_unified.py")
    print("     - Test with sample data")
    
    print("\n  3. Handle existing consolidated data:")
    print("     python Tools/convert_consolidated_to_normal_vct.py old_consolidated.json new_individual.json")

def show_validation_commands():
    """Show commands to validate the implementation."""
    print("\nStep 6: Validation Commands")
    print("=" * 50)
    
    print("\n🧪 TESTING COMMANDS:")
    print("  # Test unified architecture")
    print("  python Tools/test_unified_processing.py")
    
    print("\n  # Test with real data")
    print("  python run_importer_unified.py Data/your_file.csv VicOne")
    
    print("\n  # Convert existing consolidated data")
    print("  python Tools/convert_consolidated_to_normal_vct.py consolidated.json individual.json")
    
    print("\n  # Verify VCT responsibility identification")
    print("  python -c \"")
    print("  from core.csv_to_json_converter_unified import UnifiedCSVToJSONConverter")
    print("  import json")
    print("  converter = UnifiedCSVToJSONConverter()")
    print("  converter.convert_csv_to_json('your_file.csv', 'test.json', 'VicOne')")
    print("  with open('test.json', 'r') as f:")
    print("      entries = json.load(f)")
    print("  vct_entries = [e for e in entries if e['credit']['vendor_code'] == 'V-VC00048' and e['credit']['department'][:3] != 'VCT']")
    print("  print(f'VCT responsibility entries: {len(vct_entries)}')\"")

def main():
    """Main function to apply the unified solution."""
    print("🚀 APPLYING UNIFIED VCT SOLUTION")
    print("=" * 60)
    print("This script will help you migrate from the current fragmented")
    print("VCT processing to the unified architecture.")
    print("=" * 60)
    
    # Step 1: Backup current system
    backup_dir = backup_current_system()
    
    # Step 2: Test unified converter
    if not test_unified_converter():
        print("\n❌ Unified converter test failed. Please check the implementation.")
        return False
    
    # Step 3: Show process comparison
    show_current_vs_new_process()
    
    # Step 4: Create updated importer
    create_updated_run_importer()
    
    # Step 5: Show integration steps
    show_integration_steps()
    
    # Step 6: Show validation commands
    show_validation_commands()
    
    print("\n" + "=" * 60)
    print("✅ UNIFIED SOLUTION READY FOR APPLICATION")
    print("=" * 60)
    
    print(f"\n📁 Backup created: {backup_dir}")
    print("📄 Updated importer: run_importer_unified.py")
    print("🧪 Test suite: Tools/test_unified_processing.py")
    print("📚 Documentation: docs/vct_unified_solution_implementation_guide.md")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run: python Tools/test_unified_processing.py")
    print("2. Test: python run_importer_unified.py your_file.csv VicOne")
    print("3. Integrate VCT logic into process_japan_exports.py")
    print("4. Replace current run_importer.py with unified version")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Unified solution application completed successfully!")
    else:
        print("\n❌ Application failed. Please check the errors above.")
    sys.exit(0 if success else 1)
