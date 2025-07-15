---
title: Technical Context and Implementation Details
version: 1.0
created: 2025-01-14
last_updated: 2025-01-14
---

# Technical Context

## Technology Stack

### Core Technologies
- **Python 3.8+**: Primary development language
- **Microsoft Dynamics 365 Business Central**: Target ERP system
- **OAuth 2.0**: Authentication protocol for API access
- **REST APIs**: Integration protocol with Business Central
- **CSV/JSON**: Data formats for input and intermediate processing

### Key Python Libraries
- **chardet**: Character encoding detection for Japanese text
- **requests**: HTTP client for API calls
- **csv**: CSV file processing
- **json**: JSON data manipulation
- **logging**: Comprehensive logging framework
- **os/dotenv**: Environment variable management
- **datetime**: Date/time handling for exchange rates

### Development Tools
- **Git**: Version control (GitHub repository)
- **pip**: Package management
- **virtualenv**: Environment isolation
- **setuptools**: Package distribution

## Environment Configuration

### Development Environment
```bash
# Virtual environment setup
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Package installation
pip install -r requirements.txt
pip install -e .  # Development mode
```

### Environment Variables (.env)
```bash
# Business Central Configuration
ERP_CLIENT_ID=your_client_id
ERP_CLIENT_SECRET=your_client_secret
ERP_TOKEN_URL=https://login.microsoftonline.com/tenant_id/oauth2/v2.0/token
ERP_API_URL_BASE=https://api.businesscentral.dynamics.com/v2.0/tenant_id/Production/ODataV4/Company
ERP_SCOPE=https://api.businesscentral.dynamics.com/.default
BC_ENVIRONMENT=Production

# Optional Configuration
BALANCE_TOLERANCE=0.01
RATE_LIMIT_BASE_DELAY=5.0
MAX_RETRIES=3
```

### Production Configuration
- **Environment**: Production Business Central tenant
- **SSL Verification**: Should be enabled (`verify=True`)
- **Logging Level**: INFO or WARNING
- **Error Reporting**: File-based logging with rotation

## File Structure and Dependencies

### Core Module Dependencies
```
core/
├── __init__.py
├── charset_converter.py      # chardet, logging
├── csv_to_json_converter.py  # csv, json, logging
├── currency_converter.py     # requests, logging
├── exchange_rate_api.py      # requests, datetime, logging
├── process_japan_exports.py  # requests, json, logging, time
└── vct_responsibility_consolidation.py  # logging
```

### Utility Module Dependencies
```
utils/
├── __init__.py
├── config.py                 # os, logging
├── env_config.py            # os, dotenv
├── oauth_token_helper.py    # requests, logging
└── company_currency_mapping.py  # (no external deps)
```

### Data Flow Dependencies
```
Input: CSV (Shift-JIS/EUC-JP) 
  ↓ [chardet]
UTF-8 CSV 
  ↓ [csv module]
JSON Structure 
  ↓ [requests + OAuth]
Business Central API
```

## API Integration Details

### Business Central API Endpoints
```python
# Base URL Pattern
base_url = f"https://api.businesscentral.dynamics.com/v2.0/{tenant_id}/{environment}/ODataV4"

# Specific Endpoints
journal_lines = f"{base_url}/Company('{company_name}')/generalJournalLines"
exchange_rates = f"{base_url}/Company('{company_name}')/currencyExchangeRates"
```

### Authentication Flow
```python
# OAuth 2.0 Client Credentials
token_request = {
    'grant_type': 'client_credentials',
    'client_id': ERP_CLIENT_ID,
    'client_secret': ERP_CLIENT_SECRET,
    'scope': ERP_SCOPE
}

# Token Usage
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}
```

### Rate Limiting Implementation
```python
class RateLimiter:
    def __init__(self, base_delay=5.0, max_delay=10.0, backoff_factor=2.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.consecutive_failures = 0
        self.last_request_time = 0
    
    def wait_before_request(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if self.consecutive_failures > 0:
            delay = min(
                self.base_delay * (self.backoff_factor ** (self.consecutive_failures - 1)),
                self.max_delay
            )
        else:
            delay = self.base_delay
        
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
```

## Character Encoding Handling

### Japanese Encoding Detection
```python
def detect_encoding(file_path, japanese_optimized=True):
    """
    Detect character encoding with Japanese optimization
    """
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    
    # Primary detection
    result = chardet.detect(raw_data)
    
    if japanese_optimized and result['confidence'] < 0.7:
        # Try common Japanese encodings
        japanese_encodings = ['shift_jis', 'euc-jp', 'iso-2022-jp']
        for encoding in japanese_encodings:
            try:
                raw_data.decode(encoding)
                return {'encoding': encoding, 'confidence': 0.8}
            except UnicodeDecodeError:
                continue
    
    return result
```

