# Power Importer - Clean Project Migration Plan

## Project Overview
This migration plan outlines the steps to reorganize the Power Importer project into a clean, maintainable structure. The current project contains ~2,687 Python files with scattered test directories, temporary files, and redundant code.

## Current Structure Analysis

### Core Components Identified
- **Core Business Logic**: Located in `core/` directory
  - CSV to JSON conversion
  - Currency conversion and rounding
  - Exchange rate API integration
  - Japan exports processing
  - VCT responsibility consolidation
  
- **Utilities**: Located in `utils/` directory
  - Configuration management
  - OAuth authentication
  - Company currency mappings

- **Tests**: Scattered across multiple directories
  - `tests/` - 29 test files
  - `unittest/` - Additional test files
  - `Temp/tests/` - Temporary test files

## Proposed Clean Directory Structure

```
power-importer-clean/
├── src/
│   ├── __init__.py
│   ├── main.py (renamed from run_importer.py)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── charset_converter.py
│   │   ├── csv_to_json_converter.py
│   │   ├── process_japan_exports.py
│   │   ├── currency_converter.py
│   │   ├── currency_rounding.py
│   │   ├── company_rounding_config.py
│   │   ├── exchange_rate_api.py
│   │   ├── exchange_rate_query.py
│   │   └── vct_responsibility_consolidation.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       ├── env_config.py
│       ├── oauth_token_helper.py
│       └── company_currency_mapping.py
├── tests/
│   ├── __init__.py
│   ├── test_company_specific_rounding.py
│   ├── test_72600_shortcut_dim_code4.py
│   ├── test_apa_0000619_consolidation_fix.py
│   ├── test_comprehensive_environment.py
│   ├── test_consolidated_debit_document_no_fix.py
│   ├── test_external_document_no_length_fix.py
│   ├── test_fix_verification.py
│   ├── test_production_config.py
│   ├── test_v_vc00048_cost_center_aware_skip_logic.py
│   ├── test_v_vc00048_intercompany.py
│   ├── test_v_vc00048_mapping.py
│   ├── test_vct_responsibility_document_no_fix.py
│   ├── test_vct_responsibility_document_no_sequencing.py
│   ├── test_vct_responsibility_double_counting.py
│   ├── test_zero_decimal_rounding.py
│   ├── validate_company_rounding_examples.py
│   └── fixtures/
│       ├── test_72600_data.json
│       ├── test_before_fix.json
│       ├── test_integration.json
│       ├── test_streamlined_output.json
│       ├── test_unified_input.csv
│       └── test_v_vc00048_skip_implementation.json
├── config/
│   ├── .env.example
│   └── logging.conf
├── data/
│   └── samples/
│       └── (sample CSV/JSON files for testing)
├── docs/
│   ├── API.md
│   ├── SETUP.md
│   └── USAGE.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── README.md
├── .gitignore
├── pytest.ini
└── Makefile
```

## Migration Execution Plan

### Phase 1: Preparation (Day 1)
1. **Create backup of current project**
   ```bash
   cp -r . ../Power-importer-backup-$(date +%Y%m%d)
   ```

2. **Create new clean project structure**
   ```bash
   mkdir -p power-importer-clean/{src/{core,utils},tests/fixtures,config,data/samples,docs}
   ```

### Phase 2: Core Migration (Day 1-2)

#### Step 1: Migrate Core Modules
```bash
# Copy core business logic
cp core/charset_converter.py power-importer-clean/src/core/
cp core/csv_to_json_converter.py power-importer-clean/src/core/
cp core/process_japan_exports.py power-importer-clean/src/core/
cp core/currency_converter.py power-importer-clean/src/core/
cp core/currency_rounding.py power-importer-clean/src/core/
cp core/company_rounding_config.py power-importer-clean/src/core/
cp core/exchange_rate_api.py power-importer-clean/src/core/
cp core/exchange_rate_query.py power-importer-clean/src/core/
cp core/vct_responsibility_consolidation.py power-importer-clean/src/core/
cp core/__init__.py power-importer-clean/src/core/
```

#### Step 2: Migrate Utilities
```bash
# Copy utility modules
cp utils/config.py power-importer-clean/src/utils/
cp utils/env_config.py power-importer-clean/src/utils/
cp utils/oauth_token_helper.py power-importer-clean/src/utils/
cp utils/company_currency_mapping.py power-importer-clean/src/utils/
cp utils/__init__.py power-importer-clean/src/utils/
```

#### Step 3: Migrate Main Entry Point
```bash
# Copy and rename main entry point
cp run_importer.py power-importer-clean/src/main.py
```

### Phase 3: Test Migration (Day 2)

