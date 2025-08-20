#!/usr/bin/env python3
"""
Test the intercompany code logic for V-VC00048 vendor credit lines.
"""

import sys
import os
import unittest
from decimal import Decimal

# Add the parent directory to the path so we can import the core module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.process_japan_exports import create_journal_line
from core.vct_responsibility_consolidation import collect_vct_responsibility_candidates

class TestVVC00048Intercompany(unittest.TestCase):
    """Test the intercompany code logic for V-VC00048 vendor credit lines."""

    def test_vvc00048_credit_line_vct_cost_center(self):
        """Test that V-VC00048 credit lines with VCT cost center have empty intercompany code."""
        # Create a test entry with V-VC00048 vendor code and VCT cost center
        entry = {
            'voucher_no': 'TEST-001',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'V-VC00048',
                'department': 'VCT.1234',
                'amount': Decimal('1000.00'),
                'currency': 'NTD'
            }
        }

        # Create a credit line
        credit_line = create_journal_line(entry, 'credit')

        # Check that the intercompany code is empty
        self.assertEqual(credit_line['ShortcutDimCode3'], '')

    def test_vvc00048_credit_line_non_vct_cost_center(self):
        """Test that V-VC00048 credit lines with non-VCT cost center have intercompany code set to VCT."""
        # Create a test entry with V-VC00048 vendor code and non-VCT cost center
        entry = {
            'voucher_no': 'TEST-002',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'V-VC00048',
                'department': 'VCA.1234',
                'amount': Decimal('1000.00'),
                'currency': 'USD'
            }
        }

        # Create a credit line
        credit_line = create_journal_line(entry, 'credit')

        # Check that the intercompany code is set to VCT
        self.assertEqual(credit_line['ShortcutDimCode3'], 'VCT')

    def test_other_vendor_credit_line_vct_cost_center(self):
        """Test that other vendor credit lines with VCT cost center have empty intercompany code."""
        # Create a test entry with other vendor code and VCT cost center
        entry = {
            'voucher_no': 'TEST-003',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'OTHER-VENDOR',
                'department': 'VCT.1234',
                'amount': Decimal('1000.00'),
                'currency': 'NTD'
            }
        }

        # Create a credit line
        credit_line = create_journal_line(entry, 'credit')

        # Check that the intercompany code is empty
        self.assertEqual(credit_line['ShortcutDimCode3'], '')

    def test_other_vendor_credit_line_non_vct_cost_center(self):
        """Test that other vendor credit lines with non-VCT cost center have intercompany code set to VCT."""
        # Create a test entry with other vendor code and non-VCT cost center
        entry = {
            'voucher_no': 'TEST-004',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'OTHER-VENDOR',
                'department': 'VCA.1234',
                'amount': Decimal('1000.00'),
                'currency': 'USD'
            }
        }

        # Create a credit line
        credit_line = create_journal_line(entry, 'credit')

        # Check that the intercompany code is set to VCT
        self.assertEqual(credit_line['ShortcutDimCode3'], 'VCT')

    def test_vct_responsibility_collection_with_consolidated_entries(self):
        """Test that VCT responsibility collection excludes consolidated entries but preserves intercompany logic."""
        # Create test entries including consolidated ones
        entries = [
            {
                'voucher_no': 'TEST-VCT-001',
                'credit': {
                    'gl_account': 'Vendor',
                    'vendor_code': 'V-VC00048',
                    'department': 'VCA.1234',
                    'amount': 1000.0,
                    'currency': 'USD'
                }
            },
            {
                'voucher_no': 'TEST-VCT-001',
                'credit': {
                    'gl_account': 'Vendor',
                    'vendor_code': 'V-VC00048',
                    'department': 'VCA.1234',
                    'amount': 1000.0,
                    'currency': 'USD',
                    'consolidated': True,  # This should be excluded
                    'original_entries_count': 1
                }
            }
        ]
        
        # Collect VCT responsibility candidates
        candidates = collect_vct_responsibility_candidates(entries)
        
        # Should only collect the original entry, not the consolidated one
        self.assertEqual(len(candidates), 1)
        self.assertIn('TEST-VCT-001', candidates)
        self.assertEqual(len(candidates['TEST-VCT-001']), 1)
        
        # Verify the collected entry still has correct intercompany behavior
        collected_entry = candidates['TEST-VCT-001'][0]
        credit_line = create_journal_line(collected_entry, 'credit')
        
        # Should still set intercompany code to VCT for non-VCT cost center
        self.assertEqual(credit_line['ShortcutDimCode3'], 'VCT')

if __name__ == '__main__':
    unittest.main()
