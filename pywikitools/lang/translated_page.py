
from datetime import datetime
import difflib
from enum import Enum
import logging
import re
from typing import Final, List, Optional, Tuple

from pywikitools.resourcesbot.data_structures import TranslationProgress, FileInfo, WorksheetInfo


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
    __slots__ = ['type', 'content']

    def __init__(self, snippet_type: SnippetType, content: str):
        self.type: Final[SnippetType] = snippet_type
        self.content: str = content

    def is_text(self) -> bool:
        return self.type == SnippetType.TEXT_SNIPPET

    def is_markup(self) -> bool:
        return self.type == SnippetType.MARKUP_SNIPPET

    def is_br(self) -> bool:
        return (self.type == SnippetType.MARKUP_SNIPPET) and bool(re.match("<br ?/?>\n?", self.content))

    def __str__(self):
        return f"{self.type.name} ({len(self.content)}): {self.content}"


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

    def __init__(self, identifier: str, language_code: str, definition: str, translation: Optional[str]):
        """
        @param identifier: The key of the translation unit (e.g. "Prayer/7")
        @param definition: The original text (usually English)
        @param translation: The translation of the definition
                            None or "" have the same meaning: there is no translation
        """
        assert isinstance(identifier, str) and isinstance(language_code, str) and isinstance(definition, str)
        self.identifier: Final[str] = identifier
        self.language_code: Final[str] = language_code
        self._definition: str = definition
        self._original_definition: str = definition
        self._translation: str = ""
        if translation is not None:
            self._translation = translation
        self._original_translation: str = self._translation
        self._definition_snippets: Optional[List[TranslationSnippet]] = None
        self._translation_snippets: Optional[List[TranslationSnippet]] = None
        self._iterate_pos: int = 0      # For iterating over all snippets in this TranslationUnit
        self.logger = logging.getLogger('pywikitools.lang.TranslationUnit')

    def is_title(self) -> bool:
        """Is this unit holding the title of a page?"""
        return self.identifier.endswith("Page_display_title")

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
        """Returns an empty string if no translation exists"""
        return self._translation

    def get_original_translation(self) -> str:
        """Return the original translation this TranslationUnit was constructed with"""
        return self._original_translation

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
        return f"Translations:{self.identifier}/{self.language_code}"

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
                                f"It needs to be [[English destination/{self.language_code}|{match_t.group(2)}]]. "
                                f"Please correct {self.get_name()}")
            self._translation = link_pattern_without_bar.sub(r"\2", self._translation)

        if match_d or match_t:
            # Snippets need to be re-created. We don't have to do that right now, we'll do it just-in-time when needed
            self._definition_snippets = None
            self._translation_snippets = None

    @staticmethod
    def split_into_snippets(text: str) -> List[TranslationSnippet]:
        """
        Split the given text into snippets

        We split at the following formatting / markup items:
            * or #: bullet list / numbered list items (exception: [[#internal links]])
            == up to ======: section headings
            : at the beginning of a line: definition list / indent text
            ; at the beginning of a line: definition list
        For <br/>, if there is a following newline, include it also in the match.
        For *#;: if there is a following whitespace character, include it also in the match.
        """
        snippets: List[TranslationSnippet] = []
        last_pos = 0
        pattern = re.compile(r"<br ?/?>\n?|[*#]\s?|={2,6}|^:\s?|^;\s?", flags=re.MULTILINE)
        for match in re.finditer(pattern, text):
            if (match.group()[0] == '#') and (match.start() >= 2) and (text[match.start() - 2:match.start()] == "[["):
                continue        # Ignore '#' if it's part of an [[#internal link]]
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

    def is_translation_well_structured(self) -> Tuple[bool, str]:
        """
        Is the snippet structure of original and translation the same?

        This does quite some logging to provide helpful feedback for people working on the translations
        @return Tuple of actual return value and warning message if it is False
        """
        self._ensure_split()
        assert self._definition_snippets is not None and self._translation_snippets is not None
        is_well_structured = True

        if len(self._definition_snippets) != len(self._translation_snippets):
            is_well_structured = False
        else:
            # Iterate over both lists at the same time and check whether the snippet types fit each other
            for d_snippet, t_snippet in zip(self._definition_snippets, self._translation_snippets):
                # Currently we test only whether they have the same SnippetType. TODO check whether they actually match
                if d_snippet.type != t_snippet.type:
                    is_well_structured = False
        #            if (d_snippet.type == SnippetType.MARKUP_SNIPPET) and (d_snippet.content != t_snippet.content):
        #                return False

        if not is_well_structured:
            # TODO give more specific warnings like "missing #" or "Number of = mismatch"
            br_in_definition = len([s for s in self._definition_snippets if s.is_br()])
            br_in_translation = len([s for s in self._translation_snippets if s.is_br()])
            if br_in_definition != br_in_translation:
                warning_message = f"Missing/wrong <br/> in {self.get_name()} "
                warning_message += f"(in original: {br_in_definition}, in translation: {br_in_translation})"
            else:
                warning_message = f"Formatting issues in {self.get_name()}. "
                warning_message += "Please check that all special characters like * = # ; : <b> <i> are correct."
            return (False, warning_message)

        return (True, "")

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

    def __str__(self) -> str:
        content = f"{self.identifier}/{self.language_code}: "
        content += f"Definition={self._definition} (original: {self._original_definition}) "
        content += f"Translation={self._translation} (original: {self._original_translation}). Snippets:\n"
        self._ensure_split()
        assert self._translation_snippets is not None
        for snippet in self._translation_snippets:
            content += f"- {snippet}\n"
        return content

    def __copy__(self):
        """Return a copy of our TranslationUnit"""
        return TranslationUnit(self.identifier, self.language_code, self._definition, self._translation)

    def __lt__(self, other) -> bool:
        """
        Compare our TranslationUnit to another TranslationUnit: Is any of our snippet definitions a substring
        of a snippet of the other TranslationUnit?

        Used in TranslateODT.special_sort_units()

        Remark: We don't check whether the snippets in self._definition_snippets contain each other -
        any translation administrator should make sure that never happens...
        @return Tuple(self_is_in_other, other_is_in_self)
        """
        assert isinstance(other, TranslationUnit)
        self._ensure_split()
        assert self._definition_snippets is not None and self._translation_snippets is not None
        self_is_in_other = False
        other_is_in_self = False
        for counter, snippet in enumerate(self._definition_snippets):
            if not snippet.is_text():
                continue
            for other_snippet, other_snippet_translation in other:
                if snippet.content == other_snippet.content:
                    if self._translation_snippets[counter].content != other_snippet_translation.content:
                        self.logger.warning(f"{self.get_name()} and {other.get_name()} have same definition: "
                                            f"{other_snippet.content} but different translations: "
                                            f"{self._translation_snippets[counter].content} / "
                                            f"{other_snippet_translation.content}")
                    continue
                if snippet.content in other_snippet.content:
                    self.logger.info(f'"{snippet.content}" (in {self.get_name()}) is a substring of '
                                     f'"{other_snippet.content}" (in {other.get_name()})!')
                    self_is_in_other = True
                elif other_snippet.content in snippet.content:
                    self.logger.info(f'"{other_snippet.content}" (in {other.get_name()}) is a substring of '
                                     f'"{snippet.content}" (in {self.get_name()})!')
                    other_is_in_self = True
        if self_is_in_other and other_is_in_self:
            self.logger.warning(f"{self.get_name()} and {other.get_name()} have reciprocal substrings: "
                                f"{self.get_definition()} / {other.get_definition()} "
                                "Please resolve this conflict!")
        return self_is_in_other


