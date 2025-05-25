# Introduction

This document outlines the design for a system that processes CSV files, with a particular focus on those originating from Japanese sources. The primary purpose of this project is to convert these CSV files into a structured JSON format. This structured data will then be integrated with a Microsoft Dynamics Business Central ERP system.

The core technologies leveraged in this project include Python for data processing and transformation, and Microsoft Dynamics Business Central for the ERP integration.

# System Architecture

This section describes the components and their interactions within the CSV processing and ERP integration system.

## High-Level Diagram

```
Incoming CSV files --> [charset_converter.py] --UTF-8 CSV--> [csv_to_json_converter.py] --JSON--> [process_japan_exports.py] --Authenticated API Calls--> [ERP System (Microsoft Dynamics BC)]
                                                                                                        ^
                                                                                                        |
                                                                                              [oauth_token_helper.py] --OAuth Token-->
```

## Component Descriptions

*   **`charset_converter.py`**:
    *   **Responsibility**: Detects the character encoding of input CSV files. Converts the files from their original encoding to UTF-8 to ensure compatibility and prevent data corruption during subsequent processing steps. This is especially crucial for handling Japanese characters.

*   **`csv_to_json_converter.py`**:
    *   **Responsibility**: Takes the UTF-8 encoded CSV files as input and converts them into a structured JSON format. This script handles the mapping of CSV columns to JSON fields according to predefined or dynamically determined rules.

*   **`process_japan_exports.py`**:
    *   **Responsibility**: This is the main orchestration script. It likely utilizes `charset_converter.py` and `csv_to_json_converter.py` to process the CSV files. It then takes the generated JSON data, performs any necessary business logic transformations, and prepares it for integration with the ERP system. It will use `oauth_token_helper.py` to authenticate before sending data to the ERP.

*   **`oauth_token_helper.py`**:
    *   **Responsibility**: Manages the acquisition and refreshing of OAuth tokens required for authenticating API calls to the Microsoft Dynamics Business Central ERP system. This ensures secure communication.

*   **ERP System (Microsoft Dynamics Business Central)**:
    *   **Responsibility**: The target enterprise resource planning system. It receives the processed and structured JSON data from `process_japan_exports.py`. This data is then used to create or update records within the ERP (e.g., journal entries, sales orders).

## High-Level Data Flow Summary

1.  **CSV Input**: Raw CSV files, potentially with various character encodings (including Japanese-specific ones like Shift-JIS), are received by the system.
2.  **Character Set Conversion**: `charset_converter.py` processes these files, detects their encoding, and converts them to UTF-8.
3.  **JSON Transformation**: The UTF-8 CSV files are then fed into `csv_to_json_converter.py`, which transforms the tabular data into a structured JSON output.
4.  **Orchestration and Business Logic**: `process_japan_exports.py` takes the JSON data. It may apply further transformations, validations, or business-specific logic.
5.  **Authentication**: Before communicating with the ERP, `process_japan_exports.py` (or a module it uses) calls `oauth_token_helper.py` to obtain a valid OAuth token.
6.  **ERP Integration**: Armed with the OAuth token, `process_japan_exports.py` sends the processed JSON data to the Microsoft Dynamics Business Central ERP system via its APIs.
7.  **Data Storage/Update**: The ERP system receives the data and updates its records accordingly.

# Detailed Data Flow

This section provides a more granular step-by-step explanation of the data transformation and integration process.

**Step 1: Input CSV File**

*   The process begins with an input CSV file. These files, especially those from Japanese systems, may use various character encodings such as Shift-JIS, EUC-JP, or others. Incorrectly handling these encodings can lead to garbled text (mojibake) or data loss.
*   The CSV files are expected to contain financial transaction data.

**Step 2: Character Set Conversion (`charset_converter.py`)**

*   **Role**: To ensure data integrity and compatibility across all processing stages, the `charset_converter.py` script is employed.
*   **Detection**: This script utilizes a library like `chardet` to automatically detect the character encoding of the input CSV file.
*   **Conversion**: Once the encoding is detected (e.g., Shift-JIS), the script converts the file content to UTF-8. UTF-8 is a universal character encoding that can represent characters from virtually all languages, including Japanese.
*   **Output**: A new CSV file encoded in UTF-8.

**Step 3: CSV to JSON Conversion (`csv_to_json_converter.py`)**

