:py:mod:`correctors.universal`
==============================

.. py:module:: correctors.universal

.. autoapi-nested-parse::

   This module contains correction rules that are used in more than one language:
   - UniversalCorrector containing rules that can be applied in all languages
   - Corrector classes for groups of languages

   Caution: functions in a language-specific corrector must never have the same names as
   one of the functions here (otherwise only one of it gets called in the case of multiple inheritance)

   Each function should have a documentation string which will be used for print_stats()



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   correctors.universal.UniversalCorrector
   correctors.universal.NoSpaceBeforePunctuationCorrector
   correctors.universal.RTLCorrector




.. py:class:: UniversalCorrector

   Has language-independent correction functions

   .. py:method:: correct_wrong_capitalization(self, text: str) -> str

      Fix wrong capitalization at the beginning of a sentence or after a colon.
      Only do that if our text ends with a dot to avoid correcting single words / short phrases


   .. py:method:: correct_multiple_spaces_also_in_title(self, text: str) -> str

      Reduce multiple spaces to one space


   .. py:method:: correct_missing_spaces(self, text: str) -> str

      Insert missing spaces between punctuation and characters


   .. py:method:: correct_spaces_before_comma_and_dot(self, text: str) -> str

      Erase redundant spaces before commas and dots


   .. py:method:: correct_wrong_dash_also_in_title(self, text: str) -> str

      When finding a normal dash ( - ) surrounded by spaces: Make long dash ( – ) out of it


   .. py:method:: correct_missing_final_dot(self, text: str, original: str) -> str

      If the original has a trailing dot, the translation also needs one at the end.


   .. py:method:: correct_mediawiki_bold_italic(self, text: str) -> str

      Replace mediawiki formatting '''bold''' with <b>bold</b> and ''italic'' with <i>italic</i>


   .. py:method:: make_lowercase_extension_in_filename(self, text: str) -> str

      Have file ending in lower case


   .. py:method:: remove_spaces_in_filename(self, text: str) -> str

      Replace spaces in file name with single underscore


   .. py:method:: remove_multiple_underscores_in_filename(self, text: str) -> str

      Replace multiple consecutive underscores with single underscore in file name



.. py:class:: NoSpaceBeforePunctuationCorrector

   This is an extra class only for !?:; punctuation marks that must not be preceded by a space.
   Removing spaces before comma and dot is already covered by UniversalCorrector.correct_spaces_before_comma_and_dot()
   This class is extra as e.g. French requires non-breaking spaces before them
   (in contrast to most other languages which have no spaces before these punctuation marks as well)

   .. py:method:: correct_no_spaces_before_punctuation(self, text: str) -> str

      Erase redundant spaces before punctuation marks.



.. py:class:: RTLCorrector

   Corrections for right-to-left languages

   .. py:method:: correct_wrong_spaces_in_rtl(self, text: str) -> str

      Erase redundant spaces before RTL punctuation marks


   .. py:method:: fix_rtl_title(self, text: str) -> str

      When title ends with closing parenthesis, add a RTL mark at the end


   .. py:method:: fix_rtl_filename(self, text: str) -> str

      When file name has a closing parenthesis before the file ending, make sure we have a RTL mark afterwards!



