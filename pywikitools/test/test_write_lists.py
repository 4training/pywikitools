import json
from os.path import abspath, dirname, join
import unittest
from pywikitools.resourcesbot.changes import ChangeLog, ChangeType

from pywikitools.resourcesbot.data_structures import FileInfo, LanguageInfo, json_decode
from pywikitools.resourcesbot.write_lists import WriteList
from pywikitools.test.test_data_structures import TEST_URL

class TestWriteList(unittest.TestCase):
    def setUp(self):
        with self.assertLogs('pywikitools.resourcesbot.write_lists', level="WARNING"):
            self.write_list = WriteList(None, "", "")

    def test_force_rewrite(self):
        with self.assertLogs('pywikitools.resourcesbot.write_lists', level="WARNING"):
            write_list = WriteList(None, "", "", force_rewrite=True)
        self.assertTrue(write_list.needs_rewrite(LanguageInfo("ru"), ChangeLog()))
        self.assertFalse(self.write_list.needs_rewrite(LanguageInfo("ru"), ChangeLog()))

    def test_needs_rewrite(self):
        with open(join(dirname(abspath(__file__)), "data", "ru.json"), 'r') as f:
            language_info = json.load(f, object_hook=json_decode)
        change_log = ChangeLog()
        self.assertFalse(self.write_list.needs_rewrite(language_info, change_log))
        change_log.add_change("Time_with_God", ChangeType.NEW_ODT)
        self.assertFalse(self.write_list.needs_rewrite(language_info, change_log))
        change_log.add_change("Forgiving_Step_by_Step", ChangeType.DELETED_ODT)
        self.assertTrue(self.write_list.needs_rewrite(language_info, change_log))
        change_log = ChangeLog()
        change_log.add_change("Healing", ChangeType.UPDATED_WORKSHEET)
        self.assertFalse(self.write_list.needs_rewrite(language_info, change_log))
        change_log.add_change("Time_with_God", ChangeType.NEW_PDF)
        self.assertTrue(self.write_list.needs_rewrite(language_info, change_log))
        change_log = ChangeLog()
        change_log.add_change("Dealing_with_Money", ChangeType.NEW_WORKSHEET)
        self.assertTrue(self.write_list.needs_rewrite(language_info, change_log))

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
        with self.assertLogs('pywikitools.resourcesbot.write_lists', level="WARNING"):
            write_list = WriteList(None, "", "")
        with open(join(dirname(abspath(__file__)), "data", "ru.json"), 'r') as f:
            language_info = json.load(f, object_hook=json_decode)
        # Read the expected result and compare it
        with open(join(dirname(abspath(__file__)), "data", "Russian_resources_list.mediawiki"), 'r') as f:
            # using assertLogs() just to remove any logs from the test output
            with self.assertLogs('pywikitools.resourcesbot.write_lists', level="DEBUG"):
                self.assertEqual(self.write_list.create_mediawiki(language_info), f.read())


if __name__ == '__main__':
    unittest.main()
