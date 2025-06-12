# Setting Up Business Central API Access

This guide will walk you through the process of setting up API access to Business Central in Azure Active Directory (Azure AD) and obtaining the necessary credentials for the exchange rate API.

## Prerequisites

- Access to your organization's Azure portal (portal.azure.com)
- Administrator permissions in Azure AD
- Access to Business Central

## Step 1: Register an Application in Azure AD

1. Sign in to the [Azure portal](https://portal.azure.com).
2. Navigate to **Azure Active Directory** > **App registrations**.
3. Click **+ New registration**.
4. Enter a name for your application (e.g., "Business Central API Client").
5. Under **Supported account types**, select **Accounts in this organizational directory only**.
6. Leave the **Redirect URI** blank (not needed for client credentials flow).
7. Click **Register**.

## Step 2: Configure API Permissions

1. In your newly registered app, navigate to **API permissions**.
2. Click **+ Add a permission**.
3. Select **Dynamics 365 Business Central** (if not visible, search for it).
4. Select **Application permissions**.
5. Check the permissions you need:
   - `Financials.ReadWrite.All` (for full access)
   - `Financials.Read.All` (for read-only access)
6. Click **Add permissions**.
7. Click **Grant admin consent for [Your Organization]** and confirm.

## Step 3: Create a Client Secret

1. In your app registration, navigate to **Certificates & secrets**.
2. Under **Client secrets**, click **+ New client secret**.
3. Enter a description (e.g., "API Access") and select an expiration period.
4. Click **Add**.
5. **IMPORTANT**: Copy the **Value** of the secret immediately. You won't be able to see it again after you leave this page.

## Step 4: Get the Required Information

Collect the following information:

1. **Tenant ID**: Found in Azure AD > Properties > Directory ID
2. **Client ID**: Found in your app registration's Overview page (Application ID)
3. **Client Secret**: The value you copied in Step 3

## Step 5: Update Your .env File

1. Copy the `.env.example` file to create a new `.env` file:
   ```bash
   cp .env.example .env
   ```

2. Open the `.env` file in your editor and update it with your collected information:
   ```
   BC_TENANT_ID=your_tenant_id
   BC_CLIENT_ID=your_client_id
   BC_CLIENT_SECRET=your_client_secret
   BC_COMPANY=VCJ
   BC_SCOPE=https://api.businesscentral.dynamics.com/.default
   BC_VERIFY_SSL=True
   ```

   **IMPORTANT**: Do not use quotes around the values in the `.env` file. For example:
   - Correct: `BC_CLIENT_ID=5d0ad744-0ae3-4712-b057-2cac7afb52f8`
   - Incorrect: `BC_CLIENT_ID="5d0ad744-0ae3-4712-b057-2cac7afb52f8"`
   
   Using quotes can cause the values to be parsed incorrectly, especially if they contain hyphens or other special characters.

3. Save the file. This `.env` file will be used by all the scripts in this project, including:
   - `debug_oauth_token.py` - For debugging API access
   - `exchange_rate_api.py` - For retrieving exchange rates
   - `demo_exchange_rate_api.py` - For demonstrating the API

## Step 6: Test Your Configuration

Run the debug script to test your configuration:

```bash
python debug_oauth_token.py
```

This script will:
1. Load environment variables from the `.env` file in the current directory
2. Attempt to acquire a token using your credentials
3. If successful, test access to the Business Central API
4. Provide detailed error information and guidance if anything goes wrong
5. Save a log file with detailed debugging information

The script will output whether token acquisition and API access were successful, and provide guidance for fixing any issues.

## Common Issues and Solutions

### "unauthorized_client" Error

This typically means the application is not registered in your Azure AD tenant or the client ID is incorrect.

**Solution**: Double-check your client ID and ensure the application is registered in the correct Azure AD tenant.

### "invalid_client" Error

This usually means the client secret is incorrect or has expired.

**Solution**: Generate a new client secret in Azure AD and update your .env file.

### "invalid_scope" Error

This means the requested scope is not valid.

**Solution**: Ensure the scope is set to `https://api.businesscentral.dynamics.com/.default`.

### "insufficient_permissions" Error

This means the application doesn't have the necessary permissions to access Business Central.

**Solution**: Ensure you've granted the appropriate permissions in Azure AD and that admin consent has been provided.

### "company_not_found" Error

This means the specified company doesn't exist in your Business Central environment.

**Solution**: Check the company name in your .env file and ensure it matches a company in your Business Central environment.

## Additional Resources

- [Business Central API Documentation](https://docs.microsoft.com/en-us/dynamics365/business-central/dev-itpro/api-reference/v2.0/)
- [Azure AD Application Registration](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [OAuth 2.0 Client Credentials Flow](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow)
