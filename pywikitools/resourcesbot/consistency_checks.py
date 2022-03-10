"""
Contains consistency checks specifically for 4training.net
"""

import logging
from typing import Final, Optional, Union
from pywikitools import fortraininglib
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import LanguageInfo, WorksheetInfo
from pywikitools.resourcesbot.post_processing import LanguagePostProcessor


class ConsistencyCheck(LanguagePostProcessor):
    TITLE: Final[str] = "Page display title"

    def __init__(self):
        self.logger = logging.getLogger("pywikitools.resourcesbot.consistency_checks")

    def make_link(self, page: WorksheetInfo, translation_unit: Union[str, int]) -> str:
        return f"{fortraininglib.BASEURL}/Translations:{page.page}/{translation_unit}/{page.language_code}"

    def _load_content(self, page: WorksheetInfo, translation_unit: Union[str, int]) -> str:
        if isinstance(translation_unit, int):
            content = fortraininglib.get_translated_unit(page.page, page.language_code, translation_unit)
            if content is None:
                raise LookupError(f"Couldn't get {self.make_link(page, translation_unit)}")
            return content
        elif translation_unit == self.TITLE:
            return page.title
        else:
            raise LookupError(f"Invalid unit name {page.page}/{translation_unit}/{page.language_code}")

    def should_be_equal(self, base_page: Optional[WorksheetInfo], base_unit: Union[str, int],
                         other_page: Optional[WorksheetInfo], other_unit: Union[str, int]):
        if base_page is None or other_page is None:
            return
        base: str = self._load_content(base_page, base_unit)
        other: str = self._load_content(other_page, other_unit)
        if other == base:
            self.logger.info(f"Consistency check passed: {base} == {other}")
        else:
            self.logger.warning(f"Consistency check failed: {other} is not equal to {base}."
                                f" Check {self.make_link(base_page, base_unit)}"
                                f" and {self.make_link(other_page, other_unit)}")

    def should_start_with(self, base_page: Optional[WorksheetInfo], base_unit: Union[str, int],
                         other_page: Optional[WorksheetInfo], other_unit: Union[str, int]):
        if base_page is None or other_page is None:
            return
        base = self._load_content(base_page, base_unit)
        other = self._load_content(other_page, other_unit)
        if other.startswith(base):
            self.logger.info(f"Consistency check passed: {other} starts with {base}.")
        else:
            self.logger.warning(f"Consistency check failed: {other} does not start with {base}."
                                f" Check {self.make_link(base_page, base_unit)}"
                                f" and {self.make_link(other_page, other_unit)}")

    def should_start_with_2(self, base_page: str, language_code: str, base_unit: Union[str, int],
                         other_page: Optional[WorksheetInfo], other_unit: Union[str, int]):
        """TODO can this be done more elegant?"""
        base_content: str = ""
        if isinstance(base_unit, int):
            content = fortraininglib.get_translated_unit(base_page, language_code, base_unit)
            if content is None:
                return
            base_content = content
        elif base_unit == self.TITLE:
            content = fortraininglib.get_translated_title(base_page, language_code)
            if content is None:
                return
            base_content = content
        else:
            raise LookupError(f"Invalid unit name {base_page}/{base_unit}/{language_code}")

        if other_page is None:
            return
        other = self._load_content(other_page, other_unit)
        if other.startswith(base_content):
            self.logger.info(f"Consistency check passed: {other} starts with {base_content}.")
        else:
            self.logger.warning(f"Consistency check failed: {other} does not start with {base_content}."
                                f" Check {base_page}/{base_unit}/{language_code}"   # TODO
                                f" and {self.make_link(other_page, other_unit)}")


    def check_bible_reading_hints_titles(self, language_info: LanguageInfo):
        """Titles of the different Bible Reading Hints variants should start the same"""
        self.should_start_with(
            language_info.get_worksheet("Bible_Reading_Hints"), self.TITLE,
            language_info.get_worksheet("Bible_Reading_Hints_(Seven_Stories_full_of_Hope)"), self.TITLE)
        self.should_start_with(
            language_info.get_worksheet("Bible_Reading_Hints"), self.TITLE,
            language_info.get_worksheet("Bible_Reading_Hints_(Starting_with_the_Creation)"), self.TITLE)

    def check_gods_story_titles(self, language_info: LanguageInfo):
        """Titles of the two different variants of God's Story should start the same"""
        self.should_start_with_2(
            "God's_Story", language_info.get_language_code(), self.TITLE,
            language_info.get_worksheet("God's_Story_(first_and_last_sacrifice)"), self.TITLE)
        self.should_start_with_2(
            "God's_Story", language_info.get_language_code(), self.TITLE,
            language_info.get_worksheet("God's_Story_(five_fingers)"), self.TITLE)

    def check_who_do_i_need_to_forgive(self, language_info: LanguageInfo):
        """Should both be 'God, who do I need to forgive?'"""
        self.should_be_equal(
            language_info.get_worksheet("How_to_Continue_After_a_Prayer_Time"), 11,
            language_info.get_worksheet("Forgiving_Step_by_Step"), 34)

    def run(self, language_info: LanguageInfo, change_log: ChangeLog):
        self.check_bible_reading_hints_titles(language_info)
        self.check_gods_story_titles(language_info)
        self.check_who_do_i_need_to_forgive(language_info)

"""
TODO: implement the following checks:
Should be the same:
Translations:Bible Reading Hints (Seven Stories full of Hope)/Page display title/de
The link title in Translations:Bible Reading Hints/2/ru

Should be the same:
Translations:Bible Reading Hints (Starting with the Creation)/Page display title/de
The link title in Translations:Bible Reading Hints/2/ru

Head-Heart-Hands questions should be the same on
https://www.4training.net/Time_with_God/tr-tanri
https://www.4training.net/Template:BibleReadingHints

Many title from the Three-Thirds-Process and from Template:BibleReadingHints should be the same

Template:BibleReadingHints translation of "Acts" in should be the same in both variants:
Translations:Template:BibleReadingHints/24/de
Translations:Template:BibleReadingHints/26/de

Each list item of the Seven Stories full of hope starts with a number (in the target language of course...)
e.g. Translations:Bible Reading Hints (Seven Stories full of Hope)/7/id starts with "1."
"""