#### Step 1: Consolidate Test Files
```bash
# Copy essential test files
cp tests/test_*.py power-importer-clean/tests/
cp tests/validate_*.py power-importer-clean/tests/

# Copy test fixtures
cp tests/*.json power-importer-clean/tests/fixtures/
cp tests/*.csv power-importer-clean/tests/fixtures/
```

#### Step 2: Create Test Configuration
Create `power-importer-clean/pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

### Phase 4: Configuration Migration (Day 2)

#### Step 1: Copy Configuration Files
```bash
cp requirements.txt power-importer-clean/
cp setup.py power-importer-clean/
cp .gitignore power-importer-clean/
cp .env.example power-importer-clean/config/
```

#### Step 2: Create Additional Configuration Files

Create `power-importer-clean/requirements-dev.txt`:
```
pytest>=7.0.0
pytest-cov>=3.0.0
black>=22.3.0
flake8>=4.0.1
isort>=5.10.1
mypy>=0.950
```

Create `power-importer-clean/Makefile`:
```makefile
.PHONY: install test lint format clean

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest tests/

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
```

### Phase 5: Import Path Updates (Day 3)

#### Update Import Statements
1. **In test files**: Change imports from `from core.module` to `from src.core.module`
2. **In core modules**: Update relative imports if needed
3. **In utils modules**: Update cross-module imports
4. **In main.py**: Update all module imports

#### Example Import Updates:
```python
# Old import
from core.csv_to_json_converter import convert_csv_to_json
from utils.config import get_config

# New import
from src.core.csv_to_json_converter import convert_csv_to_json
from src.utils.config import get_config
```

### Phase 6: Documentation (Day 3)

#### Consolidate Documentation
1. Create unified `README.md` from multiple README files
2. Create `docs/API.md` for API documentation
3. Create `docs/SETUP.md` for setup instructions
4. Create `docs/USAGE.md` for usage examples

### Phase 7: Validation (Day 4)

#### Testing Checklist
- [ ] All tests pass in new structure
- [ ] Main entry point works correctly
- [ ] Import paths are correct
- [ ] Configuration loading works
- [ ] OAuth authentication works
- [ ] CSV to JSON conversion works
- [ ] API integration works

#### Command Validation:
```bash
cd power-importer-clean

# Install dependencies
pip install -e .

# Run tests
pytest tests/

# Test main functionality
python src/main.py --help

# Run linting
make lint

# Format code
make format
```

## Files to Archive (Not Migrate)

### Directories to Archive:
- `Temp/` - Temporary files and old tests
- `Tools/` - Various tools and scripts
- `docs/` - Old documentation (after consolidation)
- `Data/` - Large data files (keep samples only)
- `memory-bank/` - Memory related files
- `unittest/` - Old unittest directory
- `backup_*/` - Backup directories
- `node_modules/` - Node.js dependencies
- `venv/`, `charset_converter_env/` - Virtual environments

### Files to Archive:
- All standalone Python files in root (except run_importer.py)
- All log files (`*.log`)
- All backup files (`*backup*`, `*_old*`)
- Report files (`*_report.md`, `*_SUMMARY.md`)
- Temporary JSON/CSV files in root

## Post-Migration Tasks

### 1. Update CI/CD
Create `.github/workflows/tests.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: make install
      - run: make test
      - run: make lint
```

### 2. Update setup.py
Ensure setup.py reflects new structure:
```python
packages=find_packages(where="src"),
package_dir={"": "src"},
entry_points={
    "console_scripts": [
        "power-importer=main:main",
    ],
}
```

### 3. Environment Variables
Ensure all environment variables are documented in `.env.example`

### 4. Dependencies Audit
- Review all dependencies in requirements.txt
- Remove unused packages
- Update to latest stable versions

## Success Criteria

The migration is successful when:
1. ✅ All tests pass in the new structure
2. ✅ The application runs without import errors
3. ✅ Documentation is consolidated and clear
4. ✅ Directory structure follows Python best practices
5. ✅ No duplicate or redundant files exist
6. ✅ CI/CD pipeline is functional
7. ✅ Code is properly formatted and linted

## Rollback Plan

If issues arise during migration:
1. Stop the migration process
2. Document the issue encountered
3. Use the backup created in Phase 1
4. Address the issue before retrying

## Timeline

- **Day 1**: Preparation and Core Migration
- **Day 2**: Test and Configuration Migration
- **Day 3**: Import Updates and Documentation
- **Day 4**: Validation and Testing
- **Day 5**: Buffer for issues and final cleanup

## Notes

- Keep the original project intact until migration is validated
- Test thoroughly at each phase before proceeding
- Document any deviations from this plan
- Consider using version control branches for the migration

---

*Migration Plan Created: 2025-09-01*
*Estimated Completion: 5 working days*
*Risk Level: Low (with proper backups)*