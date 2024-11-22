import logging
from configparser import ConfigParser
from typing import Final

import pywikibot

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog, ChangeType
from pywikitools.resourcesbot.data_structures import LanguageInfo, WorksheetInfo
from pywikitools.resourcesbot.modules.post_processing import LanguagePostProcessor


class WriteSidebarMessages(LanguagePostProcessor):
    """
    Write/update the system messages for the sidebar with the translated
    titles of worksheets.
    These are used when displaying the whole website in another language
    (changing the "user interface language")

    E.g., write German headline of "Hearing from God"
    to https://www.4training.net/MediaWiki:Sidebar-hearingfromgod/de

    More information on system messages:
    https://www.mediawiki.org/wiki/Help:System_message

    This class can be re-used to call run() several times
    """
    @classmethod
    def help_summary(cls) -> str:
        return "Write the system messages for sidebar with translated titles"

    @classmethod
    def abbreviation(cls) -> str:
        return "sidebar"

    @classmethod
    def can_be_rewritten(cls) -> bool:
        return True

    def __init__(
        self,
        fortraininglib: ForTrainingLib,
        config: ConfigParser,
        site: pywikibot.site.APISite
    ):
        super().__init__(fortraininglib, config, site)
        self.logger: Final[logging.Logger] = logging.getLogger(
            "pywikitools.resourcesbot.modules.write_sidebar_messages"
        )

    def save_worksheet_title(self, worksheet: WorksheetInfo):
        """Save system message with the title of the given worksheet."""
        title = (
            f"MediaWiki:"
            f"{self.fortraininglib.title_to_message(worksheet.page).capitalize()}"
        )
        if worksheet.language_code != "en":
            title += f"/{worksheet.language_code}"
        self.logger.debug(f"save_worksheet_title(): title = {title}")
        page = pywikibot.Page(self._site, title)
        previous_content = ""
        if page.exists():
            previous_content = page.text

        if previous_content != worksheet.title:
            self.logger.info(f"Updating system message {title}")
            page.text = worksheet.title
            page.save("Updated translated worksheet title")

    @staticmethod
    def has_relevant_change(worksheet: str, changes: ChangeLog) -> bool:
        """
        Is there a relevant change for our worksheet?
        Relevant is a change indicating that the translated title might have changed
        (new / updated worksheet)
        """
        for change_item in changes:
            if change_item.worksheet == worksheet:
                if (
                    change_item.change_type == ChangeType.NEW_WORKSHEET
                    or change_item.change_type == ChangeType.UPDATED_WORKSHEET
                ):
                    return True
        return False

    def run(
        self,
        language_info: LanguageInfo,
        _english_info,
        changes: ChangeLog,
        _english_changes,
        *,
        force_rewrite: bool = False
    ) -> None:
        """Our entry function"""
        for worksheet in language_info.worksheets.values():
            if worksheet.title == "":
                continue
            if force_rewrite or self.has_relevant_change(worksheet.page, changes):
                self.save_worksheet_title(worksheet)