*   **Input**: The UTF-8 encoded CSV file from the previous step.
*   **CSV Structure**:
    *   **Two-Line Header**: The script is designed to handle CSV files with a specific two-line header structure. The first line typically contains general column names (e.g., "Transaction Date", "Account", "Details", "Debit", "Credit"), and the second line might contain more specific Japanese headers or sub-categories. The script needs to correctly interpret these lines to map data accurately.
    *   **Debit/Credit Pairs**: A key feature is the handling of debit and credit amounts, which might be in separate columns or a single column with indicators. The script transforms these into a structured format suitable for accounting entries.
*   **JSON Output Format**: The script converts the CSV data into a structured JSON array. Each object in the array typically represents a single transaction or a line item from the CSV. An example structure might be:
    ```json
    [
      {
        "transaction_date": "YYYY-MM-DD",
        "account_code": "ACC123",
        "account_name": "勘定科目名", // Account Name in Japanese
        "description": "取引内容詳細", // Transaction details
        "currency": "JPY",
        "amount": 10000, // Normalized amount
        "transaction_type": "debit" // or "credit"
        // ... other relevant fields
      }
    ]
    ```
*   **Key Data Transformations**:
    *   **Currency Normalization**: Values like "¥10,000" or "10000 JPY" are normalized to a standard numerical format (e.g., `10000`) and the currency code (e.g., "JPY") is stored in a separate field. This often involves removing currency symbols and commas.
    *   **Field Mapping**: The script maps columns from the CSV (identified by header names) to predefined fields in the JSON structure. This mapping logic needs to be robust to handle variations in CSV column ordering or naming if possible, or clearly defined if a strict format is expected.
    *   **Description Truncation**: If descriptions or text fields from the CSV exceed length limits imposed by the target ERP system, the script truncates them to a specified maximum length (e.g., 50 characters for a journal entry description), ensuring that data fits without causing errors during ERP posting.

**Step 4: ERP Integration (`process_japan_exports.py`)**

*   **Input**: The structured JSON file generated by `csv_to_json_converter.py`.
*   **JSON Reading**: The script parses the JSON data, iterating through each transaction object.
*   **Authentication**:
    *   It utilizes `oauth_token_helper.py` to acquire a valid OAuth 2.0 access token from Microsoft Dynamics Business Central.
    *   This token is then included in the authorization header of API requests to the ERP, ensuring secure communication.
*   **Field Mapping to ERP**: The script contains logic to map the fields from the JSON objects to the corresponding fields in the Microsoft Dynamics Business Central API endpoints (e.g., for creating general journal entries). This includes:
    *   Mapping `transaction_date` to the ERP's Posting Date field.
    *   Mapping `account_code` to the G/L Account No. field.
    *   Mapping `description` to the Description field.
    *   Mapping `amount` and `transaction_type` to the appropriate Debit Amount or Credit Amount fields in the ERP.
    *   Handling any necessary data type conversions or formatting required by the ERP API.
*   **Data Posting**:
    *   For each transaction, the script constructs an API request payload (typically JSON) according to the ERP's API specifications.
    *   It then sends this payload to the relevant API endpoint (e.g., `/companies({id})/journals({id})/journalLines`).
    *   Error handling is implemented to manage API response codes, log successes or failures, and potentially retry failed requests or flag them for manual review.
*   **Output**: Data is posted to Microsoft Dynamics Business Central. The script may also generate a log file summarizing the integration results.

# Design Considerations for Data Format Conversion

A key architectural decision in this project is the conversion of CSV data to an intermediate JSON format before integrating with the Microsoft Dynamics Business Central API. This section discusses the rationale, advantages, and disadvantages of this approach.

**Rationale:**

The primary input is CSV, which, while common, can be ambiguous and lacks a strict structure, especially with variations in headers, column orders, and data types. JSON, on the other hand, offers a well-defined, hierarchical structure that is natively supported by most modern APIs, including the Microsoft Dynamics Business Central API. Converting to JSON allows for a clear, validated, and transformed representation of data before the final integration step.

**Pros of Converting CSV to JSON:**

1.  **Structured Data Representation**:
    *   **Clarity**: JSON allows for a clear, human-readable, and self-describing structure with key-value pairs, making it easier to understand the data compared to relying on CSV column order.
    *   **Complex Data Types**: JSON natively supports complex data types (objects, arrays, booleans, numbers), which can be beneficial for representing structured financial data that might be flattened or awkwardly represented in CSV.
    *   **Schema Validation Potential**: An intermediate JSON format allows for schema validation (e.g., using JSON Schema) before attempting to send data to the ERP. This can catch data issues earlier.

