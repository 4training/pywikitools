:py:mod:`correct_bot`
=====================

.. py:module:: correct_bot

.. autoapi-nested-parse::

   Bot that replaces common typos for different languages.

   All correction rules for different languages are in the correctors/ folder in separate classes.

   Run with dummy page:
       python3 correct_bot.py Test de
       python3 correct_bot.py CorrectTestpage fr



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   correct_bot.CorrectBot



Functions
~~~~~~~~~

.. autoapisummary::

   correct_bot.parse_arguments



.. py:class:: CorrectBot(config: configparser.ConfigParser, simulate: bool = False)

   Main class for doing corrections

   .. py:method:: check_unit(self, corrector: pywikitools.correctbot.correctors.base.CorrectorBase, unit: pywikitools.lang.translated_page.TranslationUnit) -> Optional[pywikitools.correctbot.correctors.base.CorrectionResult]

      Check one specific translation unit: Run the right correction rules on it.
      For this we analyze: Is it a title, a file name or a "normal" translation unit?

      :returns: Result of running all correction functions on the translation unit
                None if we didn't run correctors (because the unit is not translated e.g.)


   .. py:method:: check_page(self, page: str, language_code: str) -> Optional[List[pywikitools.correctbot.correctors.base.CorrectionResult]]

      Check one specific page and store the results in this class

      This does not write anything back to the server. Changes can be read with
      get_stats(), get_correction_counter() and get_diff()

      :returns: CorrectionResult for each processed translation unit
                None if an error occurred


   .. py:method:: get_correction_stats(self) -> str

      Return a summary: which correction rules could be applied (in the last run)?


   .. py:method:: get_suggestion_stats(self) -> str

      Return a summary: which corrections are suggested (in the last run)?


   .. py:method:: get_correction_counter(self) -> int

      How many corrections did we do (in the last run)?


   .. py:method:: get_suggestion_counter(self) -> int

      How many suggestions did we receive (in the last run)?


   .. py:method:: get_correction_diff(self) -> str

      Print a diff of the corrections (made in the last run)


   .. py:method:: get_suggestion_diff(self) -> str

      Print a diff of the suggestions (made in the last run)


   .. py:method:: save_to_mediawiki(self, results: List[pywikitools.correctbot.correctors.base.CorrectionResult])

      Write changes back to mediawiki

      You should disable pywikibot throttling to avoid CorrectBot runs to take quite long:
      `put_throttle = 0` in user-config.py


   .. py:method:: empty_job_queue(self) -> bool

      Empty the mediawiki job queue by running the runJobs.php maintenance script

      See https://www.mediawiki.org/wiki/Manual:RunJobs.php

      :returns: True if we could successfully run this script
                False if paths were not configured or there was an error while executing


   .. py:method:: run(self, page: str, language_code: str)

      Correct the translation of a page.



.. py:function:: parse_arguments() -> argparse.Namespace

   Parse command-line arguments

   :returns: CorrectBot instance


