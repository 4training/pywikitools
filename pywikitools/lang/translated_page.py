
import difflib
from enum import Enum
import logging
import re
from typing import Dict, Final, List, Optional

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

    Content can be directly changed - use TranslationUnit.sync_from_snippets() to save it in the
    corresponding TranslationUnit
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

    Can be split up into one or more TranslationSnippets.
    You can make changes either with set_definition() / set_translation() or by changing the content of a snippet
    and syncing it back here with sync_from_snippets().
    There is no real persistence, so if you want to permanently store the changes in the mediawiki system
    you need to take care of that yourself.
    """
    # Font color for terminal output in diffs
    RED: Final[str] = "\033[0;31m"
    GREEN: Final[str] = "\033[0;32m"
    NO_COLOR: Final[str] = "\033[0m"

    def __init__(self, identifier: str, language_code: str, definition: str, translation: str):
        """
        @param identifier: The key of the translation unit (e.g. "Prayer/7")
        @param definition: The original text (usually English)
        @param translation: The translation of the definition
        """
        self._identifier = identifier
        self._language_code = language_code
        self._definition = definition
        self._original_definition = definition
        self._translation = translation
        self._original_translation = translation
        self._definition_snippets: Optional[List[TranslationSnippet]] = None
        self._translation_snippets: Optional[List[TranslationSnippet]] = None
        self._iterate_pos = 0      # For iterating over all snippets in this TranslationUnit
        self.logger = logging.getLogger('pywikitools.lang.TranslationUnit')

    def is_title(self) -> bool:
        """Is this unit holding the title of a page?"""
        return self._identifier.endswith("Page_display_title")

    def get_definition(self) -> str:
        return self._definition

    def set_definition(self, text: str):
        """Changes the definition of this translation unit. Caution: Changes in snippets will be discarded."""
        self._definition = text
        self._definition_snippets = None

    def sync_from_snippets(self):
        """In case changes were made to snippets, save all changes to the translation unit."""
        if self._definition_snippets is None or self._translation_snippets is None:
            self.logger.warning("Attempting to sync from non-existing snippets. Ignoring.")
            return
        self._definition = "".join([s.content for s in self._definition_snippets])
        self._translation = "".join([s.content for s in self._translation_snippets])

    def get_translation(self) -> str:
        return self._translation

    def set_translation(self, text: str):
        """Changes the translation of this translation unit. Caution: Changes in snippets will be discarded."""
        self._translation = text
        self._translation_snippets = None

    def has_translation_changes(self) -> bool:
        """
        Have there any changes been made to the translation of this unit?

        We compare to the original translation content we got during __init__().
        If you made changes to snippets, make sure you first call sync_from_snippets()!
        """
        return self._translation != self._original_translation

    def get_translation_diff(self) -> str:
        """
        Returns a diff between original translation content and current translation content.
        If you made changes to snippets, make sure you first call sync_from_snippets()!
        """
        diff: str = ""
        if self.has_translation_changes():
            seq_mat = difflib.SequenceMatcher(a=self._original_translation, b=self._translation)
            for operation, a_start, a_end, b_start, b_end in seq_mat.get_opcodes():
                if operation == "delete":
                    diff += self.RED + "{" + self._original_translation[a_start:a_end] + "}" + self.NO_COLOR
                elif operation == "replace":
                    diff += self.RED + "{" + self._original_translation[a_start:a_end] + ","
                    diff += self.GREEN + self._translation[b_start:b_end] + "}" + self.NO_COLOR
                elif operation == "insert":
                    diff += self.GREEN + "{" + self._translation[b_start:b_end] + "}" + self.NO_COLOR
                elif operation == "equal":
                    diff += self._translation[b_start:b_end]
        return diff

    def get_name(self):
        return f"Translations:{self._identifier}/{self._language_code}"

    def remove_links(self):
        """
        Remove links (both in definition and in translation). Warns also if there is a link without |
        Example: [[Prayer]] causes a warning, correct would be [[Prayer|Prayer]].
        We have this convention so that translators are less confused as they need to write e.g. [[Prayer/de|Gebet]]
        """
        # This does all necessary replacements if the link correctly uses the form [[destination|description]]
        link_pattern_with_bar = re.compile(r"\[\[(.*?)\|(.*?)\]\]")
        self._definition = link_pattern_with_bar.sub(r"\2", self._definition)
        self._translation = link_pattern_with_bar.sub(r"\2", self._translation)

        # Now we check for links that are not following the convention
        # We need to remove the # of internal links, otherwise it gets the meaning of a numbering. (#?) does the trick
        link_pattern_without_bar = re.compile(r"\[\[(#?)(.*?)\]\]")
        match_d = link_pattern_without_bar.search(self._definition)
        if match_d:
            self.logger.warning(f"Found errorneous link {match_d.group(0)} in English original in {self.get_name()}. "
                                "Please tell an administrator.")
            self._definition = link_pattern_without_bar.sub(r"\2", self._definition)

        match_t = link_pattern_without_bar.search(self._translation)
        if match_t:
            self.logger.warning(f"The following link is errorneous: {match_t.group(0)}. "
                                f"It needs to be [[English destination/{self._language_code}|{match_t.group(2)}]]. "
                                f"Please correct {self.get_name()}")
            self._translation = link_pattern_without_bar.sub(r"\2", self._translation)

        if match_d or match_t:
            # Snippets need to be re-created. We don't have to do that right now, we'll do it just-in-time when needed
            self._definition_snippets = None
            self._translation_snippets = None

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
        if self._definition_snippets is None:
            self._definition_snippets = self.split_into_snippets(self._definition)
        if self._translation_snippets is None:
            self._translation_snippets = self.split_into_snippets(self._translation)

    def is_translation_well_structured(self, use_fallback: bool = False) -> bool:
        """
        Is the snippet structure of original and translation the same?

        This does quite some logging to provide helpful feedback for people working on the translations
        TODO do some checks to see how often fallback method of split_into_snippets() is actually necessary
        Potentially remove the fallback parameter
        """
        self._ensure_split()
        assert self._definition_snippets is not None and self._translation_snippets is not None

        if len(self._definition_snippets) != len(self._translation_snippets):
            # TODO give more specific warnings like "missing #" or "Number of = mismatch"
            if use_fallback:
                self.logger.info("Number of *, =, #, italic and bold formatting, ;, : and html tags is not equal"
                                 f" in original and translation:\n{self._definition}\n{self._translation}")
                self.logger.info('Falling back: removing all formatting and trying again')
                self._definition_snippets = self.split_into_snippets(self._definition, fallback=True)
                self._translation_snippets = self.split_into_snippets(self._translation, fallback=True)

            if len(self._definition_snippets) != len(self._translation_snippets):
                br_in_definition = len([s for s in self._definition_snippets if s.is_br()])
                br_in_translation = len([s for s in self._translation_snippets if s.is_br()])
                if br_in_definition != br_in_translation:
                    # There could be another issue besides the <br/> issue. Still this warning is probably helpful
                    self.logger.warning(f"Couldn't process Translations:{self.get_name()}. "
                                        f"Reason: Missing/wrong <br/> "
                                        f"(in original: {br_in_definition}, in translation: {br_in_translation})")
                else:
                    self.logger.warning("Couldn't process the following translation unit. Reason: Formatting issues. "
                                        "Please check that all special characters like * = # ; : <b> <i> are correct.")
                self.logger.warning(f"Original: \n{self._definition}")
                self.logger.warning(f"Translation: \n{self._translation}")
                return False

            self.logger.warning("Found an issue with formatting (special characters like * = # ; : <b> <i>). "
                                "I ignored all formatting and could continue. You may ignore this error "
                                f"or correct the translation unit {self.get_name()}")

        # Iterate over both lists at the same time and check whether the snippet types fit each other
        for d_snippet, t_snippet in zip(self._definition_snippets, self._translation_snippets):
            # Currently we test only whether they have the same SnippetType. TODO check whether they actually match
            if d_snippet.get_type() != t_snippet.get_type():
                return False
#            if (d_snippet.get_type() == SnippetType.MARKUP_SNIPPET) and (d_snippet.content != t_snippet.content):
#                return False

        return True

    def __iter__(self):
        """Make this class iterable in a simple way (not suitable for concurrency!)"""
        self._ensure_split()
        self._iterate_pos = 0
        return self

    def __next__(self):
        """
        Return a next tuple of original and translated snippet with content

        This leaves out snippets that are markup. Also it assumes is_translation_well_structured(),
        otherwise this will probably raise errors (todo make it more robust?)
        """
        while self._iterate_pos < len(self._definition_snippets):
            if self._iterate_pos >= len(self._translation_snippets):
                self.logger.warning(f"Internal error while iterating over {self.get_name()}: "
                                    "Inconsistency in snippets. You didn't call is_translation_well_structured()!")
                raise StopIteration
            definition_snippet = self._definition_snippets[self._iterate_pos]
            translation_snippet = self._translation_snippets[self._iterate_pos]
            self._iterate_pos += 1
            if definition_snippet.is_text():
                return (definition_snippet, translation_snippet)
        raise StopIteration


class TranslatedPage:
    """
    Holds all translation units of a translated worksheet and analyzes them
    to provide some information we need in some places.

    This class is not fetching the content on its own, they need to provided in the constructor.
    Also there is no persistence: If you make changes it's your responsibility to write them back
    to the mediawiki system.
    """

    def __init__(self, page: str, language_code: str, units: List[TranslationUnit]):
        self.page: Final[str] = page                    # Name of the worksheet
        self.language_code: Final[str] = language_code
        self._infos: Optional[Dict[str, str]] = None    # Storing results of analyze_units()
        self.units: List[TranslationUnit] = units       # Our translation units
        self._iterate_pos = 0      # For iterating over all translation units in this TranslatedPage

    def _analyze_units(self):
        """
        Analyzes translation units to fill our self._infos data structure.

        Previously extracted information is discarded.
        Currently this is implemented as Dict[str, str] - an alternative would be to make it
        Dict[str, TranslationUnit]: that would probably save a little memory and be a bit more elegant,
        on the other hand it maybe needs some more lines of code?
        """
        self._infos = {}
        # find out version, name of original odt-file and name of translated odt-file
        for tu in self.units:
            if tu.is_title():
                self._infos["headline_original"] = tu.get_definition()
                self._infos["headline_translation"] = tu.get_translation()
            if re.search(r"\.odt$", tu.get_definition()):
                self._infos["odt_original"] = tu.get_definition()
                self._infos["odt_translation"] = tu.get_translation()
            # Searching for version number (valid examples: 1.0; 2.1; 0.7b; 1.5a)
            if re.search(r"^\d\.\d[a-zA-Z]?$", tu.get_definition()):
                self._infos["version_original"] = tu.get_definition()
                self._infos["version_translation"] = tu.get_translation()
            # TODO extract also PDF files?

    def _get_info(self, key: str) -> str:
        """
        Return the value of an item of our information storage.
        If the key doesn't exist, an empty string is returned.
        """
        if self._infos is None:
            self._analyze_units()
        assert self._infos is not None
        return self._infos[key] if key in self._infos else ""

    def get_original_headline(self) -> str:
        return self._get_info("headline_original")

    def get_translated_headline(self) -> str:
        return self._get_info("headline_translation")

    def get_original_version(self) -> str:
        return self._get_info("version_original")

    def get_translated_version(self) -> str:
        return self._get_info("version_translation")

    def get_original_odt(self) -> str:
        return self._get_info("odt_original")

    def get_translated_odt(self) -> str:
        return self._get_info("odt_translation")

    def add_translation_unit(self, unit: TranslationUnit):
        self.units.append(unit)

#    def add_translation_units(self, page: TranslatedPage):
#        for unit in page:
#            self.units.append(unit)

    def __iter__(self):
        """Make this class iterable in a simple way (not suitable for concurrency!)"""
        self._iterate_pos = 0
        return self

    def __next__(self):
        """Return a next translation unit"""
        if self._iterate_pos < len(self.units):
            self._iterate_pos += 1
            return self.units[self._iterate_pos - 1]
        raise StopIteration
