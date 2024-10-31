import json
from os.path import abspath, dirname, join
from typing import Dict
import unittest
from unittest.mock import patch
from pywikitools.resourcesbot.changes import ChangeLog, ChangeType

from pywikitools.resourcesbot.data_structures import LanguageInfo, json_decode
from pywikitools.resourcesbot.modules.write_summary import WriteSummary


class TestWriteSummary(unittest.TestCase):
    def setUp(self):
        self.language_data: Dict[str, LanguageInfo] = {}
        self.empty_change_log: Dict[str, ChangeLog] = {}
        # Load LanguageInfo for Russian, English, Spanish and Arabic so we have some meaningful data to run tests
        for language_code in ["en", "ru", "es", "ar"]:
            with open(join(dirname(abspath(__file__)), "data", f"{language_code}.json"), 'r') as f:
                self.language_data[language_code] = json.load(f, object_hook=json_decode)
            self.empty_change_log[language_code] = ChangeLog()

        self.write_summary = WriteSummary(None)

    def test_created_mediawiki(self):
        # Compare mediawiki output with the content in data/summary.mediawiki
        with open(join(dirname(abspath(__file__)), "data", "summary.mediawiki"), 'r') as f:
            expected_mediawiki = f.read()
            self.assertEqual(self.write_summary.create_language_overview(self.language_data), expected_mediawiki)
            self.assertIn(expected_mediawiki, self.write_summary.create_mediawiki(self.language_data))

    @patch("pywikibot.Page")
    def test_save_summary(self, mock_page):
        # When English LanguageInfo is missing, save_summary() should directly exit
        with self.assertLogs("pywikitools.resourcesbot.write_summary", level="WARNING"):
            self.write_summary.save_summary({})
        mock_page.return_value.exists.assert_not_called()

        # Summary report should get created if it doesn't exist
        mock_page.return_value.exists.return_value = False
        with self.assertLogs("pywikitools.resourcesbot.write_summary", level="WARNING"):
            self.write_summary.save_summary(self.language_data)
        mock_page.return_value.save.assert_called_with("Created summary report")

        # Summary report should get updated if there are changes
        mock_page.return_value.exists.return_value = True
        mock_page.return_value.text = "different"
        self.write_summary.save_summary(self.language_data)
        mock_page.return_value.save.assert_called_with("Updated summary report")

    @patch("pywikitools.resourcesbot.write_summary.WriteSummary.save_summary")
    def test_run(self, mock_save):
        # save_summary() shouldn't get called when there are no changes
        self.write_summary.run(self.language_data, self.empty_change_log)
        mock_save.assert_not_called()

        # save_summary() should get called when there is a change
        spanish_changes = ChangeLog()
        spanish_changes.add_change("Prayer", ChangeType.UPDATED_PDF)
        change_log = {"en": ChangeLog(), "ru": ChangeLog(), "ar": ChangeLog(), "es": spanish_changes}
        self.write_summary.run(self.language_data, change_log)
        mock_save.assert_called_once()

        # save_summary() should be called when we have force_rewrite (even if there are no changes)
        write_summary = WriteSummary(None, force_rewrite=True)
        write_summary.run(self.language_data, self.empty_change_log)
        self.assertEqual(mock_save.call_count, 2)


if __name__ == '__main__':
    unittest.main()
