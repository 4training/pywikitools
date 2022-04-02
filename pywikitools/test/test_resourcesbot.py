"""
Testing ResourcesBot

Currently we have only little test coverage...
TODO: Find ways to run meaningful tests that don't take too long...
"""
from configparser import ConfigParser
from datetime import datetime
import unittest
from unittest.mock import patch

import pywikibot

from pywikitools.resourcesbot.bot import ResourcesBot
from pywikitools.resourcesbot.data_structures import TranslationProgress, WorksheetInfo
from pywikitools.test.test_data_structures import TEST_PROGRESS, TEST_TIME, TEST_URL

HEARING_FROM_GOD = """[...]
<translate>This is the end of the mediawiki source of the Hearing from God worksheet...</translate>
{{PdfDownload|<translate><!--T:52--> Hearing_from_God.pdf</translate>}}
{{OdtDownload|<translate><!--T:53--> Hearing_from_God.odt</translate>}}
{{Version|<translate><!--T:55--> 1.2</translate>}}
"""

class TestResourcesBot(unittest.TestCase):
    """
    We mock pywikibot because otherwise we would need to provide a valid user-config.py (and because it saves time)
    """

    def setUp(self):
        self.config = ConfigParser()
        self.config.read_dict({"Paths": {"logs": "~/"}}) # Fill this to prevent a warning
        self.bot = ResourcesBot(self.config)

    @patch("pywikibot.FilePage")
    def test_add_english_file_infos(self, mock_filepage):
        mock_filepage.return_value.exists.return_value = True
        mock_filepage.return_value.latest_file_info.url = TEST_URL
        mock_filepage.return_value.latest_file_info.timestamp = datetime.fromisoformat(TEST_TIME)

        progress = TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Hearing_from_God", "en", "Hearing from God", progress, "1.2")
        self.bot._add_english_file_infos(HEARING_FROM_GOD, worksheet_info)
        self.assertTrue(worksheet_info.has_file_type("pdf"))
        self.assertTrue(worksheet_info.has_file_type("odt"))

        # Test correct handling for an existing page that doesn't have downloadable files
        worksheet_info = WorksheetInfo("Languages", "en", "Languages", progress, "1.2")
        self.bot._add_english_file_infos("Some mediawiki content...", worksheet_info)
        self.assertEqual(len(worksheet_info.get_file_infos()), 0)

    @patch("pywikibot.FilePage")
    def test_add_file_type_not_existing(self, mock_filepage):
        mock_filepage.return_value.exists.return_value = False
        progress = TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Hearing_from_God", "en", "Hearing from God", progress, "1.2")
        with self.assertLogs("pywikitools.resourcesbot", level="WARNING"):
            self.bot._add_file_type(worksheet_info, "pdf", "Hearing_from_God.pdf")
        self.assertFalse(worksheet_info.has_file_type("pdf"))

    @patch("pywikibot.FilePage")
    def test_add_file_type_exception(self, mock_filepage):
        mock_filepage.side_effect = pywikibot.exceptions.Error("Test error")
        progress = TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Hearing_from_God", "en", "Hearing from God", progress, "1.2")
        with self.assertLogs("pywikitools.resourcesbot", level="WARNING"):
            self.bot._add_file_type(worksheet_info, "pdf", "Hearing_from_God.pdf")
        self.assertFalse(worksheet_info.has_file_type("pdf"))

    def test_get_english_version(self):
        version, version_unit = self.bot.get_english_version(HEARING_FROM_GOD)
        self.assertEqual(version, "1.2")
        self.assertEqual(version_unit, 55)
        with self.assertLogs("pywikitools.resourcesbot", level="WARNING"):
            version, version_unit = self.bot.get_english_version("Some mediawiki content...")
        self.assertEqual(version, "")
        self.assertEqual(version_unit, 0)

if __name__ == '__main__':
    unittest.main()
