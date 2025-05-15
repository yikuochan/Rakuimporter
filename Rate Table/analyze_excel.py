import pandas as pd
import sys

def analyze_excel_file(file_path):
    """
    Analyze an Excel file and print information about its structure.
    
    Parameters:
    file_path (str): Path to the Excel file
    """
    try:
        # Get the sheet names
        xls = pd.ExcelFile(file_path)
        sheet_names = xls.sheet_names
        
        print(f"Excel File: {file_path}")
        print(f"Size: {sys.getsizeof(xls)} bytes")
        print(f"Number of sheets: {len(sheet_names)}")
        print(f"Sheet names: {', '.join(sheet_names)}")
        
        # Analyze each sheet
        for sheet_name in sheet_names:
            print(f"\n--- Sheet: {sheet_name} ---")
            
            # Read the sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            # Get basic info
            print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
            
            # Print a sample of the data (first 5 rows and columns)
            print("\nSample data (first 5 rows x 5 columns):")
            print(df.iloc[:5, :5])
            
            # Check for currency codes in the third column
            if df.shape[1] >= 3:
                print("\nCurrency codes in third column (first 10):")
                currency_codes = df.iloc[1:11, 2].tolist()
                print(currency_codes)
            
            # Check for currency symbols in the second row
            if df.shape[0] >= 2:
                print("\nCurrency symbols in second row (first 10):")
                currency_symbols = df.iloc[1, 3:13].tolist()
                print(currency_symbols)
            
    except Exception as e:
        print(f"Error analyzing Excel file: {e}")

if __name__ == "__main__":
    file_path = "Standard-Exchange-rate-for-Apr-2025.xlsx"
    analyze_excel_file(file_path)
