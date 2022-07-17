:orphan:

:py:mod:`correctors.de`
=======================

.. py:module:: correctors.de


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   correctors.de.GermanCorrector




.. py:class:: GermanCorrector

   Bases: :py:obj:`correctors.base.CorrectorBase`, :py:obj:`correctors.universal.UniversalCorrector`, :py:obj:`correctors.universal.NoSpaceBeforePunctuationCorrector`

   Correct typical German typos. Currently one rule is implemented
   * German quotations start with „ and end with “ („Beispiel“)

   .. py:method:: correct_quotes(self, text: str) -> str

      Ensure correct German quotes (example: „korrekt“)



