:py:mod:`pywikitools.resourcesbot.post_processing`
==================================================

.. py:module:: pywikitools.resourcesbot.post_processing

.. autoapi-nested-parse::

   Base classes for all functionality doing useful stuff with the data gathered previously.

   If the functionality looks only at one language at a time, implement LanguagePostProcessor.
   If the functionality needs to look at everything, implement GlobalPostProcessor.
   The resourcesbot will first call any LanguagePostProcessors for each language and
   afterwards call any GlobalPostProcessor



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.resourcesbot.post_processing.LanguagePostProcessor
   pywikitools.resourcesbot.post_processing.GlobalPostProcessor




.. py:class:: LanguagePostProcessor

   Bases: :py:obj:`abc.ABC`

   Base class for all functionality doing useful stuff with the data on one language

   .. py:method:: run(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo, change_log: pywikitools.resourcesbot.changes.ChangeLog)
      :abstractmethod:

      Entry point



.. py:class:: GlobalPostProcessor

   Bases: :py:obj:`abc.ABC`

   Base class for all functionality doing useful stuff with the data on all languages

   .. py:method:: run(self, language_data: Dict[str, pywikitools.resourcesbot.data_structures.LanguageInfo], changes: Dict[str, pywikitools.resourcesbot.changes.ChangeLog])
      :abstractmethod:

      Entry point



