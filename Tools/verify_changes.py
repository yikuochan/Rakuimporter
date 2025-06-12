import json

def verify_changes(file_path):
    """
    Verify that the currency values have been modified according to the rules:
    1. For department codes under VCT: Currency value from NTD should be empty
    2. For department codes under VCJ: If currency is JPY, currency value should be empty
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    vct_ntd_count = 0
    vcj_jpy_count = 0
    other_currencies = {}
    
    for entry in data:
        # Check debit section
        if "debit" in entry and "department_code" in entry["debit"]:
            dept_code = entry["debit"]["department_code"]
            currency = entry["debit"].get("currency", "")
            
            # Check for VCT with NTD (should be empty now)
            if dept_code.startswith("VCT") and currency == "NTD":
                vct_ntd_count += 1
            
            # Check for VCJ with JPY (should be empty now)
            if dept_code.startswith("VCJ") and currency == "JPY":
                vcj_jpy_count += 1
            
            # Count other currencies
            if currency and currency not in ["", "NTD", "JPY"]:
                other_currencies[currency] = other_currencies.get(currency, 0) + 1
        
        # Check credit section
        if "credit" in entry and "department_code" in entry["credit"]:
            dept_code = entry["credit"]["department_code"]
            currency = entry["credit"].get("currency", "")
            
            # Check for VCT with NTD (should be empty now)
            if dept_code.startswith("VCT") and currency == "NTD":
                vct_ntd_count += 1
            
            # Check for VCJ with JPY (should be empty now)
            if dept_code.startswith("VCJ") and currency == "JPY":
                vcj_jpy_count += 1
            
            # Count other currencies
            if currency and currency not in ["", "NTD", "JPY"]:
                other_currencies[currency] = other_currencies.get(currency, 0) + 1
    
    print(f"Verification Results for {file_path}:")
    print(f"- Found {vct_ntd_count} entries with VCT department code and NTD currency (should be 0)")
    print(f"- Found {vcj_jpy_count} entries with VCJ department code and JPY currency (should be 0)")
    print("- Other currencies found:")
    for currency, count in other_currencies.items():
        print(f"  * {currency}: {count} occurrences")

if __name__ == "__main__":
    verify_changes("Test Raku export-all-noNTD-truncated-modified.json")
