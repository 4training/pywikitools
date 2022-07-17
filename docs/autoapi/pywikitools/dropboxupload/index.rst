:py:mod:`pywikitools.dropboxupload`
===================================

.. py:module:: pywikitools.dropboxupload

.. autoapi-nested-parse::

   Upload created files to a shared Dropbox folder

   Dropbox account credentials are stored in a separate file



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   pywikitools.dropboxupload.upload_string
   pywikitools.dropboxupload.upload_file



.. py:function:: upload_string(languagecode: str, filename: str, content: str) -> bool

   Create a new file in the dropbox (OAuth token in config.ini)
   @param languagecode
   @param filename the name of the file that should be created (can also include a relative path)
   @param content fill the file with this content
   @return True if successful


.. py:function:: upload_file(languagecode: str, filename: str) -> bool

   Upload the specified file to the dropbox (OAuth token in config.ini)
   @param languagecode
   @param filename can also include a path
   @return True for Success, False if error occured


