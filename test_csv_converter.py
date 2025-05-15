#!/usr/bin/env python3
"""
Test script for csv_to_json_converter.py
"""

import json

# Mock data for testing
debit_data = {
    "G/L Account": "G/L Account",
    "借方：勘定科目：会計連携項目": "account_value",
    "借方：補助科目：会計連携項目": "sub_account_value",
    "支払先CD": "vendor_code_value"
}

credit_data = {
    "G/L Account": "G/L Account",
    "貸方：勘定科目：会計連携項目": "credit_account_value",
    "貸方：補助科目：会計連携項目": "credit_sub_account_value",
    "支払先CD": "credit_vendor_code_value"
}

# Test function to simulate process_gl_account
def test_process_gl_account():
    # Test debit side
    debit_entry = {"gl_account": "G/L Account", "account": "original_account"}
    
    # Simulate the process_gl_account function for debit
    if debit_entry["gl_account"] == "G/L Account":
        original_account = debit_entry["account"]
        debit_entry["account"] = debit_data.get("借方：補助科目：会計連携項目") or debit_data.get("借方：勘定科目：会計連携項目") or debit_data.get("支払先CD") or debit_entry["account"]
        print(f"Debit account changed from '{original_account}' to '{debit_entry['account']}'")
    
    # Test credit side
    credit_entry = {"gl_account": "G/L Account", "account": "original_credit_account"}
    
    # Simulate the process_gl_account function for credit
    if credit_entry["gl_account"] == "G/L Account":
        original_account = credit_entry["account"]
        credit_entry["account"] = credit_data.get("貸方：補助科目：会計連携項目") or credit_data.get("貸方：勘定科目：会計連携項目") or credit_data.get("支払先CD") or credit_entry["account"]
        print(f"Credit account changed from '{original_account}' to '{credit_entry['account']}'")
    
    # Test with missing sub_account
    debit_data_no_sub = debit_data.copy()
    debit_data_no_sub["借方：補助科目：会計連携項目"] = ""
    
    debit_entry_no_sub = {"gl_account": "G/L Account", "account": "original_account"}
    
    if debit_entry_no_sub["gl_account"] == "G/L Account":
        original_account = debit_entry_no_sub["account"]
        debit_entry_no_sub["account"] = debit_data_no_sub.get("借方：補助科目：会計連携項目") or debit_data_no_sub.get("借方：勘定科目：会計連携項目") or debit_data_no_sub.get("支払先CD") or debit_entry_no_sub["account"]
        print(f"Debit account (no sub) changed from '{original_account}' to '{debit_entry_no_sub['account']}'")
    
    # Test with missing sub_account and account
    debit_data_no_both = debit_data.copy()
    debit_data_no_both["借方：補助科目：会計連携項目"] = ""
    debit_data_no_both["借方：勘定科目：会計連携項目"] = ""
    
    debit_entry_no_both = {"gl_account": "G/L Account", "account": "original_account"}
    
    if debit_entry_no_both["gl_account"] == "G/L Account":
        original_account = debit_entry_no_both["account"]
        debit_entry_no_both["account"] = debit_data_no_both.get("借方：補助科目：会計連携項目") or debit_data_no_both.get("借方：勘定科目：会計連携項目") or debit_data_no_both.get("支払先CD") or debit_entry_no_both["account"]
        print(f"Debit account (no both) changed from '{original_account}' to '{debit_entry_no_both['account']}'")

if __name__ == "__main__":
    test_process_gl_account()
