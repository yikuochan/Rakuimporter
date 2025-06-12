# Power Importer

A tool for importing and processing financial data from various sources into Business Central.

## Overview

Power Importer is a Python-based tool designed to streamline the process of importing financial data from various sources into Microsoft Dynamics 365 Business Central. It handles character encoding conversion, CSV to JSON transformation, currency conversion, and API integration with Business Central.

## Key Features

- **Character Encoding Conversion**: Convert files between different character encodings, particularly useful for handling Japanese text.
- **CSV to JSON Transformation**: Convert CSV files to JSON format for API consumption.
- **Currency Conversion**: Handle currency conversion between different currencies using exchange rate APIs.
- **Business Central API Integration**: Post journal entries to Business Central via its API.
- **Error Handling**: Robust error handling and reporting for failed operations.
- **Logging**: Comprehensive logging for debugging and auditing.

## Project Structure

```
Power-importer/
├── core/                      # Core functionality scripts
│   ├── api/                   # API client modules
│   ├── converters/            # Data conversion modules
│   ├── currency/              # Currency-related modules
│   ├── charset_converter.py   # Converts files between different character encodings
│   ├── csv_to_json_converter.py # Converts CSV files to JSON format
│   ├── currency_converter.py  # Handles currency conversion
│   ├── exchange_rate_api.py   # API client for exchange rate services
│   ├── exchange_rate_query.py # Queries exchange rates
│   └── process_japan_exports.py # Processes export data from Japan
│
├── utils/                     # Utility functions
│   ├── company_currency_mapping.py # Maps companies to their currencies
│   ├── config.py              # Centralized configuration settings
│   ├── env_config.py          # Environment configuration handling
│   ├── oauth_token_helper.py  # OAuth token management
│   └── update_imports.py      # Script to update import statements
│
├── docs/                      # Documentation
│   ├── deployment_guide.md    # Guide for deploying the system
│   ├── migration_guide.md     # Guide for migrating to the new structure
│   └── project_structure.md   # Overview of the project structure
│
├── examples/                  # Example data and files
│
├── Temp/                      # Temporary files and test code
│   ├── data/                  # Data files
│   ├── tests/                 # Test scripts
│   └── rate_table/            # Rate table files (POC)
│
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore file
├── migrate.bat                # Windows migration script
├── migrate.sh                 # Linux/macOS migration script
├── README.md                  # Project README
├── requirements.txt           # Python dependencies
├── run_importer.py            # Main entry point
└── setup.py                   # Package setup script
```

For more details, see [docs/project_structure.md](docs/project_structure.md).

## Installation

### Prerequisites

- Python 3.8 or higher
- Git
- Access to Business Central API
- Exchange Rate API key (if using currency conversion)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/power-importer.git
   cd power-importer
   ```

2. Create a virtual environment:
   ```bash
   # On Linux/macOS
   python -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

5. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```

6. Edit the `.env` file with your configuration.

For detailed installation instructions, see [docs/deployment_guide.md](docs/deployment_guide.md).

## Usage

### Basic Usage

```bash
# Show help
python run_importer.py --help

# Basic usage
python run_importer.py "input.csv"

# Specify output JSON file
python run_importer.py "input.csv" --output-json "output.json"

# Skip importing to ERP
python run_importer.py "input.csv" --skip-import

# Dry run (generate report only without posting to API)
python run_importer.py "input.csv" --dry-run
```

### Using as a Package

If you've installed the Power Importer as a package, you can use the `power-importer` command:

```bash
# Show help
power-importer --help

# Basic usage
power-importer "input.csv"
```

For more usage options, see [docs/deployment_guide.md](docs/deployment_guide.md).

## Migration from Old Structure

If you're migrating from the old project structure, use the migration scripts:

```bash
# On Linux/macOS
./migrate.sh

# On Windows
migrate.bat
```

For detailed migration instructions, see [docs/migration_guide.md](docs/migration_guide.md).

## Documentation

- [Project Structure](docs/project_structure.md)
- [Deployment Guide](docs/deployment_guide.md)
- [Migration Guide](docs/migration_guide.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
