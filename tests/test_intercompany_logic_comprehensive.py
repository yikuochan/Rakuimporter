#!/usr/bin/env python3
"""
Comprehensive test coverage for intercompany code logic.

This test verifies the corrected business rules:
1. V-VC00048 with VCT cost center → ShortcutDimCode3 = "" (empty)
2. V-VC00048 with non-VCT cost center → ShortcutDimCode3 = "VCT"
3. All other vendors with any cost center → ShortcutDimCode3 = "" (empty)
"""

import sys
import os
import unittest
from decimal import Decimal

# Add the parent directory to the path so we can import the core module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.process_japan_exports import create_journal_line

class TestIntercompanyLogicComprehensive(unittest.TestCase):
    """Comprehensive test coverage for intercompany code assignment logic."""

    def test_v_vc00048_vct_cost_center_empty_intercompany(self):
        """Test V-VC00048 with VCT cost center gets empty ShortcutDimCode3."""
        entry = {
            'voucher_no': 'TEST-V-VCT-001',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'V-VC00048',
                'department': 'VCT.1234',  # VCT cost center
                'amount': Decimal('1000.00'),
                'currency': 'NTD'
            }
        }

        credit_line = create_journal_line(entry, 'credit')

        # V-VC00048 with VCT cost center should get empty intercompany code
        self.assertEqual(credit_line['ShortcutDimCode3'], '')
        self.assertEqual(credit_line['Account_No'], 'V-VC00048')

    def test_v_vc00048_vcp_cost_center_vct_intercompany(self):
        """Test V-VC00048 with VCP cost center gets ShortcutDimCode3='VCT'."""
        entry = {
            'voucher_no': 'TEST-V-VCP-001',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'V-VC00048',
                'department': 'VCP.1234',  # Non-VCT cost center
                'amount': Decimal('1500.00'),
                'currency': 'USD'
            }
        }

        credit_line = create_journal_line(entry, 'credit')

        # V-VC00048 with non-VCT cost center should get VCT intercompany code
        self.assertEqual(credit_line['ShortcutDimCode3'], 'VCT')
        self.assertEqual(credit_line['Account_No'], 'VCT')  # Mapped to VCT

    def test_v_vc00048_vsl_cost_center_vct_intercompany(self):
        """Test V-VC00048 with VSL cost center gets ShortcutDimCode3='VCT'."""
        entry = {
            'voucher_no': 'TEST-V-VSL-001',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'V-VC00048',
                'department': 'VSL.5678',  # Another non-VCT cost center
                'amount': Decimal('2000.00'),
                'currency': 'EUR'
            }
        }

        credit_line = create_journal_line(entry, 'credit')

        # V-VC00048 with VSL cost center should get VCT intercompany code
        self.assertEqual(credit_line['ShortcutDimCode3'], 'VCT')
        self.assertEqual(credit_line['Account_No'], 'VCT')  # Mapped to VCT

    def test_other_vendor_vct_cost_center_empty_intercompany(self):
        """Test other vendors with VCT cost center get empty ShortcutDimCode3."""
        entry = {
            'voucher_no': 'TEST-OTHER-VCT-001',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'OTHER-VENDOR-123',
                'department': 'VCT.9999',  # VCT cost center
                'amount': Decimal('800.00'),
                'currency': 'NTD'
            }
        }

        credit_line = create_journal_line(entry, 'credit')

        # Other vendors should always get empty intercompany code
        self.assertEqual(credit_line['ShortcutDimCode3'], '')
        self.assertEqual(credit_line['Account_No'], 'OTHER-VENDOR-123')

    def test_other_vendor_vcp_cost_center_empty_intercompany(self):
        """Test other vendors with VCP cost center get empty ShortcutDimCode3."""
        entry = {
            'voucher_no': 'TEST-OTHER-VCP-001',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'SUPPLIER-XYZ',
                'department': 'VCP.4567',  # Non-VCT cost center
                'amount': Decimal('1200.00'),
                'currency': 'USD'
            }
        }

        credit_line = create_journal_line(entry, 'credit')

        # Other vendors should get empty intercompany code even with non-VCT cost center
        self.assertEqual(credit_line['ShortcutDimCode3'], '')
        self.assertEqual(credit_line['Account_No'], 'SUPPLIER-XYZ')

    def test_other_vendor_vsl_cost_center_empty_intercompany(self):
        """Test other vendors with VSL cost center get empty ShortcutDimCode3."""
        entry = {
            'voucher_no': 'TEST-OTHER-VSL-001',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'VENDOR-ABC',
                'department': 'VSL.7890',  # Another non-VCT cost center
                'amount': Decimal('3000.00'),
                'currency': 'JPY'
            }
        }

        credit_line = create_journal_line(entry, 'credit')

        # Other vendors should get empty intercompany code regardless of cost center
        self.assertEqual(credit_line['ShortcutDimCode3'], '')
        self.assertEqual(credit_line['Account_No'], 'VENDOR-ABC')

    def test_v_vc00048_empty_department_empty_intercompany(self):
        """Test V-VC00048 with empty department gets empty ShortcutDimCode3."""
        entry = {
            'voucher_no': 'TEST-V-EMPTY-001',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'V-VC00048',
                'department': '',  # Empty department
                'amount': Decimal('500.00'),
                'currency': 'NTD'
            }
        }

        credit_line = create_journal_line(entry, 'credit')

        # Empty department should result in empty intercompany code
        self.assertEqual(credit_line['ShortcutDimCode3'], '')
        self.assertEqual(credit_line['Account_No'], 'V-VC00048')

    def test_other_vendor_empty_department_empty_intercompany(self):
        """Test other vendors with empty department get empty ShortcutDimCode3."""
        entry = {
            'voucher_no': 'TEST-OTHER-EMPTY-001',
            'credit': {
                'gl_account': 'Vendor',
                'vendor_code': 'VENDOR-EMPTY',
                'department': '',  # Empty department
                'amount': Decimal('750.00'),
                'currency': 'USD'
            }
        }

        credit_line = create_journal_line(entry, 'credit')

        # Other vendors with empty department should get empty intercompany code
        self.assertEqual(credit_line['ShortcutDimCode3'], '')
        self.assertEqual(credit_line['Account_No'], 'VENDOR-EMPTY')

    def test_business_rule_matrix_validation(self):
        """Validate the complete business rule matrix."""
        test_cases = [
            # (vendor, cost_center, expected_intercompany, expected_account, description)
            ('V-VC00048', 'VCT', '', 'V-VC00048', 'V-VC00048 + VCT → empty'),
            ('V-VC00048', 'VCP', 'VCT', 'VCT', 'V-VC00048 + VCP → VCT'),
            ('V-VC00048', 'VSL', 'VCT', 'VCT', 'V-VC00048 + VSL → VCT'),
            ('OTHER-VENDOR', 'VCT', '', 'OTHER-VENDOR', 'Other + VCT → empty'),
            ('OTHER-VENDOR', 'VCP', '', 'OTHER-VENDOR', 'Other + VCP → empty'),
            ('OTHER-VENDOR', 'VSL', '', 'OTHER-VENDOR', 'Other + VSL → empty'),
        ]

        for vendor, cost_center, expected_intercompany, expected_account, description in test_cases:
            with self.subTest(vendor=vendor, cost_center=cost_center, desc=description):
                entry = {
                    'voucher_no': f'TEST-MATRIX-{vendor}-{cost_center}',
                    'credit': {
                        'gl_account': 'Vendor',
                        'vendor_code': vendor,
                        'department': f'{cost_center}.1234',
                        'amount': Decimal('1000.00'),
                        'currency': 'NTD'
                    }
                }

                credit_line = create_journal_line(entry, 'credit')

                self.assertEqual(credit_line['ShortcutDimCode3'], expected_intercompany,
                    f"Failed for {description}: expected ShortcutDimCode3='{expected_intercompany}', got '{credit_line['ShortcutDimCode3']}'")
                self.assertEqual(credit_line['Account_No'], expected_account,
                    f"Failed for {description}: expected Account_No='{expected_account}', got '{credit_line['Account_No']}'")

if __name__ == '__main__':
    unittest.main()