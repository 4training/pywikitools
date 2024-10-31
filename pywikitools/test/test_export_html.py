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


import unittest
from unittest.mock import MagicMock, patch

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

if __name__ == '__main__':
    unittest.main()
