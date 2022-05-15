"""
Testing ResourcesBot

Currently we have only little test coverage...
TODO: Find ways to run meaningful tests that don't take too long...
"""
from configparser import ConfigParser
from datetime import datetime
from os.path import abspath, dirname, join
import unittest
from unittest.mock import patch, Mock

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
        self.config.read_dict({"mediawiki": {"baseurl": "https://www.4training.net", "scriptpath": "/mediawiki"},
                               "Paths": {"logs": "~/", "temp": "~/temp/"}})    # Fill this to prevent warnings
        self.bot = ResourcesBot(self.config)

    @patch("pywikibot.FilePage")
    def test_add_english_file_infos(self, mock_filepage):
        mock_filepage.return_value.exists.return_value = True
        mock_filepage.return_value.latest_file_info.url = TEST_URL
        mock_filepage.return_value.latest_file_info.timestamp = datetime.fromisoformat(TEST_TIME)
        mock_filepage.return_value.download.return_value = False

        progress = TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Hearing_from_God", "en", "Hearing from God", progress, "1.2")
        with self.assertLogs("pywikitools.resourcesbot", level="WARNING"):  # warning for not checking PDF metadata
            self.bot._add_english_file_infos(HEARING_FROM_GOD, worksheet_info)
        self.assertTrue(worksheet_info.has_file_type("pdf"))
        self.assertTrue(worksheet_info.has_file_type("odt"))

        # Test correct handling for an existing page that doesn't have downloadable files
        worksheet_info = WorksheetInfo("Languages", "en", "Languages", progress, "1.2")
        self.bot._add_english_file_infos("Some mediawiki content...", worksheet_info)
        self.assertEqual(len(worksheet_info.get_file_infos()), 0)

    @patch("pywikitools.resourcesbot.bot.os")
    @patch("pywikibot.FilePage")
    def test_add_file_type(self, mock_filepage, mock_os):
        # Testing with reading metadata from a real PDF that is in our repo
        mock_filepage.return_value.exists.return_value = True
        mock_os.path.join.return_value = join(dirname(abspath(__file__)), "data", "Gottes_Reden_wahrnehmen.pdf")
        mock_filepage.return_value.download.return_value = True
        mock_filepage.return_value.latest_file_info.url = "https://www.4training.net/test/Gottes_Reden_wahrnehmen.pdf"
        mock_filepage.return_value.latest_file_info.timestamp = datetime(1970, 1, 1)
        progress = TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Hearing_from_God", "de", "Gottes Reden wahrnehmen", progress, "1.2")
        self.bot._add_file_type(worksheet_info, "pdf", "Gottes_Reden_wahrnehmen.pdf")
        self.assertTrue(worksheet_info.has_file_type("pdf"))
        pdf_info = worksheet_info.get_file_type_info("pdf")
        self.assertIsNotNone(pdf_info.metadata)
        self.assertTrue(pdf_info.metadata.correct)

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

    @patch("pywikibot.Site", autospec=True)
    @patch("pywikibot.Page", autospec=True)
    @patch("pywikitools.resourcesbot.bot.WriteReport", autospec=True)
    @patch("pywikitools.resourcesbot.bot.WriteList", autospec=True)
    @patch("pywikitools.resourcesbot.bot.ExportRepository", autospec=True)
    @patch("pywikitools.resourcesbot.bot.ExportHTML", autospec=True)
    @patch("pywikitools.resourcesbot.bot.ConsistencyCheck", autospec=True)
    def test_run_with_cache(self, mock_consistency_check, mock_export_html, mock_export_repository,
                            mock_write_list, mock_write_report, mock_pywikibot_page, mock_pywikibot_site):
        def json_test_loader(site, page: str):
            """Load meaningful test data for languages.json, en.json and ru.json"""
            result = Mock()
            if page == "4training:languages.json":
                result.text = '["en", "ru"]'
            elif page == "4training:en.json":
                with open(join(dirname(abspath(__file__)), "data", "en.json"), 'r') as f:
                    result.text = f.read()
            elif page == "4training:ru.json":
                with open(join(dirname(abspath(__file__)), "data", "ru.json"), 'r') as f:
                    result.text = f.read()
            return result
        mock_pywikibot_page.side_effect = json_test_loader
        mock_pywikibot_site.return_value.logged_in.return_value = True
        bot = ResourcesBot(self.config, read_from_cache=True)
        bot.run()

        mock_consistency_check.assert_called_once()
        mock_export_html.assert_called_once()
        mock_export_repository.assert_called_once()
        mock_write_list.assert_called_once()

        # Get the internal variables bot._result and bot._changelog so that we can do some assertions on them
        bot_result = mock_write_report.return_value.run.call_args.args[0]
        bot_changelog = mock_write_report.return_value.run.call_args.args[1]

        self.assertIn("en", bot_result)
        self.assertIn("ru", bot_result)
        self.assertEqual(len(bot_result), 2)
        self.assertTrue(bot_changelog["en"].is_empty())     # ChangeLogs must be empty because we read data from cache
        self.assertTrue(bot_changelog["ru"].is_empty())
        self.assertEqual(len(bot_changelog), 2)


if __name__ == '__main__':
    unittest.main()
