"""
Contains consistency checks specifically for 4training.net
"""

import logging
import re
from configparser import ConfigParser
from typing import Final, Optional, Tuple, Union

import pywikibot.site

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.lang.translated_page import TranslationUnit
from pywikitools.resourcesbot.data_structures import LanguageInfo, WorksheetInfo
from pywikitools.resourcesbot.modules.post_processing import LanguagePostProcessor
from pywikitools.resourcesbot.reporting import LanguageReport


class ConsistencyCheck(LanguagePostProcessor):
    """
    Post-processing plugin: Check whether some translation units with the same English
    definition also have the same translation in the specified language

    This is completely 4training.net-specific.
    Next step: Write the results to some meaningful place on 4training.net
               so that translators can access them and correct inconsistencies
    """

    TITLE: Final[str] = "Page display title"

    @classmethod
    def help_summary(cls) -> str:
        return "Check consistency of translations"

    @classmethod
    def abbreviation(cls) -> str:
        return "check"

    @classmethod
    def can_be_rewritten(cls) -> bool:
        return False

    def __init__(
        self,
        fortraininglib: ForTrainingLib,
        config: ConfigParser = None,
        site: pywikibot.site.APISite = None
    ):
        super().__init__(fortraininglib, config, site)
        self.logger = logging.getLogger(
            "pywikitools.resourcesbot.modules.consistency_checks"
        )

    def extract_link(self, text: str) -> Tuple[str, str]:
        """
        Search in text for a mediawiki link of the form [[Destination|Title]].
        This function will only look at the first link it finds in the text, any other
        will be ignored.
        @return a tuple (destination, title). In case no link was found both strings
        will be empty.
        """
        match = re.search(r"\[\[([^|]+)\|([^\]]+)\]\]", text)
        if not match:
            return "", ""
        return match.group(1), match.group(2)

    def load_translation_unit(
        self, language_info: LanguageInfo, page: str, identifier: Union[int, str]
    ) -> Optional[TranslationUnit]:
        """
        Try to load a translation unit

        If we request the title of a worksheet, let's first try to see if it's already
        in language_info. Then we don't need to make an API query.
        Otherwise we try to load the translation unit from the mediawiki system
        """
        if isinstance(identifier, int):
            content = self.fortraininglib.get_translated_unit(
                page, language_info.language_code, identifier
            )
            if content is None:
                self.logger.info(
                    f"Couldn't load {page}/{identifier}/{language_info.language_code}"
                )
                return None
            # Leaving definition parameter empty because we don't have it and
            # don't need it
            return TranslationUnit(
                f"{page}/{identifier}", language_info.language_code, "", content
            )

        elif identifier == self.TITLE:
            worksheet_info: Optional[WorksheetInfo] = language_info.get_worksheet(page)
            if worksheet_info is not None:
                return TranslationUnit(
                    f"{page}/Page display title",
                    language_info.language_code,
                    page,
                    worksheet_info.title,
                )
            content = self.fortraininglib.get_translated_title(
                page, language_info.language_code
            )
            if content is None:
                self.logger.info(
                    f"Couldn't load {page}/{identifier}/{language_info.language_code}"
                )
                return None
            return TranslationUnit(
                f"{page}/Page display title", language_info.language_code, page, content
            )

        else:
            raise LookupError(
                f"Invalid unit name {page}/{identifier}/{language_info.language_code}"
            )

    def should_be_equal(
        self, base: Optional[TranslationUnit], other: Optional[TranslationUnit]
    ) -> bool:
        """returns True if checks pass: base and other are the same (or not existing)"""
        if base is None or other is None:
            return True
        if other.get_translation() == base.get_translation():
            self.logger.debug(
                f"Consistency check passed: {base.get_translation()} == {other.get_translation()}"
            )
            return True
        self.logger.warning(
            f"Consistency check failed: {other.get_translation()} is not equal to "
            f"{base.get_translation()}. Check {base.get_name()} and {other.get_name()}"
        )
        return False

    def should_start_with(
        self, base: Optional[TranslationUnit], other: Optional[TranslationUnit]
    ) -> bool:
        """returns True if checks pass: other starts with base (or not existing)"""
        if base is None or other is None:
            return True
        if other.get_translation().startswith(base.get_translation()):
            self.logger.debug(
                f"Consistency check passed: "
                f"{other.get_translation()} starts with {base.get_translation()}."
            )
            return True
        self.logger.warning(
            f"Consistency check failed: {other.get_translation()} does not start with "
            f"{base.get_translation()}. Check {base.get_name()} and {other.get_name()}"
        )
        return False

    def check_bible_reading_hints_titles(self, language_info: LanguageInfo) -> bool:
        """Titles of the different Bible Reading Hints variants should start the same"""
        ret1 = self.should_start_with(
            self.load_translation_unit(
                language_info, "Bible_Reading_Hints", self.TITLE
            ),
            self.load_translation_unit(
                language_info,
                "Bible_Reading_Hints_(Seven_Stories_full_of_Hope)",
                self.TITLE,
            ),
        )
        ret2 = self.should_start_with(
            self.load_translation_unit(
                language_info, "Bible_Reading_Hints", self.TITLE
            ),
            self.load_translation_unit(
                language_info,
                "Bible_Reading_Hints_(Starting_with_the_Creation)",
                self.TITLE,
            ),
        )
        return ret1 and ret2

    def check_bible_reading_hints_links(self, language_info: LanguageInfo) -> bool:
        """Check whether the link titles in https://www.4training.net/Bible_Reading_Hints
        are identical with the titles of the destination pages"""
        ret1 = True
        ret2 = True
        link_unit = self.load_translation_unit(language_info, "Bible_Reading_Hints", 2)
        if link_unit is not None:
            _, title = self.extract_link(link_unit.get_translation())
            link_unit.set_translation(title)
            ret1 = self.should_be_equal(
                link_unit,
                self.load_translation_unit(
                    language_info,
                    "Bible_Reading_Hints_(Seven_Stories_full_of_Hope)",
                    self.TITLE,
                ),
            )
        link_unit = self.load_translation_unit(language_info, "Bible_Reading_Hints", 3)
        if link_unit is not None:
            _, title = self.extract_link(link_unit.get_translation())
            link_unit.set_translation(title)
            ret2 = self.should_be_equal(
                link_unit,
                self.load_translation_unit(
                    language_info,
                    "Bible_Reading_Hints_(Starting_with_the_Creation)",
                    self.TITLE,
                ),
            )
        return ret1 and ret2

    def check_gods_story_titles(self, language_info: LanguageInfo) -> bool:
        """Titles of the two different variants of God's Story should start the same"""
        ret1 = self.should_start_with(
            self.load_translation_unit(language_info, "God's_Story", self.TITLE),
            self.load_translation_unit(
                language_info, "God's_Story_(first_and_last_sacrifice)", self.TITLE
            ),
        )
        ret2 = self.should_start_with(
            self.load_translation_unit(language_info, "God's_Story", self.TITLE),
            self.load_translation_unit(
                language_info, "God's_Story_(five_fingers)", self.TITLE
            ),
        )
        return ret1 and ret2

    def check_who_do_i_need_to_forgive(self, language_info: LanguageInfo) -> bool:
        """Should both be 'God, who do I need to forgive?'"""
        return self.should_be_equal(
            self.load_translation_unit(
                language_info, "How_to_Continue_After_a_Prayer_Time", 11
            ),
            self.load_translation_unit(language_info, "Forgiving_Step_by_Step", 34),
        )

    def check_book_of_acts(self, language_info: LanguageInfo) -> bool:
        """The name of the book of Acts should be the same in different
        Bible Reading Hints variants"""
        t24 = self.load_translation_unit(
            language_info, "Template:BibleReadingHints", 24
        )
        t26 = self.load_translation_unit(
            language_info, "Template:BibleReadingHints", 26
        )
        if (
            t24 is None
            or (len(t24.get_translation()) <= 3)
            or t26 is None
            or (len(t26.get_translation()) <= 3)
        ):
            return True
        # Text is e.g. "2. Apostelgeschichte" / "3. Apostelgeschichte" -> remove first three characters
        t24.set_translation(t24.get_translation()[3:])
        t26.set_translation(t26.get_translation()[3:])
        return self.should_be_equal(t24, t26)

    def run(
        self, language_info: LanguageInfo, _english_info, _changes, _english_changes,
        *, force_rewrite: bool = False
    ):
        checks_passed: int = 0
        checks_passed += int(self.check_bible_reading_hints_titles(language_info))
        checks_passed += int(self.check_gods_story_titles(language_info))
        checks_passed += int(self.check_who_do_i_need_to_forgive(language_info))
        checks_passed += int(self.check_bible_reading_hints_links(language_info))
        checks_passed += int(self.check_book_of_acts(language_info))
        self.logger.info(
            f"Consistency checks for {language_info.english_name}: {checks_passed}/5 passed"
        )
        lang_report = ConsistencyLanguageReport(language_info.language_code)
        lang_report.checks_passed = checks_passed
        return lang_report


