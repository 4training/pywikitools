"""
Test cases for CorrectBot: Testing core functionality as well as language-specific rules
"""
from inspect import signature
import logging
import unittest
import importlib
import os
from pywikitools import fortraininglib
from pywikitools.correctbot.correctors.ar import ArabicCorrector
from pywikitools.correctbot.correctors.base import CorrectorBase
from pywikitools.correctbot.correctors.de import GermanCorrector
from pywikitools.correctbot.correctors.fr import FrenchCorrector
from pywikitools.correctbot.correctors.universal import RTLCorrector, UniversalCorrector

from typing import Callable, List, Optional
from os import listdir
from os.path import isfile, join

from pywikitools.lang.translated_page import TranslationUnit

# Package and module names
PKG_CORRECTORS = "pywikitools.correctbot.correctors"
MOD_UNIVERSAL = f"{PKG_CORRECTORS}.universal"
MOD_BASE = f"{PKG_CORRECTORS}.base"

# Caution: This needs to be converted to an absolute path so that tests can be run safely from any folder
CORRECTORS_FOLDER = "../correctbot/correctors"

def correct(corrector: CorrectorBase, text: str, original: Optional[str] = None) -> str:
    """Shorthand function for running a test with CorrectorBase.correct()"""
    if original is None:
        original = text     # original will be ignored but make sure we have a well-structured translation unit
    unit = TranslationUnit("Test/1", "test", original, text)
    corrector.correct(unit)
    return unit.get_translation()

def title_correct(corrector: CorrectorBase, text: str, original: Optional[str] = None) -> str:
    """Shorthand function for running a test with CorrectorBase.title_correct()"""
    if original is None:
        original = ""       # title correcting functions should never use @use_snippets
    unit = TranslationUnit("Test/Page display title", "test", original, text)
    corrector.title_correct(unit)
    return unit.get_translation()

def filename_correct(corrector: CorrectorBase, text: str, original: Optional[str] = None) -> str:
    """Shorthand function for running a test with CorrectorBase.filename_correct()"""
    if original is None:
        original = ""       # filename correcting functions should never use @use_snippets
    unit = TranslationUnit("Test/3", "test", original, text)
    corrector.filename_correct(unit)
    return unit.get_translation()


