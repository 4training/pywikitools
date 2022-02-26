
from enum import Enum
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
    def __init__(self, definition: str, translation: str, language_code: str):
        """
        @param definition: The original text (usually English)
        @param translation: The translation of the definition
        """
        self.__definition = definition
        self.__translation = translation
        self.__language_code = language_code
        self.__definition_snippets: Optional[List[TranslationSnippet]] = None
        self.__translation_snippets: Optional[List[TranslationSnippet]] = None

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

class TranslatedPage:
    """TODO holds all translation units of a translatable page"""
    pass
