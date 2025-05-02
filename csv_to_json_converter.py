import csv
import json
import io
import argparse
import sys

def normalize_currency(currency):
    """
    Normalize currency values according to requirements.
    
    Args:
        currency (str): The currency value to normalize
        
    Returns:
        str: The normalized currency value
    """
    if currency == "台湾ドル":
        return "NTD"
    elif currency == "円":
        return "JPY"
    else:
        return currency

def convert_csv_to_json(csv_file_path, json_file_path):
    """
    Convert a General Journal CSV file to JSON format.
    
    Args:
        csv_file_path (str): Path to the input CSV file
        json_file_path (str): Path to the output JSON file
    """
    # Read the CSV file with proper encoding
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split the content into lines
    lines = content.splitlines()
    
    # Process the two-line header using csv module
    header1 = next(csv.reader([lines[0]]))
    header2 = next(csv.reader([lines[1]]))
    
    # Combine headers, preferring non-empty values
    combined_header = []
    for i in range(max(len(header1), len(header2))):
        if i < len(header1) and header1[i].strip():
            combined_header.append(header1[i].strip())
        elif i < len(header2) and header2[i].strip():
            combined_header.append(header2[i].strip())
        else:
            combined_header.append(f"Column_{i}")
    
    # Process data rows
    journal_entries = []
    i = 2  # Start after the header rows
    
    while i < len(lines) - 1:  # Ensure we have at least 2 more lines
        debit_line = next(csv.reader([lines[i]]))
        credit_line = next(csv.reader([lines[i + 1]]))
        
        # Skip empty lines
        if not any(debit_line) or not any(credit_line):
            i += 1
            continue
        
        # Create a dictionary for the debit and credit rows
        debit_data = dict(zip(combined_header, debit_line))
        credit_data = dict(zip(combined_header, credit_line))
        
        # Extract common fields for the journal entry
        entry = {
            "voucher_no": debit_data.get("伝票No.") or credit_data.get("伝票No.") or "",
            "transaction_date": debit_data.get("仕訳日") or credit_data.get("仕訳日") or "",
            "application_date": debit_data.get("申請日") or credit_data.get("申請日") or "",
            "journal_generation_date": debit_data.get("仕訳データ生成日") or credit_data.get("仕訳データ生成日") or "",
            "description": debit_data.get("摘要") or credit_data.get("摘要") or "",
            "note": debit_data.get("Note(明細)") or credit_data.get("Note(明細)") or "",
            "receipt_invoice": debit_data.get("Receipt/Invoice #(明細)") or credit_data.get("Receipt/Invoice #(明細)") or "",
            "debit": {
                "marker": debit_data.get("勘定奉行：伝票区切") or "",
                "gl_account": debit_data.get("G/L Account") or "",
                "account": debit_data.get("借方：勘定科目：会計連携項目") or "",
                "sub_account": debit_data.get("借方：補助科目：会計連携項目") or "",
                "amount": debit_data.get("換算前額") or "",
                "currency": normalize_currency(debit_data.get("単位") or ""),
                "department": debit_data.get("借方：負担部門：会計連携項目") or "",
                "applicant_code": debit_data.get("申請者CD/支払先CD") or "",
                "vendor_code": debit_data.get("支払先CD") or "",
                "free_field": debit_data.get("フリー２(明細)") or "",
                "department_code": debit_data.get("借方：負担部門コード") or ""
            },
            "credit": {
                "marker": credit_data.get("勘定奉行：伝票区切") or "",
                "gl_account": credit_data.get("G/L Account") or "",
                "account": credit_data.get("貸方：勘定科目：会計連携項目") or "",
                "sub_account": credit_data.get("貸方：補助科目：会計連携項目") or "",
                "amount": credit_data.get("換算前額") or "",
                "currency": normalize_currency(credit_data.get("単位") or ""),
                "department": credit_data.get("借方：負担部門：会計連携項目") or "",
                "applicant_code": credit_data.get("申請者CD/支払先CD") or "",
                "vendor_code": credit_data.get("支払先CD") or "",
                "free_field": credit_data.get("フリー２(明細)") or "",
                "department_code": credit_data.get("借方：負担部門コード") or ""
            }
        }
        
        # Convert numeric values
        try:
            if entry["debit"]["amount"]:
                entry["debit"]["amount"] = float(entry["debit"]["amount"])
        except ValueError:
            pass
            
        try:
            if entry["credit"]["amount"]:
                entry["credit"]["amount"] = float(entry["credit"]["amount"])
        except ValueError:
            pass
        
        journal_entries.append(entry)
        i += 2  # Move to the next pair of rows
    
    # Write the JSON output
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(journal_entries, json_file, ensure_ascii=False, indent=2)
    
    return len(journal_entries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert General Journal CSV file to JSON format.')
    parser.add_argument('-i', '--input', default="Raku export.csv", help='Input CSV file path (default: "Raku export.csv")')
    parser.add_argument('-o', '--output', default="journal_entries.json", help='Output JSON file path (default: "journal_entries.json")')
    
    args = parser.parse_args()
    
    try:
        entry_count = convert_csv_to_json(args.input, args.output)
        print(f"Converted {entry_count} journal entries to JSON format.")
        print(f"Output saved to {args.output}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"Please make sure the input file '{args.input}' exists.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)