2.  **Decoupling and Modularity**:
    *   **Separation of Concerns**: The conversion process is handled by `csv_to_json_converter.py`, separating the concerns of CSV parsing and initial transformation from the concerns of ERP API interaction (handled by `process_japan_exports.py`).
    *   **Intermediate Data Staging**: The JSON file acts as a staging point. If the ERP integration fails, the already processed and validated JSON data can be reused without reprocessing the original CSV. This is also useful for debugging, as the intermediate JSON can be inspected.
    *   **Future Flexibility**: If the source data format changes (e.g., from CSV to another format) or the target system changes, only the relevant conversion script (`csv_to_json_converter.py` or `process_japan_exports.py`) needs modification, rather than a monolithic script.

3.  **Ease of API Integration**:
    *   **Widely Accepted Format**: JSON is the de facto standard for most web APIs, including Microsoft Dynamics Business Central. HTTP client libraries (like `requests` in Python) can easily serialize Python dictionaries into JSON for API request bodies.
    *   **Reduced Complexity in API Calls**: The `process_japan_exports.py` script can work with clean, structured Python objects (derived from JSON) rather than performing complex CSV parsing and data manipulation simultaneously with API logic.

4.  **Data Validation and Transformation Opportunities**:
    *   The `csv_to_json_converter.py` script can perform significant data validation (e.g., checking for required fields, correct data types, valid values) and transformations (e.g., currency normalization, description truncation, mapping CSV column names to meaningful JSON keys) before the data even reaches the ERP integration stage. This reduces the likelihood of basic data errors causing API failures.

**Cons of Converting CSV to JSON:**

1.  **Intermediate Step Overhead**:
    *   **Performance**: For extremely large CSV files, the process of reading the CSV, converting it to JSON, writing the JSON to disk, and then reading the JSON again can introduce performance overhead compared to a direct CSV-to-API stream (if feasible).
    *   **Disk Space**: Storing intermediate JSON files requires additional disk space, which could be a concern for very large datasets or if many files are processed.

2.  **Increased Complexity (Initial Perception)**:
    *   Introducing an additional script (`csv_to_json_converter.py`) and an intermediate file format might seem to add more "moving parts" to the system. However, this often leads to better modularity and simpler individual components.

3.  **Error Handling in Multiple Stages**:
    *   Errors need to be handled in the CSV-to-JSON conversion stage and then separately in the JSON-to-API integration stage. This requires careful logging and error tracking across the workflow.

**Conclusion for the "toi project":**

For the "toi project," converting CSV data to an intermediate JSON format is a suitable and beneficial approach. The specific complexities associated with the input CSV files (e.g., two-line headers, Japanese character encodings, need for currency normalization and description truncation) necessitate a dedicated transformation step.

JSON provides a robust, structured way to represent this normalized data. This structured intermediate format simplifies the `process_japan_exports.py` script, allowing it to focus solely on API interaction logic using clean, pre-validated data. The benefits of decoupling, improved data validation capabilities, easier debugging, and enhanced maintainability outweigh the potential overhead for the expected scale of this project. The clarity gained from having a well-defined JSON structure before API interaction significantly aids in managing the integration with Microsoft Dynamics Business Central.

# Configuration Management

This section details how system configurations, especially sensitive data, are managed.

**`.env` Files for Local Configuration:**

*   Sensitive information such as API keys, client secrets, and specific URLs for the ERP system are stored in `.env` files.
*   Each developer or deployment environment should have its own `.env` file. This file is placed in the root directory of the project.
*   **Security**: The `.env` file is listed in the `.gitignore` file to prevent it from being committed to the version control system (Git). This is crucial for protecting sensitive credentials from being exposed in the codebase.
*   An example file, `env.example` or `.env.example`, is typically included in the repository. This file lists all the necessary environment variables that the application expects, but with placeholder or empty values. Developers can copy this example file to `.env` and fill in their specific credentials and endpoints.

**`env_config.py` for Loading Configuration:**

*   The `env_config.py` script is responsible for loading the environment variables from the `.env` file into the application's runtime environment.
*   It typically uses a Python library like `python-dotenv` which reads key-value pairs from the `.env` file and makes them available as environment variables (e.g., via `os.environ`).
*   This allows other Python scripts in the project (e.g., `oauth_token_helper.py`, `process_japan_exports.py`) to access configuration values in a clean and secure manner without hardcoding them. For instance, `erp_client_id = os.getenv("ERP_CLIENT_ID")`.

