import unittest
from pywikitools import fortraininglib

class ForTrainingLibTest(unittest.TestCase):
    """ TODO add more tests"""

    def test_get_worksheet_list(self):
        """TODO check that all worksheets exist"""

    def test_get_language_name(self):
        """We test if the function get_language_name works."""
        self.assertEqual(fortraininglib.get_language_name('de'), "Deutsch")
        self.assertEqual(fortraininglib.get_language_name('de', 'en'), "German")
        self.assertEqual(fortraininglib.get_language_name('nonsense'), "nonsense")

if __name__ == '__main__':
    unittest.main()
