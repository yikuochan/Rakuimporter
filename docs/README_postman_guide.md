# Using Postman to Verify OAuth Token Acquisition

This guide explains how to use Postman to verify that you can acquire an OAuth token from Microsoft Azure AD for the VicOne app integration with Business Central API.

## Prerequisites

1. [Postman](https://www.postman.com/downloads/) installed on your computer
2. VicOne app credentials:
   - Client ID: 5d0ad744-0ae3-4712-b057-2cac7afb52f8
   - Client Secret: (Your secret)
   - Tenant ID: 6b83c27c-aa6d-475a-9933-5c34bb008d73

## Step 1: Import the Collection

1. Open Postman
2. Click on "Import" in the top left corner
3. Select the `VicOne_OAuth_Token_Collection.postman_collection.json` file
4. Click "Import"

## Step 2: Configure the Collection

1. Replace `YOUR_CLIENT_SECRET_HERE` with your actual client secret in the "Get OAuth Token" request:
   - Click on the "Get OAuth Token" request
   - Go to the "Body" tab
   - Find the "client_secret" key-value pair
   - Replace `YOUR_CLIENT_SECRET_HERE` with your actual client secret

2. Create a Postman Environment (optional but recommended):
   - Click on the "Environments" tab in the left sidebar
   - Click "Create Environment"
   - Name it "VicOne Business Central"
   - Add a variable named "access_token" (leave the value empty)
   - Click "Save"

## Step 3: Get an OAuth Token

1. Select the "Get OAuth Token" request
2. Click "Send"
3. If successful, you should receive a response with:
   - Status code: 200 OK
   - JSON body containing:
     - `access_token`: The OAuth token
     - `token_type`: "Bearer"
     - `expires_in`: Token expiration time in seconds
     - Other fields

4. The test script will automatically save the access token to the environment variable if you're using the environment.

## Step 4: Test the Token with an API Request

1. Update the "Test Business Central API" request:
   - Replace `YOUR_COMPANY` in the URL with your actual company name or ID

2. Select the "Test Business Central API" request
3. Click "Send"
4. If successful, you should receive a response with:
   - Status code: 200 OK
   - JSON body containing company data

## Troubleshooting

### SSL Certificate Issues

If you encounter SSL certificate validation issues:

1. Click on "Settings" (gear icon) in the top right
2. Go to "General" tab
3. Scroll down to "SSL Certificate Verification"
4. Turn it OFF (Note: This is not recommended for production environments)
5. Try the request again

### Authentication Errors

If you receive a 401 Unauthorized error:

1. Verify your client ID and client secret are correct
2. Check that the tenant ID in the URL is correct
3. Ensure the scope is correct for your application

### Other Issues

If you encounter other issues:

1. Check the response body for error details
2. Verify network connectivity
3. Ensure your Azure AD application has the necessary permissions

## Related Resources

- [OAuth Token Helper Script](./oauth_token_helper.py): Python script for token acquisition
- [Test OAuth Token Script](./test_oauth_token.py): Script to test token acquisition and API access
- [GitHub Issue #16](https://github.com/yikuochan/Rakuimporter/issues/16): Related issue tracking this problem
