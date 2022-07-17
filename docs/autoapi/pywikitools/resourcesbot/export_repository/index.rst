:orphan:

:py:mod:`pywikitools.resourcesbot.export_repository`
====================================================

.. py:module:: pywikitools.resourcesbot.export_repository


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.resourcesbot.export_repository.ExportRepository




.. py:class:: ExportRepository(base_folder: str)

   Bases: :py:obj:`pywikitools.resourcesbot.post_processing.LanguagePostProcessor`

   Export the html files (result of ExportHTML) to a git repository.
   Needs to run after ExportHTML.

   .. py:method:: run(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo, change_log: pywikitools.resourcesbot.changes.ChangeLog)

      Pushing all changes in the local repository (created by ExportHTML) to the remote repository

      Currently we're ignoring change_log and just check for changes in the git repository



