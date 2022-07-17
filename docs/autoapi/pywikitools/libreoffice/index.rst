:orphan:

:py:mod:`pywikitools.libreoffice`
=================================

.. py:module:: pywikitools.libreoffice


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.libreoffice.LibreOffice




.. py:class:: LibreOffice(headless: bool = False)

   Connecting to LibreOffice via PyUNO:
   A class to open files, do some actions (search and replace; setting properties; setting locale of default style)
   and save the file as ODT or export it as PDF.

   You need to make sure that you first call open_file() before calling other functions,
   otherwise you get an AssertionError

   .. py:attribute:: TIMEOUT
      :annotation: = 200

      Class to handle files with LibreOffice write

   .. py:method:: open_file(self, file_name: str)

      Opens an existing LibreOffice document

      This starts LibreOffice and establishes a socket connection to it
      Raises ConnectionError if something doesn't work


   .. py:method:: search_and_replace(self, search: str, replace: str, warn_if_pages_change: bool = False, parse_formatting: bool = False) -> bool

      Replaces first occurence of search with replace in the currently opened LibreOffice document
      @param warn_if_pages_change: Log a warning if start and end of the passage aren't on the same page(s) as
                                   it was before the replace
      @param parse_formatting: Should we take <i>,<b>,<u>,</i>,</b> and </u> in the replace string
                               as formatting instruction?
                               The search string should contain the text content only and no <tags>
      @return True if successful


   .. py:method:: save_odt(self, file_name: str)

      Save the currently opened document as ODT file.
      @param filename: where to save the odt file (full URL, e.g. "/path/to/file.odt" )
      @raises FileExistsError if file already exists and is currently opened; OSError


   .. py:method:: export_pdf(self, file_name: str)

      Export the currently opened document as PDF
      @param filename: where to save the PDF file (full URL, e.g. "/path/to/file.pdf" )


   .. py:method:: close(self)

      Closes LibreOffice


   .. py:method:: get_properties_subject(self) -> str

      Return the subject property of the currently open document


   .. py:method:: set_properties(self, title: str, subject: str, keywords: str)

      Set the properties (subject, title and keywords) of the ODT file


   .. py:method:: set_default_style(self, language_code: str, rtl: bool = False)

      Setting properties of the ODT document's default style:
      Locale (with language code) and writing mode (LTR/RTL)
      Does some logging on errors (not optimal from software design perspective)



