"""
Test the different function of fortraininglib
TODO many tests are missing still

Run tests:
    python3 -m unittest test_fortraininglib.py
"""
import unittest
import sys
sys.path.append('../')
# TODO import that without the dirty hack above
import fortraininglib

class TestFortrainingLib(unittest.TestCase):
    def test_get_language_name(self):
        self.assertEqual(fortraininglib.get_language_name('de'), 'Deutsch')
        self.assertEqual(fortraininglib.get_language_name('en'), 'English')
        self.assertEqual(fortraininglib.get_language_name('tr'), 'Türkçe')
        self.assertEqual(fortraininglib.get_language_name('de','en'), 'German')
        self.assertEqual(fortraininglib.get_language_name('tr','de'), 'Türkisch')

    def test_list_page_translations(self):
        result = fortraininglib.list_page_translations('Prayer')
        result_with_incomplete = fortraininglib.list_page_translations('Prayer', include_unfinished=True)
        self.assertTrue(len(result) >= 5)
        self.assertTrue(len(result) <= len(result_with_incomplete))
        for language, progress in result.items():
            self.assertFalse(progress.is_unfinished())
        for language, progress in result_with_incomplete.items():
            if language not in result:
                self.assertTrue(progress.is_unfinished())
                self.assertFalse(progress.is_incomplete())


if __name__ == '__main__':
    unittest.main()
