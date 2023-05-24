"""
Test cases for CorrectBot: Testing core functionality as well as language-specific rules
"""
from configparser import ConfigParser
from inspect import signature
import subprocess
import unittest
import importlib
from os import listdir
from os.path import abspath, dirname, isfile, join, normpath
from typing import Callable, Dict, List, Optional
from unittest.mock import patch, Mock

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.correctbot.correct_bot import CorrectBot
from pywikitools.correctbot.correctors.fa import PersianCorrector
from pywikitools.correctbot.correctors.ar import ArabicCorrector
from pywikitools.correctbot.correctors.base import CorrectorBase
from pywikitools.correctbot.correctors.de import GermanCorrector
from pywikitools.correctbot.correctors.fr import FrenchCorrector
from pywikitools.correctbot.correctors.tr import TurkishCorrector
from pywikitools.correctbot.correctors.universal import NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector, \
                                                        RTLCorrector, UniversalCorrector
from pywikitools.lang.translated_page import TranslatedPage, TranslationUnit
from pywikitools.test.test_translated_page import TEST_UNIT_WITH_DEFINITION, TEST_UNIT_WITH_DEFINITION_DE_ERROR


# hyphen in module name is not recommended so we need to use import_module here
tr_tanri = importlib.import_module("pywikitools.correctbot.correctors.tr-tanri")

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
    result = corrector.correct(unit)
    return result.suggestions.get_translation()