class CorrectorTestCase(unittest.TestCase):
    """
    Adds functions to check corrections against revisions made in the mediawiki system

    Use this as base class if you need this functionality. They come with the cost of doing
    real mediawiki API calls, taking significant time. The benefit is that you don't need to include
    potentially long strings in complex languages in the source code

    If you use this as base class, you need to set it up with the right corrector class like this:
    @classmethod
    def setUpClass(cls):
        cls.corrector = GermanCorrector()

    Example: compare_revisions("How_to_Continue_After_a_Prayer_Time", "ar", 1, 62195, 62258)
    calls
    https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62195
    https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&oldid=62258
    which is similar to https://www.4training.net/mediawiki/index.php?Translations:How_to_Continue_After_a_Prayer_Time/1/ar&type=revision&diff=62258&oldid=62195
    See also https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&action=history
    """
    corrector: CorrectorBase    # Avoiding mypy/pylint warnings, see https://github.com/python/mypy/issues/8723

    def compare_revisions(self, page: str, language_code: str, identifier: int, old_revision: int, new_revision: int):
        """For all "normal" translation units: Calls CorrectorBase.correct()"""
        old_content = fortraininglib.get_translated_unit(page, language_code, identifier, old_revision)
        new_content = fortraininglib.get_translated_unit(page, language_code, identifier, new_revision)
        self.assertIsNotNone(old_content)
        self.assertIsNotNone(new_content)
        self.assertEqual(correct(self.corrector, old_content), new_content)

    def compare_title_revisions(self, page: str, language_code: str, old_revision: int, new_revision):
        """Calls CorrectBase.title_correct()"""
        old_content = fortraininglib.get_translated_title(page, language_code, old_revision)
        new_content = fortraininglib.get_translated_title(page, language_code, new_revision)
        self.assertIsNotNone(old_content)
        self.assertIsNotNone(new_content)
        self.assertEqual(title_correct(self.corrector, old_content), new_content)

    def compare_filename_revisions(self, page: str, language_code: str, identifier: int,
                                         old_revision: int, new_revision):
        """Calls CorrectorBase.filename_correct()"""
        old_content = fortraininglib.get_translated_unit(page, language_code, identifier, old_revision)
        new_content = fortraininglib.get_translated_unit(page, language_code, identifier, new_revision)
        self.assertIsNotNone(old_content)
        self.assertIsNotNone(new_content)
        # Check that we really have a translation unit with a file name. TODO use the following line instead:
        # with self.assertNoLogs(): # Available from Python 3.10
        self.assertIn(new_content[-3:], fortraininglib.get_file_types())
        self.assertEqual(filename_correct(self.corrector, old_content), new_content)


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
        """Make sure each function either starts with "correct_" or ends with "_title" or with "_filename."""
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

    def test_for_correct_parameters(self):
        """Make sure all correction functions take either one or two strings as parameters."""
        for language_corrector in self.language_correctors:
            for function_name in dir(language_corrector):
                # Ignore private functions
                if function_name.startswith('_'):
                    continue
                corrector_function = getattr(language_corrector, function_name)
                # Ignore everything inherited from CorrectorBase
                if corrector_function.__module__ == MOD_BASE:
                    continue
                count_parameters: int = 0
                for parameter in signature(corrector_function).parameters:
                    if parameter != "self":
                        count_parameters += 1
                        self.assertEqual(signature(corrector_function).parameters[parameter].annotation, str)
                self.assertGreaterEqual(count_parameters, 1)
                self.assertLessEqual(count_parameters, 2)


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
        self.assertEqual(correct(corrector, "This entry   contains     too  many spaces."),
                                            "This entry contains too many spaces.")
        self.assertEqual(correct(corrector, "Missing.Spaces,after punctuation?Behold,again."),
                                            "Missing. Spaces, after punctuation? Behold, again.")
        self.assertEqual(correct(corrector, "This entry contains redundant spaces , before , punctuation ."),
                                            "This entry contains redundant spaces, before, punctuation.")
        # now let's try if exceptions are correctly respected:
        self.assertEqual(correct(corrector, "John 3:16.Johannes 3,16."), "John 3:16. Johannes 3,16.")
        self.assertEqual(correct(corrector, "Go ,end with ."), "Go, end with.")
        self.assertEqual(correct(corrector, "Continue ..."), "Continue ...")
        # Testing also print_stats()
        self.assertIn("6 corrections", corrector.print_stats())
        self.assertIn("Reduce multiple spaces", corrector.print_stats())
        self.assertIn("Insert missing spaces", corrector.print_stats())
        self.assertIn("Erase redundant spaces", corrector.print_stats())

    def test_capitalization(self):
        corrector = UniversalCorrectorTester()
        self.assertEqual(correct(corrector, "lowercase start.<br/>and lowercase after full stop. yes."),
                                            "Lowercase start.<br/>And lowercase after full stop. Yes.")
        self.assertEqual(correct(corrector, "Question? answer!<br/>more lowercase. <b>why?</b> didn't check."),
                                            "Question? Answer!<br/>More lowercase. <b>Why?</b> didn't check.")
        self.assertEqual(correct(corrector, "After colons: and semicolons; we don't correct."),
                                            "After colons: and semicolons; we don't correct.")

    def test_filename_corrections(self):
        corrector = UniversalCorrectorTester()
        self.assertEqual(filename_correct(corrector, "dummy file name.pdf"), "dummy_file_name.pdf")
        self.assertEqual(filename_correct(corrector, "too__many___underscores.odt"), "too_many_underscores.odt")
        self.assertEqual(filename_correct(corrector, "capitalized_extension.PDF"), "capitalized_extension.pdf")
        self.assertEqual(filename_correct(corrector, "capitalized_extension.Pdf"), "capitalized_extension.pdf")
        with self.assertLogs('pywikitools.correctbot.base', level='WARNING'):
            self.assertEqual(filename_correct(corrector, "Not a filename"), "Not a filename")
        with self.assertLogs('pywikitools.correctbot.base', level='WARNING'):
            self.assertEqual(filename_correct(corrector, "other extension.exe"), "other extension.exe")

    def test_dash_correction(self):
        corrector = UniversalCorrectorTester()
        self.assertEqual(correct(corrector, "Using long dash - not easy."), "Using long dash – not easy.")

    def test_final_dot_correction(self):
        corrector = UniversalCorrectorTester()
        self.assertEqual(correct(corrector, "<b>Ein ganzer Satz</b>", "<b>A full sentence.</b>"),
                                            "<b>Ein ganzer Satz.</b>")
        self.assertEqual(correct(corrector, "Ein ganzer Satz", "A full sentence"), "Ein ganzer Satz")



