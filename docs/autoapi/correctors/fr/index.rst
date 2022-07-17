:orphan:

:py:mod:`correctors.fr`
=======================

.. py:module:: correctors.fr


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   correctors.fr.FrenchCorrector




.. py:class:: FrenchCorrector

   Bases: :py:obj:`correctors.base.CorrectorBase`, :py:obj:`correctors.universal.UniversalCorrector`

   Corrects typical French typos to follow the following rules:
   * False friends (example / exemple)
   * TODO Instead of ellipsis, use "..."
   * Ensure correct French quotation marks: « Foo » (with non-breaking whitespaces   before/after the guillemets!)

   .. py:method:: correct_false_friends(self, text: str) -> str

      Correct typical mistakes

      Currently only one rule:
      "example" is English -> "exemple" is correct French


   .. py:method:: correct_spaces_before_punctuation(self, text: str) -> str

      Ensure we have non-breaking spaces before : ; ! ?
      This is a specialty of French grammar, different to most languages


   .. py:method:: correct_quotation_marks(self, text: str) -> str

      Ensure correct French quotation marks: « Foo »
      (with non-breaking whitespaces   before/after the guillemets!)



