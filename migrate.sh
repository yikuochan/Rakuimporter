#!/bin/bash
# Migration script for Power Importer
# This script helps migrate from the old structure to the new structure

# Create necessary directories
echo "Creating directory structure..."
mkdir -p core/currency core/converters core/api utils docs examples Temp/tests Temp/data Temp/rate_table

# Create __init__.py files
echo "Creating __init__.py files..."
touch core/__init__.py core/currency/__init__.py core/converters/__init__.py core/api/__init__.py utils/__init__.py

# Move key Python scripts to core directory
echo "Moving key Python scripts to core directory..."
cp charset_converter.py core/charset_converter.py
cp exchange_rate_api.py core/exchange_rate_api.py
cp exchange_rate_query.py core/exchange_rate_query.py
cp currency_converter.py core/currency_converter.py
cp csv_to_json_converter.py core/csv_to_json_converter.py
cp process_japan_exports.py core/process_japan_exports.py

# Move utility files to utils directory
echo "Moving utility files to utils directory..."
cp company_currency_mapping.py utils/company_currency_mapping.py
cp env_config.py utils/env_config.py
cp oauth_token_helper.py utils/oauth_token_helper.py

# Move test files to Temp/tests directory
echo "Moving test files to Temp/tests directory..."
find . -maxdepth 1 -name "test_*.py" -exec cp {} Temp/tests/ \;

# Move utility scripts to Tools directory
echo "Moving utility scripts to Tools directory..."
if [ -f "description_fix.py" ]; then
    cp description_fix.py Tools/
    echo "Moved description_fix.py to Tools/"
fi
if [ -f "description_fix_v2.py" ]; then
    cp description_fix_v2.py Tools/
    echo "Moved description_fix_v2.py to Tools/"
fi
if [ -f "run_test.py" ]; then
    cp run_test.py Tools/
    echo "Moved run_test.py to Tools/"
fi
if [ -f "run_tests.py" ]; then
    cp run_tests.py Tools/
    echo "Moved run_tests.py to Tools/"
fi
if [ -f "sync_client_secret.py" ]; then
    cp sync_client_secret.py Tools/
    echo "Moved sync_client_secret.py to Tools/"
fi

# Move currency rounding fix POC files to Temp/tests directory
echo "Moving currency rounding fix POC files to Temp/tests directory..."
if [ -f "currency_rounding_fix.py" ]; then
    cp currency_rounding_fix.py Temp/tests/
    echo "Moved currency_rounding_fix.py to Temp/tests/"
fi
if [ -f "currency_rounding_fix_updated.py" ]; then
    cp currency_rounding_fix_updated.py Temp/tests/
    echo "Moved currency_rounding_fix_updated.py to Temp/tests/"
fi

# Move CSV and JSON data files to Temp/data directory
echo "Moving CSV and JSON data files to Temp/data directory..."
find . -maxdepth 1 \( -name "*.csv" -o -name "*.json" -o -name "*.xlsx" \) -not -name "package*.json" -not -name "requirements.txt" -exec cp {} Temp/data/ \;

# Move Rate Table files to Temp/rate_table directory
echo "Moving Rate Table files to Temp/rate_table directory..."
if [ -d "Data/Rate Table" ]; then
    find "Data/Rate Table" -name "*.xlsx" -exec cp {} Temp/rate_table/ \;
    echo "Moved rate table files from Data/Rate Table to Temp/rate_table"
fi

# Move documentation files to docs directory
echo "Moving documentation files to docs directory..."
find . -maxdepth 1 -name "*.md" -not -name "README.md" -exec cp {} docs/ \;

# Move example files to examples directory
echo "Moving example files to examples directory..."
cp Temp/data/*.csv examples/ 2>/dev/null || true
cp Temp/data/*.json examples/ 2>/dev/null || true

# Create .gitkeep file in examples directory
touch examples/.gitkeep

echo "Migration completed successfully!"
echo "Please review the changes and update imports in the Python files as needed."
