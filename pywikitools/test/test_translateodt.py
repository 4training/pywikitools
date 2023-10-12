from typing import List, Tuple
from os.path import abspath, dirname, join
import unittest
from unittest.mock import ANY, Mock, patch
from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.lang.translated_page import TranslatedPage, TranslationUnit
from pywikitools.libreoffice import LibreOffice

from pywikitools.translateodt import TranslateODT, TranslateOdtConfig


class DummyTranslateODT(TranslateODT):
    def __init__(self):
        super().__init__(keep_english_file=True, config={"translateodt": {"site": "4training"},
                                                         "correctbot": {"site": "4training", "username": "Test"}})
        self._loffice = Mock(spec=LibreOffice)


class TestTranslateODT(unittest.TestCase):
    def setUp(self):
        self.translate_odt = DummyTranslateODT()

    def tearDown(self):
        # workaround to remove annoying ResourceWarning: unclosed <ssl.SSLSocket ...
        self.translate_odt.fortraininglib.session.close()

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
        with self.assertLogs('pywikitools.translateodt', level='DEBUG'):
            self.translate_odt._process_snippet("original", "translation")
        self.translate_odt._loffice.search_and_replace.assert_called_once()

        self.translate_odt._loffice.search_and_replace.return_value = False
        with self.assertLogs('pywikitools.translateodt', level='WARNING'):
            self.translate_odt._process_snippet("original", "translation")
        self.assertEqual(self.translate_odt._loffice.search_and_replace.call_count, 2)

        self.translate_odt._loffice.search_and_replace.side_effect = AttributeError
        with self.assertLogs('pywikitools.translateodt', level='ERROR'):
            self.translate_odt._process_snippet("original", "translation")
        self.assertEqual(self.translate_odt._loffice.search_and_replace.call_count, 3)

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

    def test_persian_properties(self):
        # Test special case for Persian
        headline = TranslationUnit("Test/Page_display_title", "fa", "Healing", "شفا")
        unit_version = TranslationUnit("Test/2", "fa", "1.2", "1.2")
        translated_page = TranslatedPage("Test", "fa", [headline, unit_version])
        self.translate_odt._set_properties(translated_page)
        self.translate_odt._loffice.set_properties.assert_called_with("شفا", "Healing Persian Farsi فارسی", ANY)

    def test_cleanup_units(self):
        # should warn because "sin" can be found in the German translation "Wir versinken..."
        unit1 = TranslationUnit("Test/2", "de", "We're drowning in snow chaos", "Wir versinken im Schnee.")
        unit2 = TranslationUnit("Test/1", "de", "sin", "Sünde")
        translated_page = TranslatedPage("Test", "de", [unit1, unit2])
        with self.assertLogs('pywikitools.translateodt', level='WARNING'):
            cleaned_up_page = self.translate_odt._cleanup_units(translated_page, TranslateOdtConfig())
        # the TranslatedPage returned should have the same contents as before
        self.assertEqual(cleaned_up_page.page, translated_page.page)
        self.assertEqual(cleaned_up_page.language_code, translated_page.language_code)
        self.assertEqual(cleaned_up_page.units[0], translated_page.units[0])
        self.assertEqual(cleaned_up_page.units[1], translated_page.units[1])

        # TranslateOdtConfig should be processed correctly: Ignoring Test/2, having Test/1 three times
        config = TranslateOdtConfig()
        config.ignore.add("Test/2")
        config.multiple["Test/1"] = 3
        cleaned_up_page = self.translate_odt._cleanup_units(translated_page, config)
        self.assertListEqual([tu.identifier for tu in cleaned_up_page.units], ["Test/1"] * 3)

    def _sort_units(self, definitions: List[str], translations: List[str]) -> Tuple[List[str], List[str]]:
        """Create translation units, sort them and return lists of definitions and translations
        The return format is for easier comparison of the expected outcome
        """
        units: List[TranslationUnit] = []
        for counter, definition in enumerate(definitions):
            unit = TranslationUnit(f"Test/{counter}", "de", definition, translations[counter])
            units.append(unit)
        self.translate_odt.special_sort_units(units)
        sorted_definitions_list: List[str] = []
        sorted_translations_list: List[str] = []
        for unit in units:
            sorted_definitions_list.append(unit.get_definition())
            sorted_translations_list.append(unit.get_translation())
        return (sorted_definitions_list, sorted_translations_list)

    def test_special_sort_units(self):
        # Test correct sorting
        with self.assertLogs('pywikitools.translateodt', level='INFO'):
            (orig_list, trans_list) = self._sort_units(["this", "this", "is", "thistle"],
                                                       ["same", "same", "same", "same"])
        self.assertListEqual(orig_list, ["thistle", "this", "this", "is"])
        # two different translation units with the same definition but different translations should give a warning
        with self.assertLogs('pywikitools.lang.TranslationUnit', level='WARNING'):
            (orig_list, trans_list) = self._sort_units(["this", "this", "other", "content"],
                                                       ["same", "different", "same", "same"])
        self.assertListEqual(orig_list, ["this", "this", "other", "content"])
        # two snippets in a translation unit
        with self.assertLogs('pywikitools.translateodt', level='INFO'):
            (orig_list, trans_list) = self._sort_units(["this<br/>is", "this<br/>thistle"],
                                                       ["same<br/>same", "same<br/>same"])
        self.assertListEqual(orig_list, ["this<br/>thistle", "this<br/>is"])
        # reciprocal dependency should give a warning
        with self.assertLogs('pywikitools.lang.TranslationUnit', level='WARNING') as cm:
            (orig_list, trans_list) = self._sort_units(["something<br/>range", "thing<br/>strange"],
                                                       ["same<br/>same", "same<br/>same"])
        self.assertIn("reciprocal", cm.output[0])

    def test_read_worksheet_config(self):
        # TranslateOdtConfig should be empty if there is no config in the mediawiki system
        self.translate_odt.fortraininglib = Mock()
        self.translate_odt.fortraininglib.get_page_source.return_value = None
        result = self.translate_odt.read_worksheet_config("NotExisting")
        self.assertSetEqual(result.ignore, set())
        self.assertEqual(len(result.multiple), 0)

        # TranslateOdtConfig should also be empty if the config exists but has no content
        self.translate_odt.fortraininglib.get_page_source.return_value = ""
        result = self.translate_odt.read_worksheet_config("Test")
        self.assertSetEqual(result.ignore, set())
        self.assertEqual(len(result.multiple), 0)

        # Test with a realistic config file
        with open(join(dirname(abspath(__file__)), "data", "Bible_Reading_Hints.config"), 'r') as f:
            test_config = f.read()
        self.translate_odt.fortraininglib.get_page_source.return_value = test_config
        result = self.translate_odt.read_worksheet_config("Test")
        self.assertSetEqual(result.ignore,
            set(["Bible_Reading_Hints/1", "Bible_Reading_Hints/2", "Bible_Reading_Hints/3",     # noqa: E128
                 "Template:BibleReadingHints/18", "Template:BibleReadingHints/25", "Template:BibleReadingHints/26"]))
        self.assertEqual(len(result.multiple), 2)
        self.assertEqual(result.multiple["Template:BibleReadingHints/6"], 5)
        self.assertEqual(result.multiple["Bible_Reading_Hints/7"], 2)

    @patch("pywikitools.translateodt.ForTrainingLib", autospec=True)
    @patch("pywikitools.translateodt.CorrectBot", autospec=True)
    def test_translate_worksheet_aborts(self, mock_correctbot, mock_fortraininglib):
        # Testing that translate_worksheet() aborts correctly if some prerequisites are not met
        translateodt = DummyTranslateODT()

        # CorrectBot would correct something or give warnings
        mock_correctbot.return_value.get_correction_counter.return_value = 2
        with self.assertLogs('pywikitools.translateodt', level='ERROR'):
            self.assertIsNone(translateodt.translate_worksheet("Prayer", "de"))
        mock_correctbot.return_value.get_correction_counter.return_value = 0
        mock_correctbot.return_value.get_warning_counter.return_value = 1
        with self.assertLogs('pywikitools.translateodt', level='ERROR'):
            self.assertIsNone(translateodt.translate_worksheet("Prayer", "de"))

        mock_correctbot.return_value.get_warning_counter.return_value = 0

        # Can't get translation units of worksheet
        mock_fortraininglib.return_value.get_translation_units.return_value = None
        with self.assertLogs('pywikitools.translateodt', level='ERROR'):
            self.assertIsNone(translateodt.translate_worksheet("Prayer", "de"))

        # Worksheet isn't translated yet
        mock_translated_page = Mock()
        mock_translated_page.is_untranslated.return_value = True
        mock_fortraininglib.return_value.get_translation_units.return_value = mock_translated_page
        with self.assertLogs('pywikitools.translateodt', level='ERROR'):
            self.assertIsNone(translateodt.translate_worksheet("Prayer", "de"))

        # TODO test all the main functionality of translate_worksheet()


if __name__ == '__main__':
    unittest.main()