**Key Environment Variables:**

The following environment variables are essential for the system's operation, particularly for interacting with the Microsoft Dynamics Business Central ERP:

*   `ERP_CLIENT_ID`: The client ID for the application registered in Azure Active Directory, used for OAuth 2.0 authentication with the ERP.
*   `ERP_CLIENT_SECRET`: The client secret for the application, used in conjunction with the client ID to obtain access tokens. This is highly sensitive.
*   `ERP_TOKEN_URL`: The URL of the OAuth 2.0 token endpoint for Microsoft Dynamics Business Central (e.g., `https://login.microsoftonline.com/<tenant_id>/oauth2/v2.0/token`).
*   `ERP_API_URL`: The base URL for the Microsoft Dynamics Business Central API (e.g., `https://api.businesscentral.dynamics.com/v2.0/<tenant_id>/<environment_name>/api/v2.0`).
*   `ERP_SCOPE`: The scope(s) required for accessing the ERP API (e.g., `https://api.businesscentral.dynamics.com/.default`). This defines the permissions the application is requesting.

Additional variables might be defined for file paths, logging levels, or other configurable aspects of the system.

# Authentication and Authorization

This section describes the mechanisms used to authenticate with the Microsoft Dynamics Business Central ERP system and authorize API requests.

**OAuth 2.0 Client Credentials Grant Flow:**

*   The system utilizes the OAuth 2.0 client credentials grant flow for server-to-server authentication with the Microsoft Dynamics Business Central API. This flow is appropriate for applications that act on their own behalf, without direct user interaction at the time of API access.
*   **Process:**
    1.  The application (specifically, logic within `oauth_token_helper.py` or embedded in `process_japan_exports.py`) sends a POST request to the ERP's token endpoint (`ERP_TOKEN_URL`).
    2.  This request includes:
        *   `grant_type`: Set to `client_credentials`.
        *   `client_id`: The application's `ERP_CLIENT_ID`.
        *   `client_secret`: The application's `ERP_CLIENT_SECRET`.
        *   `scope`: The `ERP_SCOPE` defining the requested permissions.
    3.  If the credentials are valid, the token endpoint returns a JSON response containing an `access_token` and its `expires_in` time (among other details).

**Role of `oauth_token_helper.py`:**

*   The `oauth_token_helper.py` script (or equivalent logic within `process_japan_exports.py`) encapsulates the token acquisition and management process.
*   **Token Acquisition**: It constructs and sends the token request as described above.
*   **Token Caching**: Upon receiving a new access token, the helper caches it (e.g., in memory or a temporary file) along with its expiry time. This prevents redundant token requests for every API call. Before making an API call, the helper checks if a valid, unexpired token is available in the cache.
*   **Token Usage**: When `process_japan_exports.py` needs to make an API call to the `ERP_API_URL`, it requests a valid token from the helper. The helper returns the cached token if available and not expired, or acquires a new one if necessary.
*   **Authorization Header**: The obtained access token is then included in the `Authorization` header of API requests to the ERP, formatted as a Bearer token:
    `Authorization: Bearer <access_token>`
*   **Token Expiry and Refresh**: While the client credentials flow doesn't typically use refresh tokens (a new token is requested using the same client credentials when the old one expires), the helper logic should be mindful of token expiry. It should proactively request a new token if the current one is close to expiring or has already expired.

**SSL Certificate Verification:**

*   All communication with the ERP system's token endpoint (`ERP_TOKEN_URL`) and API endpoint (`ERP_API_URL`) occurs over HTTPS, ensuring data is encrypted in transit.
*   **Importance**: SSL certificate verification is crucial for preventing man-in-the-middle (MITM) attacks. It ensures that the application is communicating with the genuine ERP server and not an imposter.
*   **Handling**: Standard Python HTTP client libraries, such as `requests` (which is commonly used in such applications), automatically verify SSL certificates by default when making HTTPS requests. This typically involves checking the server's certificate against a set of trusted root certificates provided by the operating system or the Python environment.
*   It is important to ensure that this default behavior is not disabled unless there's a very specific, understood, and justifiable reason (e.g., in a strictly controlled development environment with self-signed certificates). Disabling SSL verification in production environments is a significant security risk.

**Authorization Scope:**

