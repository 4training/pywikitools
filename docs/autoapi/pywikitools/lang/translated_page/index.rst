:orphan:

:py:mod:`pywikitools.lang.translated_page`
==========================================

.. py:module:: pywikitools.lang.translated_page


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.lang.translated_page.SnippetType
   pywikitools.lang.translated_page.TranslationSnippet
   pywikitools.lang.translated_page.TranslationUnit
   pywikitools.lang.translated_page.TranslatedPage




.. py:class:: SnippetType

   Bases: :py:obj:`enum.Enum`

   Markup means mediawiki formatting instructions (e.g. <b>, ===, <br/>, ''', ;, # , </i> )
   Text is some human-readable content without any markup in between


.. py:class:: TranslationSnippet(snippet_type: SnippetType, content: str)

   Represents a smallest piece of mediawiki content: either markup or text.

   Content can be directly changed - use TranslationUnit.sync_from_snippets() to save it in the
   corresponding TranslationUnit


.. py:class:: TranslationUnit(identifier: str, language_code: str, definition: str, translation: Optional[str])

   Represents one translation unit of a translatable mediawiki page with its translation into a given language.
   https://www.mediawiki.org/wiki/Help:Extension:Translate/Glossary

   Can be split up into one or more TranslationSnippets.
   You can make changes either with set_definition() / set_translation() or by changing the content of a snippet
   and syncing it back here with sync_from_snippets().
   There is no real persistence, so if you want to permanently store the changes in the mediawiki system
   you need to take care of that yourself.

   .. py:method:: is_title(self) -> bool

      Is this unit holding the title of a page?


   .. py:method:: set_definition(self, text: str)

      Changes the definition of this translation unit. Caution: Changes in snippets will be discarded.


   .. py:method:: sync_from_snippets(self)

      In case changes were made to snippets, save all changes to the translation unit.


   .. py:method:: get_translation(self) -> str

      Returns an empty string if no translation exists


   .. py:method:: get_original_translation(self) -> str

      Return the original translation this TranslationUnit was constructed with


   .. py:method:: set_translation(self, text: str)

      Changes the translation of this translation unit. Caution: Changes in snippets will be discarded.


   .. py:method:: has_translation_changes(self) -> bool

      Have there any changes been made to the translation of this unit?

      We compare to the original translation content we got during __init__().
      If you made changes to snippets, make sure you first call sync_from_snippets()!


   .. py:method:: get_translation_diff(self) -> str

      Returns a diff between original translation content and current translation content.
      If you made changes to snippets, make sure you first call sync_from_snippets()!


   .. py:method:: remove_links(self)

      Remove links (both in definition and in translation). Warns also if there is a link without |
      Example: [[Prayer]] causes a warning, correct would be [[Prayer|Prayer]].
      We have this convention so that translators are less confused as they need to write e.g. [[Prayer/de|Gebet]]


   .. py:method:: split_into_snippets(text: str) -> List[TranslationSnippet]
      :staticmethod:

      Split the given text into snippets

      We split at the following formatting / markup items:
          * or #: bullet list / numbered list items
          == up to ======: section headings
          : at the beginning of a line: definition list / indent text
          ; at the beginning of a line: definition list
      For <br/>, if there is a following newline, include it also in the match.
      For *#;: if there is a following whitespace character, include it also in the match.


   .. py:method:: is_translation_well_structured(self) -> Tuple[bool, str]

      Is the snippet structure of original and translation the same?

      This does quite some logging to provide helpful feedback for people working on the translations
      @return Tuple of actual return value and warning message if it is False



.. py:class:: TranslatedPage(page: str, language_code: str, units: List[TranslationUnit])

   Holds all translation units of a translated worksheet and analyzes them
   to provide some information we need in some places.

   This class is not fetching the content on its own, they need to be provided in the constructor.
   Also there is no persistence: If you make changes it's your responsibility to write them back
   to the mediawiki system.

   .. py:method:: add_translation_unit(self, unit: TranslationUnit)

      Append a translation unit. Infos are not invalidated