def title_correct(corrector: CorrectorBase, text: str, original: Optional[str] = None) -> str:
    """Shorthand function for running a test with CorrectorBase.title_correct()"""
    if original is None:
        original = ""       # title correcting functions should never use @use_snippets
    unit = TranslationUnit("Test/Page display title", "test", original, text)
    result = corrector.title_correct(unit)
    return result.suggestions.get_translation()


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
    which is similar to https://www.4training.net/mediawiki/index.php?Translations:How_to_Continue_After_a_Prayer_Time/1/ar&type=revision&diff=62258&oldid=62195    # noqa: E501
    See also https://www.4training.net/mediawiki/index.php?title=Translations:How_to_Continue_After_a_Prayer_Time/1/ar&action=history                               # noqa: E501
    """
    corrector: CorrectorBase    # Avoiding mypy/pylint warnings, see https://github.com/python/mypy/issues/8723

    def compare_revisions(self, page: str, language_code: str, identifier: int, old_revision: int, new_revision: int):
        """For all "normal" translation units: Calls CorrectorBase.correct()"""
        fortraininglib = ForTrainingLib("https://www.4training.net")
        old_content = fortraininglib.get_translated_unit(page, language_code, identifier, old_revision)
        new_content = fortraininglib.get_translated_unit(page, language_code, identifier, new_revision)
        original_content = fortraininglib.get_translated_unit(page, "en", identifier)
        fortraininglib.session.close()
        self.assertIsNotNone(old_content)
        self.assertIsNotNone(new_content)
        self.assertEqual(correct(self.corrector, old_content, original_content), new_content)

    def compare_title_revisions(self, page: str, language_code: str, old_revision: int, new_revision):
        """Calls CorrectBase.title_correct()"""
        fortraininglib = ForTrainingLib("https://www.4training.net")
        old_content = fortraininglib.get_translated_title(page, language_code, old_revision)
        new_content = fortraininglib.get_translated_title(page, language_code, new_revision)
        fortraininglib.session.close()
        self.assertIsNotNone(old_content)
        self.assertIsNotNone(new_content)
        self.assertEqual(title_correct(self.corrector, old_content), new_content)


class TestLanguageCorrectors(unittest.TestCase):
    def setUp(self):
        """Load all language-specific corrector classes so that we can afterwards easily run our checks on them"""
        self.language_correctors: List[Callable] = []
        folder = normpath(join(dirname(abspath(__file__)), CORRECTORS_FOLDER))

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
        """Make sure each function either starts with 'correct_' or ends with '_title'"""
        for language_corrector in self.language_correctors:
            for function_name in dir(language_corrector):
                # Ignore private functions
                if function_name.startswith('_'):
                    continue
                # Ignore everything inherited from CorrectorBase
                if getattr(language_corrector, function_name).__module__ == MOD_BASE:
                    continue
                self.assertNotEqual(function_name, "filename")  # Special case from CorrectBot.check_unit()
                self.assertTrue(function_name.startswith("correct_")
                                or function_name.endswith("_title"),
                                msg=f"Invalid function name {language_corrector.__name__}.{function_name}")

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
                self.assertGreaterEqual(count_parameters, 1, msg=f"{language_corrector.__name__}.{function_name}")
                self.assertLessEqual(count_parameters, 2, msg=f"{language_corrector.__name__}.{function_name}")

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
                    self.assertNotIn(language_function, flexible_functions, msg=f"{language_corrector.__name__}: "
                                     f"Function name {language_function} already exists in a flexible corrector")

    def test_for_function_documentation(self):
        """Make sure that each corrector function has a documentation and its first line is not empty"""
        for language_corrector in self.language_correctors:
            for function_name in dir(language_corrector):
                # Ignore private functions
                if function_name.startswith('_'):
                    continue
                corrector_function = getattr(language_corrector, function_name)
                # Ignore everything inherited from CorrectorBase
                if corrector_function.__module__ == MOD_BASE:
                    continue
                # Make sure there is some documentation
                self.assertTrue(corrector_function.__doc__.strip(),
                                msg=f"Missing documentation of {language_corrector.__name__}.{function_name}")
                # Make sure the first line of the documentation isn't empty (as we take that for reporting)
                self.assertTrue(corrector_function.__doc__.partition("\n")[0].strip(),
                                msg=f"Documentation of {language_corrector.__name__}.{function_name}"
                                    " starts with empty line")

    # TODO: Write tests for use_snippets and suggest_only decorators


class UniversalCorrectorTester(CorrectorBase, UniversalCorrector):
    """With this class we can test the rules of UniversalCorrector"""
    def _suffix_for_print_version(self) -> str:
        return "_print"

    def _missing_spaces_exceptions(self) -> List[str]:
        return ["Test.This", "e.g.", "E.g."]

    def _capitalization_exceptions(self) -> List[str]:
        return ["e.g.", "E.g."]


class TestUniversalCorrector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corrector = UniversalCorrectorTester()

    def test_spaces(self):
        self.assertEqual(correct(self.corrector, "This entry   contains     too  many spaces."),
                                            "This entry contains too many spaces.")
        self.assertEqual(correct(self.corrector, "Missing.Spaces,after punctuation?Behold,again."),
                                            "Missing. Spaces, after punctuation? Behold, again.")
        self.assertEqual(correct(self.corrector, "This entry contains redundant spaces , before , punctuation ."),
                                            "This entry contains redundant spaces, before, punctuation.")
        self.assertEqual(correct(self.corrector, "Before  and   after."), "Before and after.")
        # now let's try if exceptions are correctly respected:
        self.assertEqual(correct(self.corrector, "John 3:16.Johannes 3,16."), "John 3:16. Johannes 3,16.")
        self.assertEqual(correct(self.corrector, "Test.This remains untouched."), "Test.This remains untouched.")
        self.assertEqual(correct(self.corrector, "Do not touch Test.This"), "Do not touch Test.This")
        self.assertEqual(correct(self.corrector, "Use e.g. unittest"), "Use e.g. unittest")
        self.assertEqual(correct(self.corrector, "E.g. this"), "E.g. this")
        self.assertEqual(correct(self.corrector, "Go ,end with ."), "Go, end with.")
        self.assertEqual(correct(self.corrector, "Continue ..."), "Continue ...")
        self.assertEqual(correct(self.corrector, "How do I survive if ... ?"), "How do I survive if ... ?")
        self.assertEqual(correct(self.corrector, "How do I survive if … ?"), "How do I survive if … ?")
        self.assertEqual(correct(self.corrector, "□ Yes    □ No    □"), "□ Yes    □ No    □")

    def test_print_stats(self):
        self.assertIn("Correct mediawiki links", self.corrector.print_stats({'correct_links': 4}))
        stats: Dict[str, int] = {'correct_multiple_spaces_also_in_title': 2,
                                 'correct_wrong_capitalization': 3}
        self.assertIn("Reduce multiple spaces", self.corrector.print_stats(stats))
        self.assertIn("Fix wrong capitalization", self.corrector.print_stats(stats))
        self.assertIn("not_existing", self.corrector.print_stats({'not_existing': 2}))
        self.assertIn("Correct filename", self.corrector.print_stats({'filename_correct': 5}))

    def test_capitalization(self):
        self.assertEqual(correct(self.corrector, "lowercase start.<br/>and lowercase after full stop. yes."),
                                                 "Lowercase start.<br/>And lowercase after full stop. Yes.")
        self.assertEqual(correct(self.corrector, "Question? answer!<br/>more lowercase.<br/>why? didn't check."),
                                                 "Question? Answer!<br/>More lowercase.<br/>Why? Didn't check.")
        self.assertEqual(correct(self.corrector, "After colons: and semicolons; we don't correct."),
                                                 "After colons: and semicolons; we don't correct.")

    def test_dash_correction(self):
        self.assertEqual(correct(self.corrector, "Using long dash - not easy."), "Using long dash – not easy.")

    def test_final_dot_correction(self):
        self.assertEqual(correct(self.corrector, "* Ein Wort\n* Ein ganzer Satz", "* A word\n* A full sentence."),
                                                 "* Ein Wort\n* Ein ganzer Satz.")
        self.assertEqual(correct(self.corrector, "Ein ganzer Satz", "A full sentence"), "Ein ganzer Satz")

    def test_mediawiki_bold_italic(self):
        self.assertEqual(correct(self.corrector, "''italic'' and '''bold'''"), "<i>italic</i> and <b>bold</b>")
        self.assertEqual(correct(self.corrector, "This is '''''italic and bold'''''."),
                                                 "This is <b><i>italic and bold</i></b>.")
        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            self.assertEqual(correct(self.corrector, "'''''Uneven markup"), "'''''Uneven markup")
        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            self.assertEqual(correct(self.corrector, "''''Problematic markup"), "''''Problematic markup")
        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            self.assertEqual(correct(self.corrector, "'''Uneven''' '''markup"), "'''Uneven''' '''markup")
        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            self.assertEqual(correct(self.corrector, "''Uneven'' ''markup"), "''Uneven'' ''markup")
        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            self.assertEqual(correct(self.corrector, "<b>Uneven tags<b>"), "<b>Uneven tags<b>")
        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            self.assertEqual(correct(self.corrector, "</i>Uneven tags</i>"), "</i>Uneven tags</i>")
        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            self.assertEqual(correct(self.corrector, ">i<Confused tags>b<"), "<i>Confused tags<b>")

    def test_get_language_code(self):
        # This should return an empty string as we're not in a language-specific corrector
        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            self.assertEqual(self.corrector._get_language_code(), "")

    def test_correct_links(self):
        # In this test setting nothing should be changed
        self.assertEqual(self.corrector.correct_links("[[Dest|Desc]]", "[[Orig|Orig]]"), "[[Dest|Desc]]")
        # Warn on misformatted link
        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            self.assertEqual(self.corrector.correct_links("[[Simple link]]", "[[Orig]]"), "[[Simple link]]")

    def test_remove_trailing_dot_in_title(self):
        self.assertEqual(title_correct(self.corrector, "Title."), "Title")
        self.assertEqual(title_correct(self.corrector, "Title with no dot"), "Title with no dot")

    def test_correct_by_trimming(self):
        self.assertEqual(correct(self.corrector, "\tTitle \n"), "Title")
        self.assertEqual(title_correct(self.corrector, "\tTitle \n"), "Title")

# TODO    def test_correct_ellipsis(self):
#        self.assertEqual(correct(self.corrector, "…"), "...")


class NoSpaceBeforePunctuationCorrectorTester(CorrectorBase, NoSpaceBeforePunctuationCorrector):
    """With this class we can test the rules of NoSpaceBeforePunctuationCorrector"""
    def _suffix_for_print_version(self) -> str:
        return "_print"


class TestNoSpaceBeforePunctuationCorrector(CorrectorTestCase):
    def test_spaces(self):
        corrector = NoSpaceBeforePunctuationCorrectorTester()
        self.assertEqual(correct(corrector, "I want this ! And you   ?"), "I want this! And you?")
        self.assertEqual(correct(corrector, "I want ... ! How about ___ ?"), "I want ... ! How about ___ ?")
        self.assertEqual(correct(corrector, "Ellipsis … ? Sure … !"), "Ellipsis … ? Sure … !")


class QuotationMarkCorrectorTester(CorrectorBase, QuotationMarkCorrector):
    """With this class we can test the rules of QuotationMarkCorrector"""
    def correct_quotes(self, text: str) -> str:
        return self._correct_quotes('»', '«', text)

    def _suffix_for_print_version(self) -> str:
        return "_print"


class TestQuotationMarkCorrector(CorrectorTestCase):
    def test_correct_quotes(self):
        corrector = QuotationMarkCorrectorTester()
        for wrong in ['"Test"', '“Test”', '“Test„', '„Test„', '“Test“', '„Test"', '„Test“']:
            self.assertEqual(correct(corrector, wrong), '»Test«')
            self.assertEqual(correct(corrector, f"Start and {wrong}"), 'Start and »Test«')
            self.assertEqual(correct(corrector, f"{wrong} and end."), '»Test« and end.')
            self.assertEqual(correct(corrector, f"Start and {wrong} and end."), 'Start and »Test« and end.')
            self.assertEqual(correct(corrector, f"{wrong}, {wrong} and “Test”."), '»Test«, »Test« and »Test«.')

        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            self.assertEqual(correct(corrector, '"Something" wrong"'), '"Something" wrong"')


class RTLCorrectorTester(CorrectorBase, RTLCorrector):
    """With this class we can test the rules of RTLCorrector"""
    def _suffix_for_print_version(self) -> str:
        return "_print"


class TestRTLCorrector(CorrectorTestCase):
    @classmethod
    def setUpClass(cls):
        cls.corrector = RTLCorrectorTester()

    def test_correct_punctuation(self):
        self.assertEqual(correct(self.corrector, ","), "،")
        self.assertEqual(correct(self.corrector, "منهم; حتى"), "منهم؛ حتى")
        self.assertEqual(correct(self.corrector, "ما هو من عند الله?"), "ما هو من عند الله؟")
        # Make sure mediawiki : and ; formatting (at beginning of lines) remain unchanged
        self.assertEqual(correct(self.corrector, ";التدوين و الكتابة\n:من"), ";التدوين و الكتابة\n:من")

    def test_fix_rtl_title(self):
        self.compare_title_revisions("Bible_Reading_Hints_(Seven_Stories_full_of_Hope)", "fa", 57796, 62364)


class TestGermanCorrector(CorrectorTestCase):
    @classmethod
    def setUpClass(cls):
        cls.corrector = GermanCorrector()

    def test_correct_quotes(self):
        for wrong in ['"Test"', '“Test”', '“Test„', '„Test„', '“Test“', '„Test"', '„Test“']:
            self.assertEqual(correct(self.corrector, wrong), '„Test“')
            self.assertEqual(correct(self.corrector, f"Beginn und {wrong}"), 'Beginn und „Test“')
            self.assertEqual(correct(self.corrector, f"{wrong} und Ende."), '„Test“ und Ende.')
            self.assertEqual(correct(self.corrector, f"Beginn und {wrong} und Ende."), 'Beginn und „Test“ und Ende.')

        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            self.assertEqual(correct(self.corrector, '"Das ist" seltsam"'), '"Das ist" seltsam"')

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
            self.assertEqual(correct(self.corrector, valid), valid)   # Check that correct strings remain correct
            needs_correction = valid.replace("„", '"')
            needs_correction = needs_correction.replace("”", '"')
            # Now make sure this problematic version gets corrected back to the correct form
            self.assertEqual(correct(self.corrector, needs_correction), valid)

    def test_exceptions(self):
        for exception in ["So z.B. auch", "1.Korinther 14,3", "Siehe 1.Mose 40", "Z.B.", "Ggf. möglich"]:
            self.assertEqual(correct(self.corrector, exception), exception)

    def test_get_language_code(self):
        self.assertEqual(self.corrector._get_language_code(), "de")

    def test_correct_links(self):
        to_correct = "Siehe [[Gebet| Gebet]] und [[Heilung]][[Test]] oder [[#unten]]."
        corrected = "Siehe [[Prayer/de|Gebet]] und [[Healing/de|Heilung]][[Test/de|Test]] oder [[#unten]]."
        english = "See [[Prayer|Prayer]] and [[Healing|Healing]][[Test|Test]] or [[#below]]."
        self.assertEqual(correct(self.corrector, to_correct, english), corrected)
        self.assertEqual(correct(self.corrector, corrected, english), corrected)     # correct text should not change
        with self.assertLogs('pywikitools.correctbot.correctors.universal', level='WARNING'):
            # Warn because the number of links in translation is less than in the English original
            self.assertEqual(correct(self.corrector, to_correct[21:], english), to_correct[21:])

    def test_suffix_for_print_version(self):
        self.assertNotEqual(self.corrector._suffix_for_print_version(), "_print")


"""TODO
class TestEnglishCorrector(unittest.TestCase):
    def test_correct_apostrophe(self):
        corrector = EnglishCorrector()
        self.assertEqual(correct(corrector, "God's"), "God’s")

    def test_correct_quotes(self):
        corrector = EnglishCorrector()
        for wrong in ['"Test"', '“Test”', '“Test„', '„Test„', '“Test“', '„Test"', '„Test“']:
            self.assertEqual(correct(corrector, wrong), '“Test”')