# TODO    def test_correct_ellipsis(self):
#        corrector = UniversalCorrectorTester()
#        self.assertEqual(correct(corrector, "…"), "...")


class RTLCorrectorTester(CorrectorBase, RTLCorrector):
    """With this class we can test the rules of RTLCorrector"""
    pass


class TestRTLCorrector(CorrectorTestCase):
    @classmethod
    def setUpClass(cls):
        cls.corrector = RTLCorrectorTester()

    def test_fix_rtl_title(self):
        self.compare_title_revisions("Bible_Reading_Hints_(Seven_Stories_full_of_Hope)", "fa", 57796, 62364)

    def test_fix_rtl_filename(self):
        self.compare_filename_revisions("Bible_Reading_Hints_(Seven_Stories_full_of_Hope)", "fa", 2, 22794, 22801)


class TestGermanCorrector(CorrectorTestCase):
    def test_correct_quotes(self):
        corrector = GermanCorrector()
        for wrong in ['"Test"', '“Test”', '“Test„', '„Test„', '“Test“', '„Test"', '„Test“']:
            self.assertEqual(correct(corrector, wrong), '„Test“')
            self.assertEqual(correct(corrector, f"Beginn und {wrong}"), 'Beginn und „Test“')
            self.assertEqual(correct(corrector, f"{wrong} und Ende."), '„Test“ und Ende.')
            self.assertEqual(correct(corrector, f"Beginn und {wrong} und Ende."), 'Beginn und „Test“ und Ende.')
            self.assertEqual(correct(corrector, f"Beginn und {wrong} und Ende."), 'Beginn und „Test“ und Ende.')

        with self.assertLogs('pywikitools.correctbot.de', level='WARNING'):
            self.assertEqual(correct(corrector, '"Das ist" seltsam"'), '"Das ist" seltsam"')

        valid_strings: List[str] = [    # Some more complex examples
            "(siehe Arbeitsblatt „[[Forgiving Step by Step/de|Schritte der Vergebung]]“)",
            "[[How to Continue After a Prayer Time/de|„Wie es nach einer Gebetszeit weitergeht“]]",
            "(indem er sagt: „Ich vergebe mir.“)",
            "(Zum Beispiel: „Gott, wir kommen zu dir als den Richter[...] hilf du ____ in diesem Prozess.“)",
            "(„Was heißt Vergeben?“)",
            "„ich habe mich missverstanden gefühlt“,",
            "Vergebung bedeutet nicht zu sagen „das war ja nur eine Kleinigkeit“.",
            "„Gott, bitte <b>Hilf</b> mir zu vergeben. Amen.“"
        ]
        for valid in valid_strings:
            # with self.assertNoLogs(): # Available from Python 3.10
            self.assertEqual(correct(corrector, valid), valid)   # Check that correct strings remain correct
            needs_correction = valid.replace("„", '"')
            needs_correction = needs_correction.replace("”", '"')
            # Now make sure this problematic version gets corrected back to the correct form
            self.assertEqual(correct(corrector, needs_correction), valid)


