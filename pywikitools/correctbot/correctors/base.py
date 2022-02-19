"""
This module contains the base class for all language-specific corrector classes

Every language-specific corrector inherits from multiple classes:
- CorrectorBase for the core functionality (invoking the correction and gathering statistics)
- UniversalCorrector and more classes (for groups of languages) with correction functions

By using multiple inheritance we can add correction functionality in an easy and flexible way.
The calling of corrector functions is done by introspection following these naming conventions:
Functions starting with "correct_": applied to every translation unit
Functions ending with "_title": applied only to the title translation unit
Functions ending with "_filename": applied only to translation units containing a file name

Implementation notes:
The alternative to using introspection would have been to register the correction functions
introduced by each class during initialization. That would be more explicit but
it gets a bit tricky with multiple inheritance and making sure that __init__() of
each base class gets called

"""
import logging
from typing import Generator
from collections import defaultdict

class CorrectorBase:
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
            logger = logging.getLogger("pywikitools.correctbot.base")
            logger.warning(f"Input parameter does not seem to be a file name: {text}")
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
