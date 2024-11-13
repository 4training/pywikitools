"""
Test all the functionalities of export_html.py
- creating folders if necessary
- get html contents for worksheets from API
- Export htmls into local directory
TODO download image files into local directory
TODO export content.json (with current content)

Run tests:
    python3  python3 -m unittest pywikitools/test/test_export_html.py
"""

import os
from os.path import abspath, dirname, join
import json
import unittest
from unittest.mock import MagicMock, Mock, patch, mock_open

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import LanguageInfo, json_decode
from pywikitools.resourcesbot.export_html import ExportHTML


class TestExportHTML(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        with open(join(dirname(abspath(__file__)), "data", "ru.json"), 'r') as f:
            self.language_info: LanguageInfo = json.load(f, object_hook=json_decode)
        # Create a pseudo English LanguageInfo - enough for our testing purposes (version is always the same)
        self.english_info = LanguageInfo("en", "English")
        for worksheet, info in self.language_info.worksheets.items():
            self.english_info.add_worksheet_info(worksheet, info)
        self.fortraininglib = ForTrainingLib("https://test.4training.net")

    @patch("os.makedirs")
    def test_run_with_empty_base_folder(self, mock_makedirs):
        with self.assertLogs('pywikitools.resourcesbot.export_html', level='WARNING'):
            export_html = ExportHTML(self.fortraininglib, "", force_rewrite=False)

        # run() should return without doing anything because of empty base folder
        export_html.run(self.language_info, self.english_info, ChangeLog(), ChangeLog())
        mock_makedirs.assert_not_called()

    @patch("os.makedirs")
    def test_run_filters_unfinished_worksheets(self, mock_makedirs):
        fortraininglib_mock = Mock()
        export_html = ExportHTML(fortraininglib_mock, "/mocked/path", force_rewrite=False)
        with patch.object(export_html, 'has_relevant_change', return_value=False) as mock_has_relevant_change:
            export_html.run(self.language_info, self.english_info, ChangeLog(), ChangeLog())
            calls = [call[0][0] for call in mock_has_relevant_change.call_args_list]
            # Healing is finished, Church is an unfinished worksheet
            self.assertIn('Healing', calls)
            self.assertNotIn('Church', calls)

        fortraininglib_mock.get_page_html.assert_not_called()
        # Verify that `language_info` remains unchanged
        self.assertIsNotNone(self.language_info.get_worksheet('Church'))

    @patch("os.makedirs")  # Mock os.makedirs to prevent actual directory creation
    @patch("os.path.isdir", return_value=False)  # Mock os.path.isdir to simulate directory absence
    def test_directory_structure_creation(self, mock_isdir, mock_makedirs):
        # TODO: use tempfile, create a temp directory and let ExportHTML create the directory structure
        # TODO use tempfile, create a temp directory with subdirectories and make sure ExportHTML doesn't complain

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

    @patch("pywikitools.resourcesbot.export_html.ExportHTML.download_file",
           return_value=True)  # Mock für die download_file-Methode
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")  # Mock directory creation if needed
    @patch("pywikitools.resourcesbot.export_html.ExportHTML.has_relevant_change")
    @patch("pywikitools.resourcesbot.export_html.CustomBeautifyHTML")
    @patch("pywikitools.resourcesbot.export_html.StructureEncoder.encode", return_value="{}")
    def test_download_and_save_transformed_html_and_images(self, mock_encode, MockBeautifyHTML,
                                                           mock_has_relevant_change, mock_makedirs, mock_open,
                                                           mock_download_file):

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

        # Add files to the file collector (would normally be found by BeautifyHTML)
        def sideeffect(change_hrefs, file_collector):
            file_collector.add("image1.png")
            file_collector.add("image2.png")
            return MockBeautifyHTML.return_value

        # Configure mock for CustomBeautifyHTML's process_html method
        beautifyhtml_instance = MockBeautifyHTML.return_value
        beautifyhtml_instance.process_html.return_value = "<p>Processed HTML content</p>"
        MockBeautifyHTML.side_effect = sideeffect

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
        self.assertTrue(
            any("Couldn't get content of worksheet_with_changes_2/de. Skipping" in message for message in log.output))

        # Check that content was written for the first worksheet and contents.json
        self.assertEqual(mock_open().write.call_count, 2)

        # Assert that the first call to write was for the HTML content
        mock_open().write.assert_any_call("<h1>Worksheet 1</h1><p>Processed HTML content</p>")

        # Assert that the second call to write was for contents.json
        mock_open().write.assert_any_call("{}")

        # Verify that the html_counter was incremented correctly
        expected_log_message = "pywikitools.resourcesbot.export_html:ExportHTML de: Downloaded 1 HTML files, 2 images"
        self.assertTrue(
            any(expected_log_message in message for message in log.output),
            f"Expected log message not found. Log output: {log.output}"
        )

        # Check that download_file was called for both image1.png and image2.png
        mock_download_file.assert_any_call("/mocked/path/de/files/", "image1.png")
        mock_download_file.assert_any_call("/mocked/path/de/files/", "image2.png")
        self.assertEqual(mock_download_file.call_count, 2)

    @patch("pywikitools.resourcesbot.export_html.StructureEncoder.encode", return_value='{"key": "value"}')
    @patch("builtins.open", new_callable=mock_open)  # Mock the open function
    @patch("os.makedirs")  # Mock directory creation
    def test_writes_contents_json(self, mock_makedirs, mock_open, mock_encode):
        # Test if the contents json is being created

        # Create mock objects for required parameters
        fortraininglib_mock = MagicMock()
        lang_info_mock = MagicMock()
        english_info_mock = MagicMock()
        changes_mock = MagicMock()
        english_changes_mock = MagicMock()

        # Set the language_code and worksheets so the flow proceeds as expected
        lang_info_mock.language_code = "de"
        lang_info_mock.worksheets = {
            "worksheet_with_changes_1": MagicMock(title="Worksheet 1")  # Set a title as a string
        }

        # Mock the `get_page_html` method to return valid HTML content for testing
        fortraininglib_mock.get_page_html.return_value = "<html><div class='mw-parser-output'>Some content</div></html>"

        # Create the ExportHTML instance and set _force_rewrite=True to ensure contents.json is written
        export_html = ExportHTML(fortraininglib_mock, "/mocked/path", force_rewrite=True)

        # Run the `run` method
        export_html.run(lang_info_mock, english_info_mock, changes_mock, english_changes_mock)

        # Verify StructureEncoder.encode was called
        mock_encode.assert_called_once_with(lang_info_mock)

        # Verify the contents.json file was written with the correct JSON content
        mock_open.assert_any_call("/mocked/path/de/structure/contents.json", "w")
        mock_open().write.assert_any_call(json.dumps({"key": "value"}, indent=4))


if __name__ == '__main__':
    unittest.main()
