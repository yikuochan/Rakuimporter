# Deployment Guide

This guide provides instructions for deploying and configuring the Power Importer system.

## Prerequisites

- Python 3.8 or higher
- Git
- Access to Business Central API
- Exchange Rate API key (if using currency conversion)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-organization/power-importer.git
cd power-importer
```

### 2. Create a Virtual Environment

```bash
# On Linux/macOS
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the Package in Development Mode

```bash
pip install -e .
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root directory based on the `.env.example` template:

```bash
cp .env.example .env
```

Edit the `.env` file and set the required environment variables:

```
# Business Central API Configuration
BC_TENANT_ID=6b83c27c-aa6d-475a-9933-5c34bb008d73
BC_CLIENT_ID=your-client-id
BC_CLIENT_SECRET=your-client-secret
BC_SCOPE=https://api.businesscentral.dynamics.com/.default
BC_VERIFY_SSL=True
BC_COMPANY=VCJ

# ERP API Configuration
ERP_TOKEN_URL=https://login.microsoftonline.com/6b83c27c-aa6d-475a-9933-5c34bb008d73/oauth2/v2.0/token
ERP_API_URL_BASE=https://api.businesscentral.dynamics.com/v2.0/6b83c27c-aa6d-475a-9933-5c34bb008d73/Staging/ODataV4/Company
ERP_API_ENDPOINT=PurchaseJournals
ERP_SCOPE=https://api.businesscentral.dynamics.com/.default
ERP_VERIFY_SSL=True

# Journal Entry Configuration
JOURNAL_TEMPLATE_NAME=PURCHASES
JOURNAL_BATCH_NAME=PURCHASE
DOCUMENT_TYPE=Invoice

# Exchange Rate Configuration
USE_EXCHANGE_RATE_API=True

# Rate Limiting Configuration
API_BASE_DELAY=5.0
API_MAX_DELAY=10.0
API_BACKOFF_FACTOR=2.0
API_MAX_RETRIES=3

# Balance Tolerance Configuration
BALANCE_TOLERANCE=0.01

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=erp_api_integration.log

# File Processing Configuration
DEFAULT_ENCODING=utf-8
CSV_DELIMITER=,
LINE_BREAK_REPLACEMENT= 
FIX_LINE_BREAKS=true
MAX_DESCRIPTION_LENGTH=100
```

### 2. Business Central API Setup

To set up the Business Central API:

1. Register an application in Azure Active Directory
2. Grant the application appropriate permissions for Business Central
3. Get the tenant ID, client ID, and client secret
4. Update the `.env` file with these values

For detailed instructions, see the [Business Central API Setup Guide](https://docs.microsoft.com/en-us/dynamics365/business-central/dev-itpro/api-reference/v2.0/).

### 3. Exchange Rate API Setup

If you're using currency conversion, you'll need to:

1. Sign up for an Exchange Rate API service
2. Get an API key
3. Update the `.env` file with the API key

## Usage

### Basic Usage

The Power Importer can be run using the `run_importer.py` script:

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

# Generate currency modification report
python run_importer.py "input.csv" --report "currency_report.md"

# Generate unbalanced entries report
python run_importer.py "input.csv" --unbalanced-report "unbalanced_report.md"

# Set balance tolerance
python run_importer.py "input.csv" --balance-tolerance 0.05

# Skip unbalanced entries
python run_importer.py "input.csv" --skip-unbalanced

# Set maximum description length
python run_importer.py "input.csv" --max-desc-length 150

# Disable fixing line breaks
python run_importer.py "input.csv" --no-fix-line-breaks

# Set line break replacement character
python run_importer.py "input.csv" --line-break-replacement "_"
```

### Using as a Package

If you've installed the Power Importer as a package, you can use the `power-importer` command:

```bash
# Show help
power-importer --help

# Basic usage
power-importer "input.csv"
```

## Troubleshooting

### Common Issues

#### Authentication Errors

If you encounter authentication errors:

1. Check that your tenant ID, client ID, and client secret are correct
2. Verify that the application has the appropriate permissions
3. Check that the scope is correct

#### Rate Limiting

If you encounter rate limiting issues:

1. Reduce the number of requests per minute
2. Increase the retry delay
3. Implement exponential backoff

#### File Encoding Issues

If you encounter file encoding issues:

1. Check the encoding of the input file
2. Use the `charset_converter.py` script to convert the file to UTF-8
3. Verify that the output file is correctly encoded

### Logging

The Power Importer logs information to the console and optionally to a file. To enable file logging, set the `LOG_FILE` environment variable in the `.env` file.

To change the log level, set the `LOG_LEVEL` environment variable to one of:

- `DEBUG`: Detailed debugging information
- `INFO`: General information
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

## Maintenance

### Updating Dependencies

To update dependencies:

```bash
pip install --upgrade -r requirements.txt
```

### Backup and Recovery

It's recommended to back up your configuration files and data regularly. The most important files to back up are:

- `.env` file
- Custom scripts and modifications
- Input and output data files

## Security Considerations

### API Credentials

- Store API credentials securely in the `.env` file
- Do not commit the `.env` file to version control
- Rotate API keys and secrets regularly

### Data Protection

- Encrypt sensitive data at rest
- Use HTTPS for all API communications
- Implement proper access controls for data files

## Support and Resources

For additional support and resources:

- Check the documentation in the `docs/` directory
- Contact the development team
- Submit issues to the project's issue tracker
