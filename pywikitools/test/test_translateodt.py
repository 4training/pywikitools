import unittest
from unittest.mock import Mock
from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.lang.translated_page import TranslatedPage, TranslationUnit
from pywikitools.libreoffice import LibreOffice
from pywikitools.test.test_translated_page import TEST_UNIT_WITH_DEFINITION, TEST_UNIT_WITH_DEFINITION_DE_ERROR, TEST_UNIT_WITH_LISTS, TEST_UNIT_WITH_LISTS_DE

from pywikitools.translateodt import TranslateODT

class DummyTranslateODT(TranslateODT):
    def __init__(self):
        super().__init__(keep_english_file=True, config={"mediawiki": {"baseurl": "https://www.4training.net"}})
        self._loffice = Mock(spec=LibreOffice)


class TestTranslateODT(unittest.TestCase):
    def setUp(self):
        self.translate_odt = DummyTranslateODT()

    def test_is_search_and_replace_necessary(self):
        is_necessary = self.translate_odt._is_search_and_replace_necessary  # Shorten this long name
        for extension in ForTrainingLib("").get_file_types():
            self.assertFalse(is_necessary(f"Test.{extension}", f"Translation.{extension}"))
        self.assertFalse(is_necessary("", ""))
        self.assertFalse(is_necessary("same", "same"))
        # with self.assertNoLogs(): # Available from Python 3.10
        self.assertTrue(is_necessary("original", "translation"))
        with self.assertLogs("pywikitools.translateodt", level='WARNING'):
            self.assertTrue(is_necessary(".", "some translated text"))
        with self.assertLogs("pywikitools.translateodt", level='WARNING'):
            self.assertTrue(is_necessary("is", "some translated text"))

    def test_process_snippet(self):
        self.translate_odt._loffice.search_and_replace.return_value = True
        with self.assertLogs('pywikitools.translateodt', level='INFO'):
            self.translate_odt._process_snippet("original", "translation")
        self.translate_odt._loffice.search_and_replace.assert_called_once()

        self.translate_odt._loffice.search_and_replace.return_value = False
        with self.assertLogs('pywikitools.translateodt', level='WARNING'):
            self.translate_odt._process_snippet("original", "translation")
        self.assertEqual(self.translate_odt._loffice.search_and_replace.call_count, 3)

        self.translate_odt._loffice.search_and_replace.side_effect = AttributeError
        with self.assertLogs('pywikitools.translateodt', level='ERROR'):
            self.translate_odt._process_snippet("original", "translation")
        self.assertEqual(self.translate_odt._loffice.search_and_replace.call_count, 4)

    def test_get_odt_filename(self):
        # Headline and filename fit together
        headline = TranslationUnit("Test/Page_display_title", "de", "Good Title", "Guter Titel")
        unit_odt = TranslationUnit("Test/1", "de", "Good_Title.odt", "Guter_Titel.odt")
        translated_page = TranslatedPage("Test", "de", [headline, unit_odt])
        self.assertEqual(self.translate_odt._get_odt_filename(translated_page), "Guter_Titel.odt")

        # Filename is not as expected: check that corrected form gets returned
        wrong_odt = TranslationUnit("Test/1", "de", "Good_Title.odt", "GuterTitel.odt")
        translated_page = TranslatedPage("Test", "de", [headline, wrong_odt])
        with self.assertLogs('pywikitools.translateodt', level='WARNING'):
            self.assertEqual(self.translate_odt._get_odt_filename(translated_page), "Guter_Titel.odt")

    def test_set_properties(self):
        # Test that document properties are correctly set for a worksheet with no sub-headline
        headline = TranslationUnit("Test/Page_display_title", "de", "Title", "Titel")
        unit1 = TranslationUnit("Test/1", "de", "Headline", "Überschrift")
        unit_version = TranslationUnit("Test/2", "de", "1.2", "1.2")
        translated_page = TranslatedPage("Test", "de", [headline, unit1, unit_version])
        self.translate_odt._set_properties(translated_page)
        self.translate_odt._loffice.set_properties.assert_called_with(
            "Titel", "Title German Deutsch",
            "Kein Copyright: Dieses Arbeitsblatt darf ohne Einschränkungen weitergegeben und weiterverarbeitet werden"
            " (CC0). Version 1.2 - copyright-free")

        # Test that document properties are correctly set for a worksheet with a sub-headline
        # Sub-headline is assumed when the "subject" property of the English ODT file is the same
        # as the second translation unit, so we need to let get_properties_subject() return the right value
        self.translate_odt._loffice.get_properties_subject.return_value = "Headline"
        self.translate_odt._set_properties(translated_page)
        self.translate_odt._loffice.set_properties.assert_called_with(
            "Titel - Überschrift", "Title - Headline German Deutsch",
            "Kein Copyright: Dieses Arbeitsblatt darf ohne Einschränkungen weitergegeben und weiterverarbeitet werden"
            " (CC0). Version 1.2 - copyright-free")

    def test_cleanup_units(self):
        # should warn because "sin" can be found in the German translation "Wir versinken..."
        unit1 = TranslationUnit(f"Test/2", "de", "We're drowning in snow chaos", "Wir versinken im Schnee.")
        unit2 = TranslationUnit(f"Test/1", "de", "sin", "Sünde")
        translated_page = TranslatedPage("Test", "de", [unit1, unit2])
        with self.assertLogs('pywikitools.translateodt', level='WARNING'):
            cleaned_up_page = self.translate_odt._cleanup_units(translated_page)
        # the TranslatedPage returned should have the same contents as before
        self.assertEqual(cleaned_up_page.page, translated_page.page)
        self.assertEqual(cleaned_up_page.language_code, translated_page.language_code)
        self.assertEqual(cleaned_up_page.units[0], translated_page.units[0])
        self.assertEqual(cleaned_up_page.units[1], translated_page.units[1])

        # TODO test some more stuff


if __name__ == '__main__':
    unittest.main()

