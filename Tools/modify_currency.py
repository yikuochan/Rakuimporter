import json
import os

def modify_currency_values(data):
    """
    Modify currency values based on the rules:
    1. For department codes under VCT: Change currency value from NTD to empty
    2. For department codes under VCJ: If currency is JPY, change currency value to empty
    """
    modified_count = 0
    
    for entry in data:
        # Process debit section
        if "debit" in entry and "department_code" in entry["debit"]:
            dept_code = entry["debit"]["department_code"]
            currency = entry["debit"].get("currency", "")
            
            # Rule 1: VCT department with NTD currency
            if dept_code.startswith("VCT") and currency == "NTD":
                entry["debit"]["currency"] = ""
                modified_count += 1
            
            # Rule 2: VCJ department with JPY currency
            elif dept_code.startswith("VCJ") and currency == "JPY":
                entry["debit"]["currency"] = ""
                modified_count += 1
        
        # Process credit section
        if "credit" in entry and "department_code" in entry["credit"]:
            dept_code = entry["credit"]["department_code"]
            currency = entry["credit"].get("currency", "")
            
            # Rule 1: VCT department with NTD currency
            if dept_code.startswith("VCT") and currency == "NTD":
                entry["credit"]["currency"] = ""
                modified_count += 1
            
            # Rule 2: VCJ department with JPY currency
            elif dept_code.startswith("VCJ") and currency == "JPY":
                entry["credit"]["currency"] = ""
                modified_count += 1
    
    return data, modified_count

def main():
    input_file = "Test Raku export-all-noNTD-truncated-100.json"
    output_file = "Test Raku export-all-noNTD-truncated-modified.json"
    
    try:
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' not found.")
            return
        
        print(f"Reading input file: {input_file}")
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Found {len(data)} entries in the input file.")
        
        # Modify the currency values
        modified_data, count = modify_currency_values(data)
        
        # Write the modified data to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(modified_data, f, ensure_ascii=False, indent=2)
        
        print(f"Modified {count} currency values.")
        print(f"Modified data saved to {output_file}")
        
        # Verify the output file was created
        if os.path.exists(output_file):
            print(f"Output file '{output_file}' successfully created.")
            print(f"File size: {os.path.getsize(output_file)} bytes")
        else:
            print(f"Error: Failed to create output file '{output_file}'.")
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()