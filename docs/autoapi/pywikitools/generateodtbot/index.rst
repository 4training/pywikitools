:py:mod:`pywikitools.generateodtbot`
====================================

.. py:module:: pywikitools.generateodtbot

.. autoapi-nested-parse::

   Bot that is generating translated odt files:
       - calls translateodt.py (which does the actual work)
       - calls dropboxupload.py for uploading the result to the dropbox
       - sends notification to the mediawiki user who requested the action together with log output (only warning level)
       - sends notification to admin with log output (both warning and debug level)



