# Client Secret Issue and Fix

## Issue Summary

When running the currency converter tests, we encountered authentication errors with the Business Central API:

```
Failed to acquire token. Status code: 401
Response: {"error":"invalid_client","error_description":"AADSTS7000215: Invalid client secret provided. Ensure the secret being sent in the request is the client secret value, not the client secret ID, for a secret added to app '5d0ad744-0ae3-4712-b057-2cac7afb52f8'.
```

This error indicates that the client secret being used is invalid or in the wrong format.

## Root Cause Analysis

After debugging, we found that:

1. The client secret in the `.env` file (`maskerted`) is being correctly loaded by the application.
2. However, the API is rejecting this client secret with error code `AADSTS7000215`.
3. The error message suggests that we might be using a "client secret ID" instead of the actual "client secret value".

This is a common issue with Azure AD authentication. When you create a new client secret in the Azure portal, you need to copy the actual secret value immediately, as it's only shown once. If you copy the wrong value or the secret ID instead of the secret value, authentication will fail.

## Solution

We've created two utility scripts to help update the client secret in the `.env` file:

1. **Interactive Script**: `update_client_secret.py`
   - Prompts you to enter the new client secret
   - Updates both `BC_CLIENT_SECRET` and `ERP_CLIENT_SECRET` in the `.env` file
   - Creates a backup of the original `.env` file as `.env.backup`

2. **Direct Script**: `update_client_secret_direct.py`
   - Takes the new client secret as a command-line argument
   - Updates both `BC_CLIENT_SECRET` and `ERP_CLIENT_SECRET` in the `.env` file
   - Creates a backup of the original `.env` file as `.env.backup`

## How to Fix the Issue

### Option 1: Using the Interactive Script

1. Run the interactive script:
   ```bash
   python update_client_secret.py
   ```

2. When prompted, enter the new client secret value.

3. The script will update the `.env` file and create a backup of the original.

### Option 2: Using the Direct Script

1. Run the direct script with the new client secret as an argument:
   ```bash
   python update_client_secret_direct.py "your-new-client-secret-here"
   ```

2. The script will update the `.env` file and create a backup of the original.

### After Updating the Client Secret

1. Restart any running applications to pick up the new client secret.

2. Verify that the authentication works by running the debug script:
   ```bash
   python debug_client_secret.py
   ```

3. If successful, you should see "Token acquired successfully!" in the output.

## Getting a New Client Secret

If you need to generate a new client secret:

1. Go to the Azure portal (https://portal.azure.com)
2. Navigate to Azure Active Directory > App registrations
3. Find and select your app (ID: 5d0ad744-0ae3-4712-b057-2cac7afb52f8)
4. Go to "Certificates & secrets"
5. Click "New client secret"
6. Add a description and select an expiration period
7. Click "Add"
8. **Important**: Copy the "Value" (not the "Secret ID") immediately, as it will only be shown once

## Troubleshooting

If you continue to experience authentication issues after updating the client secret:

1. Verify that the client ID is correct (5d0ad744-0ae3-4712-b057-2cac7afb52f8)
2. Ensure that the tenant ID is correct (6b83c27c-aa6d-475a-9933-5c34bb008d73)
3. Check that the scope is correct (https://api.businesscentral.dynamics.com/.default)
4. Verify that the app has the necessary API permissions in Azure AD
5. Check if the client secret has expired and needs to be renewed

## Additional Notes

- The client secret is sensitive information. Do not share it or commit it to version control.
- Consider using a secure secret management solution for production environments.
- Client secrets have expiration dates. Make sure to update them before they expire.
