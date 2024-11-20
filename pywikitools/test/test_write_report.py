import json
import unittest
from configparser import ConfigParser
from datetime import datetime
from os.path import abspath, dirname, join
from unittest.mock import Mock, patch

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import LanguageInfo, json_decode
from pywikitools.resourcesbot.modules.write_report import WriteReport


class TestWriteReport(unittest.TestCase):
    def setUp(self):
        self.config = ConfigParser()
        with open(join(dirname(abspath(__file__)), "data", "ru.json"), "r") as f:
            self.language_info = json.load(f, object_hook=json_decode)
        with open(join(dirname(abspath(__file__)), "data", "en.json"), "r") as f:
            self.english_info = json.load(f, object_hook=json_decode)
        self.fortraininglib = ForTrainingLib("https://test.4training.net")

    @staticmethod
    def mock_pywikibot_pages(site, page: str):
        """Test all different cases in create_correctbot_mediawiki"""
        result = Mock()
        if page == "Healing/ru":  # Original page doesn't exist (serious error)
            result.exists = lambda: False
            return result
        if page == "CorrectBot:Prayer/ru":  # CorrectBot report missing
            result.exists = lambda: False
            return result

        # defaults for the worksheet_page
        result.exists = lambda: True
        result.editTime = lambda: datetime(2022, 1, 1)

        if page.startswith("CorrectBot"):
            # defaults for the correctbot_page
            result.latest_revision = {
                "comment": "2 corrections, 1 suggestions, 0 warnings"
            }
            result.editTime = lambda: datetime(2022, 1, 2)

            if (
                page == "CorrectBot:Hearing_from_God/ru"
            ):  # CorrectBot report contains warnings
                result.latest_revision = {
                    "comment": "0 corrections, 5 suggestions, 2 warnings"
                }
            elif (
                page == "CorrectBot:Bible_Reading_Hints/ru"
            ):  # weird CorrectBot edit message
                result.latest_revision = {"comment": "invalid"}
            elif page == "CorrectBot:Time_with_God/ru":  # outdated CorrectBot report
                result.editTime = lambda: datetime(2021, 1, 1)

        return result

    @patch("pywikibot.Page", autospec=True)
    def test_created_mediawiki(self, mock_page):
        # Compare mediawiki output with the content in
        # data/ru_worksheet_overview.mediawiki
        write_report = WriteReport(self.fortraininglib, self.config, None)
        mock_page.side_effect = self.mock_pywikibot_pages

        with open(
            join(dirname(abspath(__file__)), "data", "ru_worksheet_overview.mediawiki"),
            "r",
        ) as f:
            expected_mediawiki = f.read()
            with self.assertLogs(
                "pywikitools.resourcesbot.modules.write_report", level="WARNING"
            ):
                self.assertEqual(
                    write_report.create_worksheet_overview(
                        self.language_info, self.english_info
                    ),
                    expected_mediawiki,
                )
                self.assertIn(
                    expected_mediawiki,
                    write_report.create_mediawiki(
                        self.language_info, self.english_info
                    ),
                )

    @patch(
        "pywikitools.resourcesbot.modules.write_report.WriteReport" ".create_mediawiki"
    )  # don't go into create_mediawiki()
    @patch("pywikibot.Page")
    def test_save_language_report(self, mock_page, mock_create_mediawiki):
        write_report = WriteReport(self.fortraininglib, self.config, None)
        # When there is no proper language name, save_language_report()
        # should directly exit
        with self.assertLogs(
            "pywikitools.resourcesbot.modules.write_report", level="WARNING"
        ):
            write_report.save_language_report(LanguageInfo("de", ""), self.english_info)
        mock_page.return_value.exists.assert_not_called()

        # Language report should get created if it doesn't exist
        mock_page.return_value.exists.return_value = False
        with self.assertLogs(
            "pywikitools.resourcesbot.modules.write_report", level="WARNING"
        ):
            write_report.save_language_report(self.language_info, self.english_info)
        mock_page.return_value.save.assert_called_with("Created language report")

        # Language report should get updated if there are changes
        mock_page.return_value.exists.return_value = True
        mock_page.return_value.text = "different"
        write_report.save_language_report(self.language_info, self.english_info)
        mock_page.return_value.save.assert_called_with("Updated language report")

    @patch(
        "pywikitools.resourcesbot.modules.write_report.WriteReport"
        ".save_language_report"
    )
    def test_run(self, mock_save):
        write_report = WriteReport(self.fortraininglib, self.config, None)
        # save_language_report() shouldn't get called when we have a language variant
        write_report.run(
            LanguageInfo("de-test", "Deutsch (Test)"),
            self.english_info,
            ChangeLog(),
            ChangeLog(),
        )
        mock_save.assert_not_called()

        # save_language_report() should be called once (for Russian) and force_rewrite
        # should be ignored
        write_report = WriteReport(self.fortraininglib, self.config, None)
        write_report.run(
            self.language_info, self.english_info, ChangeLog(), ChangeLog()
        )
        mock_save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
