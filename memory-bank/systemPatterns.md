---
title: System Architecture and Design Patterns
version: 1.0
created: 2025-01-14
last_updated: 2025-01-14
---

# System Patterns and Architecture

## High-Level Architecture

### Data Processing Pipeline
```
CSV Files (Japanese Encoding) 
    ↓ [charset_converter.py]
UTF-8 CSV Files 
    ↓ [csv_to_json_converter.py]
Structured JSON 
    ↓ [process_japan_exports.py]
Business Central Journal Entries
```

### Component Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Layer    │    │  Processing      │    │  Integration    │
│                 │    │  Layer           │    │  Layer          │
│ • CSV Files     │───▶│ • Charset Conv   │───▶│ • OAuth Helper  │
│ • JSON Files    │    │ • CSV-JSON Conv  │    │ • Exchange API  │
│ • Log Files     │    │ • Currency Conv  │    │ • BC API Client │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Core Design Patterns

### 1. Pipeline Pattern
**Implementation**: Sequential data transformation stages
- **Stage 1**: Character encoding normalization
- **Stage 2**: CSV to JSON transformation
- **Stage 3**: ERP integration and posting

**Benefits**: 
- Clear separation of concerns
- Easy to debug and maintain
- Allows for intermediate file inspection

### 2. Strategy Pattern
**Implementation**: Currency conversion strategies
- **Direct Conversion**: Home currency to foreign currency
- **Cross-Currency**: Foreign to foreign via home currency
- **Overseas Vendor**: Special handling for V-VC prefixed vendors

**Code Location**: `core/exchange_rate_api.py`

### 3. Factory Pattern
**Implementation**: Journal line creation
- **Debit Line Factory**: Creates debit journal entries
- **Credit Line Factory**: Creates credit journal entries
- **Consolidated Factory**: Creates consolidated entries for VCT responsibility

**Code Location**: `core/process_japan_exports.py`

### 4. Observer Pattern
**Implementation**: Logging and reporting
- **Progress Observer**: Tracks processing progress
- **Error Observer**: Captures and reports errors
- **Balance Observer**: Monitors debit/credit balance

### 5. Retry Pattern with Exponential Backoff
**Implementation**: API call resilience
```python
class RateLimiter:
    def __init__(self, base_delay=5.0, max_delay=10.0, backoff_factor=2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.consecutive_failures = 0
```

## Key Components and Relationships

### Core Processing Components

#### 1. Character Set Converter
**Purpose**: Encoding detection and conversion
**Pattern**: Template Method Pattern
**Key Methods**:
- `detect_encoding()`: Uses chardet with confidence scoring
- `convert_to_utf8()`: Handles conversion with validation
- `validate_conversion()`: Checks for encoding artifacts

#### 2. CSV to JSON Converter
**Purpose**: Data structure transformation
**Pattern**: Builder Pattern
**Key Features**:
- Two-line header processing
- Debit/credit pairing logic
- Currency normalization
- Entry consolidation

#### 3. Process Japan Exports
**Purpose**: ERP integration orchestrator
**Pattern**: Facade Pattern
**Responsibilities**:
- Journal line creation
- API authentication management
- Rate limiting enforcement
- Error handling and reporting

### Supporting Components

#### 4. OAuth Token Helper
**Purpose**: Authentication management
**Pattern**: Singleton Pattern (token caching)
**Features**:
- Token acquisition and refresh
- SSL verification handling
- Authorization header generation

#### 5. Exchange Rate API
**Purpose**: Currency conversion service
**Pattern**: Adapter Pattern (wraps BC API)
**Features**:
- Rate caching mechanism
- Cross-currency calculations
- Company-specific rate handling

#### 6. Company Currency Mapping
**Purpose**: Business rule configuration
**Pattern**: Configuration Pattern
**Data**:
- Company to home currency mappings
- Currency code normalization rules
- Overseas vendor identification

## Data Flow Patterns

