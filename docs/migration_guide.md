# Migration Guide

This guide helps you migrate from the old project structure to the new structure.

## Overview

The Power Importer project has been reorganized to improve maintainability and scalability. The key changes include:

1. Moving core functionality to the `core` directory
2. Moving utility modules to the `utils` directory
3. Moving test files to the `Temp/tests` directory
4. Moving data files to the `Temp/data` directory
5. Moving documentation to the `docs` directory
6. Creating a centralized configuration system
7. Creating a proper Python package structure

## Migration Steps

### Automated Migration

We provide migration scripts for both Unix/Linux/macOS and Windows:

#### Unix/Linux/macOS

```bash
# Make the script executable
chmod +x migrate.sh

# Run the migration script
./migrate.sh
```

#### Windows

```batch
# Run the migration script
migrate.bat
```

The migration script will:

1. Create the necessary directory structure
2. Create `__init__.py` files to make directories proper Python packages
3. Copy key Python scripts to the appropriate directories
4. Copy utility files to the `utils` directory
5. Copy test files to the `Temp/tests` directory
6. Copy data files to the `Temp/data` directory
7. Copy documentation files to the `docs` directory
8. Copy example files to the `examples` directory

### Manual Migration

If you prefer to migrate manually, follow these steps:

1. Create the directory structure:
   ```
   mkdir -p core/currency core/converters core/api utils docs examples Temp/tests Temp/data
   ```

2. Create `__init__.py` files:
   ```
   touch core/__init__.py core/currency/__init__.py core/converters/__init__.py core/api/__init__.py utils/__init__.py
   ```

3. Move key Python scripts to the `core` directory:
   ```
   cp charset_converter.py core/charset_converter.py
   cp exchange_rate_api.py core/exchange_rate_api.py
   cp exchange_rate_query.py core/exchange_rate_query.py
   cp currency_converter.py core/currency_converter.py
   cp csv_to_json_converter.py core/csv_to_json_converter.py
   cp process_japan_exports.py core/process_japan_exports.py
   ```

4. Move utility files to the `utils` directory:
   ```
   cp company_currency_mapping.py utils/company_currency_mapping.py
   cp env_config.py utils/env_config.py
   cp oauth_token_helper.py utils/oauth_token_helper.py
   ```

5. Move test files to the `Temp/tests` directory:
   ```
   find . -maxdepth 1 -name "test_*.py" -exec cp {} Temp/tests/ \;
   ```

6. Move currency rounding fix POC files to the `Temp/tests` directory:
   ```
   # For Unix/Linux/macOS
   if [ -f "currency_rounding_fix.py" ]; then
       cp currency_rounding_fix.py Temp/tests/
   fi
   if [ -f "currency_rounding_fix_updated.py" ]; then
       cp currency_rounding_fix_updated.py Temp/tests/
   fi
   
   # For Windows
   if exist "currency_rounding_fix.py" (
       copy currency_rounding_fix.py Temp\tests\
   )
   if exist "currency_rounding_fix_updated.py" (
       copy currency_rounding_fix_updated.py Temp\tests\
   )
   ```

6. Move data files to the `Temp/data` directory:
   ```
   find . -maxdepth 1 \( -name "*.csv" -o -name "*.json" -o -name "*.xlsx" \) -not -name "package*.json" -not -name "requirements.txt" -exec cp {} Temp/data/ \;
   ```

7. Move rate table files to the `Temp/rate_table` directory:
   ```
   # For Unix/Linux/macOS
   if [ -d "Data/Rate Table" ]; then
       find "Data/Rate Table" -name "*.xlsx" -exec cp {} Temp/rate_table/ \;
   fi
   
   # For Windows
   if exist "Data\Rate Table" (
       for %f in ("Data\Rate Table\*.xlsx") do copy "%f" Temp\rate_table\
   )
   ```

7. Move documentation files to the `docs` directory:
   ```
   find . -maxdepth 1 -name "*.md" -not -name "README.md" -exec cp {} docs/ \;
   ```

## Updating Import Statements

After migrating the files, you need to update the import statements in the Python files to reflect the new structure. We provide a utility script for this purpose:

```bash
# Run the import updater script
python utils/update_imports.py
```

This script will scan the Python files in the `core` and `utils` directories and update the import statements accordingly.

## Configuration

The new project structure uses a centralized configuration system. The configuration is loaded from environment variables with sensible defaults. You can customize the configuration by creating a `.env` file based on the `.env.example` file:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your preferred editor
nano .env  # or vim .env, etc.
```

## Running the Application

The main entry point for the application is now `run_importer.py`. You can run it with:

```bash
# Run the application
python run_importer.py <input_csv_file> [options]
```

For more information on the available options, run:

```bash
python run_importer.py --help
```

## Installing as a Package

You can install the Power Importer as a Python package:

```bash
# Install in development mode
pip install -e .

# Run the application using the installed package
power-importer <input_csv_file> [options]
```

## Troubleshooting

If you encounter any issues during the migration, please check the following:

1. Make sure you have the necessary permissions to create directories and files
2. Make sure you have the necessary Python packages installed (see `requirements.txt`)
3. Make sure you have set up the environment variables correctly (see `.env.example`)

If you still have issues, please contact the development team for assistance.
