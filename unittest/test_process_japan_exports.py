# test_process_japan_exports.py
import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import os
import json
import sys
import requests # For requests.exceptions.HTTPError

# Import the script to be tested
# Ensure process_japan_exports.py is in the same directory or accessible in PYTHONPATH
import process_japan_exports as erp_script

# Helper to create a mock response for requests.post
class MockResponse:
    def __init__(self, json_data, status_code, text="", headers=None):
        self.json_data = json_data
        self.status_code = status_code
        self.text = text if text else json.dumps(json_data) if json_data else ""
        self.headers = headers if headers is not None else {"Content-Type": "application/json"}

    def json(self):
        if self.status_code >= 400 and self.json_data is None: # Simulate error response without JSON body
             raise json.JSONDecodeError("Mocking JSONDecodeError", self.text, 0)
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.exceptions.HTTPError(f"{self.status_code} Error")
            error.response = self
            raise error

class TestERPIntegration(unittest.TestCase):

    def setUp(self):
        # Suppress logging output during tests to keep test output clean
        # You can also mock logger calls to assert specific log messages
        self.patcher = patch('process_japan_exports.logger', MagicMock())
        self.mock_logger = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        
    # Tests for transform_currency_code
    def test_transform_currency_code(self):
        # Test cases where currency should be emptied
        self.assertEqual(erp_script.transform_currency_code("VCT", "NTD"), "")
        self.assertEqual(erp_script.transform_currency_code("VCP", "R-PHP"), "")
        self.assertEqual(erp_script.transform_currency_code("VCA", "R-USD"), "")
        self.assertEqual(erp_script.transform_currency_code("VCG", "R-EUR"), "")
        self.assertEqual(erp_script.transform_currency_code("VCJ", "JPY"), "")
        
        # Test cases where currency should remain unchanged
        self.assertEqual(erp_script.transform_currency_code("VCT", "USD"), "USD")
        self.assertEqual(erp_script.transform_currency_code("VCP", "EUR"), "EUR")
        self.assertEqual(erp_script.transform_currency_code("VCA", "JPY"), "JPY")
        self.assertEqual(erp_script.transform_currency_code("VCG", "NTD"), "NTD")
        self.assertEqual(erp_script.transform_currency_code("VCJ", "USD"), "USD")
        
        # Test with unknown company code
        self.assertEqual(erp_script.transform_currency_code("XYZ", "NTD"), "NTD")
        
        # Test with empty inputs
        self.assertEqual(erp_script.transform_currency_code("", ""), "")
        self.assertEqual(erp_script.transform_currency_code("VCT", ""), "")
        self.assertEqual(erp_script.transform_currency_code("", "NTD"), "NTD")

    # Tests for get_env_var (assuming the fallback implementation is used)
    @patch.dict(os.environ, {"TEST_VAR": "test_value"}, clear=True)
    def test_get_env_var_existing(self):
        self.assertEqual(erp_script.get_env_var("TEST_VAR"), "test_value")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_env_var_missing_with_default(self):
        self.assertEqual(erp_script.get_env_var("MISSING_VAR", default="default_val"), "default_val")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_env_var_required_missing_raises_error(self):
        with self.assertRaisesRegex(ValueError, "Required environment variable 'MISSING_VAR' is not set"):
            erp_script.get_env_var("MISSING_VAR", required=True)

    @patch.dict(os.environ, {"INT_VAR": "123"}, clear=True)
    def test_get_env_var_as_type_int(self):
        # Note: The script's get_env_var only has `as_type=str` in its fallback.
        # If it were extended, this test would be for `as_type=int`.
        # For the current script, this will try `int("123")` if `as_type` was `int`
        # but the script's fallback is `as_type=str` by default.
        # Let's test the provided as_type=str.
        self.assertEqual(erp_script.get_env_var("INT_VAR", as_type=str), "123")
        # If we wanted to test conversion, we'd need to modify get_env_var or call it like:
        # self.assertEqual(int(erp_script.get_env_var("INT_VAR")), 123)

    # Tests for get_access_token
    @patch('process_japan_exports.requests.post')
    @patch('process_japan_exports.CLIENT_ID', 'test_client_id')
    @patch('process_japan_exports.CLIENT_SECRET', 'test_client_secret')
    @patch('process_japan_exports.SCOPE', 'test_scope')
    @patch('process_japan_exports.TOKEN_URL', 'http://fake-token-url.com')
    def test_get_access_token_success(self, mock_post):
        mock_response = MockResponse({"access_token": "fake_token", "expires_in": 3600}, 200)
        mock_post.return_value = mock_response
        
        token = erp_script.get_access_token()
        self.assertEqual(token, "fake_token")
        expected_data = {
            "grant_type": "client_credentials",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scope": "test_scope"
        }
        mock_post.assert_called_once_with('http://fake-token-url.com', data=expected_data)

    @patch('process_japan_exports.requests.post')
    @patch('process_japan_exports.CLIENT_ID', 'test_client_id') # Ensure globals are patched
    def test_get_access_token_failure(self, mock_post):
        mock_response = MockResponse(None, 400, text="Error")
        mock_post.return_value = mock_response
        
        with self.assertRaises(requests.exceptions.HTTPError):
            erp_script.get_access_token()

    # Tests for create_journal_line
    def test_create_journal_line_debit(self):
        entry = {
            "voucher_no": "V001",
            "description": "Test Debit Entry",
            "debit": {
                "gl_account": "Expense",
                "account": "6000",
                "currency": "JPY",
                "amount": 1000,
                "department": "SALESDP", # Full department code
                "applicant_code": "APP01"
            },
            "credit": {} # Not used for this specific line creation
        }
        expected_line = {
            "Journal_Template_Name": "PURCHASES",
            "Journal_Batch_Name": "PURCHASE",
            "Document_Type": "Invoice",
            "External_Document_No": "V001",
            "Account_Type": "Expense",
            "Account_No": "6000",
            "Description": "Test Debit Entry",
            "Currency_Code": "JPY",
            "Amount": 1000,
            "Shortcut_Dimension_1_Code": "SAL", # First 3 chars
            "Shortcut_Dimension_2_Code": "SALESDP", # department
            "ShortcutDimCode3": "", "ShortcutDimCode4": "APP01", "ShortcutDimCode5": "",
            "ShortcutDimCode6": "", "ShortcutDimCode7": "", "ShortcutDimCode8": "",
            "ShortcutDimCode9": "", "ShortcutDimCode10": "", "ShortcutDimCode11": "",
            "ShortcutDimCode12": "", "ShortcutDimCode13": "", "ShortcutDimCode14": "",
            "ShortcutDimCode15": ""
        }
        actual_line = erp_script.create_journal_line(entry, "debit")
        self.assertDictEqual(actual_line, expected_line)

    def test_create_journal_line_credit_vendor(self):
        entry = {
            "voucher_no": "V002",
            "description": "Test Credit Vendor",
            "debit": {}, # Not used
            "credit": {
                "gl_account": "Vendor",
                "vendor_code": "VEND001",
                "currency": "USD",
                "amount": 500,
                "department_code": "FINANCE", # For Vendor account, this is transformed
            }
        }
        expected_line = {
            "Journal_Template_Name": "PURCHASES",
            "Journal_Batch_Name": "PURCHASE",
            "Document_Type": "Invoice",
            "External_Document_No": "V002",
            "Account_Type": "Vendor",
            "Account_No": "VEND001",
            "Description": "Test Credit Vendor",
            "Currency_Code": "USD",
            "Amount": -500, # Negative for credit
            "Shortcut_Dimension_1_Code": "", # department not present in credit for non-vendor logic path
            "Shortcut_Dimension_2_Code": "FIN.9999", # Transformed department_code
            "ShortcutDimCode3": "", "ShortcutDimCode4": "", "ShortcutDimCode5": "",
            "ShortcutDimCode6": "", "ShortcutDimCode7": "", "ShortcutDimCode8": "",
            "ShortcutDimCode9": "", "ShortcutDimCode10": "", "ShortcutDimCode11": "",
            "ShortcutDimCode12": "", "ShortcutDimCode13": "", "ShortcutDimCode14": "",
            "ShortcutDimCode15": ""
        }
        actual_line = erp_script.create_journal_line(entry, "credit")
        self.assertDictEqual(actual_line, expected_line)

    def test_create_journal_line_missing_fields_handled_gracefully(self):
        entry = {
            # Missing voucher_no, description
            "debit": {
                # Missing many fields
                "amount": 100,
            },
            "credit": {}
        }
        # Check that it doesn't crash and defaults are applied (e.g. empty strings)
        journal_line = erp_script.create_journal_line(entry, "debit")
        self.assertEqual(journal_line["External_Document_No"], "")
        self.assertEqual(journal_line["Description"], "")
        self.assertEqual(journal_line["Amount"], 100)
        self.assertEqual(journal_line["Shortcut_Dimension_1_Code"], "")
        self.assertEqual(journal_line["Shortcut_Dimension_2_Code"], "")
        self.assertEqual(journal_line["ShortcutDimCode4"], "")


    # Tests for post_journal_line
    @patch('process_japan_exports.requests.post')
    @patch('process_japan_exports.API_URL', 'http://fake-api-url.com/PurchaseJournals')
    def test_post_journal_line_success(self, mock_post):
        mock_response = MockResponse({"id": "123", "status": "posted"}, 201)
        mock_post.return_value = mock_response
        journal_line_payload = {"Account_No": "ACC001", "Amount": 100}
        
        success, response_data = erp_script.post_journal_line(journal_line_payload, "fake_access_token")
        
        self.assertTrue(success)
        self.assertEqual(response_data, {"id": "123", "status": "posted"})
        mock_post.assert_called_once_with(
            'http://fake-api-url.com/PurchaseJournals',
            json=journal_line_payload,
            headers={
                "Authorization": "Bearer fake_access_token",
                "Content-Type": "application/json"
            }
        )

    @patch('process_japan_exports.requests.post')
    @patch('process_japan_exports.API_URL', 'http://fake-api-url.com/PurchaseJournals')
    def test_post_journal_line_http_error_with_json_response(self, mock_post):
        error_payload = {"error": {"message": "Invalid data"}}
        mock_response = MockResponse(error_payload, 400, text=json.dumps(error_payload))
        mock_post.return_value = mock_response
        journal_line_payload = {"Account_No": "ACC001", "Amount": 100}
        
        success, response_data = erp_script.post_journal_line(journal_line_payload, "fake_access_token")
        
        self.assertFalse(success)
        self.assertEqual(response_data, error_payload)

    @patch('process_japan_exports.requests.post')
    @patch('process_japan_exports.API_URL', 'http://fake-api-url.com/PurchaseJournals')
    def test_post_journal_line_http_error_without_json_response(self, mock_post):
        mock_response = MockResponse(None, 500, text="Internal Server Error") # No JSON in error response
        mock_post.return_value = mock_response
        journal_line_payload = {"Account_No": "ACC001", "Amount": 100}
        
        success, response_data = erp_script.post_journal_line(journal_line_payload, "fake_access_token")
        
        self.assertFalse(success)
        self.assertIn("500 Error", response_data["error"]) # Check for string representation of HTTPError


    # Tests for process_entries
    @patch('process_japan_exports.create_journal_line')
    @patch('process_japan_exports.post_journal_line')
    @patch('time.sleep', return_value=None) # Mock time.sleep to speed up test
    def test_process_entries_all_success(self, mock_post_journal, mock_create_journal, mock_sleep):
        entries = [
            {"voucher_no": "E001", "debit": {"amount": 10}, "credit": {"amount": 10}},
            {"voucher_no": "E002", "debit": {"amount": 20}, "credit": {"amount": 20}}
        ]
        # Mock create_journal_line to return distinct identifiable payloads
        mock_create_journal.side_effect = [
            {"id": "debit1"}, {"id": "credit1"}, # For entry 1
            {"id": "debit2"}, {"id": "credit2"}  # For entry 2
        ]
        # Mock post_journal_line to always succeed
        mock_post_journal.return_value = (True, {"status": "success"})
        
        success_count, failure_count = erp_script.process_entries(entries, "fake_token")
        
        self.assertEqual(success_count, 4) # 2 entries * 2 lines each
        self.assertEqual(failure_count, 0)
        self.assertEqual(mock_create_journal.call_count, 4)
        self.assertEqual(mock_post_journal.call_count, 4)
        # Check calls to post_journal_line
        expected_post_calls = [
            call({"id": "debit1"}, "fake_token"),
            call({"id": "credit1"}, "fake_token"),
            call({"id": "debit2"}, "fake_token"),
            call({"id": "credit2"}, "fake_token"),
        ]
        mock_post_journal.assert_has_calls(expected_post_calls)
        self.assertEqual(mock_sleep.call_count, 4) # 2 * (0.5s after debit + 0.5s after credit)

    @patch('process_japan_exports.create_journal_line')
    @patch('process_japan_exports.post_journal_line')
    @patch('time.sleep', return_value=None)
    def test_process_entries_mixed_success_failure(self, mock_post_journal, mock_create_journal, mock_sleep):
        entries = [{"voucher_no": "E001", "debit": {"amount": 10}, "credit": {"amount": 10}}]
        mock_create_journal.side_effect = [{"id": "debit1"}, {"id": "credit1"}]
        # Simulate debit success, credit failure
        mock_post_journal.side_effect = [
            (True, {"status": "success_debit"}),  # Debit posts successfully
            (False, {"error": "failure_credit"})  # Credit fails
        ]
        
        success_count, failure_count = erp_script.process_entries(entries, "fake_token")
        
        self.assertEqual(success_count, 1)
        self.assertEqual(failure_count, 1)
        mock_post_journal.assert_any_call({"id": "debit1"}, "fake_token")
        mock_post_journal.assert_any_call({"id": "credit1"}, "fake_token")

    # Tests for generate_currency_modification_report
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_currency_modification_report(self, mock_file):
        entries = [
            {
                "voucher_no": "V001",
                "debit": {"department": "VCT.1234", "currency": "NTD"},
                "credit": {"department": "VCT.5678", "currency": "USD"}
            },
            {
                "voucher_no": "V002",
                "debit": {"department": "VCP.1234", "currency": "R-PHP"},
                "credit": {"department": "VCA.5678", "currency": "R-USD"}
            }
        ]
        
        modifications = erp_script.generate_currency_modification_report(entries, "test_report.md")
        
        # Check that the report file was opened for writing
        mock_file.assert_called_once_with("test_report.md", 'w')
        
        # Check that the correct number of modifications were detected
        self.assertEqual(len(modifications), 3)
        
        # Check the content of the modifications
        expected_mods = [
            {"voucher_no": "V001", "line_type": "debit", "company_code": "VCT", "original_currency": "NTD", "transformed_currency": ""},
            {"voucher_no": "V002", "line_type": "debit", "company_code": "VCP", "original_currency": "R-PHP", "transformed_currency": ""},
            {"voucher_no": "V002", "line_type": "credit", "company_code": "VCA", "original_currency": "R-USD", "transformed_currency": ""}
        ]
        
        for expected, actual in zip(expected_mods, modifications):
            self.assertEqual(expected, actual)
        
        # Check that the write method was called with the correct content
        write_calls = mock_file().write.call_args_list
        self.assertTrue(any("# Currency Modification Report" in args[0] for args, _ in write_calls))
        self.assertTrue(any("| Voucher No | Line Type | Company Code | Original Currency | Transformed Currency |" in args[0] for args, _ in write_calls))
        self.assertTrue(any("Total modifications: 3" in args[0] for args, _ in write_calls))

    # Tests for main function (high-level integration)
    @patch('process_japan_exports.argparse.ArgumentParser')
    @patch('process_japan_exports.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='[{"id":1}]')
    @patch('process_japan_exports.json.load')
    @patch('process_japan_exports.get_access_token')
    @patch('process_japan_exports.process_entries')
    @patch('sys.exit') # To prevent test runner from exiting
    def test_main_successful_run(self, mock_sys_exit, mock_process_entries, mock_get_access_token,
                                 mock_json_load, mock_file_open, mock_path_exists, mock_arg_parser):
        # Setup mocks
        mock_args = MagicMock()
        mock_args.input_file = "test.json"
        mock_arg_parser.return_value.parse_args.return_value = mock_args
        
        mock_path_exists.return_value = True
        mock_json_load.return_value = [{"entry": 1}]
        mock_get_access_token.return_value = "fake_token_main"
        mock_process_entries.return_value = (1, 0) # 1 success, 0 failure
        
        erp_script.main()
        
        mock_arg_parser.return_value.parse_args.assert_called_once()
        mock_path_exists.assert_called_once_with("test.json")
        mock_file_open.assert_called_once_with("test.json", 'r', encoding='utf-8')
        mock_json_load.assert_called_once_with(mock_file_open.return_value)
        mock_get_access_token.assert_called_once()
        mock_process_entries.assert_called_once_with([{"entry": 1}], "fake_token_main")
        mock_sys_exit.assert_not_called() # Should not exit on success
        self.mock_logger.info.assert_any_call("Processing complete. Success: 1/2, Failure: 0/2")


    @patch('process_japan_exports.argparse.ArgumentParser')
    @patch('process_japan_exports.os.path.exists')
    @patch('sys.exit')
    def test_main_input_file_not_found(self, mock_sys_exit, mock_path_exists, mock_arg_parser):
        mock_args = MagicMock()
        mock_args.input_file = "nonexistent.json"
        mock_arg_parser.return_value.parse_args.return_value = mock_args
        mock_path_exists.return_value = False
        
        erp_script.main()
        
        self.mock_logger.error.assert_called_with("Input file not found: nonexistent.json")
        mock_sys_exit.assert_called_once_with(1)

    @patch('process_japan_exports.argparse.ArgumentParser')
    @patch('process_japan_exports.os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('process_japan_exports.json.load', side_effect=json.JSONDecodeError("err", "doc", 0))
    @patch('sys.exit')
    def test_main_json_decode_error(self, mock_sys_exit, mock_json_load, mock_file_open, mock_path_exists, mock_arg_parser):
        mock_args = MagicMock()
        mock_args.input_file = "bad.json"
        mock_arg_parser.return_value.parse_args.return_value = mock_args

        erp_script.main()

        self.mock_logger.error.assert_called_with("Error loading input file: err: line 1 column 1 (char 0)")
        mock_sys_exit.assert_called_once_with(1)


    @patch('process_japan_exports.argparse.ArgumentParser')
    @patch('process_japan_exports.os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='[{"id":1}]')
    @patch('process_japan_exports.json.load', return_value=[{"entry":1}])
    @patch('process_japan_exports.generate_currency_modification_report')
    @patch('process_japan_exports.get_access_token', side_effect=Exception("Token fetch failed"))
    @patch('sys.exit')
    def test_main_token_acquisition_failure(self, mock_sys_exit, mock_get_access_token, mock_generate_report, 
                                           mock_json_load, mock_file_open, mock_path_exists, mock_arg_parser):
        mock_args = MagicMock()
        mock_args.input_file = "good.json"
        mock_args.report = "report.md"
        mock_args.dry_run = False
        mock_arg_parser.return_value.parse_args.return_value = mock_args
        mock_generate_report.return_value = []

        erp_script.main()
        
        mock_generate_report.assert_called_once_with([{"entry":1}], "report.md")
        self.mock_logger.error.assert_called_with("Failed to get access token: Token fetch failed")
        mock_sys_exit.assert_called_once_with(1)
        
    @patch('process_japan_exports.argparse.ArgumentParser')
    @patch('process_japan_exports.os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='[{"id":1}]')
    @patch('process_japan_exports.json.load', return_value=[{"entry":1}])
    @patch('process_japan_exports.generate_currency_modification_report')
    @patch('sys.exit')
    def test_main_dry_run(self, mock_sys_exit, mock_generate_report, mock_json_load, 
                         mock_file_open, mock_path_exists, mock_arg_parser):
        mock_args = MagicMock()
        mock_args.input_file = "good.json"
        mock_args.report = "report.md"
        mock_args.dry_run = True
        mock_arg_parser.return_value.parse_args.return_value = mock_args
        mock_generate_report.return_value = [{"modification": "test"}]

        erp_script.main()
        
        mock_generate_report.assert_called_once_with([{"entry":1}], "report.md")
        self.mock_logger.info.assert_any_call("Generated currency modification report with 1 modifications")
        self.mock_logger.info.assert_any_call("Dry run completed. Exiting without posting to API.")
        mock_sys_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
