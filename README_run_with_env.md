# Running Japan Exports with Environment Variables

This guide explains how to use the `run_with_env.sh` script to process Japan exports with the required environment variables.

## Background

The `process_japan_exports.py` script requires certain environment variables to be set, particularly:

- `ERP_CLIENT_ID`
- `ERP_CLIENT_SECRET`

These variables are used for authentication with the Business Central API.

## Using the Script

The `run_with_env.sh` script automatically loads environment variables from the `.env` file and then runs the `process_japan_exports.py` script.

### Prerequisites

1. Make sure you have a `.env` file in the project root directory with the required environment variables.
2. Ensure the script has execute permissions: `chmod +x run_with_env.sh`

### Running the Script

```bash
./run_with_env.sh <input_json_file>
```

For example:

```bash
./run_with_env.sh examples/0604-Raku\ export-\ VCT\ credit\ card\ 1.utf8.json
```

### What the Script Does

1. Loads environment variables from the `.env` file
2. Checks if the required environment variables (`ERP_CLIENT_ID` and `ERP_CLIENT_SECRET`) are set
3. Runs the `process_japan_exports.py` script with the provided arguments

## Troubleshooting

If you encounter errors:

1. **Missing .env file**: Make sure the `.env` file exists in the project root directory.
2. **Missing environment variables**: Check that `ERP_CLIENT_ID` and `ERP_CLIENT_SECRET` are properly set in the `.env` file.
3. **Permission denied**: Make sure the script has execute permissions with `chmod +x run_with_env.sh`.

## Example .env File

```
# Business Central API Configuration
BC_TENANT_ID=6b83c27c-aa6d-475a-9933-5c34bb008d73
BC_CLIENT_ID=your-client-id
BC_CLIENT_SECRET=your-client-secret
BC_SCOPE=https://api.businesscentral.dynamics.com/.default
BC_VERIFY_SSL=True
BC_COMPANY=VCJ

# ERP API Configuration
ERP_CLIENT_ID=your-client-id
ERP_CLIENT_SECRET=your-client-secret
ERP_TOKEN_URL=https://login.microsoftonline.com/6b83c27c-aa6d-475a-9933-5c34bb008d73/oauth2/v2.0/token
ERP_API_URL_BASE=https://api.businesscentral.dynamics.com/v2.0/6b83c27c-aa6d-475a-9933-5c34bb008d73/Staging/ODataV4/Company
ERP_API_ENDPOINT=PurchaseJournals
ERP_SCOPE=https://api.businesscentral.dynamics.com/.default
ERP_VERIFY_SSL=True
```

Replace `your-client-id` and `your-client-secret` with your actual credentials.
