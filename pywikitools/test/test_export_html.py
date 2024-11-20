"""
Test all the functionalities of export_html.py
- creating folders if necessary
- get html contents for worksheets from API
- Export htmls into local directory
- download image files into local directory
- export content.json (with current content)

Run tests:
    python3  python3 -m unittest pywikitools/test/test_export_html.py
"""

import os
from os.path import abspath, dirname, join
import tempfile
import json
import unittest

import requests
from unittest.mock import Mock, patch

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
        self.changelog = ChangeLog()
        self.changelog.add_change('Healing', 'updated worksheet')
        self.changelog.add_change("Church", 'new worksheet')
        with open(join(dirname(abspath(__file__)), "data", "example.html"), 'r') as f:
            self.html_content = f.read()

        self.response = requests.Response()
        self.response.status_code = 200  # Setze einen Statuscode
        with open(join(dirname(abspath(__file__)), "data", "Hand_1.png"), 'rb') as f:
            self.response._content = f.read()

        temp_dir = tempfile.TemporaryDirectory()
        self.perm_temp_dir = temp_dir

    def mock_get_page_html(self, arg):
        return self.html_content

    @patch("os.makedirs")
    def test_run_with_empty_base_folder(self, mock_makedirs):
        with self.assertLogs('pywikitools.resourcesbot.export_html', level='WARNING'):
            export_html = ExportHTML(self.fortraininglib, "", force_rewrite=False)

        # run() should return without doing anything because of empty base folder
        export_html.run(self.language_info, self.english_info, ChangeLog(), ChangeLog())
        mock_makedirs.assert_not_called()

    def test_run_filters_unfinished_worksheets(self):
        fortraininglib_mock = Mock()
        export_html = ExportHTML(fortraininglib_mock, self.perm_temp_dir.name, force_rewrite=False)
        with patch.object(export_html, 'has_relevant_change', return_value=False) as mock_has_relevant_change:
            export_html.run(self.language_info, self.english_info, ChangeLog(), ChangeLog())
            calls = [call[0][0] for call in mock_has_relevant_change.call_args_list]
            # Healing is finished, Church is an unfinished worksheet
            self.assertIn('Healing', calls)
            self.assertNotIn('Church', calls)

        fortraininglib_mock.get_page_html.assert_not_called()
        # Verify that `language_info` remains unchanged
        self.assertIsNotNone(self.language_info.get_worksheet('Church'))

    # Just for debugging-purposes...
    def print_folder_structure(self, start_path, indent=0):
        for root, dirs, files in os.walk(start_path):
            level = root.replace(start_path, "").count(os.sep) + indent
            indent_str = " " * (level * 4)
            print(f"{indent_str}- {os.path.basename(root)}/")
            sub_indent_str = " " * ((level + 1) * 4)
            for file in files:
                print(f"{sub_indent_str}- {file}")

    def test_directory_structure_creation(self):

        # Initialize the ExportHTML class with a valid base folder
        with tempfile.TemporaryDirectory() as temp_dir:

            # Create target paths to check later
            folder = os.path.join(temp_dir, "base")
            main_folder = os.path.join(folder, "ru")
            files_folder = os.path.join(main_folder, "files/")
            structure_folder = os.path.join(main_folder, "structure/")

            # At object creation, the main folder should be created.
            export_html = ExportHTML(self.fortraininglib, folder, force_rewrite=False)
            self.assertTrue(os.path.exists(folder), f"Pfad existiert nicht: {folder}")
            export_html.run(self.language_info, self.english_info, ChangeLog(), ChangeLog())

            # Assert that the right directories were created
            self.assertTrue(os.path.exists(main_folder), f"Pfad existiert nicht: {main_folder}")
            self.assertTrue(os.path.exists(files_folder), f"Pfad existiert nicht: {files_folder}")
            self.assertTrue(os.path.exists(structure_folder), f"Pfad existiert nicht: {structure_folder}")

            # assert that the method still works if the folders are already there
            # currently errors are captured directly in the run methods and therefore dont show in this test
            export_html.run(self.language_info, self.english_info, ChangeLog(), ChangeLog())

    def test_download_and_save_transformed_html_and_images(self):

        fortraininglib_mock = Mock()
        fortraininglib_mock.get_page_html.side_effect = self.mock_get_page_html

        # Initialize the ExportHTML class with a valid base folder
        with tempfile.TemporaryDirectory() as temp_dir:
            export_html = ExportHTML(fortraininglib_mock, temp_dir, force_rewrite=False)

            with patch('requests.get', return_value=self.response):
                export_html.run(self.language_info, self.english_info, self.changelog, ChangeLog())

            # Assert the file was created correctly
            path_to_transformed_html = os.path.join(temp_dir, 'ru', 'Исцеление.html')
            self.assertTrue(os.path.exists(path_to_transformed_html), "The html is not in the expected location.")

            # Assert the content is correct
            with open(path_to_transformed_html, 'r', encoding='utf-8') as test_file:
                test_content = test_file.read()
            path_to_template_html = os.path.join(dirname(abspath(__file__)), "data", "correct_transformed_html.html")
            with open(path_to_template_html, 'r', encoding='utf-8') as template_file:
                template_content = template_file.read()
            self.assertEqual(template_content, test_content,
                             "The content of the saved html is different than expected.")

            path_to_image = os.path.join(temp_dir, 'ru', 'files', 'Hand_1.png')
            self.assertTrue(os.path.exists(path_to_image), 'Downloaded image missing.')

            path_to_contents = os.path.join(temp_dir, 'ru', 'structure', 'contents.json')
            self.assertTrue(os.path.exists(path_to_contents), 'Contents.json not found.')
            with open(path_to_contents, 'r') as f:
                with open(os.path.join(dirname(abspath(__file__)), "data", 'template_content.json'), 'r') as g:
                    self.assertEqual(g.read(), f.read(), 'Wrong content in contents.json')

    # TODO create overall test with real objects, testing everything at once.
    def test_complex_export_html(self):

        # Setup complex Test-Objects
        ar_changelog = ChangeLog()
        ar_changelog.add_change('A_Daily_Prayer', 'updated worksheet')  # normal worksheet
        ar_changelog.add_change('Time_with_God', 'updated worksheet')  # worksheet with images
        ar_changelog.add_change("Church", 'new worksheet')  # unfinished -> shouldn't be exported

        with open(join(dirname(abspath(__file__)), "data", "ar.json"), 'r') as f:
            ar_language_info: LanguageInfo = json.load(f, object_hook=json_decode)
        with open(join(dirname(abspath(__file__)), "data", "en.json"), 'r') as f:
            en_language_info: LanguageInfo = json.load(f, object_hook=json_decode)

        export_html = ExportHTML(self.fortraininglib, self.perm_temp_dir.name, force_rewrite=False)
        try:
            export_html.run(ar_language_info, en_language_info, ar_changelog, ChangeLog())
        except Exception as e:
            print(f"Connection error occurred: {e}")
            raise AssertionError(f"Test failed due to connection error: {e}")

        path_to_transformed_html1 = os.path.join(self.perm_temp_dir.name, 'ar', 'قضاء_وقت_مع_الله.html')
        path_to_transformed_html2 = os.path.join(self.perm_temp_dir.name, 'ar', 'الصلاة_اليومية.html')
        path_to_image = os.path.join(self.perm_temp_dir.name, 'ar', 'files', 'Head-32.png')
        self.assertTrue(os.path.exists(path_to_image), 'Downloaded image missing.')
        self.assertTrue(os.path.exists(path_to_transformed_html1), "The html is not in the expected location.")
        self.assertTrue(os.path.exists(path_to_transformed_html2), "The html is not in the expected location.")

        # run with force rewrite
        export_html_fr = ExportHTML(self.fortraininglib, self.perm_temp_dir.name, force_rewrite=True)
        try:
            export_html_fr.run(ar_language_info, en_language_info, ar_changelog, ChangeLog())
        except Exception as e:
            print(f"Connection error occurred: {e}")
            raise AssertionError(f"Test failed due to connection error: {e}")

        path_to_transformed_html3 = os.path.join(self.perm_temp_dir.name, 'ar', 'الصلاة.html')
        self.assertTrue(os.path.exists(path_to_transformed_html3), "The html is not in the expected location.")


if __name__ == '__main__':
    unittest.main()
