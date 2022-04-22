"""
Test the different function of fortraininglib
TODO many tests are missing still

Run tests:
    python3 -m unittest test_fortraininglib.py
"""
import unittest
from unittest.mock import Mock, patch
import requests
#import logging

from pywikitools.fortraininglib import ForTrainingLib

class TestFortrainingLib(unittest.TestCase):
    def setUp(self):
# use this to see logging messages (can be increased to logging.DEBUG)
#        logging.basicConfig(level=logging.INFO)
        self.lib = ForTrainingLib("https://www.4training.net")

    @patch("pywikitools.fortraininglib.requests.get")
    def test_get(self, mock_get):
        # Emulate a successful get request
        response = requests.Response()
        response.status_code = 200
        response.json = Mock()
        response.json.return_value = {}
        mock_get.return_value = response
        self.lib._get({})
        mock_get.assert_called_once()

    @patch("pywikitools.fortraininglib.requests.get")
    def test_get_with_timeouts(self, mock_get):
        # Let's emulate repeated Timeouts and assert that requests.get() got called CONNECT_RETRIES times
        mock_get.side_effect = requests.exceptions.Timeout
        with self.assertLogs('pywikitools.lib', level='WARNING') as logs:
            self.lib._get({})
            self.assertEqual(len(logs.output), self.lib.CONNECT_RETRIES + 1)
        self.assertEqual(mock_get.call_count, self.lib.CONNECT_RETRIES)

    @patch("pywikitools.fortraininglib.requests.get")
    def test_get_with_single_timeout(self, mock_get):
        # One request times out and afterwards all works fine again
        response = requests.Response()
        response.status_code = 200
        response.json = Mock()
        response.json.return_value = {}
        mock_get.side_effect = [requests.exceptions.Timeout, response]
        with self.assertLogs('pywikitools.lib', level='WARNING') as logs:
            self.lib._get({})
            self.assertEqual(len(logs.output), 1)   # there should be only one warning
        self.assertEqual(mock_get.call_count, 2)

    @patch("pywikitools.fortraininglib.requests.get")
    def test_get_with_json_decode_error(self, mock_get):
        response = requests.Response()
        response.status_code = 200
        response.json = Mock()
        response.json.side_effect = requests.exceptions.JSONDecodeError
        mock_get.return_value = response
        with self.assertLogs('pywikitools.lib', level='WARNING'):
            self.lib._get({})
        mock_get.assert_called_once()

    def test_get_language_name(self):
        self.assertEqual(self.lib.get_language_name('de'), 'Deutsch')
        self.assertEqual(self.lib.get_language_name('en'), 'English')
        self.assertEqual(self.lib.get_language_name('tr'), 'Türkçe')
        self.assertEqual(self.lib.get_language_name('de', 'en'), 'German')
        self.assertEqual(self.lib.get_language_name('tr', 'de'), 'Türkisch')

    def test_list_page_translations(self):
        with self.assertLogs('pywikitools.lib', level='INFO'):
            result = self.lib.list_page_translations('Prayer')
        with self.assertLogs('pywikitools.lib', level='INFO'):
            result_with_incomplete = self.lib.list_page_translations('Prayer', include_unfinished=True)
        self.assertTrue(len(result) >= 5)
        self.assertTrue(len(result) <= len(result_with_incomplete))
        for language, progress in result.items():
            self.assertFalse(progress.is_unfinished())
        for language, progress in result_with_incomplete.items():
            if language not in result:
                self.assertTrue(progress.is_unfinished())
                self.assertFalse(progress.is_incomplete())

        # Check correct error handling for non-existing page
        self.assertEqual(len(self.lib.list_page_translations("NotExisting", "de")), 0)

    def test_list_page_templates(self):
        result = self.lib.list_page_templates('Polish')
        result_de = self.lib.list_page_templates('Polish/de')
        self.assertListEqual(result, result_de)     # Make sure that language codes at the end are removed
        self.assertIn("Template:BibleTranslation", result)
        self.assertIn("Template:JesusFilm", result)
        self.assertIn("Template:Translatable template", result)
        self.assertEqual(len(self.lib.list_page_templates('NotExisting')), 0)

    def test_get_pdf_name(self):
        self.assertEqual(self.lib.get_pdf_name('Forgiving_Step_by_Step', 'en'), 'Forgiving_Step_by_Step.pdf')
        self.assertEqual(self.lib.get_pdf_name('Forgiving_Step_by_Step', 'de'), 'Schritte_der_Vergebung.pdf')
        self.assertIsNone(self.lib.get_pdf_name('NotExisting', 'en'))

    def test_get_version(self):
        self.assertEqual(self.lib.get_version('Forgiving_Step_by_Step', 'en'), '1.3')
        self.assertEqual(self.lib.get_version('Forgiving_Step_by_Step', 'de'), '1.3')
        self.assertIsNone(self.lib.get_version('NotExisting', 'en'))

    def test_title_to_message(self):
        self.assertEqual(self.lib.title_to_message('Time_with_God'), 'sidebar-timewithgod')
        self.assertEqual(self.lib.title_to_message('Dealing with Money'), 'sidebar-dealingwithmoney')

# Disabled because this test takes fairly long (currently demands more than half of the time of a full test run)
#    def test_get_worksheet_list(self):
#        for worksheet in self.lib.get_worksheet_list():
#            page_source = self.lib.get_page_source(worksheet)
#            self.assertIsNotNone(page_source)
#            self.assertGreater(len(page_source), 100)

    def test_get_file_url(self):
        test_file = 'Forgiving_Step_by_Step.pdf'
        self.assertIsNone(self.lib.get_file_url('NotExisting'))
        self.assertTrue(self.lib.get_file_url(test_file).startswith('https://www.4training.net'))
        self.assertTrue(self.lib.get_file_url(test_file).endswith(test_file))

    def test_get_translation_units(self):
        # Not existing page should return an empty list
        with self.assertLogs("pywikitools.lib", level="WARNING"):
            self.assertIsNone(self.lib.get_translation_units("Invalid", "de"))
        # Check that there are translation units returned for a valid page
        translated_page = self.lib.get_translation_units("Healing", "de")
        counter = 0
        for translation_unit in translated_page:
            counter += 1
            self.assertGreater(len([snippet for snippet in translation_unit]), 0)
        self.assertGreater(counter, 10)

if __name__ == '__main__':
    unittest.main()