"""TODO
class TestEnglishCorrector(unittest.TestCase):
    def test_correct_apostrophe(self):
        corrector = EnglishCorrector()
        self.assertEqual(correct(corrector, "God's"), "God’s")

    def test_correct_quotation_marks(self):
        corrector = EnglishCorrector()
        for wrong in ['"Test"', '“Test”', '“Test„', '„Test„', '“Test“', '„Test"', '„Test“']:
            self.assertEqual(correct(corrector, wrong), '“Test”')
"""

class TestFrenchCorrector(unittest.TestCase):
    def test_punctuation(self):
        """
        Ensure correct spaces around punctuation:

        No space before comma and dot, space before ; : ! ?
        Space after all punctuation marks.
        """
        corrector = FrenchCorrector()
        self.assertEqual(correct(corrector, "Mais moi , je vous dis: Si"), "Mais moi, je vous dis\u00a0: Si")
        self.assertEqual(correct(corrector, "Si quelqu’un dit à son frère: “Imbécile!”"),
                                           "Si quelqu’un dit à son frère\u00a0: “Imbécile\u00a0!”")
        self.assertEqual(correct(corrector, "Comment prier?<br/>Comment jeûner?"),
                                           "Comment prier\u00a0?<br/>Comment jeûner\u00a0?")
        self.assertEqual(correct(corrector, "Ne jugez pas les autres,et Dieu ne vous jugera pas . En effet ,Dieu"),
                                           "Ne jugez pas les autres, et Dieu ne vous jugera pas. En effet, Dieu")

    def test_false_friends_replacement(self):
        corrector = FrenchCorrector()
        self.assertEqual(correct(corrector, "Example"), "Exemple")

    def test_correct_quotation_marks(self):
        corrector = FrenchCorrector()
        wrongs: List[str] = ['"Test"', "« Test »", "«Test»"]
        for wrong in wrongs:
            self.assertEqual(correct(corrector, wrong), "«\u00a0Test\u00a0»")
        # Make sure several corrections in one longer string also work correctly
        self.assertEqual(correct(corrector, " Connect ".join(wrongs)), " Connect ".join(["«\u00a0Test\u00a0»"] * 3))
        with self.assertLogs('pywikitools.correctbot.fr', level="WARNING"):
            self.assertEqual(correct(corrector, "“Test”"), "“Test”")

class TestArabicCorrector(CorrectorTestCase):
    # TODO research which of these changes to improve Arabic language quality could be automated:
    # https://www.4training.net/mediawiki/index.php?title=Forgiving_Step_by_Step%2Far&type=revision&diff=29760&oldid=29122
    @classmethod
    def setUpClass(cls):
        cls.corrector = ArabicCorrector()

    def test_correct_punctuation(self):
        self.assertEqual(correct(self.corrector, ","), "،")
        self.assertEqual(correct(self.corrector, "منهم،حتى"), "منهم، حتى")
        with self.assertLogs('pywikitools.correctbot.base', level='WARNING'):
            self.assertEqual(correct(self.corrector, ";"),  "؛")
        self.assertEqual(correct(self.corrector, "ما هو من عند الله?"), "ما هو من عند الله؟")

    def test_correct_spaces(self):
        self.assertEqual(correct(self.corrector, "يدعي  و يصلي"), "يدعي و يصلي")
        self.assertEqual(correct(self.corrector, "بحرص ،  أن"), "بحرص، أن")

    def test_real_life_examples(self):
        self.compare_revisions("How to Continue After a Prayer Time", "ar", 4, 62201, 62260)
        self.compare_revisions("How to Continue After a Prayer Time", "ar", 16, 62225, 62270)
        self.compare_title_revisions("How to Continue After a Prayer Time", "ar", 62193, 62274)
#       TODO this would require passing the original text as well so that final dot gets added
#        self.compare_revisions("How_to_Continue_After_a_Prayer_Time", "ar", 1, 62195, 62258)


if __name__ == '__main__':
    unittest.main()
