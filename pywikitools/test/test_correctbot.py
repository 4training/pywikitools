"""
Test cases for CorrectBot
"""
import unittest
import importlib
import os
from pywikitools.correctbot.correctors.base import CorrectorBase
from pywikitools.correctbot.correctors.de import GermanCorrector
from pywikitools.correctbot.correctors.universal import UniversalCorrector

from typing import Callable, List
from os import listdir
from os.path import isfile, join

# lots of TODOS here
#
# def create_reduced_page(language: str, input: List) -> ReducedPage:
#     pass
#
#
# def execute_test(language: str, input_to_test: List[str], expectation: str) -> None:
#     """
#     Execute the comparison test if input to test will be processed in the way that it matches with the given
#     expectation.
#
#     Args:
#         language (str): language of the page. Use "__" as placeholder if language is not imporant.
#         input_to_test (List[str]): List of inputs to test the unit on
#         expectation (str): Expected output.
#     """
#     input_to_test: ReducedPage = create_reduced_page(language, input_to_test)
#     expected_outcome: ReducedPage = create_reduced_page(language, [expectation])
#     # create corrector in fixture, e.g. with https://pythontesting.net/framework/unittest/unittest-fixtures/
#     # run correction and ckeck correction with "self.assertEqual(s.split(), ['hello', 'world'])"
#
#
# class CorrectBotLanguageIndependent(unittest.TestCase):
#     # TODO: clarify if we want any uniform rule on the special character "…" versus "..."
#     def test_multiple_spaces(self):
#         execute_test("__", ["Multiple  whitespaces   test"], "Multiple whitespaces test")
#
#     def test_missing_spaces(self):
#         execute_test("__", ["Full stop.Continue,with spaces.Okay?"], "Full stop. Continue, with spaces. Okay?")
#
#     def test_correct_dash(self):
#         execute_test("__", ["We don't want this - do we?"], "We don’t want this – do we?")
#
#     def test_file_name(self):
#         # TODO real life example of correcting file name reference, see below
#         execute_test("__", "Translations:Bible Reading Hints (Seven Stories full of Hope)/6/ml", 62256, 62281)
#
#
# class CorrectBotRTL(unittest.TestCase):
#     """ Test the common rules for right-to-left languages"""
#
#     def test_file_name(self):
#         # Check that we're correctly adding a RTL mark when there are parenthesis in file name
#         execute_test("__", "Translations:Bible_Reading_Hints_(Seven_Stories_full_of_Hope)/2/fa", 22794, 22801)
#
#     def test_title(self):
#         # Check that we're correctly adding a RTL mark when title ends with closing paranthesis: )
#         execute_test("__", "Translations:Bible_Reading_Hints_(Seven_Stories_full_of_Hope)/Page_display_title/fa", 57796,
#                      62364)
#
#
# class CorrectBotEnglish(unittest.TestCase):
#     def test_fix_apostrophe(self):
#         execute_test("en", ["God's"], "God’s")
#
#     def test_fix_quotation_marks(self):
#         execute_test("en", ["\"foo\"", "„foo“"], "“foo”")
#
#
#
#
#class CorrectBotFrench(unittest.TestCase):
#    def test_false_friends_replacement(self):
#        execute_test("fr", ["example"], "exemple")

#    def test_ellipsis_fix(self):
#        execute_test("fr", ["…"], "...")

#    def test_quotation_marks_fix(self):
        # Verify replacement of non-french quotation marks
#        execute_test("fr", ["“foo”", "\"foo\""], "«\u00a0foo\u00a0»")
        # Verify that french quotation marks are used correctly
