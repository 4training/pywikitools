import unittest
from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog

from pywikitools.resourcesbot.consistency_checks import ConsistencyCheck
from pywikitools.resourcesbot.data_structures import LanguageInfo


class TestConsistencyCheck(unittest.TestCase):
    def setUp(self):
        self.fortraininglib = ForTrainingLib("https://test.4training.net")

    def tearDown(self):
        # workaround to remove annoying ResourceWarning: unclosed <ssl.SSLSocket ...
        self.fortraininglib.session.close()

    def test_extract_link(self):
        cc = ConsistencyCheck(self.fortraininglib)
        dest, title = cc.extract_link("Here is a link: [[Destination|Title]].")
        self.assertEqual(dest, "Destination")
        self.assertEqual(title, "Title")
        # Now check that empty strings are returned when there is no link in the translation unit
        dest, title = cc.extract_link("Nothing. [[This link won't be considered.]]")
        self.assertEqual(dest, "")
        self.assertEqual(title, "")

    def test_everything_in_english(self):
        """All consistency checks should pass in English"""
        cc = ConsistencyCheck(self.fortraininglib)
        language_info = LanguageInfo("en", "English")
        with self.assertLogs("pywikitools.resourcesbot.consistency_checks", level="INFO") as logs:
            cc.run(language_info, LanguageInfo("en", "English"), ChangeLog(), ChangeLog())
        self.assertIn("Consistency checks for English: 5/5 passed", logs.output[0])


if __name__ == '__main__':
    unittest.main()