"""
TODO implement more consistency checks:
- Each list item of the Seven Stories full of Hope should start with a number
(in the target language of course...)
  e.g. Translations:Bible Reading Hints (Seven Stories full of Hope)/7/id starts with "1."

- Check each link: Is the title the same as the title of the destination page?

More consistency checks that currently can't be automated:

Head-Heart-Hands questions should be the same on
https://www.4training.net/Time_with_God
https://www.4training.net/Template:BibleReadingHints
-> not automated because the first uses "me", the latter "we"

Many title from the Three-Thirds-Process and from Template:BibleReadingHints should
be the same
-> needs to be checked manually
"""


class ConsistencyLanguageReport(LanguageReport):
    """
    A specialized report for export_pdf,
    containing information about saved pdfs
    """

    def __init__(self, language_code: str):
        super().__init__(language_code)

        self.checks_passed = 0

    @classmethod
    def get_module_name(cls) -> str:
        return "export_pdf"

    def consistent(self):
        if self.checks_passed == 5:
            return True
        else:
            return False

    def get_summary(self) -> str:
        return (f"Ran Consistency checks for: {self.language}: {self.checks_passed}/5 checks passed.")

    @classmethod
    def get_module_summary(cls, lang_reports: list) -> str:
        if len(lang_reports) == 0:
            return ""

        total_checks_passed = sum(report.checks_passed for report in lang_reports)
        consistent_reports = [report for report in lang_reports if report.consistent()]

        return (f"Ran Consistency checks for {len(lang_reports)} languages. "
                f"Consistent languages: {len(consistent_reports)}/{len(lang_reports)}, "
                f"Overall: {total_checks_passed}/{len(lang_reports) * 5} checks passed.")
