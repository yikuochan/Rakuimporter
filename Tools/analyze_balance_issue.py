#!/usr/bin/env python3
"""
Detailed balance analysis tool to investigate VCT consolidation balance issues.

This tool will:
1. Process the same CSV with both original and enhanced converters
2. Compare the results entry by entry
3. Identify where the balance discrepancy occurs
4. Analyze consolidation logic step by step
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from collections import defaultdict

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.csv_to_json_converter_enhanced import convert_csv_to_json as convert_enhanced
from core.csv_to_json_converter import convert_csv_to_json as convert_original

def analyze_balance_issue():
    """Detailed analysis of balance discrepancy between original and enhanced converters."""
    
    print("=" * 80)
    print("DETAILED BALANCE ANALYSIS")
    print("=" * 80)
    
    # Test with the problematic CSV file
    csv_file = "Data/Testing Data/0523-Raku export-VCT PR-1.utf8.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ Test CSV file not found: {csv_file}")
        return False
    
    print(f"✅ Using test CSV file: {csv_file}")
    
    # Create temporary output files
    with tempfile.NamedTemporaryFile(mode='w', suffix='_original.json', delete=False) as temp_orig:
        output_original = temp_orig.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_enhanced.json', delete=False) as temp_enh:
        output_enhanced = temp_enh.name
    
    try:
        print(f"\n📝 Step 1: Converting with ORIGINAL converter...")
        
        # Convert using original converter
        try:
            entry_count_original = convert_original(
                csv_file, 
                output_original, 
                max_desc_length=100
            )
            print(f"✅ Original converter: Generated {entry_count_original} entries.")
        except Exception as e:
            print(f"❌ Original converter failed: {str(e)}")
            return False
        
        print(f"\n📝 Step 2: Converting with ENHANCED converter...")
        
        # Convert using enhanced converter
        try:
            entry_count_enhanced = convert_enhanced(
                csv_file, 
                output_enhanced, 
                max_desc_length=100,
                use_comprehensive_fix=True,
                keep_temp_files=False
            )
            print(f"✅ Enhanced converter: Generated {entry_count_enhanced} entries.")
        except Exception as e:
            print(f"❌ Enhanced converter failed: {str(e)}")
            return False
        
        # Load and analyze both results
        print(f"\n📊 Step 3: Loading and analyzing results...")
        
        with open(output_original, 'r', encoding='utf-8') as f:
            entries_original = json.load(f)
        
        with open(output_enhanced, 'r', encoding='utf-8') as f:
            entries_enhanced = json.load(f)
        
        print(f"Original entries: {len(entries_original)}")
        print(f"Enhanced entries: {len(entries_enhanced)}")
        
        # Calculate balances for both
        def calculate_balance(entries, label):
            total_debit = sum(entry.get('debit', {}).get('amount', 0) for entry in entries)
            total_credit = sum(entry.get('credit', {}).get('amount', 0) for entry in entries)
            difference = abs(total_debit - total_credit)
            
            print(f"\n⚖️  {label} BALANCE:")
            print(f"Total debit: {total_debit:,.2f} NTD")
            print(f"Total credit: {total_credit:,.2f} NTD")
            print(f"Difference: {difference:,.2f} NTD")
            
            if difference < 0.01:
                print(f"✅ {label} is balanced!")
                return True
            else:
                print(f"❌ {label} is NOT balanced!")
                return False
        
        original_balanced = calculate_balance(entries_original, "ORIGINAL")
        enhanced_balanced = calculate_balance(entries_enhanced, "ENHANCED")
        
        # Detailed analysis of enhanced converter entries
        print(f"\n🔍 Step 4: Detailed analysis of ENHANCED converter...")
        
        consolidated_entries = []
        vct_responsibility_entries = []
        regular_entries = []
        
        for entry in entries_enhanced:
            if entry.get('credit', {}).get('consolidated'):
                consolidated_entries.append(entry)
            elif (entry.get('debit', {}).get('vct_responsibility') or 
                  entry.get('credit', {}).get('vct_responsibility')):
                vct_responsibility_entries.append(entry)
            else:
                regular_entries.append(entry)
        
        print(f"Regular entries: {len(regular_entries)}")
        print(f"Consolidated entries: {len(consolidated_entries)}")
        print(f"VCT responsibility entries: {len(vct_responsibility_entries)}")
        
        # Analyze consolidated entries in detail
        if consolidated_entries:
            print(f"\n📋 CONSOLIDATED ENTRIES ANALYSIS:")
            consolidated_debit_total = 0
            consolidated_credit_total = 0
            
            for entry in consolidated_entries:
                debit_amt = entry.get('debit', {}).get('amount', 0)
                credit_amt = entry.get('credit', {}).get('amount', 0)
                consolidated_debit_total += debit_amt
                consolidated_credit_total += credit_amt
                
                if credit_amt > 0:  # This is a consolidated credit entry
                    original_count = entry.get('credit', {}).get('original_entries_count', 'N/A')
                    vendor = entry.get('credit', {}).get('vendor_code', 'N/A')
                    voucher = entry.get('voucher_no', 'N/A')
                    print(f"  Credit: {voucher} | {vendor} | {credit_amt:,.2f} NTD | {original_count} orig entries")
            
            print(f"\nConsolidated totals:")
            print(f"  Debit: {consolidated_debit_total:,.2f} NTD")
            print(f"  Credit: {consolidated_credit_total:,.2f} NTD")
            print(f"  Difference: {abs(consolidated_debit_total - consolidated_credit_total):,.2f} NTD")
        
        # Compare voucher totals between original and enhanced
        print(f"\n🔍 Step 5: Voucher-by-voucher comparison...")
        
        def get_voucher_totals(entries, label):
            voucher_totals = defaultdict(lambda: {'debit': 0, 'credit': 0})
            
            for entry in entries:
                voucher = entry.get('voucher_no', 'UNKNOWN')
                debit_amt = entry.get('debit', {}).get('amount', 0)
                credit_amt = entry.get('credit', {}).get('amount', 0)
                
                voucher_totals[voucher]['debit'] += debit_amt
                voucher_totals[voucher]['credit'] += credit_amt
            
            print(f"\n{label} voucher totals:")
            total_debit = 0
            total_credit = 0
            unbalanced_vouchers = []
            
            for voucher, amounts in sorted(voucher_totals.items()):
                debit = amounts['debit']
                credit = amounts['credit']
                diff = abs(debit - credit)
                
                total_debit += debit
                total_credit += credit
                
                if diff > 0.01:  # Unbalanced voucher
                    unbalanced_vouchers.append((voucher, debit, credit, diff))
                    print(f"  ❌ {voucher}: Debit={debit:,.2f}, Credit={credit:,.2f}, Diff={diff:,.2f}")
                else:
                    print(f"  ✅ {voucher}: Debit={debit:,.2f}, Credit={credit:,.2f}")
            
            print(f"\n{label} summary:")
            print(f"  Total debit: {total_debit:,.2f}")
            print(f"  Total credit: {total_credit:,.2f}")
            print(f"  Overall difference: {abs(total_debit - total_credit):,.2f}")
            print(f"  Unbalanced vouchers: {len(unbalanced_vouchers)}")
            
            return voucher_totals, unbalanced_vouchers
        
        orig_vouchers, orig_unbalanced = get_voucher_totals(entries_original, "ORIGINAL")
        enh_vouchers, enh_unbalanced = get_voucher_totals(entries_enhanced, "ENHANCED")
        
        # Find vouchers that became unbalanced in enhanced version
        print(f"\n🚨 Step 6: Identifying problematic vouchers...")
        
        problematic_vouchers = []
        for voucher, debit, credit, diff in enh_unbalanced:
            # Check if this voucher was balanced in original
            if voucher in orig_vouchers:
                orig_debit = orig_vouchers[voucher]['debit']
                orig_credit = orig_vouchers[voucher]['credit']
                orig_diff = abs(orig_debit - orig_credit)
                
                if orig_diff < 0.01:  # Was balanced in original
                    problematic_vouchers.append({
                        'voucher': voucher,
                        'original': {'debit': orig_debit, 'credit': orig_credit, 'diff': orig_diff},
                        'enhanced': {'debit': debit, 'credit': credit, 'diff': diff}
                    })
        
        if problematic_vouchers:
            print(f"\n🔥 PROBLEMATIC VOUCHERS (balanced in original, unbalanced in enhanced):")
            for pv in problematic_vouchers:
                print(f"\n  Voucher: {pv['voucher']}")
                print(f"    Original:  Debit={pv['original']['debit']:,.2f}, Credit={pv['original']['credit']:,.2f}, Diff={pv['original']['diff']:,.2f}")
                print(f"    Enhanced:  Debit={pv['enhanced']['debit']:,.2f}, Credit={pv['enhanced']['credit']:,.2f}, Diff={pv['enhanced']['diff']:,.2f}")
                print(f"    Change:    Debit={pv['enhanced']['debit'] - pv['original']['debit']:+,.2f}, Credit={pv['enhanced']['credit'] - pv['original']['credit']:+,.2f}")
        else:
            print(f"\n✅ No vouchers became unbalanced (all unbalanced vouchers were already unbalanced in original)")
        
        # Summary and recommendations
        print(f"\n" + "=" * 80)
        print("SUMMARY AND RECOMMENDATIONS")
        print("=" * 80)
        
        if original_balanced and not enhanced_balanced:
            print("🚨 CRITICAL: Original converter produces balanced entries, but enhanced converter does not!")
            print("   This indicates the consolidation logic is introducing the imbalance.")
            
            if consolidated_entries:
                print(f"\n💡 LIKELY CAUSE: Consolidation logic issue")
                print(f"   - {len(consolidated_entries)} consolidated entries found")
                print(f"   - Check if consolidation is double-counting amounts")
                print(f"   - Verify currency conversion consistency")
                print(f"   - Review VCT responsibility entry creation")
        
        elif not original_balanced and not enhanced_balanced:
            print("⚠️  Both converters produce unbalanced entries.")
            print("   The issue may be in the source data or base conversion logic.")
        
        elif original_balanced and enhanced_balanced:
            print("✅ Both converters produce balanced entries.")
            print("   The balance issue may be in the test setup.")
        
        print(f"\n📄 Detailed results saved to:")
        print(f"   Original: {output_original}")
        print(f"   Enhanced: {output_enhanced}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(output_original):
                os.remove(output_original)
            if os.path.exists(output_enhanced):
                os.remove(output_enhanced)
        except:
            pass

if __name__ == "__main__":
    success = analyze_balance_issue()
    sys.exit(0 if success else 1)
