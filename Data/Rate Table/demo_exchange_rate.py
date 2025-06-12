from exchange_rate_query import get_exchange_rate

def main():
    print("Currency Exchange Rate Query Demo")
    print("--------------------------------")
    
    try:
        # Example 1: Basic usage
        print("\nExample 1: Basic usage")
        from_currency = "USD"
        to_currency = "JPY"
        rate = get_exchange_rate(from_currency, to_currency, debug=True)
        print(f"Exchange rate from {from_currency} to {to_currency}: {rate}")
        
        # Example 2: Different currencies
        print("\nExample 2: Different currencies")
        from_currency = "NTD"
        to_currency = "GBP"
        rate = get_exchange_rate(from_currency, to_currency, debug=True)
        print(f"Exchange rate from {from_currency} to {to_currency}: {rate}")
        
        # Example 3: Error handling
        print("\nExample 3: Error handling")
        try:
            # Intentionally using an invalid currency code
            rate = get_exchange_rate("XYZ", "USD", debug=True)
            print(f"Exchange rate: {rate}")
        except Exception as e:
            print(f"Caught error: {e}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("\nNote: Make sure the Excel file 'Standard-Exchange-rate-for-Apr-2025.xlsx' is in the current directory")
        print("and contains a sheet named '25 Apr for BS' with the expected format.")

if __name__ == "__main__":
    main()
