:orphan:

:py:mod:`pywikitools.resourcesbot.bot`
======================================

.. py:module:: pywikitools.resourcesbot.bot


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.resourcesbot.bot.ResourcesBot




.. py:class:: ResourcesBot(config: configparser.ConfigParser, limit_to_lang: Optional[str] = None, rewrite_all: bool = False, read_from_cache: bool = False)

   Contains all the logic of our bot

   .. py:method:: get_english_version(self, page_source: str) -> Tuple[str, int]

      Extract version of an English worksheet
      @return Tuple of version string and the number of the translation unit where it is stored