"""

FRENCH_CORRECTIONS: Dict[str, str] = {
    "Mais moi , je vous dis: Si":
    "Mais moi, je vous dis\u00a0: Si",
    "Si quelqu’un dit à son frère: Imbécile!":
    "Si quelqu’un dit à son frère\u00a0: Imbécile\u00a0!",
    "Comment prier?<br/>Comment jeûner?":
    "Comment prier\u00a0?<br/>Comment jeûner\u00a0?",
    "Ne jugez pas les autres,et Dieu ne vous jugera pas . En effet ,Dieu":
    "Ne jugez pas les autres, et Dieu ne vous jugera pas. En effet, Dieu"
}


class TestFrenchCorrector(unittest.TestCase):
    def test_punctuation(self):
        """
        Ensure correct spaces around punctuation:

        No space before comma and dot, space before ; : ! ?
        Space after all punctuation marks.
        """
        corrector = FrenchCorrector()
        for faulty, corrected in FRENCH_CORRECTIONS.items():
            self.assertEqual(correct(corrector, faulty), corrected)
        # Bible references (punctuation between digits) should not be touched
        self.assertEqual(correct(corrector, "Romains 12:2"), "Romains 12:2")
        # Make sure mediawiki : and ; formatting (at beginning of lines) remain unchanged
        self.assertEqual(correct(corrector, ";L'écriture\n:Il"), ";L'écriture\n:Il")

    def test_false_friends_replacement(self):
        corrector = FrenchCorrector()
        self.assertEqual(correct(corrector, "Example"), "Exemple")

    def test_correct_quotes(self):
        corrector = FrenchCorrector()
        wrongs: List[str] = ['"Test"', "« Test »", "«Test»"]
        for wrong in wrongs:
            self.assertEqual(correct(corrector, wrong), "«\u00a0Test\u00a0»")
        # Make sure several corrections in one longer string also work correctly
        self.assertEqual(correct(corrector, " Connect ".join(wrongs)), " Connect ".join(["«\u00a0Test\u00a0»"] * 3))
        with self.assertLogs('pywikitools.correctbot.correctors.fr', level="WARNING"):
            self.assertEqual(correct(corrector, "Test a “test”"), "Test a “test”")

    def test_get_language_code(self):
        corrector = FrenchCorrector()
        self.assertEqual(corrector._get_language_code(), "fr")

    def test_suffix_for_print_version(self):
        corrector = FrenchCorrector()
        self.assertNotEqual(corrector._suffix_for_print_version(), "_print")


class TestTurkishCorrector(CorrectorTestCase):
    def test_all_rules(self):
        corrector = TurkishCorrector()
        self.assertEqual(corrector._get_language_code(), "tr")
        self.assertEqual(corrector._compose_filename("Şifa", ".pdf", False), "Şifa.pdf")
        self.assertEqual(corrector._compose_filename("Kutsal_Kitabı_okuma_ipuçları", ".pdf", True),
                                                     "Kutsal_Kitabı_okuma_ipuçları_yazdır.pdf")
        self.assertEqual(correct(corrector, '"küçük"  bir günah işlediler - bizim için.devam , bitti .'),
                                            '“küçük” bir günah işlediler – bizim için. Devam, bitti.')
        self.assertEqual(correct(corrector, "1.Yuhanna, 1.Petrus,1.Timoteos vs. okuyun ."),
                                            "1.Yuhanna, 1.Petrus, 1.Timoteos vs. okuyun.")


class TestTurkishSecularCorrector(CorrectorTestCase):
    def test_all_rules(self):
        corrector = tr_tanri.TurkishSecularCorrector()
        self.assertEqual(corrector._get_language_code(), "tr-tanri")
        self.assertEqual(corrector._compose_filename("Şifa", ".pdf", False), "Şifa_(Tanrı).pdf")
        self.assertEqual(corrector._compose_filename("Kutsal_Kitabı_okuma_ipuçları", ".pdf", True),
                                                     "Kutsal_Kitabı_okuma_ipuçları_(Tanrı)_yazdır.pdf")
        self.assertEqual(corrector._compose_filename("Tanrının_Hikâyesi", ".pdf", False),
                                                     "Tanrının_Hikâyesi.pdf")
        self.assertEqual(correct(corrector, '"küçük"  bir günah işlediler - bizim vs. için.devam , bitti .'),
                                            '“küçük” bir günah işlediler – bizim vs. için. Devam, bitti.')


class TestArabicCorrector(CorrectorTestCase):
    # TODO research which of these changes to improve Arabic language quality could be automated:
    # https://www.4training.net/mediawiki/index.php?title=Forgiving_Step_by_Step%2Far&type=revision&diff=29760&oldid=29122
    @classmethod
    def setUpClass(cls):
        cls.corrector = ArabicCorrector()

    def test_correct_spaces(self):
        self.assertEqual(correct(self.corrector, "منهم،حتى"), "منهم، حتى")
        self.assertEqual(correct(self.corrector, "يدعي  و يصلي"), "يدعي و يصلي")
        self.assertEqual(correct(self.corrector, "بحرص ،  أن"), "بحرص، أن")

    def test_correct_quotes(self):
        self.assertEqual(correct(self.corrector, 'و "كلمة الله" و'), 'و ”كلمة الله“ و')
        self.assertEqual(correct(self.corrector, 'و “كلمة الله” و'), 'و ”كلمة الله“ و')

    def test_real_life_examples(self):
        self.compare_revisions("How to Continue After a Prayer Time", "ar", 4, 62201, 62260)
        self.compare_revisions("How to Continue After a Prayer Time", "ar", 16, 62225, 62270)
        self.compare_title_revisions("How to Continue After a Prayer Time", "ar", 62193, 62274)
        self.compare_revisions("How_to_Continue_After_a_Prayer_Time", "ar", 1, 62195, 62258)


class TestPersianCorrector(CorrectorTestCase):
    def test_correct_quotes(self):
        corrector = PersianCorrector()
        self.assertEqual(correct(corrector, 'کلمه "شنیدن" استفاده'), 'کلمه «شنیدن» استفاده')
        self.assertEqual(correct(corrector, 'کلمه ”شنیدن“ استفاده'), 'کلمه «شنیدن» استفاده')


class TestCorrectBot(unittest.TestCase):
    def setUp(self):
        self.config = ConfigParser()
        self.config.read_dict({"mediawiki": {"baseurl": "https://www.4training.net", "scriptpath": "/mediawiki"}})
        self.correctbot = CorrectBot(self.config, True)

    @patch("pywikitools.correctbot.correct_bot.subprocess.Popen")
    def test_empty_job_queue(self, mock_popen):
        # configuration for emptying job queue missing
        with self.assertLogs("pywikitools.correctbot", level="WARNING"):
            self.assertFalse(self.correctbot.empty_job_queue())

        self.config.read_dict({"Paths": {"php": "path/to/php"},
                               "correctbot": {"runjobs": "/path/to/runJobs.php"}})

        # successfully emptying job queue
        mock_popen.return_value.wait.return_value = 0
        self.assertTrue(self.correctbot.empty_job_queue())

        # runJobs.php failed
        mock_popen.return_value.wait.return_value = 1
        with self.assertLogs("pywikitools.correctbot", level="WARNING") as logs:
            self.assertFalse(self.correctbot.empty_job_queue())
        self.assertIn("Exit code: 1", logs.output[0])

        # runJobs.php times out
        mock_popen.return_value.wait.side_effect = subprocess.TimeoutExpired("", 15)
        with self.assertLogs("pywikitools.correctbot", level="WARNING"):
            self.assertFalse(self.correctbot.empty_job_queue())

    def test_check_unit(self):
        corrector = FrenchCorrector()
        # check_unit() should return None if translation is empty
        self.assertIsNone(self.correctbot.check_unit(corrector, TranslationUnit("Test/1", "fr", "Test", "")))

        # check_unit() should return None if we have the translation unit with version information
        self.assertIsNone(self.correctbot.check_unit(corrector, TranslationUnit("Test/1", "fr", "1.2", "1.2a")))

        for faulty, corrected in FRENCH_CORRECTIONS.items():
            translation_unit = TranslationUnit("Test", "fr", "ignored", faulty)
            result = self.correctbot.check_unit(corrector, translation_unit)
            self.assertEqual(faulty, result.corrections.get_original_translation())
            self.assertEqual(corrected, result.suggestions.get_translation())
            # Apply only one rule which doesn't even exist: No changes should be made
            result = self.correctbot.check_unit(corrector, translation_unit, "not_existing_rule")
            self.assertEqual(faulty, result.corrections.get_original_translation())
            self.assertEqual(faulty, result.suggestions.get_translation())

        # Test that apply_only_rule works as expected
        translation_unit = TranslationUnit("Test", "fr", "ignored", "Mais moi , je vous dis: Si")
        result = self.correctbot.check_unit(corrector, translation_unit, "correct_spaces_before_comma_and_dot")
        self.assertEqual("Mais moi, je vous dis: Si", result.suggestions.get_translation())
        result = self.correctbot.check_unit(corrector, translation_unit, "correct_spaces_before_punctuation")
        self.assertEqual("Mais moi , je vous dis\u00a0: Si", result.suggestions.get_translation())

        # Test correction of file name according to title
        unit_title = TranslationUnit("Test/Page_display_title", "fr", "Testing: Now", "Tester: Maintenant")
        self.correctbot.check_unit(corrector, unit_title)
        self.assertEqual(self.correctbot._translated_title, "Tester: Maintenant")
        unit_filename = TranslationUnit("Test/5", "fr", "Testing_Now.pdf", "Wrong.pdf")
        result = self.correctbot.check_unit(corrector, unit_filename)
        self.assertIsNotNone(result)
        self.assertTrue(result.corrections.has_translation_changes())
        self.assertEqual(result.corrections.get_translation(), "Tester_Maintenant.pdf")
        self.assertFalse(unit_filename.has_translation_changes())    # The unit we gave shouldn't be touched
        # A special PDF for printing should receive the translated suffix
        unit_filename_print = TranslationUnit("Test/6", "fr", "Testing_Now_print.pdf", "Pas_correcte.pdf")
        result = self.correctbot.check_unit(corrector, unit_filename_print)
        self.assertEqual(result.corrections.get_translation(), "Tester_Maintenant_impression.pdf")
        # Internal error: we haven't information on title yet
        self.correctbot._translated_title = None
        with self.assertLogs("pywikitools.correctbot", level="WARNING"):
            self.assertIsNone(self.correctbot.check_unit(corrector, unit_filename))
        # Title isn't translated
        self.correctbot._translated_title = ""
        self.assertIsNone(self.correctbot.check_unit(corrector, unit_filename))

        # If original and translation is the same: Below a length of 15 characters we assume that's okay
        unit = TranslationUnit("Test/2", "fr", "accident", "accident")
        self.assertIsNone(self.correctbot.check_unit(corrector, unit))
        unit = TranslationUnit("Test/2", "fr", "Please translate this.", "Please translate this.")
        result = self.correctbot.check_unit(corrector, unit)
        self.assertIsNotNone(result)
        self.assertFalse(result.corrections.has_translation_changes())
        self.assertFalse(result.suggestions.has_translation_changes())
        self.assertNotEqual(result.warnings, "")

    def prepare_translated_page(self) -> TranslatedPage:
        """Prepare a TranslatedPage object out of the FRENCH_CORRECTIONS dictionary"""
        translation_units: List[TranslationUnit] = []
        for counter, faulty in enumerate(FRENCH_CORRECTIONS.keys(), start=1):
            # The structure of original and translation needs to be the same
            original = "ignored" if "<br/>" not in faulty else "ignored<br/>ignored"
            translation_units.append(TranslationUnit(f"Test/{counter}", "fr", original, faulty))
        # Add one translation unit that will produce warnings because of wrong structure
        translation_units.append(TranslationUnit("Test/warnings1", "fr",
                                 TEST_UNIT_WITH_DEFINITION, TEST_UNIT_WITH_DEFINITION_DE_ERROR))
        # This unit will produce two warnings in correct_quotes()
        translation_units.append(TranslationUnit("Test/warnings2", "fr",
                                 'this is a "quote"', 'Ceci est une „citation"'))
        return TranslatedPage("Test", "fr", translation_units)

    def test_check_page(self):
        # check_page() raises RuntimeError if the page isn't existing
        mock_lib = Mock()
        mock_lib.get_translation_units.return_value = None
        self.correctbot.fortraininglib = mock_lib
        with self.assertRaises(RuntimeError):
            results = self.correctbot.check_page("NotExisting", "fr")
        mock_lib.get_translation_units.assert_called_once()

        # let's correct a page with some French translation units for testing
        mock_lib.get_translation_units.return_value = self.prepare_translated_page()
        with self.assertLogs("pywikitools.correctbot", level="WARNING"):
            results = self.correctbot.check_page("Test", "fr")
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 6)
        for result in results:
            if "warnings" in result.corrections.get_name():
                self.assertNotEqual(result.warnings, "")
                if "Test/warnings2" in result.corrections.get_name():
                    # There should be two warnings (separated by a line break)
                    self.assertIn("\n", result.warnings)
                continue
            faulty = result.corrections.get_original_translation()
            self.assertEqual(FRENCH_CORRECTIONS[faulty], result.suggestions.get_translation())

        # _load_corrector() and then check_page() should raise RuntimeError in case we can't load the corrector class
        with self.assertRaises(RuntimeError):
            self.correctbot.check_page("Test", "invalid")

    @patch("pywikibot.Page")
    def test_save_report(self, mock_page):
        """Check that output of CorrectBot.save_report() is the same as expected in data/correctbot_report.mediawiki

        The test page we use is constructed in self.prepare_translated_page()
        """
        mock_lib = Mock()
        mock_lib.index_url = "https://www.4training.net/mediawiki/index.php"
        mock_lib.get_translation_units.return_value = self.prepare_translated_page()
        mock_lib.count_jobs.return_value = 0
        self.correctbot.fortraininglib = mock_lib
        with self.assertLogs("pywikitools.correctbot", level="WARNING"):
            results = self.correctbot.check_page("Test", "fr")
        self.correctbot.save_report("Test", "fr", results)
        with open(join(dirname(abspath(__file__)), "data", "correctbot_report.mediawiki"), 'r') as f:
            self.assertEqual(mock_page.return_value.text, f.read())

        # if job queue is not empty a warning will be added to the report page
        self.assertNotIn("job queue is not empty", mock_page.return_value.text)
        mock_lib.count_jobs.return_value = 42
        with self.assertLogs("pywikitools.correctbot", level="WARNING"):
            self.correctbot.save_report("Test", "fr", results)
        self.assertIn("job queue is not empty", mock_page.return_value.text)
        mock_lib.count_jobs.return_value = 0

        self.assertNotIn(r"|direction=rtl}}", mock_page.return_value.text)
        self.assertNotIn("mw-content-rtl", mock_page.return_value.text)
        # check correct formatting for right-to-left languages
        mock_lib.get_language_direction.return_value = "rtl"
        self.correctbot.save_report("Test", "ar", results)
        self.assertIn(r"|direction=rtl}}", mock_page.return_value.text)
        self.assertIn('class="wikitable mw-content-rtl"', mock_page.return_value.text)


if __name__ == '__main__':
    unittest.main()