*   The permissions granted to the application are determined by the `ERP_SCOPE` requested during the token acquisition and the permissions configured for the application's service principal in Azure Active Directory / Microsoft Dynamics Business Central.
*   The principle of least privilege should be applied: the application should only be granted the minimum necessary permissions (scopes) required to perform its tasks (e.g., read/write specific journal entries).

# Error Handling and Logging

This section outlines the strategies for handling errors and logging activities within the system. Robust error handling and comprehensive logging are essential for troubleshooting, monitoring, and maintaining the application.

**General Error Handling Strategy:**

*   **Try-Except Blocks**: Core logic in all scripts is enclosed in `try-except` blocks to catch potential exceptions gracefully.
*   **Specific Exceptions**: Scripts aim to catch specific exceptions (e.g., `FileNotFoundError`, `requests.exceptions.RequestException`, `ValueError`, `KeyError`) rather than generic `Exception` where possible, allowing for more targeted error handling and logging.
*   **Fail Fast/Graceful Degradation**: For critical errors (e.g., inability to load configuration, authentication failure), scripts may "fail fast" by logging the error and exiting. For non-critical errors (e.g., an issue with a single record in a batch), the script may log the error and continue processing other records.

**Error Handling in Specific Scripts:**

*   **`charset_converter.py`**:
    *   **File Not Found**: Handles `FileNotFoundError` if the input CSV file does not exist. Logs an error and exits.
    *   **Encoding Detection Errors**: If the `chardet` library fails to detect encoding or returns a low-confidence result, logs a warning and may proceed with a default encoding (e.g., UTF-8) or skip the file.
    *   **File I/O Errors**: Catches `IOError` or `OSError` during file reading or writing (e.g., disk full, permission issues). Logs the error and potentially skips the problematic file.

*   **`csv_to_json_converter.py`**:
    *   **File Not Found**: Handles `FileNotFoundError` for the input UTF-8 CSV file. Logs an error and exits.
    *   **CSV Parsing Errors**: Catches errors from the `csv` module (e.g., `csv.Error`) for malformed CSV files or if the header structure is not as expected (e.g., missing key columns). Logs the error, may skip the file or problematic rows.
    *   **Data Conversion Errors**: Handles `ValueError` (e.g., failure to normalize currency amounts to numbers) or `KeyError` (e.g., expected CSV column missing). Logs the specific error and the problematic row/data, then skips that row.
    *   **File I/O Errors**: Catches `IOError` or `OSError` for issues writing the output JSON file. Logs the error and exits.

*   **`oauth_token_helper.py` (and token logic in `process_japan_exports.py`)**:
    *   **Network Errors**: Catches `requests.exceptions.ConnectionError`, `requests.exceptions.Timeout` during token requests to `ERP_TOKEN_URL`. Logs the error and may implement a retry mechanism for transient network issues.
    *   **Token Endpoint Errors**: Checks HTTP status codes from the token endpoint. Logs detailed error messages if the ERP returns errors (e.g., 400 Bad Request, 401 Unauthorized for invalid client credentials or scope). Exits on authentication failure.

*   **`process_japan_exports.py`**:
    *   **File Not Found**: Handles `FileNotFoundError` for the input JSON data file. Logs an error and exits.
    *   **JSON Parsing Errors**: Catches `json.JSONDecodeError` if the input file is not valid JSON. Logs an error and exits.
    *   **API Errors from Microsoft Dynamics Business Central**:
        *   Catches `requests.exceptions.HTTPError` or checks HTTP status codes for API responses.
        *   **4xx Client Errors**: (e.g., 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found). These usually indicate issues with the request data, permissions, or authentication. Logs the full error response from the API, including error messages in the response body. Problematic data entries might be skipped and flagged for manual review.
        *   **5xx Server Errors**: (e.g., 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable). These indicate issues on the ERP server side. Logs the error and may implement a retry strategy with exponential backoff for transient errors.
    *   **Network Errors**: Catches `requests.exceptions.ConnectionError`, `requests.exceptions.Timeout` during API calls to `ERP_API_URL`. Logs the error and may retry.
    *   **Data Validation Errors**: If the ERP API returns specific validation errors (e.g., a field value is incorrect), these are logged with details of the problematic data.

**Logging Mechanisms:**

The system employs a combination of console output and file-based logging using Python's built-in `logging` module.

*   **Console Output**:
    *   Provides immediate feedback during script execution, especially useful for development, debugging, or when running scripts manually.
    *   Typically logs messages of INFO level and above. Verbosity can be controlled via command-line arguments or configuration.

