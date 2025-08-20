#!/usr/bin/env python3
"""
Test VCT responsibility double counting fix.

This test module validates that the fix for VCT responsibility double counting works correctly.
The issue was that consolidated V-VC00048 entries were being treated as additional source entries
for VCT responsibility processing, causing amounts to be doubled.

Example scenario:
- Original entries: 5600 + 10000 = 15600
- Consolidated entry: 15600 (result of consolidation)
- Before fix: VCT responsibility processed 5600 + 10000 + 15600 = 31200 (WRONG)
- After fix: VCT responsibility processes 5600 + 10000 = 15600 (CORRECT)
"""

import sys
import os
import unittest
from decimal import Decimal

# Add the parent directory to the path so we can import the core module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.vct_responsibility_consolidation import collect_vct_responsibility_candidates


class TestVCTResponsibilityDoubleCountingFix(unittest.TestCase):
    """Test VCT responsibility double counting fix."""

    def create_vvc_entry(self, voucher_no, amount, cost_center, consolidated=False, original_entries_count=None):
        """Helper to create V-VC00048 test entries."""
        entry = {
            'voucher_no': voucher_no,
            'transaction_date': '2025/05/14',
            'External_Document_No': '20250514',
            'Document_Date': '2025/05/14',
            'description': 'Test entry',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'V-VC00048',
                'amount': amount,
                'currency': 'R-USD',
                'department': f'{cost_center}.1342G',
                'department_code': f'{cost_center}.9999'
            }
        }
        
        if consolidated:
            entry['credit']['consolidated'] = True
            if original_entries_count:
                entry['credit']['original_entries_count'] = original_entries_count
                entry['credit']['consolidation_note'] = f"Consolidated from {original_entries_count} entries"
        
        return entry

    def test_exclude_consolidated_entries_from_vct_responsibility(self):
        """Test that consolidated V-VC00048 entries are excluded from VCT responsibility collection."""
        # Create test data matching the actual scenario from VCA-0721.json
        entries = [
            # Original entries (should be collected)
            self.create_vvc_entry("APA-0000470", 5600.0, "VCA", consolidated=False),
            self.create_vvc_entry("APA-0000470", 10000.0, "VCA", consolidated=False),
            # Consolidated entry (should be excluded)
            self.create_vvc_entry("APA-0000470", 15600.0, "VCA", consolidated=True, original_entries_count=2)
        ]
        
        candidates = collect_vct_responsibility_candidates(entries)
        
        # Should only collect 2 original entries, not the consolidated one
        self.assertIn("APA-0000470", candidates)
        self.assertEqual(len(candidates["APA-0000470"]), 2)
        
        # Verify total amount is correct (not doubled)
        total_amount = sum(e["credit"]["amount"] for e in candidates["APA-0000470"])
        self.assertEqual(total_amount, 15600.0)  # Not 31200.0
        
        # Verify the entries are the original ones, not the consolidated one
        amounts = [e["credit"]["amount"] for e in candidates["APA-0000470"]]
        self.assertIn(5600.0, amounts)
        self.assertIn(10000.0, amounts)
        self.assertNotIn(15600.0, amounts)  # Consolidated amount should not be in candidates

    def test_vct_responsibility_correct_total_calculation(self):
        """Test that VCT responsibility calculates correct total amounts without doubling."""
        # Test with multiple vouchers to ensure comprehensive coverage
        entries = [
            # APA-0000470: Two original entries + one consolidated
            self.create_vvc_entry("APA-0000470", 5600.0, "VCA"),
            self.create_vvc_entry("APA-0000470", 10000.0, "VCA"),
            self.create_vvc_entry("APA-0000470", 15600.0, "VCA", consolidated=True),
            
            # APA-0000579: Single entry + consolidated (should still work)
            self.create_vvc_entry("APA-0000579", 300.0, "VCA"),
            self.create_vvc_entry("APA-0000579", 300.0, "VCA", consolidated=True),
            
            # APA-0000600: Single entry + consolidated
            self.create_vvc_entry("APA-0000600", 873.96, "VCA"),
            self.create_vvc_entry("APA-0000600", 873.96, "VCA", consolidated=True)
        ]
        
        candidates = collect_vct_responsibility_candidates(entries)
        
        # Verify each voucher has correct number of candidates
        self.assertEqual(len(candidates["APA-0000470"]), 2)  # 2 original entries
        self.assertEqual(len(candidates["APA-0000579"]), 1)  # 1 original entry
        self.assertEqual(len(candidates["APA-0000600"]), 1)  # 1 original entry
        
        # Verify amounts are correct (not doubled)
        apa_470_total = sum(e["credit"]["amount"] for e in candidates["APA-0000470"])
        apa_579_total = sum(e["credit"]["amount"] for e in candidates["APA-0000579"])
        apa_600_total = sum(e["credit"]["amount"] for e in candidates["APA-0000600"])
        
        self.assertEqual(apa_470_total, 15600.0)
        self.assertEqual(apa_579_total, 300.0)
        self.assertEqual(apa_600_total, 873.96)

    def test_original_entries_still_processed(self):
        """Test that original V-VC00048 entries are still processed correctly."""
        # Create test data with only original entries (no consolidated ones)
        entries = [
            self.create_vvc_entry("APA-0000123", 1000.0, "VCA"),
            self.create_vvc_entry("APA-0000123", 2000.0, "VCA"),
            self.create_vvc_entry("APA-0000456", 500.0, "VCP")
        ]
        
        candidates = collect_vct_responsibility_candidates(entries)
        
        # All entries should be collected since none are consolidated
        self.assertEqual(len(candidates["APA-0000123"]), 2)
        self.assertEqual(len(candidates["APA-0000456"]), 1)
        
        # Verify amounts
        apa_123_total = sum(e["credit"]["amount"] for e in candidates["APA-0000123"])
        apa_456_total = sum(e["credit"]["amount"] for e in candidates["APA-0000456"])
        
        self.assertEqual(apa_123_total, 3000.0)
        self.assertEqual(apa_456_total, 500.0)

    def test_vct_cost_center_entries_excluded(self):
        """Test that V-VC00048 entries with VCT cost center are still excluded."""
        entries = [
            # VCA cost center (should be collected)
            self.create_vvc_entry("APA-0000111", 1000.0, "VCA"),
            # VCT cost center (should be excluded - existing logic)
            self.create_vvc_entry("APA-0000222", 2000.0, "VCT"),
            # VCA consolidated (should be excluded - new logic)
            self.create_vvc_entry("APA-0000111", 1000.0, "VCA", consolidated=True)
        ]
        
        candidates = collect_vct_responsibility_candidates(entries)
        
        # Only APA-0000111 VCA original entry should be collected
        self.assertEqual(len(candidates), 1)
        self.assertIn("APA-0000111", candidates)
        self.assertEqual(len(candidates["APA-0000111"]), 1)
        self.assertEqual(candidates["APA-0000111"][0]["credit"]["amount"], 1000.0)

    def test_non_vvc00048_vendors_unaffected(self):
        """Test that non-V-VC00048 vendors are not affected by the fix."""
        entries = [
            # V-VC00048 entries
            self.create_vvc_entry("APA-0000111", 1000.0, "VCA"),
            self.create_vvc_entry("APA-0000111", 1000.0, "VCA", consolidated=True),
            # Non-V-VC00048 vendor
            {
                'voucher_no': 'APA-0000222',
                'credit': {
                    'vendor_code': 'V-US00007',
                    'amount': 2000.0,
                    'department': 'VCA.1342G',
                    'consolidated': True  # This should not affect non-V-VC00048 vendors
                }
            }
        ]
        
        candidates = collect_vct_responsibility_candidates(entries)
        
        # Only V-VC00048 original entry should be collected
        self.assertEqual(len(candidates), 1)
        self.assertIn("APA-0000111", candidates)
        self.assertEqual(len(candidates["APA-0000111"]), 1)

    def test_edge_case_empty_entries(self):
        """Test edge cases with empty or malformed entries."""
        entries = [
            # Normal entry
            self.create_vvc_entry("APA-0000111", 1000.0, "VCA"),
            # Entry without credit section
            {'voucher_no': 'APA-0000222'},
            # Entry with empty credit section
            {'voucher_no': 'APA-0000333', 'credit': {}},
            # Entry without vendor_code
            {'voucher_no': 'APA-0000444', 'credit': {'amount': 500.0, 'department': 'VCA.1342G'}}
        ]
        
        candidates = collect_vct_responsibility_candidates(entries)
        
        # Only the normal entry should be collected
        self.assertEqual(len(candidates), 1)
        self.assertIn("APA-0000111", candidates)

    def test_real_world_scenario_vca_0721(self):
        """Test with data structure similar to actual VCA-0721.json file."""
        # Simulate the actual data structure from VCA-0721.json
        entries = [
            # APA-0000470 original entries
            {
                "voucher_no": "APA-0000470",
                "transaction_date": "2025/05/14",
                "External_Document_No": "20250514",
                "credit": {
                    "gl_account": "Vendor",
                    "vendor_code": "V-VC00048",
                    "amount": 5600.0,
                    "currency": "R-USD",
                    "department": "VCA.1342G",
                    "department_code": "VCA.9999",
                    "account_source": "vendor_code"
                }
            },
            {
                "voucher_no": "APA-0000470",
                "transaction_date": "2025/05/27",
                "External_Document_No": "20250525",
                "credit": {
                    "gl_account": "Vendor",
                    "vendor_code": "V-VC00048",
                    "amount": 10000.0,
                    "currency": "R-USD",
                    "department": "VCA.1342G",
                    "department_code": "VCA.9999",
                    "account_source": "vendor_code"
                }
            },
            # APA-0000470 consolidated entry (should be excluded)
            {
                "voucher_no": "APA-0000470",
                "credit": {
                    "gl_account": "Vendor",
                    "vendor_code": "V-VC00048",
                    "amount": 15600.0,
                    "currency": "R-USD",
                    "department": "VCA.1342G",
                    "department_code": "VCA.9999",
                    "consolidated": True,
                    "original_entries_count": 2,
                    "account_source": "vendor_code",
                    "raw_total_before_rounding": 15600.0,
                    "consolidation_note": "Consolidated from 2 entries"
                }
            }
        ]
        
        candidates = collect_vct_responsibility_candidates(entries)
        
        # Should collect only the 2 original entries for APA-0000470
        self.assertEqual(len(candidates), 1)
        self.assertIn("APA-0000470", candidates)
        self.assertEqual(len(candidates["APA-0000470"]), 2)
        
        # Verify total is 15600, not 31200
        total = sum(e["credit"]["amount"] for e in candidates["APA-0000470"])
        self.assertEqual(total, 15600.0)
        
        # Verify individual amounts
        amounts = sorted([e["credit"]["amount"] for e in candidates["APA-0000470"]])
        self.assertEqual(amounts, [5600.0, 10000.0])


if __name__ == '__main__':
    unittest.main()