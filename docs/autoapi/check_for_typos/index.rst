:py:mod:`check_for_typos`
=========================

.. py:module:: check_for_typos

.. autoapi-nested-parse::

   Checks all translations of one language for typos.
   Runs the corrector on it and prints out the result but doesn't write any changes to the mediawiki system.

   Usage:
   python3 check_for_typos.py language_code



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   check_for_typos.parse_arguments



.. py:function:: parse_arguments() -> argparse.Namespace

   Parses the arguments given from outside

   :returns: parsed arguments
   :rtype: argparse.Namespace