*   **File-based Logging**:
    *   **`erp_api_integration.log`**:
        *   **Purpose**: Dedicated log file for events related to ERP interaction, primarily used by `process_japan_exports.py` and `oauth_token_helper.py`.
        *   **Content**: Logs successful and failed token acquisitions, details of API requests (endpoint, method, sanitized payload if necessary), API responses (status code, key parts of the response body, especially errors), and summary of integration results (e.g., number of records processed, successful, failed).
    *   **`csv_conversion.log`**:
        *   **Purpose**: Dedicated log file for events related to CSV processing, used by `charset_converter.py` and `csv_to_json_converter.py`.
        *   **Content**: Logs input file names, detected encodings, results of encoding conversion, CSV parsing successes or failures, errors encountered during data transformation (e.g., currency normalization, field mapping), and names of output files generated.
*   **Log Format**:
    *   Log entries are formatted to include:
        *   Timestamp (e.g., `YYYY-MM-DD HH:MM:SS,ms`)
        *   Log Level (e.g., `INFO`, `WARNING`, `ERROR`, `DEBUG`)
        *   Script Name (or Logger Name) (e.g., `charset_converter`, `process_japan_exports`)
        *   Function Name (if applicable and available)
        *   Log Message: Clear, concise description of the event or error.
    *   Example: `2023-10-27 10:30:00,123 - ERROR - process_japan_exports - post_journal_entry - API request failed for transaction_id 789: 400 Bad Request - {"error":{"code":"BadRequest_InvalidDocumentDate","message":"The document date is outside the allowed posting range."}}`

*   **Log Levels**:
    *   **DEBUG**: Detailed information, typically of interest only when diagnosing problems.
    *   **INFO**: Confirmation that things are working as expected (e.g., file processed successfully, token acquired, data posted).
    *   **WARNING**: An indication of an unexpected event or a potential problem that doesn't prevent the current operation from completing but might lead to issues later (e.g., encoding detection low confidence, a non-critical field missing from a CSV row).
    *   **ERROR**: A more serious problem due to which the software was unable to perform a specific function (e.g., API call failed, file not found, data conversion error for a record).
    *   **CRITICAL**: A very serious error, indicating that the program itself may be unable to continue running.

Configuration for log file paths, log levels, and formats is managed centrally, potentially within `env_config.py` or a dedicated logging configuration setup.

# Key Scripts and Their Usage

This section provides an overview of the main Python scripts, their command-line usage, and expected inputs/outputs.

**1. `charset_converter.py`**

*   **Purpose**: Detects the character encoding of a given CSV file (especially useful for non-UTF-8 files like those encoded in Shift-JIS or EUC-JP) and converts it to UTF-8.
*   **Command-line Arguments**:
    *   `input_file_path`: Path to the source CSV file.
    *   `output_file_path`: Path where the UTF-8 encoded CSV file will be saved.
    *   (Optional) `--source_encoding <encoding>`: Manually specify the source encoding if known, bypassing automatic detection.
*   **Example Usage**:
    ```bash
    python charset_converter.py "Evelyn Raku export.csv" "Evelyn Raku export_utf8.csv"
    ```
    To manually specify Shift-JIS encoding:
    ```bash
    python charset_converter.py "input_shift_jis.csv" "output_utf8.csv" --source_encoding shift_jis
    ```

**2. `csv_to_json_converter.py`**

*   **Purpose**: Converts a UTF-8 encoded CSV file (specifically one with a two-line header format from Japanese systems) into a structured JSON format suitable for ERP integration. It performs tasks like currency normalization and description truncation.
*   **Command-line Arguments**:
    *   `csv_file_path`: Path to the input UTF-8 encoded CSV file.
    *   `json_file_path`: Path where the output JSON file will be saved.
*   **Input CSV Format Overview**:
    *   Must be UTF-8 encoded.
    *   Expected to have a two-line header. The first line contains general headers, and the second often contains Japanese specific headers that are used for mapping.
    *   Relevant columns typically include transaction date, account codes, account names, descriptions, and debit/credit amounts (which may be in separate columns or need to be derived).
*   **Output JSON Format**:
    *   An array of JSON objects, where each object represents a transaction or journal line.
    *   Key fields in each JSON object include: `transaction_date`, `account_code`, `account_name`, `description` (truncated if necessary), `currency` (e.g., "JPY"), `amount` (normalized numerical value), and `transaction_type` ("debit" or "credit").
