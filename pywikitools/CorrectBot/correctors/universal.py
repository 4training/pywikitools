"""
This module contains core classes for the correcting functionality:
- LanguageCorrector as the base class for all language-specific corrector classes
- UniversalCorrector containing rules that can be applied in all languages
- Corrector classes for groups of languages

Every language-specific corrector inherits from multiple classes:
- LanguageCorrector for the core functionality (invoking the correction and gathering statistics)
- UniversalCorrector and more classes (for groups of languages) with correction functions

By using multiple inheritance we can add correction functionality in an easy and flexible way.
The calling of corrector functions is done by introspection following these naming conventions:
Functions starting with "correct_": applied to every translation unit
Functions ending with "_title": applied only to the title translation unit
Functions ending with "_filename": applied only to translation units containing a file name

Caution: functions in a language-specific corrector must never have the same names as
one of the functions here (otherwise only one of it gets called in the case of multiple inheritance)

Each function should have a documentation string which will be used for print_stats()

Implementation notes:
The alternative to using introspection would be to register the correction functions
introduced by each class during initialization. That would be more explicit but
it gets a bit tricky with multiple inheritance and making sure that __init__() of
each base class gets called

"""
import re
from typing import List, Generator
from collections import defaultdict

class LanguageCorrector:
    """
    Base class for all language-specific correctors

    Correctors should inherit from this class first.
    Correctors for groups of languages should not inherit from the class.

    """
    def __init__(self):
        # Counter for how often a particular rule (function) corrected something
        self._stats = defaultdict(int)

    def correct(self, text: str) -> str:
        """ Call all available correction functions one after the other and return the corrected string. """
        return self._run_correction_functions(text, (s for s in dir(self) if s.startswith("correct_")))

    def title_correct(self, text: str) -> str:
        """ Call all correction functions for titles one after the other and return the corrected string. """
        return self._run_correction_functions(text, (s for s in dir(self) if s.endswith("_title")))

    def filename_correct(self, text: str) -> str:
        """
        Call all correction functions for filenames one after the other and return the corrected string.

        Only correct if we have a file name with one of the following extensions: '.doc', '.odg', '.odt', '.pdf'
        """
        if not text.lower().endswith(('.doc', '.odg', '.odt', '.pdf')):
            # TODO better logging?
            print(f"WARNING: input parameter does not seem to be a file name: {text}")
            return text

        return self._run_correction_functions(text, (s for s in dir(self) if s.endswith("_filename")))

    def _run_correction_functions(self, text: str, functions: Generator[str, None, None]) -> str:
        """
        Call all the functions given by the generator one after the other and return the corrected string.

        Caution: the generator must not yield any function from this class, otherwise we run into indefinite recursion
        """
        result = text

        for corrector_function in functions:
            # calling each function
            result = getattr(self, corrector_function)(text)
            if text != result:
                self._stats[corrector_function] += 1
            text = result

        return result

    def print_stats(self) -> str:
        """
        Give a detailed overview how much corrections were made and by which functions.

        In the details we'll read from the documentation strings of the functions used.
        If a function is not documented then just its name is printed.
        """
        details: str = ""
        total_counter: int = 0
        for function_name, counter in self._stats.items():
            total_counter += counter
            documentation = getattr(self, function_name).__doc__
            if documentation is not None:
                details += " - " + documentation
            else:
                details += " - " + function_name
            details += f" ({counter}x)\n"
        result = f"{total_counter} corrections"
        if details != "":
            result += ":\n" + details
        return result


class UniversalCorrector():
    """Has language-independent correction functions"""
    # TODO: Instead of ellipsis (…), use "..." - write a function for it.
    # Should we have that in this class, e.g. do we want this for all languages?

    def correct_replace_e_with_i(self, text: str) -> str:
        """TODO for testing only: Replace e with i"""
        return text.replace("e", "i")

    def correct_wrong_capitalization(self, text: str) -> str:
        """Fix wrong capitalization at the beginning of a sentence or after a colon"""
        # Or to say it differently: the letter following a .!?;: will be capitalized

        # TODO maybe this needs to be cut out of UniversalCorrector into a separate class
        # because there may be languages where this doesn't work

        # TODO: Quotation marks are not yet covered - double check if necessary
        find_wrong_capitalization = re.compile(r'[.!?:;]\s*([a-z])')
        matches = re.finditer(find_wrong_capitalization, text)
        for match in reversed(list(matches)):
            text = text[:match.end() - 1] + match.group(1).upper() + text[match.end():]
        text = text[0].upper() + text[1:]
        return text

    def correct_multiple_spaces(self, text: str) -> str:
        """Reduce multiple spaces to one space"""
        check_multiple_spaces = re.compile(r'( ){2,}')
        return re.sub(check_multiple_spaces, ' ', text)

    def correct_missing_spaces(self, text: str) -> str:
        """Insert missing spaces between punctuation and characters"""
        check_missing_spaces = re.compile(r'([.!?;,])(\w)')
        return re.sub(check_missing_spaces, r'\1 \2', text)

    def correct_wrong_spaces(self, text: str) -> str:
        """Erase redundant spaces before punctuation"""
        check_wrong_spaces = re.compile(r'\s+([.!?;,])')
        return re.sub(check_wrong_spaces, r'\1', text)

    def make_lowercase_extension_in_filename(self, text: str) -> str:
        """Have file ending in lower case"""
        if len(text) <= 4:
            print(f"WARNING: File name too short: {text}")
            return text
        return text[:-4] + text[-4:].lower()

    def remove_spaces_in_filename(self, text: str) -> str:
        """Replace spaces in file name with single underscore"""
        return re.sub(r"( )+", '_', text)

    def remove_multiple_underscores_in_filename(self, text: str) -> str:
        """Replace multiple consecutive underscores with single underscore in file name"""
        return re.sub(r"_+", '_', text)


class RTLCorrector():
    """Corrections for right-to-left languages"""

    def fix_rtl_title(self, text: str) -> str:
        """When title ends with closing parenthesis, add a RTL mark at the end"""
        return re.sub(r'\)$', ')\u200f', text)

    def fix_rtl_filename(self, text: str) -> str:
        """ when file name has a closing parenthesis right before the file ending,
        make sure we have a RTL mark in there!
        """
        file_extensions: List[str] = ['.pdf', '.odt', '.doc', '.odg']
        if not text.endswith(tuple(file_extensions)):
            # TODO log something / write warning
            return text
        re.sub(r'\)\.([a-z][a-z][a-z])$', ')\u200f.\\1', text)
        return text
