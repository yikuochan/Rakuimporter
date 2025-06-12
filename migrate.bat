@echo off
REM Migration script for Power Importer
REM This script helps migrate from the old structure to the new structure

echo Creating directory structure...
mkdir core\currency core\converters core\api utils docs examples Temp\tests Temp\data Temp\rate_table 2>nul

echo Creating __init__.py files...
type nul > core\__init__.py
type nul > core\currency\__init__.py
type nul > core\converters\__init__.py
type nul > core\api\__init__.py
type nul > utils\__init__.py

echo Moving key Python scripts to core directory...
copy charset_converter.py core\charset_converter.py
copy exchange_rate_api.py core\exchange_rate_api.py
copy exchange_rate_query.py core\exchange_rate_query.py
copy currency_converter.py core\currency_converter.py
copy csv_to_json_converter.py core\csv_to_json_converter.py
copy process_japan_exports.py core\process_japan_exports.py

echo Moving utility files to utils directory...
copy company_currency_mapping.py utils\company_currency_mapping.py
copy env_config.py utils\env_config.py
copy oauth_token_helper.py utils\oauth_token_helper.py

echo Moving test files to Temp\tests directory...
for %%f in (test_*.py) do copy %%f Temp\tests\

echo Moving utility scripts to Tools directory...
if exist "description_fix.py" (
    copy description_fix.py Tools\
    echo Moved description_fix.py to Tools\
)
if exist "description_fix_v2.py" (
    copy description_fix_v2.py Tools\
    echo Moved description_fix_v2.py to Tools\
)
if exist "run_test.py" (
    copy run_test.py Tools\
    echo Moved run_test.py to Tools\
)
if exist "run_tests.py" (
    copy run_tests.py Tools\
    echo Moved run_tests.py to Tools\
)
if exist "sync_client_secret.py" (
    copy sync_client_secret.py Tools\
    echo Moved sync_client_secret.py to Tools\
)

echo Moving currency rounding fix POC files to Temp\tests directory...
if exist "currency_rounding_fix.py" (
    copy currency_rounding_fix.py Temp\tests\
    echo Moved currency_rounding_fix.py to Temp\tests\
)
if exist "currency_rounding_fix_updated.py" (
    copy currency_rounding_fix_updated.py Temp\tests\
    echo Moved currency_rounding_fix_updated.py to Temp\tests\
)

echo Moving CSV and JSON data files to Temp\data directory...
for %%f in (*.csv *.json *.xlsx) do (
    if not "%%f"=="package.json" if not "%%f"=="package-lock.json" if not "%%f"=="requirements.txt" (
        copy %%f Temp\data\
    )
)

echo Moving Rate Table files to Temp\rate_table directory...
if exist "Data\Rate Table" (
    for %%f in ("Data\Rate Table\*.xlsx") do (
        copy "%%f" Temp\rate_table\
    )
    echo Moved rate table files from Data\Rate Table to Temp\rate_table
)

echo Moving documentation files to docs directory...
for %%f in (*.md) do (
    if not "%%f"=="README.md" (
        copy %%f docs\
    )
)

echo Moving example files to examples directory...
copy Temp\data\*.csv examples\ 2>nul
copy Temp\data\*.json examples\ 2>nul

echo Creating .gitkeep file in examples directory...
type nul > examples\.gitkeep

echo Migration completed successfully!
echo Please review the changes and update imports in the Python files as needed.