*   **Example Usage**:
    ```bash
    python csv_to_json_converter.py "Evelyn Raku export_utf8.csv" "Evelyn Raku export.json"
    ```

**3. `process_japan_exports.py`**

*   **Purpose**: Orchestrates the final step of the ERP integration. It reads the structured JSON data (produced by `csv_to_json_converter.py`), authenticates with the Microsoft Dynamics Business Central ERP system using OAuth 2.0 (via `oauth_token_helper.py` logic), maps JSON fields to ERP API fields, and posts the data to the ERP.
*   **Command-line Arguments**:
    *   `json_file_path`: Path to the input JSON file containing the transaction data to be posted.
    *   (Optional) `--validate_only`: If specified, the script will validate the data and attempt to simulate the API calls without actually posting data to the ERP. (This is a hypothetical useful argument, actual implementation may vary).
*   **Role in ERP Integration**:
    *   Loads ERP connection details and credentials from environment variables (see Configuration Management).
    *   Acquires an OAuth token.
    *   Reads and parses the input JSON file.
    *   For each transaction in the JSON:
        *   Maps the data to the format required by the ERP API (e.g., general journal lines).
        *   Makes an API POST request to the relevant ERP endpoint.
        *   Logs the success or failure of each posting attempt.
*   **Example Usage**:
    ```bash
    python process_japan_exports.py "Evelyn Raku export.json"
    ```
    Example with hypothetical validate_only flag:
    ```bash
    python process_japan_exports.py "Evelyn Raku export.json" --validate_only
    ```

**Note**: The `oauth_token_helper.py` script is not typically run directly by the user. It's designed to be imported and used by `process_japan_exports.py` to handle the complexities of OAuth token acquisition and management. Similarly, `env_config.py` is imported by other scripts to load environment variables.

# Testing

This section outlines the testing strategy for the system, ensuring its components function correctly and data is processed accurately.

**Testing Directories:**

*   **`Tesing/` (Note: should ideally be named `Testing/`)**:
    *   This directory contains a collection of sample CSV files (with various encodings like Shift-JIS, and their UTF-8 converted counterparts) and corresponding expected JSON output files.
    *   **Purpose**: These files are primarily used for:
        *   **Manual Testing**: Developers can run the scripts (`charset_converter.py`, `csv_to_json_converter.py`, `process_japan_exports.py`) with these sample files to manually verify the output at each stage.
        *   **End-to-End Testing**: The sample files allow for testing the entire workflow from an original CSV file to the (simulated or actual) data posting to the ERP.
        *   **Integration Testing**: Verifying that the different scripts work together as expected (e.g., output from `charset_converter.py` is correctly consumed by `csv_to_json_converter.py`).
        *   **Specific Scenarios**: Includes various CSV examples to test different data formats, edge cases (e.g., empty files, files with only headers, files with unusual characters), and currency formats. Sample JSONs like `Evelyn Raku export_journal_data.json` or `custom_output.json` represent expected structures for ERP integration.

*   **`unittest/`**:
    *   This directory houses automated unit tests written using Python's `unittest` framework (or a similar framework like `pytest`).
    *   **Purpose**: To test individual functions and classes (units of code) in isolation to ensure they behave as expected.
    *   **Focus**:
        *   **`unittest/test_process_japan_exports.py`**: Contains unit tests specifically for `process_japan_exports.py`. These tests likely mock external dependencies (like the actual ERP API and `oauth_token_helper.py`) and focus on:
            *   Correctness of business logic (e.g., data transformations specific to ERP requirements).
            *   Accuracy of data mapping from the input JSON to the structure required by the ERP API.
            *   Handling of various data inputs and edge cases.
            *   Error handling logic within `process_japan_exports.py`.
        *   Unit tests for other scripts (e.g., `test_csv_to_json_converter.py`, `test_charset_converter.py`) would also reside here, testing their specific functionalities (e.g., header parsing, currency normalization, encoding detection logic).

**Testing Workflow and Strategy:**

1.  **Unit Tests**: Developers should run unit tests frequently during development to catch issues early. These tests ensure that individual components are working correctly. Automated execution of these tests (e.g., via a CI/CD pipeline) is recommended.
2.  **Manual/Integration Testing with `Tesing/` data**:
    *   Use sample CSVs in `Tesing/` to run `charset_converter.py` and verify the UTF-8 output.
    *   Use the generated UTF-8 CSVs to run `csv_to_json_converter.py` and compare the output JSON with the sample JSONs provided in `Tesing/`.
    *   Use the generated JSONs (or sample JSONs) to run `process_japan_exports.py`. Initially, this might be done with a mock ERP endpoint or a `--validate_only` flag (if implemented) to check data mapping and API call structure without actual data posting.
