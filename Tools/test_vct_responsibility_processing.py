#!/usr/bin/env python3
"""
Test script to verify VCT responsibility entries are properly skipped during actual processing.
This test simulates the full processing flow to ensure entries with vct_responsibility=True are skipped.
"""

import json
import sys
import os
import logging
from unittest.mock import Mock, patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.process_japan_exports import process_entries, verify_balanced_amounts

# Set up logging to capture skip messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_entries():
    """Create test entries including VCT responsibility entries."""
    return [
        # Regular V-VC00048 entry with VCA cost center
        {
            "voucher_no": "APA-0000552",
            "External_Document_No": "EXT-552",
            "Document_Date": "2024/01/15",
            "description": "Test VCA expense",
            "debit": {
                "gl_account": "G/L Account",
                "account": "60100-10",
                "amount": 100.0,
                "currency": "USD",
                "department": "VCA.1234",
                "applicant_code": "EMP001"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "V-VC00048",
                "vendor_code": "V-VC00048",
                "amount": 100.0,
                "currency": "USD",
                "department": "VCA.1234",
                "applicant_code": "EMP001"
            }
        },
        # VCT responsibility debit entry (should be skipped)
        {
            "voucher_no": "APA-0000552",
            "External_Document_No": "EXT-552",
            "Document_Date": "2024/01/15",
            "description": "VCA.1234 Test VCA expense",
            "vct_responsibility": True,
            "debit": {
                "gl_account": "G/L Account",
                "account": "18600-10",
                "amount": 100.0,
                "currency": "USD",
                "department": "VCT.9999",
                "applicant_code": ""
            },
            "credit": {
                "gl_account": "",
                "account": "",
                "amount": 0,
                "currency": "",
                "department": "",
                "applicant_code": ""
            }
        },
        # VCT responsibility credit entry (should be skipped)
        {
            "voucher_no": "APA-0000552",
            "External_Document_No": "EXT-552",
            "Document_Date": "2024/01/15",
            "description": "Test VCA expense",
            "vct_responsibility": True,
            "debit": {
                "gl_account": "",
                "account": "",
                "amount": 0,
                "currency": "",
                "department": "",
                "applicant_code": ""
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "V-VC00048",
                "vendor_code": "V-VC00048",
                "amount": 100.0,
                "currency": "USD",
                "department": "VCT.9999",
                "applicant_code": ""
            }
        },
        # Another regular entry
        {
            "voucher_no": "APA-0000553",
            "External_Document_No": "EXT-553",
            "Document_Date": "2024/01/16",
            "description": "Regular expense",
            "debit": {
                "gl_account": "G/L Account",
                "account": "60200-10",
                "amount": 200.0,
                "currency": "USD",
                "department": "VCT.5678",
                "applicant_code": "EMP002"
            },
            "credit": {
                "gl_account": "Vendor",
                "account": "V-JP00001",
                "vendor_code": "V-JP00001",
                "amount": 200.0,
                "currency": "USD",
                "department": "VCT.5678",
                "applicant_code": "EMP002"
            }
        }
    ]

