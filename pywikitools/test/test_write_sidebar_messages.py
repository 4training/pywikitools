import unittest
from configparser import ConfigParser
from unittest.mock import patch
from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog, ChangeType

from pywikitools.resourcesbot.data_structures import LanguageInfo, TranslationProgress, WorksheetInfo
from pywikitools.resourcesbot.modules.write_sidebar_messages import WriteSidebarMessages
from pywikitools.test.test_data_structures import TEST_PROGRESS


class TestWriteSidebarMessages(unittest.TestCase):
    def setUp(self):
        self.config = ConfigParser()
        self.worksheet = WorksheetInfo("Hearing_from_God", "de", "Gottes Reden wahrnehmen",
                                       TranslationProgress(**TEST_PROGRESS), "1.2")
        self.language_info = LanguageInfo("de", "German")
        self.language_info.add_worksheet_info("Hearing_from_God", self.worksheet)

        self.write_sidebar_messages = WriteSidebarMessages(
            ForTrainingLib("https://test.4training.net"),
            self.config,
            None)

    @patch("pywikibot.Page")
    def test_save_worksheet_title(self, mock_page):
        # System message shouldn't be touched if it exists and content doesn't change
        mock_page.return_value.exists.return_value = True
        mock_page.return_value.text = self.worksheet.title
        self.write_sidebar_messages.save_worksheet_title(self.worksheet)
        mock_page.return_value.save.assert_not_called()

        # System message should get created if it doesn't exist
        mock_page.return_value.exists.return_value = False
        self.write_sidebar_messages.save_worksheet_title(self.worksheet)
        mock_page.return_value.save.assert_called_once()

        # System message should get updated if there are changes
        mock_page.return_value.exists.return_value = True
        mock_page.return_value.text = "different"
        self.write_sidebar_messages.save_worksheet_title(self.worksheet)
        self.assertEqual(mock_page.return_value.save.call_count, 2)

        # Check that we're writing to the correct system message
        mock_page.assert_called_with(None, "MediaWiki:Sidebar-hearingfromgod/de")

        en_worksheet = WorksheetInfo("Hearing_from_God", "en", "Hearing from God",
                                     TranslationProgress(**TEST_PROGRESS), "1.2")
        self.write_sidebar_messages.save_worksheet_title(en_worksheet)
        # Note: It's not MediaWiki:Sidebar-hearingfromgod/en as English is our source language
        mock_page.assert_called_with(None, "MediaWiki:Sidebar-hearingfromgod")

    @patch("pywikitools.resourcesbot.modules.write_sidebar_messages.WriteSidebarMessages.save_worksheet_title")
    def test_run(self, mock_save):
        # save_worksheet_title() shouldn't get called when there are no changes
        self.write_sidebar_messages.run(self.language_info, None, ChangeLog(), ChangeLog())
        mock_save.assert_not_called()

        # save_worksheet_title() should get called when there is a change
        changes = ChangeLog()
        changes.add_change("Hearing_from_God", ChangeType.UPDATED_WORKSHEET)
        self.write_sidebar_messages.run(self.language_info, None, changes, ChangeLog())
        mock_save.assert_called_once()

        # save_worksheet_title() shouldn't get called when there change is irrelevant
        irrelevant_changes = ChangeLog()
        irrelevant_changes.add_change("Hearing_from_God", ChangeType.NEW_PDF)
        self.write_sidebar_messages.run(self.language_info, None, irrelevant_changes, ChangeLog())
        mock_save.assert_called_once()

        # save_worksheet_title() should be called when we have force_rewrite (even if there are no changes)
        write_sidebar_messages = WriteSidebarMessages(
            fortraininglib=None,
            config=self.config,
            site=None,
            force_rewrite=True
        )
        write_sidebar_messages.run(self.language_info, None, ChangeLog(), ChangeLog())
        self.assertEqual(mock_save.call_count, 2)


if __name__ == '__main__':
    unittest.main()
