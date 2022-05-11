import unittest
from pywikitools.fortraininglib import ForTrainingLib

from pywikitools.resourcesbot.consistency_checks import ConsistencyCheck
from pywikitools.resourcesbot.data_structures import LanguageInfo


class TestConsistencyCheck(unittest.TestCase):
    def test_extract_link(self):
        cc = ConsistencyCheck(ForTrainingLib("https://www.4training.net"))
        dest, title = cc.extract_link("Here is a link: [[Destination|Title]].")
        self.assertEqual(dest, "Destination")
        self.assertEqual(title, "Title")
        # Now check that empty strings are returned when there is no link in the translation unit
        dest, title = cc.extract_link("Nothing. [[This link won't be considered.]]")
        self.assertEqual(dest, "")
        self.assertEqual(title, "")

    def test_everything_in_english(self):
        """All consistency checks should pass in English"""
        cc = ConsistencyCheck(ForTrainingLib("https://www.4training.net"))
        language_info = LanguageInfo("en", "English")
        self.assertTrue(cc.check_bible_reading_hints_titles(language_info))
        self.assertTrue(cc.check_gods_story_titles(language_info))
        self.assertTrue(cc.check_who_do_i_need_to_forgive(language_info))
        self.assertTrue(cc.check_bible_reading_hints_links(language_info))
        self.assertTrue(cc.check_book_of_acts(language_info))


if __name__ == '__main__':
    unittest.main()
