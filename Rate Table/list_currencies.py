import pandas as pd

def list_available_currencies(file_path="Standard-Exchange-rate-for-Apr-2025.xlsx", sheet_name="25 Apr for BS"):
    """
    List all available currency codes in the Excel file.
    
    Parameters:
    file_path (str): Path to the Excel file
    sheet_name (str): Name of the sheet containing exchange rates
    
    Returns:
    list: List of available currency codes
    """
    try:
        # Read the Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        # Currency codes are in the third column and row
        currency_codes_col = df.iloc[1:, 2]  # Third column (currency codes)
        
        # Filter out NaN values and convert to list
        currencies = [code for code in currency_codes_col if pd.notna(code)]
        
        return currencies
        
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    print("Available Currency Codes:")
    print("------------------------")
    
    currencies = list_available_currencies()
    
    if currencies:
        for i, currency in enumerate(currencies, 1):
            print(f"{i}. {currency}")
        
        print(f"\nTotal: {len(currencies)} currencies found")
    else:
        print("No currencies found or an error occurred.")
