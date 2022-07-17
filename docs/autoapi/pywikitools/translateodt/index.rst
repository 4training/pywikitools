:py:mod:`pywikitools.translateodt`
==================================

.. py:module:: pywikitools.translateodt

.. autoapi-nested-parse::

   This script produces a translated ODT file for a given worksheet and a given language.
   It does so by:
   1. accessing the worksheet in the mediawiki system together with its translation
   2. downloading the English ODT file (the URL is found in the result of the first step)
   3. doing search and replace: For each translation unit
      - do some cleansing (removing links, unnecessary spaces)
      - split it up even further into small snippets (when the translation unit contains lists etc.)
      - search for each snippet and replace it by its translation
   4. saving the created ODT file

   It does quite some logging:
       - error level: serious issues where the script had to be aborted
       - warning level: these should be checked afterwards
       - info level: going along what the script does
       - debug level: extensive details for debugging

   Command line options:
       -h, --help: help message
       -l [debug, info, warning, error]: set loglevel
       --keep-english-file: don't delete the downloaded English ODT file after we're finished



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.translateodt.TranslateOdtConfig




.. py:class:: TranslateOdtConfig

   Contains configuration on how to process one worksheet:
   Which translation units should be ignored?
   Which translation units should be processed multiple times?

   It is read from a config file (see TranslateODT.read_worksheet_config()) of the following structure:
   [Ignore]
   # Don't process the following translation units
   Template:BibleReadingHints/18
   Template:BibleReadingHints/25

   [Multiple]
   # Process the following translation unit 5 times
   Template:BibleReadingHints/6 = 5


