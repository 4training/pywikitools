:py:mod:`pywikitools.pdftools.metadata`
=======================================

.. py:module:: pywikitools.pdftools.metadata

.. autoapi-nested-parse::

   A module for analyzing PDF metadata with pikepdf:
   - PDF 1/A compatibility
   - is it using XMP metadata or the deprecated DocInfo?
   - are the title, subject and keywords properties set as expected?

   This contains our standards for filling metadata.
   TODO: Find a good place for our standards in a dedicated module and avoid duplicate code -
         they're also in TranslateODT._set_properties()



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   pywikitools.pdftools.metadata.check_metadata



.. py:function:: check_metadata(fortraininglib: pywikitools.fortraininglib.ForTrainingLib, filename: str, info: pywikitools.resourcesbot.data_structures.WorksheetInfo) -> pywikitools.resourcesbot.data_structures.PdfMetadataSummary

   Check the PDF metadata whether it meets our standards. This involves:
   - title must start with translated title (identical if there is no subheadline)
   - subject must start with English worksheet name and end with correct language names
   - keywords must include version number

   Extracts the version number as well ("" indicates an error)
   @param filename: path of the PDF file to analyze
   @param info: WorksheetInfo so that we can compare the PDF metadata with the expected results


