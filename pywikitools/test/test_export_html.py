"""
Test all the functionalities of export_html.py
- creating folders if necessary
TODO get html contents for worksheets from API
TODO Export htmls into local directory
TODO download image files into local directory
TODO export content.json (with current content)

Run tests:
    python3  python3 -m unittest pywikitools/test/test_export_html.py
"""

import os
import unittest
from unittest.mock import MagicMock, patch, mock_open, call

from pywikitools.resourcesbot.export_html import ExportHTML


class TestExportHTML(unittest.TestCase):
    def test_run_with_empty_base_folder(self):
        # Create Mock objects
        fortraininglib_mock = MagicMock()
        language_info_mock = MagicMock()
        english_info_mock = MagicMock()
        changes_mock = MagicMock()
        english_changes_mock = MagicMock()

        # Initialize ExportHTML with empty _base_folder
        with self.assertLogs('pywikitools.resourcesbot.export_html', level='WARNING') as log:
            export_html = ExportHTML(fortraininglib_mock, "", force_rewrite=False)
            self.assertTrue(any("Missing htmlexport path in config.ini. Won't export HTML files." in message for message in log.output))

        # Execute "run" method - should return without doing anything because of empty base folder
        export_html.run(language_info_mock, english_info_mock, changes_mock, english_changes_mock)

        # Assert that no directory was created and no further action took place
        language_info_mock.assert_not_called()
        english_info_mock.assert_not_called()
        changes_mock.assert_not_called()
        english_changes_mock.assert_not_called()

    @patch("os.makedirs")  # Mock directory creation if needed
    def test_run_filters_finished_worksheets(self, mock_makedirs):
        # Here we test whether unfinished worksheets are filtered out and if nothing happens if there were no changes

        # Initialize mock objects for language_info, english_info, and other arguments
        fortraininglib_mock = MagicMock()
        language_info = MagicMock()
        english_info = MagicMock()
        changes_mock = MagicMock()
        english_changes_mock = MagicMock()

        # Mock data to represent finished and unfinished worksheets
        # Assumption: show_in_list returns True for finished and False for unfinished worksheets
        language_info.language_code = "de"
        language_info.worksheets = {
            "finished_worksheet": MagicMock(),
            "unfinished_worksheet": MagicMock()
        }
        english_info.worksheets = {
            "finished_worksheet": MagicMock(),
            "unfinished_worksheet": MagicMock()
        }

        # Set worksheets: only `finished_worksheet` should be kept in the final result
        language_info.worksheets["finished_worksheet"].show_in_list.return_value = True
        language_info.worksheets["unfinished_worksheet"].show_in_list.return_value = False

        # Initialize ExportHTML with a valid _base_folder
        export_html = ExportHTML(fortraininglib_mock, "/mocked/path", force_rewrite=False)

        # Run the `run` method
        export_html.run(language_info, english_info, changes_mock, english_changes_mock)

        # Verify that `language_info` remains unchanged
        self.assertIn("unfinished_worksheet", language_info.worksheets)
        self.assertIn("finished_worksheet", language_info.worksheets)

        with patch.object(export_html, 'has_relevant_change', return_value=False) as mock_has_relevant_change:
            # Run the `run` method
            export_html.run(language_info, english_info, changes_mock, english_changes_mock)

            # Verify that has_relevant_change was called for both worksheets
            mock_has_relevant_change.assert_any_call("finished_worksheet", changes_mock)
            calls = [call[0][0] for call in mock_has_relevant_change.call_args_list]
            self.assertNotIn("unfinished_worksheet", calls)

        # Since has_relevant_change returns False, no further processing should occur.
        # Ensure that fortraininglib_mock.get_page_html is not called
        fortraininglib_mock.get_page_html.assert_not_called()


    @patch("os.makedirs")  # Mock os.makedirs to prevent actual directory creation
    @patch("os.path.isdir", return_value=False)  # Mock os.path.isdir to simulate directory absence
    def test_directory_structure_creation(self, mock_isdir, mock_makedirs):
        # Create mock objects for the required parameters
        fortraininglib_mock = MagicMock()
        language_info_mock = MagicMock()
        english_info_mock = MagicMock()
        changes_mock = MagicMock()
        english_changes_mock = MagicMock()

        # Create target paths
        folder = os.path.join("/mocked", "path")
        main_folder = os.path.join(folder, "de")
        files_folder = os.path.join(main_folder, "files/")
        structure_folder = os.path.join(main_folder, "structure/")

        # Set up the mock language information
        language_info_mock.language_code = "de"
        language_info_mock.worksheets = {
            "finished_worksheet": MagicMock(show_in_list=lambda x: False),
        }

        # Initialize the ExportHTML class with a valid base folder
        export_html = ExportHTML(fortraininglib_mock, folder, force_rewrite=False)

        # check if constructor created base_directory
        mock_makedirs.assert_any_call(folder, exist_ok=True)
        self.assertEqual(mock_makedirs.call_count, 1)

        # Run the method under test
        export_html.run(language_info_mock, english_info_mock, changes_mock, english_changes_mock)


        # Assert that os.makedirs was called with the correct arguments
        mock_makedirs.assert_any_call(main_folder, exist_ok=True)
        mock_makedirs.assert_any_call(files_folder)
        mock_makedirs.assert_any_call(structure_folder)

        # Check that all required directories were attempted to be created
        self.assertEqual(mock_makedirs.call_count, 4)  # Three calls should have been made

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")  # Mock directory creation if needed
    @patch("pywikitools.resourcesbot.export_html.ExportHTML.has_relevant_change")
    @patch("pywikitools.resourcesbot.export_html.CustomBeautifyHTML")
    @patch("pywikitools.resourcesbot.export_html.StructureEncoder.encode", return_value="{}")
    def test_download_and_save_transformed_html(self, mock_encode, MockBeautifyHTML, mock_has_relevant_change, mock_makedirs, mock_open):
        # Set up mock objects
        fortraininglib_mock = MagicMock()
        language_info_mock = MagicMock()
        english_info_mock = MagicMock()
        changes_mock = MagicMock()
        english_changes_mock = MagicMock()

        # Configure the language info mock with three worksheets
        language_info_mock.language_code = "de"
        language_info_mock.worksheets = {
            "worksheet_with_changes_1": MagicMock(title="Worksheet 1"),
            "worksheet_with_changes_2": MagicMock(title="Worksheet 2"),
            "worksheet_no_changes": MagicMock(title="Worksheet 3"),
        }
        english_info_mock.worksheets = language_info_mock.worksheets

        # Configure has_relevant_change to return True for specific worksheets and False for others
        mock_has_relevant_change.side_effect = lambda ws, _: {
            "worksheet_with_changes_1": True,
            "worksheet_with_changes_2": True,
            "worksheet_no_changes": False
        }.get(ws, False)

        # Set up get_page_html behavior: None for "worksheet_with_changes_2" to simulate no content
        fortraininglib_mock.get_page_html.side_effect = lambda ws: None if "worksheet_with_changes_2" in ws \
                                                                        else "<html>Some content</html>"

        # Configure mock for CustomBeautifyHTML's process_html method
        beautifyhtml_instance = MockBeautifyHTML.return_value
        beautifyhtml_instance.process_html.return_value = "<p>Processed HTML content</p>"

        # Initialize ExportHTML with valid folder and force_rewrite = False
        export_html = ExportHTML(fortraininglib_mock, "/mocked/path", force_rewrite=False)

        with self.assertLogs('pywikitools.resourcesbot.export_html', level='INFO') as log:
            # Run `run` method
            export_html.run(language_info_mock, english_info_mock, changes_mock, english_changes_mock)

        # Verify get_page_html was called only for the two worksheets with relevant changes
        fortraininglib_mock.get_page_html.assert_any_call("worksheet_with_changes_1/de")
        fortraininglib_mock.get_page_html.assert_any_call("worksheet_with_changes_2/de")
        self.assertEqual(fortraininglib_mock.get_page_html.call_count, 2)

        # Verify warning was logged for the worksheet with no content
        self.assertTrue(any("Couldn't get content of worksheet_with_changes_2/de. Skipping" in message for message in log.output))

        # Check that content was written for the first worksheet and contents.json
        self.assertEqual(mock_open().write.call_count, 2)

        # Assert that the first call to write was for the HTML content
        mock_open().write.assert_any_call("<h1>Worksheet 1</h1><p>Processed HTML content</p>")

        # Assert that the second call to write was for contents.json
        mock_open().write.assert_any_call("{}")

        # Verify that the html_counter was incremented correctly
        expected_log_message = "pywikitools.resourcesbot.export_html:ExportHTML de: Downloaded 1 HTML files, 0 images"
        self.assertTrue(
            any(expected_log_message in message for message in log.output),
            f"Expected log message not found. Log output: {log.output}"
        )


if __name__ == '__main__':
    unittest.main()
