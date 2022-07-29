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
import copy
import functools
from inspect import signature
import logging
from logging.handlers import QueueHandler
from queue import SimpleQueue
from typing import Callable, DefaultDict, Dict, Final, Generator, List
from collections import defaultdict

from pywikitools.lang.translated_page import TranslationUnit


def use_snippets(func):
    """Decorator: indicate that a correction function should run on the snippets of a translation unit"""
    @functools.wraps(func)
    def decorator_use_snippets(*args, **kwargs):
        return func(*args, **kwargs)
    decorator_use_snippets.use_snippets = True
    return decorator_use_snippets


def suggest_only(func):
    """Decorator: correction function should not directly correct but suggest its changes to the user"""
    @functools.wraps(func)
    def decorator_suggest_only(*args, **kwargs):
        return func(*args, **kwargs)
    decorator_suggest_only.suggest_only = True
    return decorator_suggest_only


class CorrectionResult:
    """Returns any warnings and suggestions of running a corrector on one translation unit

    This data structure is meant to be read-only after creation.
    """
    __slots__ = ["corrections", "suggestions", "correction_stats", "suggestion_stats", "warnings"]
    def __init__(self, corrections: TranslationUnit, suggestions: TranslationUnit,
                 correction_stats: Dict[str, int], suggestion_stats: Dict[str, int], warnings: str):
        self.corrections: Final[TranslationUnit] = corrections
        self.suggestions: Final[TranslationUnit] = suggestions
        self.correction_stats: Final[Dict[str, int]] = correction_stats
        self.suggestion_stats: Final[Dict[str, int]] = suggestion_stats
        self.warnings: Final[str] = warnings


class CorrectorBase:
    """
    Base class for all language-specific correctors

    Correctors should inherit from this class first.
    Correctors for groups of languages should not inherit from the class.

    correct(), title_correct() and filename_correct() are the three entry functions. They don't touch
    the given translation unit but return all changes and suggestions in the CorrectionResult structure
    """
    def correct(self, unit: TranslationUnit) -> CorrectionResult:
        """Call all available correction functions one after the other"""
        return self._run_functions(unit, (s for s in dir(self) if s.startswith("correct_")))

    def title_correct(self, unit: TranslationUnit) -> CorrectionResult:
        """Call all correction functions for titles one after the other
        We don't do any checks if unit actually is a title - that's the responsibility of the caller
        """
        return self._run_functions(unit, (s for s in dir(self) if s.endswith("_title")))

    def filename_correct(self, unit: TranslationUnit) -> CorrectionResult:
        """Call all correction functions for filenames one after the other
        We don't do any checks if unit actually is a filename - that's the responsibility of the caller"""
        return self._run_functions(unit, (s for s in dir(self) if s.endswith("_filename")))

    def _run_functions(self, unit: TranslationUnit, functions: Generator[str, None, None]) -> CorrectionResult:
        """
        Call all the functions given by the generator one after the other

        Caution: the generator must not yield any function from this class, otherwise we run into indefinite recursion
        """
        is_unit_well_structured, warning = unit.is_translation_well_structured()

        # Catch any warning coming from the Corrector class in a simple queue
        corrector_logger = logging.getLogger("pywikitools.correctbot.correctors")
        corrector_logger.propagate = False
        log_queue: SimpleQueue = SimpleQueue()
        log_handler = QueueHandler(log_queue)
        corrector_logger.addHandler(log_handler)

        # Sort: which functions correct directly and which give only suggestions?
        correction_functions: List[Callable] = []
        suggestion_functions: List[Callable] = []
        for function_name in functions:
            func: Callable = getattr(self, function_name)
            if hasattr(func, "suggest_only"):
                suggestion_functions.append(func)
            else:
                correction_functions.append(func)

        # First run all functions that directly correct
        corrections: TranslationUnit = copy.copy(unit)
        correction_stats: DefaultDict[str, int] = defaultdict(int)
        for correction_function in correction_functions:
            if self._correct_unit(correction_function, corrections,
                                  hasattr(correction_function, "use_snippets") and is_unit_well_structured):
                correction_stats[correction_function.__name__] += 1

        # Now run all functions that make suggestions
        suggestions = copy.copy(corrections)
        suggestion_stats: DefaultDict[str, int] = defaultdict(int)
        for suggestion_function in suggestion_functions:
            if self._correct_unit(suggestion_function, suggestions,
                                  hasattr(suggestion_function, "use_snippets") and is_unit_well_structured):
                suggestion_stats[suggestion_function.__name__] += 1

        # Save warnings from the Corrector class in our CorrectionResult
        while not log_queue.empty():
            record: logging.LogRecord = log_queue.get()
            if warning != "":
                warning += "\n"
            warning += record.message
        return CorrectionResult(corrections, suggestions, correction_stats, suggestion_stats, warning)

    def _correct_unit(self, corrector_function: Callable, unit: TranslationUnit, correct_snippets: bool) -> bool:
        """
        Run a correction function on a translation unit
        @param unit: the translation unit the correction function should be applied to. Will be modified directly
        @param correct_snippets: Should we run all correction functions on each snippets or just on the complete unit?
                                 Caution! The caller is responsible that the unit is well-structured!
        @return did we make any changes?
        """
        has_changes = False
        if correct_snippets:
            # run correction function on snippets
            for orig_snippet, trans_snippet in unit:
                result = self._call_function(corrector_function, trans_snippet.content, orig_snippet.content)
                if result != trans_snippet.content:
                    has_changes = True
                    trans_snippet.content = result
            if has_changes:
                unit.sync_from_snippets()
        else:
            # otherwise run the correction function on the whole translation unit
            result = self._call_function(corrector_function, unit.get_translation(), unit.get_definition())
            if result != unit.get_translation():
                has_changes = True
                unit.set_translation(result)

        return has_changes

    def _call_function(self, corrector_function: Callable, text: str, original: str) -> str:
        """
        Call a correction function with the correct number of parameters

        We check with introspection if we need to give both parameters or just one.
        @return corrected text
        """
        if len(signature(corrector_function).parameters) == 2:
            result = corrector_function(text, original)
        else:
            assert len(signature(corrector_function).parameters) == 1
            result = corrector_function(text)
        return result

    def print_stats(self, stats: Dict[str, int]) -> str:
        """
        Write a detailed overview with how many corrections were made and by which functions.

        In the details we'll read from the documentation strings of the functions used
        and take the first line (in case the documentation has several lines)
        If a function is not documented then just its name is printed.

        Args:
            stats: Dictionary with the "raw" statistics (name of the function -> how many times was it applied)

        Returns:
            A human-readable string with individual lines for each rule that was applied at least once.
            The string is at the same time valid mediawiki code for rendering a list
            An empty string if no rules were applied
        """
        details: str = ""
        for function_name, counter in stats.items():
            documentation = getattr(self, function_name).__doc__
            if documentation is not None:
                details += "* " + documentation.partition("\n")[0]
            else:
                details += "* " + function_name
            details += f" ({counter}x)\n"
        return details
