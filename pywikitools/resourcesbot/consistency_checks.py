"""
Contains consistency checks specifically for 4training.net
"""

import logging
from typing import Final, Optional, Union
from pywikitools import fortraininglib
from pywikitools.lang.translated_page import TranslationUnit
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import LanguageInfo, WorksheetInfo
from pywikitools.resourcesbot.post_processing import LanguagePostProcessor


class ConsistencyCheck(LanguagePostProcessor):
    TITLE: Final[str] = "Page display title"

    def __init__(self):
        self.logger = logging.getLogger("pywikitools.resourcesbot.consistency_checks")

    def load_translation_unit(self, language_info: LanguageInfo, page: str,
            identifier: Union[int, str]) -> Optional[TranslationUnit]:
        """
        Try to load a translation unit

        If we request the title of a worksheet, let's first try to see if it's already in language_info.
        Then we don't need to make an API query.
        Otherwise we try to load the translation unit from the mediawiki system
        """
        if isinstance(identifier, int):
            content = fortraininglib.get_translated_unit(page, language_info.get_language_code(), identifier)
            if content is None:
                self.logger.info(f"Couldn't load {page}/{identifier}/{language_info.get_language_code()}")
                return None
            return TranslationUnit(f"{page}/{identifier}", language_info.get_language_code(),
                "", content) # Leaving definition parameter empty because we don't have it and don't need it

        elif identifier == self.TITLE:
            worksheet_info: Optional[WorksheetInfo] = language_info.get_worksheet(page)
            if worksheet_info is not None:
                return TranslationUnit(f"{page}/{language_info.get_language_code()}",
                    language_info.get_language_code(), page, worksheet_info.title)
            content = fortraininglib.get_translated_title(page, language_info.get_language_code())
            if content is None:
                self.logger.info(f"Couldn't load {page}/{identifier}/{language_info.get_language_code()}")
                return None
            return TranslationUnit(f"{page}/Page display title",
                language_info.get_language_code(), page, content)

        else:
            raise LookupError(f"Invalid unit name {page}/{identifier}/{language_info.get_language_code()}")

    def should_be_equal(self, base: Optional[TranslationUnit], other: Optional[TranslationUnit]):
        if base is None or other is None:
            return
        if other.get_translation() == base.get_translation():
            self.logger.info(f"Consistency check passed: {base.get_translation()} == {other.get_translation()}")
        else:
            self.logger.warning(f"Consistency check failed: {other.get_translation()} is not equal to "
                                f"{base.get_translation()}. Check {base.get_name()} and {other.get_name()}")

    def should_start_with(self, base: Optional[TranslationUnit], other: Optional[TranslationUnit]):
        if base is None or other is None:
            return
        if other.get_translation().startswith(base.get_translation()):
            self.logger.info(f"Consistency check passed: {other.get_translation()} starts with {base.get_translation()}.")
        else:
            self.logger.warning(f"Consistency check failed: {other.get_translation()} does not start with "
                                f"{base.get_translation()}. Check {base.get_name()} and {other.get_name()}")

    def check_bible_reading_hints_titles(self, language_info: LanguageInfo):
        """Titles of the different Bible Reading Hints variants should start the same"""
        self.should_start_with(
            self.load_translation_unit(language_info, "Bible_Reading_Hints", self.TITLE),
            self.load_translation_unit(language_info, "Bible_Reading_Hints_(Seven_Stories_full_of_Hope)", self.TITLE))
        self.should_start_with(
            self.load_translation_unit(language_info, "Bible_Reading_Hints", self.TITLE),
            self.load_translation_unit(language_info, "Bible_Reading_Hints_(Starting_with_the_Creation)", self.TITLE))

    def check_gods_story_titles(self, language_info: LanguageInfo):
        """Titles of the two different variants of God's Story should start the same"""
        self.should_start_with(
            self.load_translation_unit(language_info, "God's_Story", self.TITLE),
            self.load_translation_unit(language_info, "God's_Story_(first_and_last_sacrifice)", self.TITLE))
        self.should_start_with(
            self.load_translation_unit(language_info, "God's_Story", self.TITLE),
            self.load_translation_unit(language_info, "God's_Story_(five_fingers)", self.TITLE))

    def check_who_do_i_need_to_forgive(self, language_info: LanguageInfo):
        """Should both be 'God, who do I need to forgive?'"""
        self.should_be_equal(self.load_translation_unit(language_info, "How_to_Continue_After_a_Prayer_Time", 11),
            self.load_translation_unit(language_info, "Forgiving_Step_by_Step", 34))

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