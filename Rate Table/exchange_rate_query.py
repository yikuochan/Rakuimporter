import pandas as pd

def get_exchange_rate(from_currency, to_currency, file_path="Standard-Exchange-rate-for-Apr-2025.xlsx", sheet_name="25 Apr for BS", debug=False):
    """
    Get the exchange rate between two currencies from the Excel file.
    
    Parameters:
    from_currency (str): The source currency code
    to_currency (str): The target currency code
    file_path (str): Path to the Excel file
    sheet_name (str): Name of the sheet containing exchange rates
    debug (bool): Whether to print debug information
    
    Returns:
    float: The exchange rate from source to target currency
    """
    try:
        # Read the Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        if debug:
            print(f"Excel file loaded successfully: {file_path}, sheet: {sheet_name}")
        
        # Get currency codes from column and row
        currency_codes_col = df.iloc[1:, 2]  # Third column (currency codes)
        currency_symbols_row = df.iloc[1, 3:]  # Third row (currency symbols/names)
        
        if debug:
            print(f"Currency codes in column: {list(currency_codes_col)}")
            print(f"Currency symbols in row: {list(currency_symbols_row)}")
        
        # Create a mapping of currency codes to their row indices
        currency_row_indices = {}
        for idx, code in enumerate(currency_codes_col):
            if pd.notna(code):
                currency_row_indices[str(code).strip()] = idx + 1  # +1 because we skipped the header row
        
        # Find the row index for from_currency
        if from_currency not in currency_row_indices:
            raise ValueError(f"Source currency '{from_currency}' not found in the exchange rate table")
        
        from_idx = currency_row_indices[from_currency]
        
        if debug:
            print(f"Found source currency '{from_currency}' at row index {from_idx}")
            print(f"Looking for target currency '{to_currency}' in column indices")
        
        # Find the column index for to_currency
        # First, check if the target currency is directly in the row
        to_idx = None
        for idx, symbol in enumerate(currency_symbols_row):
            if pd.notna(symbol) and to_currency in str(symbol):
                to_idx = idx + 3  # +3 because we skipped the header row and first three columns
                break
        
        # If not found directly, look for the target currency in the column and find its corresponding symbol in the row
        if to_idx is None and to_currency in currency_row_indices:
            target_row_idx = currency_row_indices[to_currency]
            # Get the currency code at this row
            target_currency_code = df.iloc[target_row_idx, 2]
            
            if debug:
                print(f"Target currency '{to_currency}' found in column at row {target_row_idx}")
                print(f"Looking for corresponding symbol in row")
            
            # Now find the column index where this currency appears in the header row
            for idx, code in enumerate(df.iloc[0, 3:]):
                if pd.notna(code) and target_currency_code in str(code):
                    to_idx = idx + 3
                    break
        
        if to_idx is None:
            # As a last resort, try to find the column by matching the currency code position
            # This assumes the currencies in the row match the order of currencies in the column
            if to_currency in currency_row_indices:
                position = list(currency_row_indices.keys()).index(to_currency)
                if position < len(currency_symbols_row):
                    to_idx = position + 3
        
        if to_idx is None:
            raise ValueError(f"Target currency '{to_currency}' not found in the exchange rate table")
        
        if debug:
            print(f"Found target currency '{to_currency}' at column index {to_idx}")
        
        # Get the exchange rate at the intersection
        rate = df.iloc[from_idx, to_idx]
        
        if debug:
            print(f"Exchange rate at intersection: {rate}")
        
        # Check if the rate is valid
        if pd.isna(rate) or rate == 0:
            raise ValueError(f"No valid exchange rate found between {from_currency} and {to_currency}")
            
        return rate
        
    except Exception as e:
        # Handle file not found, sheet not found, etc.
        if debug:
            import traceback
            print(f"Error details: {traceback.format_exc()}")
        raise Exception(f"Error retrieving exchange rate: {str(e)}")


# Example usage
if __name__ == "__main__":
    try:
        # Example: Get exchange rate from USD to EUR
        # Replace with actual currency codes from your Excel file
        rate = get_exchange_rate("USD", "EUR")
        print(f"Exchange rate from USD to EUR: {rate}")
        
        # You can also specify a different file path or sheet name
        # rate = get_exchange_rate("USD", "EUR", file_path="path/to/your/file.xlsx", sheet_name="Sheet1")
        
    except Exception as e:
        print(f"Error: {e}")