### 1. Consolidation Pattern
**Use Case**: VCT Responsibility Entries
**Logic**:
```
Voucher APA-0000552 with 4 V-VC00048 entries:
├── Individual Debit 1 (500.0, VCA, APA-0000552-1)
├── Individual Debit 2 (500.0, VCA, APA-0000552-1)  
├── Individual Debit 3 (566.94, VCA, APA-0000552-1)
├── Individual Debit 4 (225.0, VCA, APA-0000552-1)
└── Consolidated Credit (-1791.94, VCT, APA-0000552-1)
```

### 2. Balance Verification Pattern
**Implementation**: Pre-posting validation
```python
def verify_balanced_amounts(entries, tolerance=0.01):
    for voucher_group in group_by_voucher(entries):
        debit_total = sum(entry.amount for entry in voucher_group if entry.amount > 0)
        credit_total = sum(entry.amount for entry in voucher_group if entry.amount < 0)
        if abs(debit_total + credit_total) > tolerance:
            report_unbalanced(voucher_group)
```

### 3. Error Recovery Pattern
**Implementation**: Multi-level error handling
- **Level 1**: Individual entry errors (log and continue)
- **Level 2**: API errors (retry with backoff)
- **Level 3**: System errors (fail fast with detailed logging)

## Configuration Patterns

### Environment-Based Configuration
**Pattern**: Strategy Pattern for environment switching
```python
environment = get_env_var("BC_ENVIRONMENT", default="Production")
base_url = f"https://api.businesscentral.dynamics.com/v2.0/{tenant_id}/{environment}/ODataV4"
```

### Centralized Configuration
**File**: `utils/config.py`
**Pattern**: Configuration Object Pattern
**Features**:
- Environment variable loading
- Default value management
- Type conversion support

## Performance Patterns

### 1. Rate Limiting Pattern
**Implementation**: Token bucket algorithm
**Configuration**:
- Base delay: 5 seconds between calls
- Max delay: 10 seconds for failures
- Exponential backoff: 2x multiplier

### 2. Caching Pattern
**Implementation**: In-memory caching for exchange rates
**Strategy**: Cache by (company, currency, date) key
**Benefits**: Reduces API calls by ~80%

### 3. Batch Processing Pattern
**Implementation**: Consolidation reduces API calls
**Example**: 8 individual entries → 5 consolidated entries (37.5% reduction)

## Error Handling Patterns

### 1. Circuit Breaker Pattern
**Implementation**: API failure detection
**Thresholds**:
- 3 consecutive failures trigger circuit open
- 30-second timeout before retry
- Exponential backoff on repeated failures

### 2. Compensation Pattern
**Implementation**: Rollback on critical failures
**Use Cases**:
- Unbalanced entries (generate report, allow override)
- Encoding failures (try alternative encodings)
- API failures (retry with different parameters)

## Security Patterns

### 1. Credential Management Pattern
**Implementation**: Environment variable isolation
**Files**: `.env` (local), environment variables (production)
**Scope**: OAuth client credentials, API endpoints

### 2. SSL Verification Pattern
**Current**: Disabled for development (`verify=False`)
**Production**: Should enable SSL verification (`verify=True`)
**Pattern**: Environment-based security configuration

## Testing Patterns

### 1. Test Data Pattern
**Location**: `examples/` directory
**Format**: Real CSV files with Japanese encoding
**Coverage**: Various scenarios (VCA, VCP, VCT companies)

### 2. Verification Pattern
**Implementation**: Automated test scripts
**Examples**:
- `test_production_config.py`: Environment verification
- `test_vct_consolidation.py`: Consolidation logic testing
- `test_external_doc_no_uniqueness.py`: Document numbering testing

## Deployment Patterns

### 1. Migration Pattern
**Scripts**: `migrate.sh` (Unix), `migrate.bat` (Windows)
**Purpose**: Project structure updates
**Pattern**: Automated refactoring with backup

### 2. Package Pattern
**File**: `setup.py`
**Installation**: `pip install -e .`
**Command**: `power-importer` CLI tool
**Pattern**: Standard Python package distribution
