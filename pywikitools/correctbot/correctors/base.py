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

All correction functions must take one string and return the corrected string.
In case the correction function needs also the original string to decide what to do, it
takes two strings as parameters (the original string is the second parameter).
Most of the correction functions don't need to look at the original string, so they only take one parameter.

By default, a correction function is run on the whole content of a translation unit. This is necessary
for some rules like correcting quotation marks in 'he says, "very<br/>confusing".': This would be split into
3 snippets which have 0 or 1 quotation marks, but the function needs to have both quotation marks in one string.
If a function is decorated with @use_snippets, the translation unit is split into snippets and the correction
function runs on all snippets.

Implementation notes:
The alternative to using introspection would have been to register the correction functions
introduced by each class during initialization. That would be more explicit but
it gets a bit tricky with multiple inheritance and making sure that __init__() of
each base class gets called

"""
import functools
from inspect import signature
import logging
from typing import Callable, Generator
from collections import defaultdict

from pywikitools.lang.translated_page import TranslationUnit

def use_snippets(func):
    """Decorator: indicate that a correction function should run on the snippets of a translation unit"""
    @functools.wraps(func)
    def decorator_use_snippets(*args, **kwargs):
        return func(*args, **kwargs)
    decorator_use_snippets.use_snippets = True
    return decorator_use_snippets


class CorrectorBase:
    """
    Base class for all language-specific correctors

    Correctors should inherit from this class first.
    Correctors for groups of languages should not inherit from the class.

    """
    def __init__(self):
        # Counter for how often a particular rule (function) corrected something
        self._stats = defaultdict(int)

    def correct(self, unit: TranslationUnit) -> str:
        """Call all available correction functions one after the other to directly correct the unit

        @return any warning message or empty string if there was no warning
        """
        return self._run_correction_functions(unit, (s for s in dir(self) if s.startswith("correct_")))

    def title_correct(self, unit: TranslationUnit) -> str:
        """Call all correction functions for titles one after the other to directly correct the unit

        @return any warning message or empty string if there was no warning
        """
        return self._run_correction_functions(unit, (s for s in dir(self) if s.endswith("_title")))

    def filename_correct(self, unit: TranslationUnit) -> str:
        """
        Call all correction functions for filenames one after the other to directly correct the unit

        Only correct if we have a file name with one of the following extensions: '.doc', '.odg', '.odt', '.pdf'
        @return any warning message or empty string if there was no warning
        """
        if not unit.get_translation().lower().endswith(('.doc', '.odg', '.odt', '.pdf')):
            logger = logging.getLogger("pywikitools.correctbot.base")
            logger.warning(f"No file name: {unit.get_translation()} (in {unit.get_name()})")
        else:
            return self._run_correction_functions(unit, (s for s in dir(self) if s.endswith("_filename")))

    def _run_correction_functions(self, unit: TranslationUnit, functions: Generator[str, None, None]) -> str:
        """
        Call all the functions given by the generator one after the other to directly correct the unit

        Caution: the generator must not yield any function from this class, otherwise we run into indefinite recursion
        @return any warning message or empty string if there was no warning
        """
        is_unit_well_structured, warning = unit.is_translation_well_structured()

        for function_name in functions:
            corrector_function: Callable = getattr(self, function_name)
            if hasattr(corrector_function, "use_snippets"):
                if is_unit_well_structured:
                    # run correction function on snippets
                    for orig_snippet, trans_snippet in unit:
                        trans_snippet.content = self._call_function(corrector_function,
                                                                    trans_snippet.content, orig_snippet.content)
                    unit.sync_from_snippets()
                    continue
            # otherwise run correction function on the whole translation unit
            unit.set_translation(self._call_function(corrector_function,
                                                     unit.get_translation(), unit.get_definition()))

        return warning

    def _call_function(self, corrector_function: Callable, text: str, original: str) -> str:
        """
        Call a correction function with the correct number of parameters, update statistics if necessary

        We check with introspection if we need to give both parameters or just one.
        @return corrected text
        """
        if len(signature(corrector_function).parameters) == 2:
            result = corrector_function(text, original)
        else:
            assert len(signature(corrector_function).parameters) == 1
            result = corrector_function(text)

        # Update statistics if the correction function changed something
        if text != result:
            self._stats[corrector_function.__name__] += 1
        return result

    def reset_stats(self) -> None:
        """Reset all statistics gathered until now"""
        self._stats.clear()

    def count_corrections(self) -> int:
        """
        Returns the number of corrections that were made.
        See print_stats() to get more details
        """
        return sum(self._stats.values())

    def print_stats(self) -> str:
        """
        Give a detailed overview how much corrections were made and by which functions.

        In the details we'll read from the documentation strings of the functions used
        and take the first line (in case the documentation has several lines)
        If a function is not documented then just its name is printed.
        """
        details: str = ""
        total_counter: int = 0
        for function_name, counter in self._stats.items():
            total_counter += counter
            documentation = getattr(self, function_name).__doc__
            if documentation is not None:
                details += " - " + documentation.partition("\n")[0]
            else:
                details += " - " + function_name
            details += f" ({counter}x)\n"
        result = f"{total_counter} corrections"
        if details != "":
            result += ":\n" + details
        return result
