import pandas as pd
from exchange_rate_query import get_exchange_rate

def convert_amount(amount, from_currency, to_currency):
    """
    Convert an amount from one currency to another.
    
    Parameters:
    amount (float): The amount to convert
    from_currency (str): The source currency code
    to_currency (str): The target currency code
    
    Returns:
    float: The converted amount
    """
    rate = get_exchange_rate(from_currency, to_currency)
    return amount * rate

def get_all_available_currencies():
    """
    Get a list of all available currency codes in the Excel file.
    
    Returns:
    list: List of available currency codes
    """
    try:
        # Read the Excel file
        df = pd.read_excel("Standard-Exchange-rate-for-Apr-2025.xlsx", sheet_name="25 Apr for BS", header=None)
        
        # Currency codes are in the third column
        currency_codes_col = df.iloc[1:, 2]  # Third column (currency codes)
        
        # Filter out NaN values and convert to list
        currencies = [code for code in currency_codes_col if pd.notna(code)]
        
        return currencies
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def main():
    print("Currency Exchange Rate Converter Example")
    print("---------------------------------------")
    
    # Get all available currencies
    currencies = get_all_available_currencies()
    print(f"Available currencies: {', '.join(currencies)}")
    
    # Example 1: Convert USD to JPY
    amount = 100
    from_currency = "USD"
    to_currency = "JPY"
    converted = convert_amount(amount, from_currency, to_currency)
    print(f"\nExample 1: {amount} {from_currency} = {converted:.2f} {to_currency}")
    
    # Example 2: Convert NTD to USD
    amount = 1000
    from_currency = "NTD"
    to_currency = "USD"
    converted = convert_amount(amount, from_currency, to_currency)
    print(f"Example 2: {amount} {from_currency} = {converted:.2f} {to_currency}")
    
    # Example 3: Convert multiple currencies to USD
    print("\nExample 3: Converting 100 units of various currencies to USD")
    amount = 100
    to_currency = "USD"
    for from_currency in ["JPY", "GBP", "AUD", "CAD"]:
        try:
            converted = convert_amount(amount, from_currency, to_currency)
            print(f"  {amount} {from_currency} = {converted:.2f} {to_currency}")
        except Exception as e:
            print(f"  Error converting {from_currency} to {to_currency}: {e}")
    
    # Example 4: Create a conversion table
    print("\nExample 4: Conversion table (1 unit to USD)")
    print("-" * 30)
    print(f"{'Currency':<10} | {'Rate to USD':<15}")
    print("-" * 30)
    
    for currency in currencies[:10]:  # Show first 10 currencies
        try:
            if currency != "USD" and currency != "Curr-CD":
                rate = get_exchange_rate(currency, "USD")
                print(f"{currency:<10} | {rate:<15.6f}")
        except Exception:
            pass

if __name__ == "__main__":
    main()
