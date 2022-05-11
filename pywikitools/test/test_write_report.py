import json
from os.path import abspath, dirname, join
import unittest
from unittest.mock import patch
from pywikitools.resourcesbot.changes import ChangeLog

from pywikitools.resourcesbot.data_structures import LanguageInfo, json_decode
from pywikitools.resourcesbot.write_report import WriteReport


class TestWriteReport(unittest.TestCase):
    def setUp(self):
        with open(join(dirname(abspath(__file__)), "data", "ru.json"), 'r') as f:
            self.language_info = json.load(f, object_hook=json_decode)
        with open(join(dirname(abspath(__file__)), "data", "en.json"), 'r') as f:
            self.english_info = json.load(f, object_hook=json_decode)

    def test_created_mediawiki(self):
        # Compare mediawiki output with the content in data/ru_worksheet_overview.mediawiki
        write_report = WriteReport(None)
        with open(join(dirname(abspath(__file__)), "data", "ru_worksheet_overview.mediawiki"), 'r') as f:
            expected_mediawiki = f.read()
            self.assertEqual(write_report.create_worksheet_overview(self.language_info, self.english_info),
                             expected_mediawiki)
            self.assertIn(expected_mediawiki, write_report.create_mediawiki(self.language_info, self.english_info))

    @patch("pywikibot.Page")
    def test_save_language_report(self, mock_page):
        write_report = WriteReport(None)
        # When there is no proper language name, save_language_report() should directly exit
        with self.assertLogs("pywikitools.resourcesbot.write_report", level="WARNING"):
            write_report.save_language_report(LanguageInfo("de", ""), self.english_info)
        mock_page.return_value.exists.assert_not_called()

        # Language report should get created if it doesn't exist
        mock_page.return_value.exists.return_value = False
        with self.assertLogs("pywikitools.resourcesbot.write_report", level="WARNING"):
            write_report.save_language_report(self.language_info, self.english_info)
        mock_page.return_value.save.assert_called_with("Created language report")

        # Language report should get updated if there are changes
        mock_page.return_value.exists.return_value = True
        mock_page.return_value.text = "different"
        write_report.save_language_report(self.language_info, self.english_info)
        mock_page.return_value.save.assert_called_with("Updated language report")

    @patch("pywikitools.resourcesbot.write_report.WriteReport.save_language_report")
    def test_run(self, mock_save):
        # run() should abort with warning if we don't provide English language info
        write_report = WriteReport(None)
        language_data = {"ru": self.language_info}
        changes = {"ru": ChangeLog()}
        with self.assertLogs("pywikitools.resourcesbot.write_report", level="WARNING"):
            write_report.run(language_data, changes)
        mock_save.assert_not_called()

        # save_language_report() shouldn't get called when there are no changes
        language_data = {"en": self.english_info, "ru": self.language_info}
        changes = {"en": ChangeLog(), "ru": ChangeLog()}
        write_report.run(language_data, changes)
        mock_save.assert_not_called()

        # save_language_report() should be called once (for Russian) when we have force_rewrite
        write_report = WriteReport(None, force_rewrite=True)
        write_report.run(language_data, changes)
        mock_save.assert_called_once()


if __name__ == '__main__':
    unittest.main()