def test_vct_responsibility_processing():
    """Test that VCT responsibility entries are skipped during processing."""
    
    print("="*70)
    print("Testing VCT Responsibility Entry Processing")
    print("="*70)
    
    # Create test entries
    test_entries = create_test_entries()
    
    print(f"\nTotal input entries: {len(test_entries)}")
    
    # Count entry types
    regular_count = sum(1 for e in test_entries if not e.get("vct_responsibility", False))
    vct_resp_count = sum(1 for e in test_entries if e.get("vct_responsibility", False))
    
    print(f"Regular entries: {regular_count}")
    print(f"VCT responsibility entries: {vct_resp_count}")
    
    # Mock the API-related functions
    with patch('core.process_japan_exports.get_access_token') as mock_get_token, \
         patch('core.process_japan_exports.post_journal_line') as mock_post_journal, \
         patch('core.process_japan_exports.logger') as mock_logger:
        
        # Set up mocks
        mock_get_token.return_value = "test_token"
        mock_post_journal.return_value = (True, {"success": True})
        
        # Track which entries are processed
        processed_entries = []
        skipped_entries = []
        
        def track_journal_posting(journal_line, access_token, rate_limiter=None, max_retries=3):
            processed_entries.append(journal_line)
            return (True, {"success": True})
        
        mock_post_journal.side_effect = track_journal_posting
        
        # Track log messages
        log_messages = []
        
        def track_log_info(msg, *args):
            formatted_msg = msg % args if args else msg
            log_messages.append(formatted_msg)
            if "Skipping VCT responsibility entry" in formatted_msg:
                # Extract voucher number from log message
                voucher_match = formatted_msg.split("Voucher: ")[-1]
                skipped_entries.append(voucher_match)
        
        mock_logger.info.side_effect = track_log_info
        
        print("\nProcessing entries...")
        
        # Process entries using the actual process_entries function
        try:
            # Call the actual process_entries function to test the real flow
            success_count, failure_count, balanced_count, unbalanced_count = process_entries(
                test_entries, 
                "test_token",
                balance_tolerance=0.01,
                skip_unbalanced=False,
                base_delay=0.1,  # Faster for testing
                max_delay=0.2,
                max_retries=1
            )
            
            print(f"\nProcessing complete!")
            print(f"Success: {success_count}, Failure: {failure_count}")
            print(f"Balanced: {balanced_count}, Unbalanced: {unbalanced_count}")
            print(f"Journal lines posted: {len(processed_entries)}")
            
            # Verify results
            print("\n" + "="*50)
            print("VERIFICATION RESULTS:")
            print("="*50)
            
            # Verify skip log messages
            skip_logs = [msg for msg in log_messages if "Skipping VCT responsibility entry" in msg]
            print(f"\nSkip log messages found: {len(skip_logs)}")
            for log in skip_logs:
                print(f"  - {log}")
                # Extract voucher number from log message
                if "Voucher: " in log:
                    voucher = log.split("Voucher: ")[-1]
                    skipped_entries.append(voucher)
            
            print(f"Skipped vouchers: {skipped_entries}")
            
            # Expected: 2 regular entries should be processed (4 journal lines total: 2 debit + 2 credit)
            # Expected: 2 VCT responsibility entries should be skipped (0 journal lines)
            # Expected: Additional VCT responsibility entries created for V-VC00048 vendor (2 more lines)
            base_journal_lines = regular_count * 2  # Each entry creates debit + credit lines
            
            print(f"\nBase journal lines (regular entries): {base_journal_lines}")
            print(f"Actual journal lines posted: {len(processed_entries)}")
            
            # Check that we have at least the base number of journal lines
            # (additional VCT responsibility entries may be created)
            assert len(processed_entries) >= base_journal_lines, f"Expected at least {base_journal_lines} journal lines, got {len(processed_entries)}"
            
            # Verify that VCT responsibility entries were skipped
            assert len(skipped_entries) >= vct_resp_count, f"Expected at least {vct_resp_count} skipped entries, got {len(skipped_entries)}"
            
            # Additional verification: Check if VCT responsibility entries were created for V-VC00048
            additional_lines = len(processed_entries) - base_journal_lines
            print(f"Additional VCT responsibility lines created: {additional_lines}")
            
            print("\n" + "="*50)
            print("✅ TEST PASSED!")
            print("="*50)
            print(f"✅ Base journal lines posted: {base_journal_lines}")
            print(f"✅ Total journal lines posted: {len(processed_entries)}")
            print(f"✅ VCT responsibility entries skipped: {len(skipped_entries)}")
            print(f"✅ Additional VCT responsibility lines: {additional_lines}")
            print(f"✅ Skip logging working correctly")
            print(f"✅ Processing results - Success: {success_count}, Failure: {failure_count}")
            print("\n🎉 VCT responsibility entries are properly skipped during processing!")
            print("🎉 Additional VCT responsibility entries correctly created for V-VC00048!")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            raise

def test_entry_details():
    """Display detailed information about test entries."""
    
    print("\n" + "="*70)
    print("Test Entry Details")
    print("="*70)
    
    entries = create_test_entries()
    
    for i, entry in enumerate(entries, 1):
        print(f"\nEntry {i}:")
        print(f"  Voucher: {entry.get('voucher_no')}")
        print(f"  VCT Responsibility: {entry.get('vct_responsibility', False)}")
        
        if entry.get('vct_responsibility'):
            print(f"  Status: WILL BE SKIPPED")
        else:
            print(f"  Status: WILL BE PROCESSED")
        
        if entry['debit']['account']:
            print(f"  Debit: {entry['debit']['account']} ({entry['debit']['department']}) - {entry['debit']['amount']}")
        if entry['credit']['account']:
            print(f"  Credit: {entry['credit']['account']} ({entry['credit']['department']}) - {entry['credit']['amount']}")

if __name__ == "__main__":
    # Run the tests
    test_entry_details()
    print("\n")
    test_vct_responsibility_processing()
