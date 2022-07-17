:py:mod:`pywikitools.resourcesbot.consistency_checks`
=====================================================

.. py:module:: pywikitools.resourcesbot.consistency_checks

.. autoapi-nested-parse::

   Contains consistency checks specifically for 4training.net



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.resourcesbot.consistency_checks.ConsistencyCheck




.. py:class:: ConsistencyCheck(fortraininglib: pywikitools.fortraininglib.ForTrainingLib)

   Bases: :py:obj:`pywikitools.resourcesbot.post_processing.LanguagePostProcessor`

   Post-processing plugin: Check whether some translation units with the same English definition
   also have the same translation in the specified language

   This is completely 4training.net-specific.
   Next step: Write the results to some meaningful place on 4training.net
              so that translators can access them and correct inconsistencies

   .. py:method:: extract_link(self, text: str) -> Tuple[str, str]

      Search in text for a mediawiki link of the form [[Destination|Title]].
      This function will only look at the first link it finds in the text, any other will be ignored.
      @return a tuple (destination, title). In case no link was found both strings will be empty.


   .. py:method:: load_translation_unit(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo, page: str, identifier: Union[int, str]) -> Optional[pywikitools.lang.translated_page.TranslationUnit]

      Try to load a translation unit

      If we request the title of a worksheet, let's first try to see if it's already in language_info.
      Then we don't need to make an API query.
      Otherwise we try to load the translation unit from the mediawiki system


   .. py:method:: should_be_equal(self, base: Optional[pywikitools.lang.translated_page.TranslationUnit], other: Optional[pywikitools.lang.translated_page.TranslationUnit]) -> bool

      returns True if checks pass: base and other are the same (or not existing)


   .. py:method:: should_start_with(self, base: Optional[pywikitools.lang.translated_page.TranslationUnit], other: Optional[pywikitools.lang.translated_page.TranslationUnit]) -> bool

      returns True if checks pass: other starts with base (or not existing)


   .. py:method:: check_bible_reading_hints_titles(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo) -> bool

      Titles of the different Bible Reading Hints variants should start the same


   .. py:method:: check_bible_reading_hints_links(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo) -> bool

      Check whether the link titles in https://www.4training.net/Bible_Reading_Hints
      are identical with the titles of the destination pages


   .. py:method:: check_gods_story_titles(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo) -> bool

      Titles of the two different variants of God's Story should start the same


   .. py:method:: check_who_do_i_need_to_forgive(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo) -> bool

      Should both be 'God, who do I need to forgive?'


   .. py:method:: check_book_of_acts(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo) -> bool

      Name of the book of Acts should be the same in different Bible Reading Hints variants


   .. py:method:: run(self, language_info: pywikitools.resourcesbot.data_structures.LanguageInfo, change_log: pywikitools.resourcesbot.changes.ChangeLog)

      Entry point



