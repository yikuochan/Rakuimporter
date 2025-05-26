# Using Postman with Business Central API

This guide explains how to use the provided Postman collection to test and interact with the Business Central API, particularly for retrieving exchange rates.

## Prerequisites

- [Postman](https://www.postman.com/downloads/) installed on your computer
- Business Central API credentials (see [README_bc_api_setup.md](README_bc_api_setup.md) for setup instructions)

## Setting Up the Postman Collection

1. **Import the Collection**:
   - Open Postman
   - Click "Import" in the top left corner
   - Select the `Business_Central_API.postman_collection.json` file
   - The collection will appear in your Postman workspace

2. **Import the Environment**:
   - Click "Import" again
   - Select the `Business_Central_API.postman_environment.json` file
   - The environment will be added to your Postman environments

3. **Configure the Environment**:
   - Click the gear icon in the top right corner
   - Click on the "Business Central API" environment
   - Update the following variables:
     - `client_id`: Your application client ID
     - `client_secret`: Your application client secret
     - Optionally update other variables as needed:
       - `tenant_id`: Your Azure AD tenant ID (default is already set)
       - `company_name`: The Business Central company name (default: "VCJ")
       - `currency_code`: Default currency code for testing (default: "USD")
       - `date`: Default date for testing (default: "2025-04-01")
   - Click "Save"
   - Select the environment from the dropdown in the top right corner

## Using the Collection

The collection is organized into folders for different types of API requests:

### Authentication

1. **Get OAuth Token**:
   - This request obtains an OAuth token for accessing the API
   - The token is automatically saved to the environment variables
   - The collection includes a pre-request script that automatically refreshes the token when needed

### Exchange Rates

1. **Get All Exchange Rates**:
   - Retrieves all exchange rates for the specified company
   - Uses the OAuth token for authentication

2. **Get Exchange Rates by Currency**:
   - Retrieves exchange rates for a specific currency
   - Uses the `currency_code` environment variable

3. **Get Exchange Rates by Date**:
   - Retrieves exchange rates effective on or before a specific date
   - Uses the `date` environment variable

4. **Get Exchange Rates by Currency and Date**:
   - Combines the currency and date filters
   - Useful for finding historical rates for a specific currency

5. **Get Latest Exchange Rates by Currency**:
   - Retrieves the most recent exchange rate for a specific currency
   - Uses `$orderby` and `$top` to get only the latest rate

### Companies

1. **Get All Companies**:
   - Lists all companies in your Business Central environment
   - Useful for finding the correct company name to use

2. **Get Company Details**:
   - Retrieves details for a specific company
   - Uses the `company_name` environment variable

### Currencies

1. **Get All Currencies**:
   - Lists all currencies defined in a specific company
   - Useful for finding available currency codes

2. **Get Currency Details**:
   - Retrieves details for a specific currency
   - Uses the `currency_code` environment variable

## Troubleshooting

### Authentication Issues

If you encounter authentication issues:

1. **Check your credentials**:
   - Verify that your `tenant_id`, `client_id`, and `client_secret` are correct
   - Make sure the application has the necessary permissions

2. **Manually get a token**:
   - Run the "Get OAuth Token" request
   - Check the response for error messages
   - If successful, the token will be saved to the environment variables

3. **Check token expiration**:
   - The token expires after a certain period (usually 1 hour)
   - The collection includes a pre-request script that automatically refreshes the token
   - You can manually run the "Get OAuth Token" request to get a new token

### API Request Issues

If your API requests fail:

1. **Check the response status code and body**:
   - 401 Unauthorized: Token is invalid or expired
   - 403 Forbidden: Token doesn't have permission to access the resource
   - 404 Not Found: The requested resource doesn't exist

2. **Check your environment variables**:
   - Make sure `company_name`, `currency_code`, and `date` are set correctly
   - The company name is case-sensitive

3. **Check the request URL and parameters**:
   - Make sure the URL is correctly formatted
   - Check that filter parameters are correctly formatted

## Advanced Usage

### Modifying Requests

You can modify the requests to suit your needs:

1. **Change filter parameters**:
   - Edit the URL query parameters to filter by different fields
   - Use OData filter syntax (e.g., `$filter=Currency_Code eq 'EUR'`)

2. **Add pagination**:
   - Use `$top` and `$skip` to paginate results
   - Example: `$top=10&$skip=10` for the second page of 10 results

3. **Change sorting**:
   - Use `$orderby` to sort results
   - Example: `$orderby=Starting_Date desc` to sort by date descending

### Using the Pre-request Script

The collection includes a pre-request script that automatically refreshes the token when needed. You can modify this script to add additional functionality:

1. **Add logging**:
   - Use `console.log()` to log information during the request
   - Useful for debugging

2. **Add custom headers**:
   - Modify the script to add custom headers to the request
   - Useful for adding tracking or debugging information

3. **Add request validation**:
   - Add code to validate the request parameters before sending
   - Useful for preventing errors

## Using with the Exchange Rate API

The Postman collection is particularly useful for testing and understanding the Business Central API before using it in your code. You can use it to:

1. **Verify API access**:
   - Confirm that your credentials work
   - Check that you have access to the necessary resources

2. **Explore available data**:
   - Find available companies and currencies
   - Understand the structure of exchange rate data

3. **Test API queries**:
   - Try different filter combinations
   - Understand how to retrieve specific exchange rates

4. **Debug API issues**:
   - If your code encounters API errors, use Postman to reproduce and diagnose the issue
   - Compare working Postman requests with your code to identify differences

## Additional Resources

- [Business Central API Documentation](https://docs.microsoft.com/en-us/dynamics365/business-central/dev-itpro/api-reference/v2.0/)
- [OData Query Options](https://docs.microsoft.com/en-us/dynamics365/business-central/dev-itpro/api-reference/v2.0/dynamics-odata-query-options)
- [Postman Documentation](https://learning.postman.com/docs/getting-started/introduction/)
