import logging
import re
from configparser import ConfigParser
from typing import Final, Optional, Tuple

import pywikibot

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog, ChangeType
from pywikitools.resourcesbot.data_structures import FileInfo, LanguageInfo
from pywikitools.resourcesbot.modules.post_processing import LanguagePostProcessor
from pywikitools.resourcesbot.reporting import LanguageReport


class WriteList(LanguagePostProcessor):
    """
    Write/update the list of available training resources for languages.

    We only show worksheets that have a PDF file (to ensure good quality)

    This class can be re-used to call run() several times
    """
    @classmethod
    def help_summary(cls) -> str:
        return "Write list of available training resources for languages"

    @classmethod
    def abbreviation(cls) -> str:
        return "list"

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
        self._username: Final[str] = config.get("resourcesbot", "username", fallback="")
        self._password: Final[str] = config.get("resourcesbot", "password", fallback="")
        self.logger: Final[logging.Logger] = logging.getLogger(
            "pywikitools.resourcesbot.modules.write_lists"
        )

        if self._username == "" or self._password == "":
            self.logger.warning(
                "Missing user name and/or password in config."
                "Won't mark pages for translation."
            )

    def needs_rewrite(self, language_info: LanguageInfo, changes: ChangeLog) -> bool:
        """Determine whether the list of available training resources needs
        to be rewritten.
        """
        lang = language_info.language_code
        needs_rewrite = False
        for change_item in changes:
            if change_item.change_type in [
                ChangeType.UPDATED_PDF,
                ChangeType.NEW_PDF,
                ChangeType.DELETED_PDF,
                ChangeType.NEW_WORKSHEET,
                ChangeType.DELETED_WORKSHEET,
            ]:
                needs_rewrite = True
            if (
                change_item.change_type in [ChangeType.NEW_ODT, ChangeType.DELETED_ODT]
            ) and language_info.worksheet_has_type(change_item.worksheet, "pdf"):
                needs_rewrite = True

        if needs_rewrite:
            self.logger.info(
                f"List of available training resources in language {lang} needs "
                f"to be re-written."
            )
        else:
            self.logger.info(
                f"List of available training resources in language {lang} doesn't "
                f"need to be re-written."
            )

        return needs_rewrite

    def _create_file_mediawiki(self, file_info: Optional[FileInfo]) -> str:
        """
        Return string with mediawiki code to display a downloadable file

        Example: [[File:pdficon_small.png|link={{filepath:Gebet.pdf}}]]
        @return empty string if file_info is None
        """
        if file_info is None:
            return ""
        file_name: str = file_info.url
        pos: int = file_name.rfind("/")
        if pos > -1:
            file_name = file_name[pos + 1:]
        else:
            self.logger.warning(f"Couldn't find / in {file_name}")
        return (
            f" [[File:{file_info.file_type.lower()}icon_small.png|"
            + r"link={{filepath:"
            + file_name
            + r"}}]]"
        )

    def create_mediawiki(
        self, language_info: LanguageInfo, english_info: LanguageInfo
    ) -> str:
        """
        Create the mediawiki string for the list of available training resources

        Output should look like the following line:
        * [[God's_Story_(five_fingers)/de|{{int:sidebar-godsstory-fivefingers}}]] \
          [[File:pdficon_small.png|link={{filepath:Gottes_Geschichte_(fünf_Finger).pdf}}]] \
          [[File:printpdficon_small.png|link={{filepath:Gottes_Geschichte_(fünf_Finger).pdf}}]] \
          [[File:odticon_small.png|link={{filepath:Gottes_Geschichte_(fünf_Finger).odt}}]]
        """
        content: str = ""
        for worksheet, worksheet_info in language_info.worksheets.items():
            if worksheet_info.show_in_list(english_info.worksheets[worksheet]):
                content += f"* [[{worksheet}/{language_info.language_code}|"
                content += (
                    "{{int:" + self.fortraininglib.title_to_message(worksheet) + "}}]]"
                )
                content += self._create_file_mediawiki(worksheet_info.get_file_type_info("pdf"))
                content += self._create_file_mediawiki(
                    worksheet_info.get_file_type_info("printPdf")
                )
                content += self._create_file_mediawiki(
                    worksheet_info.get_file_type_info("odt")
                )
                content += "\n"
                if worksheet_info.progress.translated < worksheet_info.progress.total:
                    self.logger.warning(
                        f"Worksheet {worksheet}/{language_info.language_code} "
                        f"is not fully translated!"
                    )

        self.logger.debug(content)
        return content

    def _find_resources_list(self, page_content: str, language: str) -> Tuple[int, int]:
        """Find the exact positions of the existing list of available training
        resources in the page.
        @param page_content: mediawiki "source" of the language info page that we're
        searching through
        @param language: The language name (as in LanguageInfo.english_name)
        @return Tuple of start and end position. (0, 0) indicates we couldn't find it
        """
        language_re = language.replace(
            "(", r"\("
        )  # if language name contains brackets, we need to escape them
        language_re = language_re.replace(
            ")", r"\)"
        )  # Example would be language Turkish (secular)-
        match = re.search(
            f"Available training resources in {language_re}\\s*?</translate>\\s*?==",
            page_content,
        )
        if not match:
            return 0, 0
        list_start = 0
        list_end = 0
        # Find all following list entries: must start with *
        pattern = re.compile(r"^\*.*$", re.MULTILINE)
        for m in pattern.finditer(page_content, match.end()):
            if list_start == 0:
                list_start = m.start()
            else:
                # Make sure there is no other line in between: We only want to find
                # lines directly following each other
                if m.start() > (list_end + 1):
                    self.logger.info(
                        f"Looks like there is another list later in page {language}. "
                        f"Ignoring it."
                    )
                    break
            list_end = m.end()
            self.logger.debug(
                f"Matching line: start={m.start()}, end={m.end()}, {m.group(0)}"
            )
        return list_start, list_end

    def run(
        self,
        language_info: LanguageInfo,
        english_info: LanguageInfo,
        changes: ChangeLog,
        _english_changes,
        *,
        force_rewrite: bool = False
    ) -> LanguageReport:
        lang_report = WriteListLanguageReport(language_info.language_code)
        if not force_rewrite and not self.needs_rewrite(language_info, changes):
            return lang_report

        # Saving this to the language information page, e.g. https://www.4training.net/German
        language = language_info.english_name
        if language == "":
            self.logger.warning(
                f"English language name of {language_info.language_code} missing! "
                f"Skipping WriteList"
            )
            return lang_report
        self.logger.debug(f"Writing list of available resources in {language}...")
        page = pywikibot.Page(self._site, language)
        if not page.exists():
            self.logger.warning(f"Language information page {language} doesn't exist!")
            return lang_report
        if page.isRedirectPage():
            self.logger.info(
                f"Language information page {language} is a redirect. Following the "
                f"redirect..."
            )
            page = page.getRedirectTarget()
            if not page.exists():
                self.logger.warning(
                    f"Redirect target for language {language} doesn't exist!"
                )
                return lang_report
            language = page.title()

        list_start, list_end = self._find_resources_list(page.text, language)
        if (list_start == 0) or (list_end == 0):
            self.logger.warning(
                f"Couldn't find list of available training resources in {language}! "
                f"Doing nothing."
            )
            self.logger.info(page.text)
            return lang_report
        self.logger.debug(
            f"Found existing list of available training resources "
            f"@{list_start}-{list_end}. Replacing..."
        )
        new_page_content = page.text[0:list_start] + self.create_mediawiki(
            language_info, english_info
        )
        new_page_content += page.text[list_end + 1:]
        self.logger.debug(new_page_content)

        # Save page and mark it for translation if necessary
        if page.text.strip() == new_page_content.strip():
            return lang_report
        page.text = new_page_content
        page.save(
            "Updated list of available training resources"
        )  # TODO write list of changes here in the save message
        if self._username != "" and self._password != "":
            self.fortraininglib.mark_for_translation(
                page.title(), self._username, self._password
            )
            self.logger.info(
                f"Updated language information page {language} and marked it "
                f"for translation."
            )
            lang_report.updated_language_info = True
        else:
            self.logger.info(
                f"Updated language information page {language}. Couldn't mark it "
                f"for translation."
            )
        return lang_report


class WriteListLanguageReport(LanguageReport):
    """
    A specialized report for write_list.
    """

    def __init__(self, language_code: str):
        super().__init__(language_code)
        self.updated_language_info = False

    @classmethod
    def get_module_name(cls) -> str:
        return "write_list"

    def get_summary(self) -> str:
        if self.updated_language_info:
            return f"Updated language information page for {self.language}."
        else:
            return ""

    @classmethod
    def get_module_summary(cls, lang_reports: list) -> str:
        if len(lang_reports) == 0:
            return ""

        exported_languages = [report for report in lang_reports if report.updated_language_info]

        return (f"Updated language information page for {len(exported_languages)}/{len(lang_reports)} languages.")