class TranslatedPage:
    """
    Holds all translation units of a translated worksheet and analyzes them
    to provide some information we need in some places.

    This class is not fetching the content on its own, they need to be provided in the constructor.
    Also there is no persistence: If you make changes it's your responsibility to write them back
    to the mediawiki system.
    """
    __slots__ = ["page", "language_code", "units", "_english_info", "_worksheet_info", "_iterate_pos"]

    def __init__(self, page: str, language_code: str, units: List[TranslationUnit]):
        self.page: Final[str] = page                    # Name of the worksheet
        self.language_code: Final[str] = language_code
        self.units: List[TranslationUnit] = units       # Our translation units
        self._english_info: Optional[WorksheetInfo] = None      # WorksheetInfo of English original
        self._worksheet_info: Optional[WorksheetInfo] = None    # WorksheetInfo of translation
        self._iterate_pos: int = 0      # For iterating over all translation units in this TranslatedPage

    def get_english_info(self) -> WorksheetInfo:
        if self._english_info is None:
            self._analyze_units()
        assert self._english_info is not None
        return self._english_info

    def get_worksheet_info(self) -> WorksheetInfo:
        if self._worksheet_info is None:
            self._analyze_units()
        assert self._worksheet_info is not None
        return self._worksheet_info

    def is_untranslated(self) -> bool:
        return self.get_worksheet_info().progress.translated == 0

    def _analyze_units(self):
        """
        Analyzes translation units to fill our self._english_info and self._worksheet_info

        Previously extracted information is discarded.
        Information on ODT files is added (if existing) with url = filename (no full URL) and incorrect timestamp
        Information information on PDF files is not extracted as it is currently not needed.
        As we don't know here whether a translation is fuzzy (possible outdated) or not, the generated
        TranslationProgress will always have fuzzy = 0.
        Currently we are not giving any warnings even if headline_original or version_original is empty
        """
        # find out headline, version, name of original odt-file and name of translated odt-file
        translated_units: int = 0
        headline_original: str = ""
        headline_translation: str = ""
        odt_original: str = ""
        odt_translation: str = ""
        version_original: str = ""
        version_translation: str = ""
        for u in self.units:
            if u.get_translation() != "":
                translated_units += 1
            if u.is_title():
                headline_original = u.get_definition()
                headline_translation = u.get_translation()
            if re.search(r"\.odt$", u.get_definition()):
                odt_original = u.get_definition()
                odt_translation = u.get_translation()
            # Searching for version number (valid examples: 1.0; 2.1; 0.7b; 1.5a)
            if re.search(r"^\d\.\d[a-zA-Z]?$", u.get_definition()):
                version_original = u.get_definition()
                version_translation = u.get_translation()

        self._english_info = WorksheetInfo(self.page, "en", headline_original,
            TranslationProgress(len(self.units), 0, len(self.units)), version_original)      # noqa: E128
        if odt_original != "":
            self._english_info.add_file_info(FileInfo("odt", odt_original, datetime(1970, 1, 1)))
        self._worksheet_info = WorksheetInfo(self.page, self.language_code, headline_translation,
            TranslationProgress(translated_units, 0, len(self.units)), version_translation)  # noqa: E128
        if odt_translation != "":
            self._worksheet_info.add_file_info(FileInfo("odt", odt_translation, datetime(1970, 1, 1)))

    def add_translation_unit(self, unit: TranslationUnit):
        """Append a translation unit. Infos are not invalidated"""
        self.units.append(unit)

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
