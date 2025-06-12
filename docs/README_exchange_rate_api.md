# Exchange Rate API Integration

This module provides functionality to retrieve currency exchange rates from the Business Central API.

## Features

- **API-Based Exchange Rates**: Retrieves up-to-date exchange rates from Business Central API
- **Company-Specific Rates**: Handles different home currencies for different companies
- **Currency Code Normalization**: Handles currency code prefixes (R-, Z-)
- **Cross-Currency Conversion**: Calculates rates between any two currencies
- **Caching**: Minimizes API calls by caching results

## Setup

1. **Install Dependencies**:
   ```bash
   pip install requests pandas python-dotenv
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and update with your credentials:
   ```bash
   cp .env.example .env
   # Then edit .env with your actual credentials
   ```

3. **Required Environment Variables**:
   - `BC_CLIENT_ID`: Your Business Central API client ID
   - `BC_CLIENT_SECRET`: Your Business Central API client secret
   - `BC_TENANT_ID`: Your Business Central tenant ID (default: "6b83c27c-aa6d-475a-9933-5c34bb008d73")
   - `BC_COMPANY`: Default company to use for exchange rates (default: "VCJ")
   - `BC_SCOPE`: API scope (default: "https://api.businesscentral.dynamics.com/.default")
   - `BC_VERIFY_SSL`: Whether to verify SSL certificates (default: "True")
   - `USE_EXCHANGE_RATE_API`: Whether to use the API (default: "True")

## Usage

### Basic Usage

```python
from exchange_rate_query import get_exchange_rate

# Get exchange rate from USD to EUR
rate = get_exchange_rate("USD", "EUR")
print(f"1 USD = {rate} EUR")

# With debug information
rate = get_exchange_rate("USD", "JPY", debug=True)
print(f"1 USD = {rate} JPY")

# Using first day of the month for exchange rates
rate = get_exchange_rate("USD", "EUR", use_month_start=True)
print(f"1 USD = {rate} EUR (using first day of current month)")
```

### Advanced Usage

```python
from exchange_rate_api import ExchangeRateAPI

# Create API client
api_client = ExchangeRateAPI()

# Get exchange rate with specific company and date
rate = api_client.get_exchange_rate(
    from_currency="USD",
    to_currency="EUR",
    company_name="VCJ",
    date="2025-04-01"
)
print(f"1 USD = {rate} EUR on 2025-04-01")

# Use the first day of the month for exchange rates
rate = api_client.get_exchange_rate(
    from_currency="USD",
    to_currency="EUR",
    use_month_start=True
)
print(f"1 USD = {rate} EUR (using first day of current month)")

# Handle currency code prefixes
rate = api_client.get_exchange_rate("R-USD", "JPY")
print(f"1 R-USD = {rate} JPY")
```

## Understanding the API Response

The Business Central API returns exchange rates in the following format:

```json
{
    "Currency_Code": "USD",
    "Exchange_Rate_Amount": 1,
    "Relational_Exch_Rate_Amount": 149.53,
    "Starting_Date": "2025-04-01"
}
```

Where:
- `Currency_Code`: The foreign currency code
- `Exchange_Rate_Amount`: The amount of foreign currency (e.g., 1 or 100)
- `Relational_Exch_Rate_Amount`: The equivalent amount in home currency
- `Starting_Date`: The date from which this rate is effective

For example, if the home currency is JPY:
- `Exchange_Rate_Amount: 1, Relational_Exch_Rate_Amount: 149.53` means 1 USD = 149.53 JPY

If the home currency is NTD:
- `Exchange_Rate_Amount: 100, Relational_Exch_Rate_Amount: 3233` means 100 USD = 3233 NTD, or 1 USD = 32.33 NTD

## Company-Specific Home Currencies

Each company has its own home currency:

- VCT: NTD (Taiwan Dollar)
- VCA: USD (US Dollar)
- VCP: PHP (Philippine Peso)
- VCG: EUR (Euro)
- VCJ: JPY (Japanese Yen)

## Running Tests

Run the unit tests to verify the functionality:

```bash
python -m unittest test_exchange_rate.py
```

## Demo Script

Run the demo script to see the API in action:

```bash
python demo_exchange_rate_api.py
```

## Troubleshooting

### API Connection Issues

If you encounter API connection issues:

1. Check your credentials in the `.env` file
2. Ensure you have network connectivity to the Business Central API
3. Try setting `BC_VERIFY_SSL=False` if you have SSL certificate issues
4. Check the logs for detailed error messages

## Contributing

When contributing to this module:

1. Add tests for any new functionality
2. Ensure backward compatibility with existing code
3. Update documentation to reflect changes
