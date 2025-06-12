# Currency Exchange Rate Query

This project provides a Python function to query currency exchange rates from an Excel file containing a country-to-country matrix of exchange rates.

## Files

- `exchange_rate_query.py`: Contains the main function for querying exchange rates
- `demo_exchange_rate.py`: Basic demonstration of the exchange rate query function
- `example_usage.py`: Comprehensive example showing real-world usage scenarios
- `list_currencies.py`: Utility script to list all available currency codes in the Excel file
- `Standard-Exchange-rate-for-Apr-2025.xlsx`: Excel file containing the exchange rates (must be in the same directory)
- `setup_and_run.sh`: Shell script to set up the virtual environment and run the scripts

## Requirements

- Python 3.6 or higher
- pandas library
- openpyxl library (for Excel file handling)

## Setup and Running

### Option 1: Using the Setup Script (Recommended)

The easiest way to run the scripts is to use the provided setup script:

```bash
./setup_and_run.sh
```

This script will:
1. Set up a Python virtual environment
2. Install the required packages (pandas and openpyxl)
3. Offer you a choice of which script to run:
   - Basic demo (demo_exchange_rate.py)
   - Comprehensive example (example_usage.py)
   - List available currencies (list_currencies.py)
4. Run your selected script
5. Deactivate the virtual environment when done

### Option 2: Manual Setup

If you prefer to set up the environment manually:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install pandas openpyxl
```

Then you can run the demo:

```bash
python demo_exchange_rate.py
```

When you're done, deactivate the virtual environment:

```bash
deactivate
```

## Usage

### Basic Usage

```python
from exchange_rate_query import get_exchange_rate

# Get exchange rate from USD to EUR
rate = get_exchange_rate("USD", "EUR")
print(f"Exchange rate from USD to EUR: {rate}")
```

### Function Parameters

```python
get_exchange_rate(from_currency, to_currency, file_path="Standard-Exchange-rate-for-Apr-2025.xlsx", sheet_name="25 Apr for BS")
```

- `from_currency` (str): The source currency code
- `to_currency` (str): The target currency code
- `file_path` (str, optional): Path to the Excel file (default: "Standard-Exchange-rate-for-Apr-2025.xlsx")
- `sheet_name` (str, optional): Name of the sheet containing exchange rates (default: "25 Apr for BS")

### Running the Demo

To run the demonstration script:

```bash
python demo_exchange_rate.py
```

## Excel File Format

The function expects the Excel file to have a specific format:
- A country-to-country matrix table
- First column: Country names
- Second column: Additional information (if any)
- Third column: Currency codes (e.g., "USD", "JPY", "GBP")
- First row: Headers
- Second row: Currency symbols or names (e.g., "US$", "Yen", "STG￡")
- The exchange rates are located at the intersections of currencies in the matrix

**Important Note**: The function handles the difference between currency codes in the column and currency symbols/names in the row. You should use the currency codes (like "USD", "JPY") when calling the function, not the symbols.

## Error Handling

The function includes error handling for common issues:
- Currency code not found in the table
- Invalid exchange rate (NaN or 0)
- File not found
- Sheet not found

When an error occurs, the function raises an exception with a descriptive message.