#        execute_test("fr", ["« foo »", "«foo»"], "«\u00a0foo\u00a0»")
#
#
# class CorrectBotSpain(unittest.TestCase):
#     def test_fix_ellipsis(self):
#         execute_test("es", ["…"], "...")
#
#
# class CorrectBotArabic(unittest.TestCase):
#     def test_fix_comma(self):
#         execute_test("ar", [","], "،")
#         execute_test("ar", ["منهم،حتى"], "منهم، حتى")
#
#     def test_fix_multiple_spaces(self):
#         test_removal_double_whitespaces: List(str) = ["يدعي  و يصلي"]
#         expectation_double_whitespaces: str = "يدعي و يصلي"
#         execute_test("ar", test_removal_double_whitespaces, expectation_double_whitespaces)
#
#         test_removal_whitespaces_before_comma: List(str) = ["بحرص ،  أن"]
#         expectation_whitespaces_before_comma: str = "بحرص، أن"
#         execute_test("ar", test_removal_whitespaces_before_comma, expectation_whitespaces_before_comma)
#
#     def test_real_life_examples(self):
#         # TODO can we have an option to read real translations from the system and compares them?
#         # Liking checking that correctbot would correct in the same way as it was done here manually:
#         # something like execute_test(language_code: str, translation_unit: str, revision_id_before, revision_id_after)
#         # See these API calls for the first line:
#         # https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&action=history
#         # https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62195
#         # https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62258
#         execute_test("ar", "Translations:How_to_Continue_After_a_Prayer_Time/1/ar", 62195, 62258)
#         execute_test("ar", "Translations:How to Continue After a Prayer Time/4/ar", 62201, 62260)
#         execute_test("ar", "Translations:How to Continue After a Prayer Time/16/ar", 62225, 62270)
#         execute_test("ar", "Translations:How to Continue After a Prayer Time/Page_display_title/ar", 62193, 62274)
#
#     # TODO research which of these changes to improve Arabic language quality could be automated:
#     # https://www.4training.net/mediawiki/index.php?title=Forgiving_Step_by_Step%2Far&type=revision&diff=29760&oldid=29122
#

# Package and module names
PKG_CORRECTORS = "pywikitools.correctbot.correctors"
MOD_UNIVERSAL = f"{PKG_CORRECTORS}.universal"
MOD_BASE = f"{PKG_CORRECTORS}.base"

# Caution: This needs to be converted to an absolute path so that tests can be run safely from any folder
CORRECTORS_FOLDER = "../correctbot/correctors"

class TestLanguageCorrectors(unittest.TestCase):
    def setUp(self):
        """Load all language-specific corrector classes so that we can afterwards easily run our checks on them"""
        self.language_correctors: List[Callable] = []
        folder = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), CORRECTORS_FOLDER))

        # Search for all language-specific files in the correctors/ folder and get the classes in them
        for corrector_file in [f for f in listdir(folder) if isfile(join(folder, f))]:
            if not corrector_file.endswith(".py"):
                continue
            if corrector_file in ['__init__.py', 'universal.py', 'base.py']:
                continue

            language_code = corrector_file[0:-3]
            module_name = f"{PKG_CORRECTORS}.{language_code}"
            module = importlib.import_module(module_name)
            # There should be exactly one class named "XYCorrector" in there - let's get it
            class_counter = 0
            for class_name in dir(module):
                if "Corrector" in class_name:
                    corrector_class = getattr(module, class_name)
                    # Filter out CorrectorBase (in module correctors.base) and classes from correctors.universal
                    if corrector_class.__module__ == module_name:
                        class_counter += 1
                        # Let's load it and store it in self.language_correctors
                        self.language_correctors.append(getattr(module, class_name))
            self.assertEqual(class_counter, 1)

        # Now load all classes for correctors used by several languages
        self.flexible_correctors: List[Callable] = []
        universal_module = importlib.import_module(MOD_UNIVERSAL)
        for class_name in [s for s in dir(universal_module) if "Corrector" in s]:
            self.flexible_correctors.append(getattr(universal_module, class_name))

    def test_for_meaningful_names(self):
        """Make sure each function either starts with "correct_" or ends with "_title" or with "_filename"""
        for language_corrector in self.language_correctors:
            for function_name in dir(language_corrector):
                # Ignore private functions
                if function_name.startswith('_'):
                    continue
                # Ignore everything inherited from CorrectorBase
                if getattr(language_corrector, function_name).__module__ == MOD_BASE:
                    continue
                self.assertTrue(function_name.startswith("correct_")
                                or function_name.endswith("_title")
                                or function_name.endswith("_filename"))

    def test_for_unique_function_names(self):
        """Make sure that there are no functions with the same name in a language-specific corrector
        and a flexible corrector"""
        flexible_functions: List[str] = []
        for flexible_corrector in self.flexible_correctors:
            for flexible_function in dir(flexible_corrector):
                if flexible_function.startswith('_'):
                    continue
                flexible_functions.append(flexible_function)

        for language_corrector in self.language_correctors:
            for language_function in dir(language_corrector):
                if language_function.startswith('_'):
                    continue
                if getattr(language_corrector, language_function).__module__ != MOD_UNIVERSAL:
                    self.assertNotIn(language_function, flexible_functions)

