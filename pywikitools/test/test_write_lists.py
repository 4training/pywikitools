import json
from os.path import abspath, dirname, join
import unittest
from unittest.mock import patch
from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog, ChangeType

from pywikitools.resourcesbot.data_structures import FileInfo, LanguageInfo, json_decode
from pywikitools.resourcesbot.write_lists import WriteList
from pywikitools.test.test_data_structures import TEST_URL


class TestWriteList(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        with self.assertLogs('pywikitools.resourcesbot.write_lists', level="WARNING"):
            self.write_list = WriteList(ForTrainingLib("https://www.4training.net"), None, "", "")
        with open(join(dirname(abspath(__file__)), "data", "ru.json"), 'r') as f:
            self.language_info: LanguageInfo = json.load(f, object_hook=json_decode)

    def test_force_rewrite(self):
        with self.assertLogs('pywikitools.resourcesbot.write_lists', level="WARNING"):
            write_list = WriteList(ForTrainingLib("https://www.4training.net"), None, "", "", force_rewrite=True)
        self.assertTrue(write_list.needs_rewrite(LanguageInfo("ru", "Russian"), ChangeLog()))
        self.assertFalse(self.write_list.needs_rewrite(LanguageInfo("ru", "Russian"), ChangeLog()))

    def test_needs_rewrite(self):
        change_log = ChangeLog()
        self.assertFalse(self.write_list.needs_rewrite(self.language_info, change_log))
        change_log.add_change("Time_with_God", ChangeType.NEW_ODT)
        self.assertFalse(self.write_list.needs_rewrite(self.language_info, change_log))
        change_log.add_change("Church", ChangeType.DELETED_ODT)
        self.assertFalse(self.write_list.needs_rewrite(self.language_info, change_log))
        change_log.add_change("My_Story_with_God", ChangeType.DELETED_ODT)
        self.assertTrue(self.write_list.needs_rewrite(self.language_info, change_log))
        change_log = ChangeLog()
        change_log.add_change("Healing", ChangeType.UPDATED_WORKSHEET)
        self.assertFalse(self.write_list.needs_rewrite(self.language_info, change_log))
        change_log.add_change("Time_with_God", ChangeType.NEW_PDF)
        self.assertTrue(self.write_list.needs_rewrite(self.language_info, change_log))
        change_log = ChangeLog()
        change_log.add_change("Dealing_with_Money", ChangeType.NEW_WORKSHEET)
        self.assertTrue(self.write_list.needs_rewrite(self.language_info, change_log))

    def test_create_file_mediawiki(self):
        pdf_mediawiki = r" [[File:pdficon_small.png|link={{filepath:Gottes_Reden_wahrnehmen.pdf}}]]"
        file_info = FileInfo("pdf", TEST_URL, "2018-12-23T13:11:23+00:00")
        # Should return empty string if file_info is None
        self.assertEqual(self.write_list._create_file_mediawiki(None), "")
        # Test a "normal" call
        self.assertEqual(self.write_list._create_file_mediawiki(file_info), pdf_mediawiki)
        # Test for robust handling if URL is just a filename
        file_info = FileInfo("pdf", "Gottes_Reden_wahrnehmen.pdf", "2018-12-23T13:11:23+00:00")
        with self.assertLogs('pywikitools.resourcesbot.write_lists', level="WARNING"):
            self.assertEqual(self.write_list._create_file_mediawiki(file_info), pdf_mediawiki)

    def test_create_mediawiki(self):
        """Test creation of the list of available resources for a language"""
        # Read the expected result and compare it
        with open(join(dirname(abspath(__file__)), "data", "Russian_resources_list.mediawiki"), 'r') as f:
            # using assertLogs() just to remove any logs from the test output
            with self.assertLogs('pywikitools.resourcesbot.write_lists', level="DEBUG"):
                self.assertEqual(self.write_list.create_mediawiki(self.language_info), f.read())

    @patch("pywikibot.Page")
    def test_run_edge_cases(self, mock_page):
        # run() should return directly if there are no changes
        changes = ChangeLog()
        self.write_list.run(self.language_info, changes)
        mock_page.assert_not_called()

        # run() should warn and directly return if there language name is missing in LanguageInfo
        problematic_language_info = LanguageInfo("de", "")
        changes.add_change("Prayer", ChangeType.NEW_WORKSHEET)   # we need a relevant change
        with self.assertLogs('pywikitools.resourcesbot.write_lists', level="WARNING"):
            self.write_list.run(problematic_language_info, changes)
        mock_page.return_value.exists.assert_not_called()

        # run() should warn and return if there is no language information page
        # (has the same name as LanguageInfo.english_name)
        not_existing_language_info = LanguageInfo("none", "NotExisting")
        mock_page.return_value.exists.return_value = False
        with self.assertLogs('pywikitools.resourcesbot.write_lists', level="WARNING"):
            self.write_list.run(not_existing_language_info, changes)
        mock_page.return_value.exists.assert_called_once()
        mock_page.return_value.isRedirectPage.assert_not_called()

        # run() should warn and return if language information page is redirect but the redirect target doesn't exist
        mock_page.return_value.exists.return_value = True
        mock_page.return_value.isRedirectPage.return_value = True
        mock_page.return_value.getRedirectTarget.return_value.exists.return_value = False
        with self.assertLogs('pywikitools.resourcesbot.write_lists', level="WARNING"):
            self.write_list.run(not_existing_language_info, changes)
        mock_page.return_value.text.assert_not_called()


if __name__ == '__main__':
    unittest.main()
