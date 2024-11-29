"""
Test all the functionalities of export_pdf.py
- creating folders if necessary
- get pdf files for worksheets from API
- Export pdfs into local directory

Run tests:
    python3 pywikitools/test/test_export_pdf.py
"""

import unittest
from unittest.mock import Mock, patch
from configparser import ConfigParser
from os.path import abspath, dirname, join, exists
import json
import requests
import tempfile
from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog, ChangeType
from pywikitools.resourcesbot.data_structures import LanguageInfo, json_decode
from pywikitools.resourcesbot.modules.export_pdf import ExportPDF


class TestExportPDF(unittest.TestCase):
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
        empty_config = ConfigParser()
        with self.assertLogs('pywikitools.resourcesbot.modules.export_pdf', level='WARNING'):
            export_pdf = ExportPDF(self.fortraininglib, empty_config, None)

        # run() should return without doing anything because of empty base folder
        export_pdf.run(self.language_info, self.english_info, ChangeLog(), ChangeLog(), force_rewrite=False)
        mock_makedirs.assert_not_called()

    def test_run_filters_unfinished_worksheets(self):
        fortraininglib_mock = Mock()
        temp_config = ConfigParser()
        temp_config.add_section("Paths")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_config.set("Paths", "pdfexport", temp_dir)
            export_pdf = ExportPDF(fortraininglib_mock, temp_config, None)
            with patch.object(export_pdf, 'has_relevant_change', return_value=False) as mock_has_relevant_change:
                export_pdf.run(self.language_info, self.english_info, ChangeLog(), ChangeLog(), force_rewrite=False)
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
            config = ConfigParser()
            config.add_section("Paths")
            config.set("Paths", "pdfexport", base_folder)

            # Base folder should be created directly when initializing the class
            export_pdf = ExportPDF(self.fortraininglib, config, None)
            self.assertTrue(exists(base_folder))
            export_pdf.run(self.language_info, self.english_info, ChangeLog(), ChangeLog(), force_rewrite=False)

            # Assert that the right directories were created
            self.assertTrue(exists(join(base_folder, "ru")))

            # assert that the method still works if the folders are already there
            with self.assertNoLogs(level='WARNING'):
                export_pdf.run(self.language_info, self.english_info, ChangeLog(), ChangeLog(), force_rewrite=False)

    def test_download_and_save_transformed_html_and_images(self):
        changelog = ChangeLog()
        changelog.add_change('Healing', ChangeType.UPDATED_WORKSHEET)
        changelog.add_change("Church", ChangeType.NEW_WORKSHEET)

        config = ConfigParser()
        config.add_section("Paths")

        # Mock the response for the image download
        response = requests.Response()
        response.status_code = 200
        with open(join(dirname(abspath(__file__)), "data", "Исцеление.pdf"), 'rb') as f:
            response._content = f.read()

        # Initialize the ExportHTML class with a valid base folder
        with tempfile.TemporaryDirectory() as temp_dir:
            config.set("Paths", "pdfexport", temp_dir)
            export_pdf = ExportPDF(self.fortraininglib, config, None)

            with patch('requests.get', return_value=response):
                export_pdf.run(self.language_info, self.english_info, changelog, ChangeLog(), force_rewrite=False)

            # Assert the file was created correctly
            expected_path_to_pdf = join(temp_dir, 'ru', 'Исцеление.pdf')
            self.assertTrue(exists(expected_path_to_pdf))

            # Assert the content is correct
            expected_pdf = join(dirname(abspath(__file__)), "data", "Исцеление.pdf")
            with open(expected_path_to_pdf, 'rb') as test_file:
                with open(expected_pdf, 'rb') as expected_file:
                    self.assertEqual(test_file.read(), expected_file.read())

    def test_complex_export_pdf(self):
        config = ConfigParser()
        config.add_section("Paths")

        with tempfile.TemporaryDirectory() as temp_dir:
            config.set("Paths", "pdfexport", temp_dir)
            ar_changelog = ChangeLog()
            # normal worksheet
            ar_changelog.add_change('Hearing_from_God', ChangeType.UPDATED_WORKSHEET)
            expected_path_hearing = join(temp_dir, 'ar', 'الاستماع_من_الله.pdf')
            # worksheet with images
            ar_changelog.add_change('Time_with_God', ChangeType.UPDATED_WORKSHEET)
            expected_path_time = join(temp_dir, 'ar', 'قضاء_وقت_مع_الله.pdf')
            # unfinished worksheet -> shouldn't be exported
            ar_changelog.add_change("Church", ChangeType.NEW_WORKSHEET)
            expected_path_church = join(temp_dir, 'ar', 'كنيسة.pdf')
            # normal worksheet -> will only be created with force rewrite
            expected_path_prayer = join(temp_dir, 'ar', 'الصلاة.pdf')

            with open(join(dirname(abspath(__file__)), "data", "ar.json"), 'r') as f:
                ar_language_info: LanguageInfo = json.load(f, object_hook=json_decode)
            with open(join(dirname(abspath(__file__)), "data", "en.json"), 'r') as f:
                en_language_info: LanguageInfo = json.load(f, object_hook=json_decode)

            export_pdf = ExportPDF(self.fortraininglib, config, None)
            export_pdf.run(ar_language_info, en_language_info, ar_changelog, ChangeLog(), force_rewrite=False)

            self.assertTrue(exists(expected_path_hearing))
            self.assertTrue(exists(expected_path_time))
            self.assertFalse(exists(expected_path_church))

            # run with force rewrite
            self.assertFalse(exists(expected_path_prayer))
            with self.assertLogs():
                export_pdf.run(ar_language_info, en_language_info, ar_changelog, ChangeLog(), force_rewrite=True)
            self.assertTrue(exists(expected_path_prayer))


if __name__ == '__main__':
    unittest.main()
