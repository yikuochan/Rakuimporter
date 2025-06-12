# Power Importer Project Structure

This document describes the structure of the Power Importer project.

## Directory Structure

```
power-importer/
├── core/                   # Core functionality
│   ├── api/                # API client modules
│   ├── converters/         # Data conversion modules
│   ├── currency/           # Currency-related modules
│   ├── __init__.py
│   ├── charset_converter.py    # Character set conversion
│   ├── csv_to_json_converter.py # CSV to JSON conversion
│   ├── currency_converter.py   # Currency conversion
│   ├── exchange_rate_api.py    # Exchange rate API client
│   ├── exchange_rate_query.py  # Exchange rate query interface
│   └── process_japan_exports.py # Main processing script
├── docs/                   # Documentation
│   ├── deployment_guide.md
│   ├── migration_guide.md
│   └── project_structure.md
├── examples/               # Example files
│   └── .gitkeep
├── Temp/                   # Temporary files
│   ├── data/               # Data files
│   ├── tests/              # Test files
│   └── rate_table/         # Rate table files (POC)
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── company_currency_mapping.py # Company-currency mappings
│   ├── config.py           # Configuration management
│   ├── env_config.py       # Environment variable handling
│   ├── oauth_token_helper.py # OAuth token management
│   └── update_imports.py   # Import statement updater
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore file
├── migrate.bat             # Migration script (Windows)
├── migrate.sh              # Migration script (Unix)
├── README.md               # Project README
├── requirements.txt        # Python dependencies
├── run_importer.py         # Main entry point
└── setup.py                # Package setup script
```

## Core Modules

The `core` directory contains the main functionality of the Power Importer:

- `charset_converter.py`: Converts files from various charsets to UTF-8
- `csv_to_json_converter.py`: Converts CSV files to JSON format
- `currency_converter.py`: Handles currency conversion
- `exchange_rate_api.py`: Client for accessing currency exchange rates from the Business Central API
- `exchange_rate_query.py`: Interface for querying exchange rates
- `process_japan_exports.py`: Main processing script for importing data into the ERP system

## Utility Modules

The `utils` directory contains utility modules:

- `company_currency_mapping.py`: Mappings between companies and their currencies
- `config.py`: Configuration management
- `env_config.py`: Environment variable handling
- `oauth_token_helper.py`: OAuth token management
- `update_imports.py`: Script to update import statements in Python files

## Documentation

The `docs` directory contains documentation:

- `deployment_guide.md`: Guide for deploying the Power Importer
- `migration_guide.md`: Guide for migrating from the old structure to the new structure
- `project_structure.md`: This document

## Examples

The `examples` directory contains example files for testing and demonstration.

## Temporary Files

The `Temp` directory contains temporary files:

- `data`: Data files (CSV, JSON, etc.)
- `tests`: Test files

## Configuration

- `.env.example`: Example environment variables
- `requirements.txt`: Python dependencies
- `setup.py`: Package setup script

## Scripts

- `migrate.bat`: Migration script for Windows
- `migrate.sh`: Migration script for Unix
- `run_importer.py`: Main entry point for the Power Importer