3.  **End-to-End Testing**: Once unit and integration tests pass, perform end-to-end tests using sample data from `Tesing/` against a staging or test environment of Microsoft Dynamics Business Central to verify the entire process flow, including actual data posting and validation within the ERP.
4.  **Regression Testing**: Before any new release, all relevant unit and end-to-end tests should be executed to ensure that new changes have not broken existing functionality.

This multi-layered testing approach helps ensure the reliability and correctness of the CSV processing and ERP integration system.

# Conclusion

This design document has detailed a system for processing CSV files, with a special focus on Japanese formats, converting them to a structured JSON, and subsequently integrating this data with Microsoft Dynamics Business Central. The process involves character set conversion, data transformation and normalization, and authenticated API communication with the ERP.

The system is modular, with distinct Python scripts handling different stages of the process: `charset_converter.py` for encoding, `csv_to_json_converter.py` for JSON transformation, and `process_japan_exports.py` for ERP integration, supported by `oauth_token_helper.py` for authentication and `env_config.py` for configuration management. Error handling, logging, and testing strategies have been outlined to ensure robustness and maintainability.

**Potential Areas for Future Improvement and Maintenance:**

While the current design provides a functional baseline, several areas could be enhanced in future iterations:

*   **Enhanced Test Coverage**:
    *   Expand unit tests for `charset_converter.py` to cover a wider variety of encodings and edge-case file structures.
    *   Increase unit test coverage for `csv_to_json_converter.py`, particularly for complex mapping logic, diverse currency formats, and various two-line header configurations.
    *   Develop more comprehensive integration tests that can be automated.

*   **CI/CD Integration**:
    *   Implement a formal Continuous Integration/Continuous Deployment (CI/CD) pipeline (e.g., using GitHub Actions, Jenkins, GitLab CI). This would automate testing, linting, and potentially deployment processes, improving code quality and development velocity.

*   **Encoding Detection Robustness**:
    *   If `chardet` proves insufficient for certain rare or ambiguous encodings, research and integrate more specialized Japanese encoding detection libraries.
    *   Enhance the `--source_encoding` command-line argument in `charset_converter.py` or provide a configuration option for default/fallback encodings if detection is consistently problematic for specific data sources.

*   **Standardized OAuth Handling**:
    *   Ensure that all OAuth 2.0 token acquisition, caching, and refresh logic is strictly consolidated within `oauth_token_helper.py`. Refactor `process_japan_exports.py` if any significant token management responsibilities still reside there, making the helper the sole authority for token concerns.

*   **Configuration-Driven Mappings**:
    *   **CSV-to-JSON Mapping**: Externalize the mapping rules used by `csv_to_json_converter.py` (e.g., how CSV columns map to JSON fields, which header lines to use) into configuration files (e.g., JSON or YAML). This would make it easier to adapt the script to different CSV layouts without code changes.
    *   **JSON-to-ERP Mapping**: Similarly, the field mappings used by `process_japan_exports.py` to prepare data for the ERP API could be made configurable.

*   **Batch Processing and Enhanced Error Reporting**:
    *   For `process_japan_exports.py`, implement more sophisticated batch processing for large JSON files. This could involve sending multiple journal entries in a single API request if the ERP API supports it, or managing a queue of records to be posted.
    *   Improve error reporting for failed records during ERP posting. Instead of just logging, consider generating a separate error file or report detailing which records failed and why, making it easier for users to correct and reprocess them.

*   **Idempotency**:
    *   Investigate and implement mechanisms to ensure idempotency in `process_japan_exports.py` for ERP data posting. This would prevent duplicate record creation if the script is run multiple times with the same input due to an error or retry. This might involve checking if a record with a unique identifier already exists in the ERP before attempting to create it.

*   **User Interface/Orchestration Layer**:
    *   For less technical users, a simple user interface (web-based or desktop GUI) could be developed to manage the execution of these scripts, select input files, and view logs/results.
    *   Alternatively, a more robust workflow orchestration tool (e.g., Apache Airflow) could be used if the processing pipeline becomes more complex or needs to be scheduled regularly.

Addressing these areas will contribute to a more robust, maintainable, and user-friendly system in the long term.
