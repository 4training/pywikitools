:py:mod:`check_language_directions`
===================================

.. py:module:: check_language_directions

.. autoapi-nested-parse::

   Little script to check whether fortraininglib.get_language_direction()
   is correct for all the languages in use. It does so by doing API calls like
   https://www.4training.net/mediawiki/api.php?action=query&titles=Start/fa&prop=info
   It doesn't matter which page is requested - the language direction is always returned,
   also if the page doesn't exist.

   Also we don't include this script in the test suite because it takes maybe a minute and increases
   test run time too much - it's sufficient to run it once in a while to check correctness.



