"""
Test the different function of fortraininglib
TODO many tests are missing still

Run tests:
    python3 -m unittest test_fortraininglib.py
"""
import unittest
#import logging

from pywikitools import fortraininglib

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
        with self.assertLogs('pywikitools.lib', level='INFO'):
            result = fortraininglib.list_page_translations('Prayer')
        with self.assertLogs('pywikitools.lib', level='INFO'):
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

    def test_get_version(self):
        self.assertEqual(fortraininglib.get_version('Forgiving_Step_by_Step', 'en'), '1.3')
        self.assertEqual(fortraininglib.get_version('Forgiving_Step_by_Step', 'de'), '1.3')
        self.assertIsNone(fortraininglib.get_version('NotExisting', 'en'))

    def test_title_to_message(self):
        self.assertEqual(fortraininglib.title_to_message('Time_with_God'), 'sidebar-timewithgod')
        self.assertEqual(fortraininglib.title_to_message('Dealing with Money'), 'sidebar-dealingwithmoney')

# Disabled because this test takes fairly long (currently demands more than half of the time of a full test run)
#    def test_get_worksheet_list(self):
#        for worksheet in fortraininglib.get_worksheet_list():
#            page_source = fortraininglib.get_page_source(worksheet)
#            self.assertIsNotNone(page_source)
#            self.assertGreater(len(page_source), 100)

    def test_get_file_url(self):
        test_file = 'Forgiving_Step_by_Step.pdf'
        self.assertIsNone(fortraininglib.get_file_url('NotExisting'))
        self.assertTrue(fortraininglib.get_file_url(test_file).startswith('https://www.4training.net'))
        self.assertTrue(fortraininglib.get_file_url(test_file).endswith(test_file))

    def test_get_translation_units(self):
        # Not existing page should return an empty list
        with self.assertLogs("pywikitools.lib", level="WARNING"):
            self.assertEqual(len(fortraininglib.get_translation_units("Invalid", "de")), 0)
        # Check that there are translation units returned for a valid page
        translation_units = fortraininglib.get_translation_units("Healing", "de")
        counter = 0
        for translation_unit in translation_units:
            counter += 1
            self.assertGreater(len([snippet for snippet in translation_unit]), 0)
        self.assertGreater(counter, 10)


if __name__ == '__main__':
    unittest.main()