### Conversion Validation
```python
def validate_conversion(original_path, converted_path, source_encoding):
    """
    Validate encoding conversion quality
    """
    with open(converted_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Count problematic characters
    replacement_chars = content.count('�')
    total_chars = len(content)
    
    if total_chars == 0:
        return False, "Empty file after conversion"
    
    problem_percentage = (replacement_chars / total_chars) * 100
    
    if problem_percentage > 10:
        return False, f"High replacement character rate: {problem_percentage:.2f}%"
    
    return True, "Conversion successful"
```

## Data Processing Algorithms

### CSV to JSON Transformation
```python
def process_csv_row(row, headers):
    """
    Transform CSV row to JSON structure
    """
    entry = {
        'voucher_no': row.get('伝票No.', ''),
        'transaction_date': row.get('仕訳日', ''),
        'debit': {
            'gl_account': row.get('借方G/L Account', ''),
            'account': determine_account(row, 'debit'),
            'amount': float(row.get('借方換算前額', 0)),
            'currency': normalize_currency(row.get('借方単位', ''))
        },
        'credit': {
            'gl_account': row.get('貸方G/L Account', ''),
            'account': determine_account(row, 'credit'),
            'amount': float(row.get('貸方換算前額', 0)),
            'currency': normalize_currency(row.get('貸方単位', ''))
        }
    }
    return entry
```

### Currency Normalization
```python
def normalize_currency(currency_text):
    """
    Normalize Japanese currency names to standard codes
    """
    currency_mapping = {
        '台湾ドル': 'NTD',
        '円': 'JPY',
        'ドル': 'USD',
        'ユーロ': 'EUR'
    }
    return currency_mapping.get(currency_text, currency_text)
```

### Consolidation Algorithm
```python
def create_consolidated_vct_responsibility_entries(voucher_entries, document_counter):
    """
    Consolidate V-VC00048 entries per voucher
    """
    consolidated_entries = []
    
    # Create individual debit entries
    for entry in voucher_entries:
        debit_entry = create_debit_journal_line(entry, document_counter)
        consolidated_entries.append(debit_entry)
    
    # Create single consolidated credit entry
    total_amount = sum(entry['debit']['amount'] for entry in voucher_entries)
    credit_entry = create_consolidated_credit_line(voucher_entries[0], total_amount, document_counter)
    consolidated_entries.append(credit_entry)
    
    return consolidated_entries
```

## Error Handling and Logging

### Logging Configuration
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s',
    handlers=[
        logging.FileHandler('erp_api_integration.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Error Classification
```python
def handle_api_error(response, entry_data):
    """
    Classify and handle API errors
    """
    if response.status_code == 429:
        # Rate limiting - increase delay
        return 'rate_limit', 'Too many requests'
    elif 400 <= response.status_code < 500:
        # Client error - data issue
        return 'client_error', f"Data validation error: {response.text}"
    elif 500 <= response.status_code < 600:
        # Server error - retry
        return 'server_error', f"Server error: {response.text}"
    else:
        return 'unknown_error', f"Unexpected status: {response.status_code}"
```

## Performance Considerations

### Memory Management
- **Streaming Processing**: Process CSV files line by line for large files
- **Rate Caching**: Cache exchange rates to reduce API calls
- **Connection Pooling**: Reuse HTTP connections for API calls

### Processing Optimization
- **Batch Processing**: Group related entries for consolidation
- **Parallel Processing**: Could be implemented for independent vouchers
- **Early Validation**: Validate data before API calls to avoid unnecessary requests

### Monitoring Points
- **Processing Time**: Track time per file and per entry
- **API Response Times**: Monitor Business Central API performance
- **Error Rates**: Track success/failure ratios
- **Memory Usage**: Monitor for large file processing

## Security Considerations

### Credential Management
- **Environment Variables**: Store sensitive data in .env files
- **No Hardcoding**: Never commit credentials to version control
- **Scope Limitation**: Use minimal required OAuth scopes

### Data Security
- **Temporary Files**: Clean up intermediate files after processing
- **Logging**: Avoid logging sensitive data (amounts, account numbers)
- **SSL/TLS**: Enable certificate verification in production

### Access Control
- **Environment Separation**: Separate dev/staging/production configurations
- **Audit Trail**: Complete logging of all operations
- **Error Reporting**: Detailed error logs for troubleshooting

## Deployment Requirements

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: Minimum 512MB RAM
- **Storage**: 1GB for logs and temporary files
- **Network**: HTTPS access to Business Central API

### Installation Process
```bash
# Clone repository
git clone https://github.com/your-org/power-importer.git
cd power-importer

# Setup environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with actual values

# Verify installation
power-importer --help
```

### Maintenance Tasks
- **Log Rotation**: Implement log file rotation to prevent disk space issues
- **Token Refresh**: Monitor OAuth token expiration
- **Rate Limit Monitoring**: Adjust rate limiting based on API performance
- **Error Report Review**: Regular review of error logs and reports
