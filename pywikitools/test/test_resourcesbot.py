"""
Testing ResourcesBot

Currently we have only little test coverage...
TODO: Find ways to run meaningful tests that don't take too long...
"""
import unittest

from pywikitools import fortraininglib
from pywikitools.resourcesbot.bot import ResourcesBot
from pywikitools.resourcesbot.data_structures import WorksheetInfo
from pywikitools.test.test_data_structures import TEST_PROGRESS

class TestResourcesBot(unittest.TestCase):
    def test_add_english_file_infos(self):
        # This test is requesting data from 4training.net - find a better and faster solution?
        bot = ResourcesBot()
        progress = fortraininglib.TranslationProgress(**TEST_PROGRESS)
        worksheet_info = WorksheetInfo("Hearing_from_God", "en", "Hearing from God", progress)
        bot._add_english_file_infos(worksheet_info)
        self.assertTrue(worksheet_info.has_file_type("pdf"))
        self.assertTrue(worksheet_info.has_file_type("odt"))

        # Test correct error handling for non-existing page
        worksheet_info = WorksheetInfo("Not_Existing", "en", "Not Existing", progress)
        with self.assertLogs("pywikitools.resourcesbot", level="WARNING"):
            bot._add_english_file_infos(worksheet_info)

        # Test correct handling for an existing page that doesn't have downloadable files
        worksheet_info = WorksheetInfo("Languages", "en", "Languages", progress)
        bot._add_english_file_infos(worksheet_info)
        self.assertEqual(len(worksheet_info.get_file_infos()), 0)


if __name__ == '__main__':
    unittest.main()
