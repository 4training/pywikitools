"""
Test the different function of fortraininglib
TODO many tests are missing still

Run tests:
    python3 -m unittest test_fortraininglib.py
"""
import unittest
import logging
import sys
sys.path.append('../')
# TODO import that without the dirty hack above
import fortraininglib

class TestFortrainingLib(unittest.TestCase):
# use this to see logging messages (can be increased to logging.DEBUG)
#    def setUp(self):
#        logging.basicConfig(level=logging.INFO)

    def test_get_language_name(self):
        self.assertEqual(fortraininglib.get_language_name('de'), 'Deutsch')
        self.assertEqual(fortraininglib.get_language_name('en'), 'English')
        self.assertEqual(fortraininglib.get_language_name('tr'), 'Türkçe')
        self.assertEqual(fortraininglib.get_language_name('de', 'en'), 'German')
        self.assertEqual(fortraininglib.get_language_name('tr', 'de'), 'Türkisch')

    def test_list_page_translations(self):
        with self.assertLogs('4training.lib', level='INFO'):
            result = fortraininglib.list_page_translations('Prayer')
        with self.assertLogs('4training.lib', level='INFO'):
            result_with_incomplete = fortraininglib.list_page_translations('Prayer', include_unfinished=True)
        self.assertTrue(len(result) >= 5)
        self.assertTrue(len(result) <= len(result_with_incomplete))
        for language, progress in result.items():
            self.assertFalse(progress.is_unfinished())
        for language, progress in result_with_incomplete.items():
            if language not in result:
                self.assertTrue(progress.is_unfinished())
                self.assertFalse(progress.is_incomplete())

    def test_get_pdf_name(self):
        self.assertEqual(fortraininglib.get_pdf_name('Forgiving_Step_by_Step', 'en'), 'Forgiving_Step_by_Step.pdf')
        self.assertEqual(fortraininglib.get_pdf_name('Forgiving_Step_by_Step', 'de'), 'Schritte_der_Vergebung.pdf')
        self.assertIsNone(fortraininglib.get_pdf_name('NotExisting', 'en'))


if __name__ == '__main__':
    unittest.main()
