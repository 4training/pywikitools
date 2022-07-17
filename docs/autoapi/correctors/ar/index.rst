:orphan:

:py:mod:`correctors.ar`
=======================

.. py:module:: correctors.ar


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   correctors.ar.ArabicCorrector




.. py:class:: ArabicCorrector

   Bases: :py:obj:`correctors.base.CorrectorBase`, :py:obj:`correctors.universal.UniversalCorrector`, :py:obj:`correctors.universal.RTLCorrector`

   Base class for all language-specific correctors

   Correctors should inherit from this class first.
   Correctors for groups of languages should not inherit from the class.

   correct(), title_correct() and filename_correct() are the three entry functions. They don't touch
   the given translation unit but return all changes and suggestions in the CorrectionResult structure

   .. py:method:: correct_punctuation(self, text: str) -> str

      Replace normal comma, semicolon, question mark with Arabic version of it



