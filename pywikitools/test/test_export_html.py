"""
Test all the functionalities of export_html.py
- creating folders if necessary
- get html contents for worksheets from API
- Export htmls into local directory
- download image files into local directory
- export content.json (with current content)

Run tests:
    python3 pywikitools/test/test_export_html.py
"""

from os.path import abspath, dirname, join, exists
import tempfile
import json
import unittest

import requests
from unittest.mock import Mock, patch

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog, ChangeType
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

    def test_run_filters_unfinished_worksheets(self):
        fortraininglib_mock = Mock()
        with tempfile.TemporaryDirectory() as temp_dir:
            export_html = ExportHTML(fortraininglib_mock, temp_dir, force_rewrite=False)
            with patch.object(export_html, 'has_relevant_change', return_value=False) as mock_has_relevant_change:
                export_html.run(self.language_info, self.english_info, ChangeLog(), ChangeLog())
                calls = [call[0][0] for call in mock_has_relevant_change.call_args_list]
                # Healing is finished, Church is an unfinished worksheet
                self.assertIn('Healing', calls)
                self.assertNotIn('Church', calls)

            fortraininglib_mock.get_page_html.assert_not_called()
            # Verify that `language_info` remains unchanged
            self.assertIsNotNone(self.language_info.get_worksheet('Church'))

    def test_directory_structure_creation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create target paths to check later
            base_folder = join(temp_dir, "not_existing_yet")

            # Base folder should be created directly when initializing the class
            export_html = ExportHTML(self.fortraininglib, base_folder, force_rewrite=False)
            self.assertTrue(exists(base_folder))
            export_html.run(self.language_info, self.english_info, ChangeLog(), ChangeLog())

            # Assert that the right directories were created
            self.assertTrue(exists(join(base_folder, "ru")))
            self.assertTrue(exists(join(base_folder, "ru", "files/")))
            self.assertTrue(exists(join(base_folder, "ru", "structure/")))

            # assert that the method still works if the folders are already there
            with self.assertNoLogs(level='WARNING'):
                export_html.run(self.language_info, self.english_info, ChangeLog(), ChangeLog())

    @patch('pywikitools.fortraininglib.ForTrainingLib.get_page_html')
    def test_download_and_save_transformed_html_and_images(self, mock_get_page_html):
        with open(join(dirname(abspath(__file__)), "data", "example.html"), 'r') as f:
            mock_get_page_html.return_value = f.read()
        changelog = ChangeLog()
        changelog.add_change('Healing', ChangeType.UPDATED_WORKSHEET)
        changelog.add_change("Church", ChangeType.NEW_WORKSHEET)

        # Mock the response for the image download
        response = requests.Response()
        response.status_code = 200
        with open(join(dirname(abspath(__file__)), "data", "Heart-32.png"), 'rb') as f:
            response._content = f.read()

        # Initialize the ExportHTML class with a valid base folder
        with tempfile.TemporaryDirectory() as temp_dir:
            export_html = ExportHTML(self.fortraininglib, temp_dir, force_rewrite=False)

            with patch('requests.get', return_value=response):
                export_html.run(self.language_info, self.english_info, changelog, ChangeLog())

            # Assert the file was created correctly
            path_to_transformed_html = join(temp_dir, 'ru', 'Исцеление.html')
            self.assertTrue(exists(path_to_transformed_html))

            # Assert the content is correct
            expected_html = join(dirname(abspath(__file__)), "data", "htmlexport", "ru", "files", "Исцеление.html")
            with open(path_to_transformed_html, 'r', encoding='utf-8') as test_file:
                with open(expected_html, 'r', encoding='utf-8') as expected_file:
                    self.assertEqual(test_file.read(), expected_file.read())

            self.assertTrue(exists(join(temp_dir, 'ru', 'files', 'Heart-32.png')))

            path_to_contents = join(temp_dir, 'ru', 'structure', 'contents.json')
            self.assertTrue(exists(path_to_contents))
            with open(path_to_contents, 'r') as test_file:
                with open(join(dirname(abspath(__file__)),
                               "data", "htmlexport", "ru", "structure", "content.json"), 'r') as expected_file:
                    self.assertEqual(expected_file.read(), test_file.read())

    def test_complex_export_html(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ar_changelog = ChangeLog()
            # normal worksheet
            ar_changelog.add_change('Hearing_from_God', ChangeType.UPDATED_WORKSHEET)
            expected_path_hearing = join(temp_dir, 'ar', 'الاستماع_من_الله.html')
            # worksheet with images
            ar_changelog.add_change('Time_with_God', ChangeType.UPDATED_WORKSHEET)
            expected_path_time = join(temp_dir, 'ar', 'قضاء_وقت_مع_الله.html')
            # unfinished worksheet -> shouldn't be exported
            ar_changelog.add_change("Church", ChangeType.NEW_WORKSHEET)
            expected_path_church = join(temp_dir, 'ar', 'كنيسة.html')
            # normal worksheet -> will only be created with force rewrite
            expected_path_prayer = join(temp_dir, 'ar', 'الصلاة.html')

            with open(join(dirname(abspath(__file__)), "data", "ar.json"), 'r') as f:
                ar_language_info: LanguageInfo = json.load(f, object_hook=json_decode)
            with open(join(dirname(abspath(__file__)), "data", "en.json"), 'r') as f:
                en_language_info: LanguageInfo = json.load(f, object_hook=json_decode)

            export_html = ExportHTML(self.fortraininglib, temp_dir, force_rewrite=False)
            export_html.run(ar_language_info, en_language_info, ar_changelog, ChangeLog())

            self.assertTrue(exists(join(temp_dir, 'ar', 'files', 'Head-32.png')))
            self.assertTrue(exists(expected_path_hearing))
            self.assertTrue(exists(expected_path_time))
            self.assertFalse(exists(expected_path_church))

            # run with force rewrite
            self.assertFalse(exists(expected_path_prayer))
            export_html = ExportHTML(self.fortraininglib, temp_dir, force_rewrite=True)
            with self.assertLogs():
                export_html.run(ar_language_info, en_language_info, ar_changelog, ChangeLog())
            self.assertTrue(exists(expected_path_prayer))


if __name__ == '__main__':
    unittest.main()
