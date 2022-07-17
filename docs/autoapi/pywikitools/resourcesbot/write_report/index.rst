:orphan:

:py:mod:`pywikitools.resourcesbot.write_report`
===============================================

.. py:module:: pywikitools.resourcesbot.write_report


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.resourcesbot.write_report.Color
   pywikitools.resourcesbot.write_report.WriteReport




.. py:class:: Color

   Bases: :py:obj:`enum.Enum`

   Generic enumeration.

   Derive from this class to define new enumerations.


.. py:class:: WriteReport(site: pywikibot.site.APISite, force_rewrite: bool = False)

   Bases: :py:obj:`pywikitools.resourcesbot.post_processing.GlobalPostProcessor`

   Write/update status reports for all languages (for translators and translation coordinators).

   Every language report has a table with the translation status of all worksheets:
   Which worksheet is translated? Is the translation 100% complete? Is it the same version as the English original?
   Do we have ODT and PDF files for download?
   To help interpreting the results, we use colors (green / orange / red) for each cell.

   We can't implement this as a LanguagePostProcessor because we need the English LanguageInfo object
   as well to write a report for one language.

   .. py:method:: run(self, language_data: Dict[str, pywikitools.resourcesbot.data_structures.LanguageInfo], changes: Dict[str, pywikitools.resourcesbot.changes.ChangeLog])

      Entry function


   .. py:method:: save_language_report(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo, english_info: pywikitools.resourcesbot.data_structures.LanguageInfo)

      Saving a language report (URL e.g.: https://www.4training.net/4training:German)
      @param language_info: The language we want to write the report for
      @param english_info: We need the details of the English original worksheets as well


   .. py:method:: create_mediawiki(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo, english_info: pywikitools.resourcesbot.data_structures.LanguageInfo) -> str

      Build mediawiki code for the complete report page


   .. py:method:: create_worksheet_overview(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo, english_info: pywikitools.resourcesbot.data_structures.LanguageInfo) -> str

      Create mediawiki code to display the whole worksheet overview table


   .. py:method:: create_worksheet_line(self, english_info: pywikitools.resourcesbot.data_structures.WorksheetInfo, worksheet_info: Optional[pywikitools.resourcesbot.data_structures.WorksheetInfo]) -> str

      Create mediawiki code with report for one worksheet (one line of the overview)



