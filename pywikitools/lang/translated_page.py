
from enum import Enum
import logging
import re
from typing import List, Optional

class SnippetType(Enum):
    """
    Markup means mediawiki formatting instructions (e.g. <b>, ===, <br/>, ''', ;, # , </i> )
    Text is some human-readable content without any markup in between
    """
    TEXT_SNIPPET = "Text"
    MARKUP_SNIPPET = "Markup"


class TranslationSnippet:
    """
    Represents a smallest piece of mediawiki content: either markup or text.
    """
    __slots__ = ['_type', 'content']

    def __init__(self, snippet_type: SnippetType, content: str):
        self._type: SnippetType = snippet_type
        self.content: str = content

    def get_type(self) -> SnippetType:
        return self._type

    def is_text(self) -> bool:
        return self._type == SnippetType.TEXT_SNIPPET

    def is_markup(self) -> bool:
        return self._type == SnippetType.MARKUP_SNIPPET

    def is_br(self) -> bool:
        return (self._type == SnippetType.MARKUP_SNIPPET) and bool(re.match("<br ?/?>\n?", self.content))

    def __str__(self):
        return f"{self._type}({len(self.content)}): {self.content}"


class TranslationUnit:
    """
    Represents one translation unit of a translatable mediawiki page with its translation into a given language.
    https://www.mediawiki.org/wiki/Help:Extension:Translate/Glossary

    Can be split up into one or more TranslationSnippets
    TODO save identifier/name of the unit also properly
    """
    def __init__(self, identifier: str, language_code: str, definition: str, translation: str):
        """
        @param identifier: The key of the translation unit (e.g. "Prayer/7")
        @param definition: The original text (usually English)
        @param translation: The translation of the definition
        """
        self.__identifier = identifier
        self.__language_code = language_code
        self.__definition = definition
        self.__translation = translation
        self.__definition_snippets: Optional[List[TranslationSnippet]] = None
        self.__translation_snippets: Optional[List[TranslationSnippet]] = None
        self.logger = logging.getLogger('pywikitools.lang.TranslationUnit')

    def get_definition(self) -> str:
        return self.__definition

    def set_definition(self, text: str):
        self.__definition = text
        self.__definition_snippets = None

    def get_translation(self) -> str:
        return self.__translation

    def set_translation(self, text: str):
        self.__translation = text
        self.__translation_snippets = None

    def get_name(self):
        return f"Translations:{self.__identifier}/{self.__language_code}"

    def remove_links(self):
        """
        Remove links (both in definition and in translation). Warns also if there is a link without |
        Example: [[Prayer]] causes a warning, correct would be [[Prayer|Prayer]].
        We have this convention so that translators are less confused as they need to write e.g. [[Prayer/de|Gebet]]
        """
        # This does all necessary replacements if the link correctly uses the form [[destination|description]]
        link_pattern_with_bar = re.compile(r"\[\[(.*?)\|(.*?)\]\]")
        self.__definition = link_pattern_with_bar.sub(r"\2", self.__definition)
        self.__translation = link_pattern_with_bar.sub(r"\2", self.__translation)

        # Now we check for links that are not following the convention
        # We need to remove the # of internal links, otherwise it gets the meaning of a numbering. (#?) does the trick
        link_pattern_without_bar = re.compile(r"\[\[(#?)(.*?)\]\]")
        match_d = link_pattern_without_bar.search(self.__definition)
        if match_d:
            self.logger.warning(f"Found errorneous link {match_d.group(0)} in English original in {self.get_name()}. "
                                "Please tell an administrator.")
            self.__definition = link_pattern_without_bar.sub(r"\2", self.__definition)

        match_t = link_pattern_without_bar.search(self.__translation)
        if match_t:
            self.logger.warning(f"The following link is errorneous: {match_t.group(0)}. "
                                f"It needs to be [[English destination/{self.__language_code}|{match_t.group(2)}]]. "
                                f"Please correct {self.get_name()}")
            self.__translation = link_pattern_without_bar.sub(r"\2", self.__translation)

        if match_d or match_t:
            # Snippets need to be re-created. We don't have to do that right now, we'll do it just-in-time when needed
            self.__definition_snippets = None
            self.__translation_snippets = None

    @staticmethod
    def split_into_snippets(text: str, fallback: bool = False) -> List[TranslationSnippet]:
        """
        Split the given text into snippets

        We split at all kinds of formattings / markup:
            '' or ''': italic / bold formatting
            <tags>: all kind of html tags like <i> or <b> or </i> or </b>
            * or #: bullet list / numbered list items
            == up to ======: section headings
            : at the beginning of a line: definition list / indent text
            ; at the beginning of a line: definition list
        For <br/>, include a following newline in the match.
        For *#;: include a following whitespace character in the match.
        @param fallback: Should we try the fallback splitting-up?
        """
        if fallback:
            # We replace <br/> line breaks with \n line breaks
            # and remove italic and bold formatting and all kind of <tags>
            text = re.sub("<br ?/?>", '\n', text)
            text = re.sub("\'\'+|<.*?>", '', text, flags=re.MULTILINE)

        snippets: List[TranslationSnippet] = []
        last_pos = 0
        pattern = re.compile("\'\'+|<br ?/?>\n?|<.*?>|[*#]\s?|={2,6}|^:\s?|^;\s?", flags=re.MULTILINE)
        for match in re.finditer(pattern, text):
            if match.start() > last_pos:
                text_snippet = TranslationSnippet(SnippetType.TEXT_SNIPPET, text[last_pos:match.start()])
                snippets.append(text_snippet)
            markup_snippet = TranslationSnippet(SnippetType.MARKUP_SNIPPET, match.group())
            snippets.append(markup_snippet)
            last_pos = match.end()

        if last_pos < len(text):
            snippets.append(TranslationSnippet(SnippetType.TEXT_SNIPPET, text[last_pos:]))
        return snippets

    def _ensure_split(self):
        """Split into snippets if that hasn't happened yet"""
        if self.__definition_snippets is None:
            self.__definition_snippets = self.split_into_snippets(self.__definition)
        if self.__translation_snippets is None:
            self.__translation_snippets = self.split_into_snippets(self.__translation)

    def is_translation_well_structured(self) -> bool:
        """
        Is the snippet structure of original and translation the same?

        This does quite some logging to provide helpful feedback for people working on the translations
        TODO do some checks to see how often fallback method of split_into_snippets() is actually necessary
        Potentially remove the fallback parameter
        """
        self._ensure_split()
        assert self.__definition_snippets is not None and self.__translation_snippets is not None

        if len(self.__definition_snippets) != len(self.__translation_snippets):
            # TODO give more specific warnings like "missing #" or "Number of = mismatch"
            self.logger.info("Number of *, =, #, italic and bold formatting, ;, : and html tags is not equal"
                            f" in original and translation:\n{self.__definition}\n{self.__translation}")
            self.logger.info('Falling back: removing all formatting and trying again')
            self.__definition_snippets = self.split_into_snippets(self.__definition, fallback=True)
            self.__translation_snippets = self.split_into_snippets(self.__translation, fallback=True)

            if len(self.__definition_snippets) != len(self.__translation_snippets):
                br_in_definition = len([s for s in self.__definition_snippets if s.is_br()])
                br_in_translation = len([s for s in self.__translation_snippets if s.is_br()])
                if br_in_definition != br_in_translation:
                    # There could be another issue besides the <br/> issue. Still this warning is probably helpful
                    self.logger.warning(f"Couldn't process Translations:{self.get_name()}. "
                                        f"Reason: Missing/wrong <br/> "
                                        f"(in original: {br_in_definition}, in translation: {br_in_translation})")
                else:
                    self.logger.warning("Couldn't process the following translation unit. Reason: Formatting issues. "
                                        "Please check that all special characters like * = # ; : <b> <i> are correct.")
                self.logger.warning(f"Original: \n{self.__definition}")
                self.logger.warning(f"Translation: \n{self.__translation}")
                return False

            self.logger.warning("Found an issue with formatting (special characters like * = # ; : <b> <i>). "
                                "I ignored all formatting and could continue. You may ignore this error "
                               f"or correct the translation unit {self.get_name()}")

        # Iterate over both lists at the same time and check whether the snippet types fit each other
        for d_snippet, t_snippet in zip(self.__definition_snippets, self.__translation_snippets):
            # Currently we test only whether they have the same SnippetType. TODO check whether they actually match
            if d_snippet.get_type() != t_snippet.get_type():
                return False

        return True

    def __iter__(self):
        """Make this class iterable in a simple way (not suitable for concurrency!)"""
        self._ensure_split()
        self.iterate_pos = 0
        return self

    def __next__(self):
        """
        Return a next tuple of original and translated snippet with content

        This leaves out snippets that are markup. Also it assumes is_translation_well_structured(),
        otherwise this will probably raise errors (todo make it more robust?)
        """
        while self.iterate_pos + 1 <= len(self.__definition_snippets):
            definition_snippet = self.__definition_snippets[self.iterate_pos]
            translation_snippet = self.__translation_snippets[self.iterate_pos]
            self.iterate_pos += 1
            if definition_snippet.is_text():
                return (definition_snippet, translation_snippet)
        raise StopIteration


class TranslatedPage:
    """TODO holds all translation units of a translatable page"""
    pass
