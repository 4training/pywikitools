:py:mod:`correctors.base`
=========================

.. py:module:: correctors.base

.. autoapi-nested-parse::

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



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   correctors.base.CorrectionResult
   correctors.base.CorrectorBase



Functions
~~~~~~~~~

.. autoapisummary::

   correctors.base.use_snippets
   correctors.base.suggest_only



.. py:function:: use_snippets(func)

   Decorator: indicate that a correction function should run on the snippets of a translation unit


.. py:function:: suggest_only(func)

   Decorator: correction function should not directly correct but suggest its changes to the user


.. py:class:: CorrectionResult(corrections: pywikitools.lang.translated_page.TranslationUnit, suggestions: pywikitools.lang.translated_page.TranslationUnit, correction_stats: Dict[str, int], suggestion_stats: Dict[str, int], warnings: str)

   Returns any warnings and suggestions of running a corrector on one translation unit

   This data structure is meant to be read-only after creation.


.. py:class:: CorrectorBase

   Base class for all language-specific correctors

   Correctors should inherit from this class first.
   Correctors for groups of languages should not inherit from the class.

   correct(), title_correct() and filename_correct() are the three entry functions. They don't touch
   the given translation unit but return all changes and suggestions in the CorrectionResult structure

   .. py:method:: correct(self, unit: pywikitools.lang.translated_page.TranslationUnit) -> CorrectionResult

      Call all available correction functions one after the other


   .. py:method:: title_correct(self, unit: pywikitools.lang.translated_page.TranslationUnit) -> CorrectionResult

      Call all correction functions for titles one after the other
      We don't do any checks if unit actually is a title - that's the responsibility of the caller


   .. py:method:: filename_correct(self, unit: pywikitools.lang.translated_page.TranslationUnit) -> CorrectionResult

      Call all correction functions for filenames one after the other
      We don't do any checks if unit actually is a filename - that's the responsibility of the caller


   .. py:method:: print_stats(self, stats: Dict[str, int]) -> str

      Write a detailed overview with how many corrections were made and by which functions.

      In the details we'll read from the documentation strings of the functions used
      and take the first line (in case the documentation has several lines)
      If a function is not documented then just its name is printed.

      :param stats: Dictionary with the "raw" statistics (name of the function -> how many times was it applied)

      :returns: A human-readable string with individual lines for each rule that was applied at least once.
                The string is at the same time valid mediawiki code for rendering a list
                An empty string if no rules were applied



