:orphan:

:py:mod:`correctors.en`
=======================

.. py:module:: correctors.en


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   correctors.en.EnglishCorrector




.. py:class:: EnglishCorrector

   Bases: :py:obj:`correctors.base.CorrectorBase`, :py:obj:`correctors.universal.UniversalCorrector`

   Corrects typical English typos to follow the following rules:
   * TODO: No plain quotation marks: instead of "Foo" use “Foo”
   * TODO: No German quotation marks
     * “ must be at the beginning of a word, not at the end as in German (check for trailing whitespace?)
   * Substitute wrong apostrophe

   .. py:method:: correct_single_apostrophe(self, text: str) -> str

      Correct single apostrophe ' with ’



