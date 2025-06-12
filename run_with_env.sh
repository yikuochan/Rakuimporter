#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

# Check if required environment variables are set
if [ -z "$ERP_CLIENT_ID" ]; then
    echo "Error: ERP_CLIENT_ID is not set"
    exit 1
fi

if [ -z "$ERP_CLIENT_SECRET" ]; then
    echo "Error: ERP_CLIENT_SECRET is not set"
    exit 1
fi

# Run the script with the provided arguments
echo "Running process_japan_exports.py with environment variables"
python -m core.process_japan_exports "$@"
