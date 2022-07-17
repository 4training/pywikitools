:orphan:

:py:mod:`pywikitools.resourcesbot.export_html`
==============================================

.. py:module:: pywikitools.resourcesbot.export_html


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.resourcesbot.export_html.CustomBeautifyHTML
   pywikitools.resourcesbot.export_html.ExportHTML




.. py:class:: CustomBeautifyHTML(change_hrefs: Dict[str, str], file_collector: Set[str])

   Bases: :py:obj:`pywikitools.htmltools.beautify_html.BeautifyHTML`

   Class to collect all images used in the generated HTML files
   TODO do something about links to worksheets that are not translated yet

   .. py:method:: img_rewrite_handler(self, element)

      Do some rewriting of <img> elements

      In our default implementation we remove the srcset attribute (as we don't need it)
      and apply replacements for the src attribute.

      You can customize the behaviour by sub-classing BeautifyHTML and overwriting this method
      @param element: Part of the BeautifulSoup data structure, will be modified directly



.. py:class:: ExportHTML(fortraininglib: pywikitools.fortraininglib.ForTrainingLib, folder: str, force_rewrite: bool = False)

   Bases: :py:obj:`pywikitools.resourcesbot.post_processing.LanguagePostProcessor`

   Export all finished worksheets of this language as HTML into a folder
   This is a step towards having a git repo with this content always up-to-date

   .. py:method:: has_relevant_change(self, worksheet: str, change_log: pywikitools.resourcesbot.changes.ChangeLog)

      Is there a relevant change for worksheet?
      TODO: Define what exactly we consider relevant (for re-generating that worksheet's HTML)


   .. py:method:: download_file(self, files_folder: str, filename: str) -> bool

      Download a file from the mediawiki server

      If a file already exists locally, we don't download it again because usually those
      files (graphics) don't change.
      TODO: Implement a way to force re-downloading of files (in case a file was updated in the mediawiki system).
      Two possible ways:
      - an extra flag (e.g. --force-rewrite-files)
      - by getting the time stamp of the file in the mediawiki system, comparing it with the last
      modified timestamp of the local file and download again if the first is newer
      (would require adjustments of get_file_url() to also request timestamp)

      @return True if we actually downloaded the file, False if not


   .. py:method:: run(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo, change_log: pywikitools.resourcesbot.changes.ChangeLog)

      Entry point