class UniversalCorrectorTester(CorrectorBase, UniversalCorrector):
    """With this class we can test the rules of UniversalCorrector"""
    pass

class TestUniversalCorrector(unittest.TestCase):
    def test_spaces(self):
        corrector = UniversalCorrectorTester()
        self.assertEqual(corrector.correct("This entry   contains     too  many spaces."),
                                        "This entry contains too many spaces.")
        self.assertEqual(corrector.correct("This entry.Contains.Missing.Spaces.Between.Punctuation.And.Chars."),
                                           "This entry. Contains. Missing. Spaces. Between. Punctuation. And. Chars.")
        self.assertEqual(corrector.correct("This entry contains redundant spaces.  Before.   Punctuation."),
                                           "This entry contains redundant spaces. Before. Punctuation.")

    def test_capitalization(self):
        corrector = UniversalCorrectorTester()
        self.assertEqual(corrector.correct("lowercase start. and lowercase after full stop."),
                                           "Lowercase start. And lowercase after full stop.")
        self.assertEqual(corrector.correct("Question? answer! more lowercase. why? didn't check."),
                                           "Question? Answer! More lowercase. Why? Didn't check.")
        self.assertEqual(corrector.correct("After colons: and semicolons; we don't correct."),
                                           "After colons: and semicolons; we don't correct.")

    def test_filename_corrections(self):
        corrector = UniversalCorrectorTester()
        self.assertEqual(corrector.filename_correct("dummy file name.pdf"), "dummy_file_name.pdf")
        self.assertEqual(corrector.filename_correct("too__many___underscores.odt"), "too_many_underscores.odt")
        self.assertEqual(corrector.filename_correct("capitalized_extension.PDF"), "capitalized_extension.pdf")
        with self.assertLogs('pywikitools.correctbot.base', level='WARNING'):
            self.assertEqual(corrector.filename_correct("Not a filename"), "Not a filename")
        with self.assertLogs('pywikitools.correctbot.base', level='WARNING'):
            self.assertEqual(corrector.filename_correct("other extension.exe"), "other extension.exe")

class TestGermanCorrector(unittest.TestCase):
    def test_correct_quotes(self):
        corrector = GermanCorrector()
        for wrong in ['"Test"', '“Test”', '“Test„', '„Test„', '“Test“', '„Test"', '„Test“']:
            self.assertEqual(corrector.correct(wrong), '„Test“')
            self.assertEqual(corrector.correct(f"Beginn und {wrong}"), 'Beginn und „Test“')
            self.assertEqual(corrector.correct(f"{wrong} und Ende."), '„Test“ und Ende.')
            self.assertEqual(corrector.correct(f"Beginn und {wrong} und Ende."), 'Beginn und „Test“ und Ende.')

        with self.assertLogs('pywikitools.correctbot.de', level='WARNING'):
            self.assertEqual(corrector.correct(' " “ ” „'), ' " “ ” „')
        with self.assertLogs('pywikitools.correctbot.de', level='WARNING'):
            self.assertEqual(corrector.correct('"f“al"sc”h"'), '„f“al"sc”h“')
        with self.assertLogs('pywikitools.correctbot.de', level='WARNING'):
            self.assertEqual(corrector.correct('"Das ist" seltsam"'), '„Das ist“ seltsam“')


if __name__ == '__main__':
    unittest.main()
