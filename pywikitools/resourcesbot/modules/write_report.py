from enum import Enum
import logging
import re
from typing import Final, Optional
import pywikibot
from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import LanguageInfo, WorksheetInfo
from pywikitools.resourcesbot.modules.post_processing import LanguagePostProcessor


class Color(Enum):
    GREEN = "green"
    ORANGE = "orange"
    RED = "red"
    GREY = "grey"

    def __str__(self) -> str:
        return self.value


class WriteReport(LanguagePostProcessor):
    """
    Write/update status reports for all languages (for translators and translation coordinators).

    Every language report has a table with the translation status of all worksheets:
    Which worksheet is translated? Is the translation 100% complete? Is it the same version as the English original?
    Do we have ODT and PDF files for download?
    To help interpreting the results, we use colors (green / orange / red) for each cell.
    """

    def __init__(
        self,
        fortraininglib: ForTrainingLib,
        config: ConfigParser,
        site: pywikibot.site.APISite,
        *,
        force_rewrite: bool = False,
    ):
        """
        Args:
            site: our pywikibot object to be able to write to the mediawiki system
            force_rewrite: is ignored as we need to check CorrectBot reports anyway
        """
        super().__init__(fortraininglib,config, site, force_rewrite=force_rewrite)
        self.logger: Final[logging.Logger] = logging.getLogger(
            "pywikitools.resourcesbot.modules.write_report"
        )

    def run(self, language_info: LanguageInfo, english_info: LanguageInfo,
            changes: ChangeLog, english_changes: ChangeLog):
        """Entry function

        We run everything and don't look whether we have changes because we need to look at all CorrectBot reports
        and according to them may need to rewrite the report even if changes and english_changes are empty
        """
        if language_info.language_code == "en":   # We don't need a report for English as it is the source language
            return
        if "-" in language_info.language_code and language_info.language_code != "pt-br":
            # Don't write reports for language variants
            # (except Brazilian Portuguese) TODO this should go somewhere else
            return
        self.save_language_report(language_info, english_info)

    def create_correctbot_mediawiki(self, worksheet: str, language_code: str) -> str:
        """Check Correctbot report status for one worksheet

        Returns:
            mediawiki string to fill one cell (for one worksheet in the CorrectBot column)
        """
        page = f"{worksheet}/{language_code}"
        worksheet_page = pywikibot.Page(self._site, page)
        if not worksheet_page.exists():
            self.logger.warning(f"Couldn't access page {page}")
            return f'| style="background-color:{Color.RED}" | ERROR\n'

        correctbot_page = pywikibot.Page(self._site, f"CorrectBot:{page}")
        if not correctbot_page.exists():
            return f'| style="background-color:{Color.RED}" | Missing\n'

        # Analyze the result of the last CorrectBot run (from edit summary)
        correctbot_summary = correctbot_page.latest_revision["comment"]
        match = re.match(r"^(\d+) corrections, (\d+) suggestions, (\d+) warnings$", correctbot_summary)
        if not match:
            # Somehow the edit summary is not as we expect it
            self.logger.warning(f"Couldn't parse edit summary '{correctbot_summary}' in page CorrectBot:{page}")
            return f'| style="background-color:{Color.RED}" | Invalid. Please run CorrectBot again.\n'

        if int(match.group(3)) > 0:
            # CorrectBot gave warnings - something is definitely not okay
            return f'| style="background-color:{Color.RED}" | [[CorrectBot:{page}|{match.group(3)} warnings]]\n'

        report_link = f'[[CorrectBot:{page}|{match.group(1)} corrections, {match.group(2)} suggestions]]'
        if correctbot_page.editTime() > worksheet_page.editTime():
            # Perfect: CorrectBot report is newer than latest change on the worksheet page
            return f'| style="background-color:{Color.GREEN}" | {report_link}\n'

        # we don't know if still everything is okay or whether there were problems introduced since the
        # last time CorrectBot ran, so we suggest to re-run CorrectBot
        return f'| style="background-color:{Color.ORANGE}" | ' \
               f'<span title="Possibly outdated: please run CorrectBot again">⚠</span> {report_link}\n'

    def save_language_report(self, language_info: LanguageInfo, english_info: LanguageInfo):
        """
        Create language report and save it if it's different from the previous report

        Example: https://www.4training.net/4training:German
        Args:
            language_info: The language we want to write the report for
            english_info: We need the details of the English original worksheets as well
        """
        if language_info.english_name == "":
            self.logger.warning(f"English name of language {language_info.language_code} empty! Skipping WriteReport")
            return
        page_url = f"4training:{language_info.english_name}"
        page = pywikibot.Page(self._site, page_url)
        report = self.create_mediawiki(language_info, english_info)
        if not page.exists():
            self.logger.warning(f"Language report page {page_url} doesn't exist, creating...")
            page.text = report
            page.save("Created language report")
        else:
            if page.text.strip() != report.strip():
                page.text = report
                page.save("Updated language report")    # TODO write human-readable changes here in the save message
                self.logger.info(f"Updated language report for {language_info.english_name}")

    def create_mediawiki(self, language_info: LanguageInfo, english_info: LanguageInfo) -> str:
        """Build mediawiki code for the complete report page"""
        content: str = "__NOEDITSECTION__"
        content += self.create_worksheet_overview(language_info, english_info)
        content += "Check also the mediawiki [https://www.4training.net/Special:LanguageStats"
        content += f"?language={language_info.language_code}&x=D Language Statistics for {language_info.english_name}]"
        return content

    def create_worksheet_overview(self, language_info: LanguageInfo, english_info: LanguageInfo) -> str:
        """Create mediawiki code to display the whole worksheet overview table

        Args:
            language_info: all information on the language we're writing this report for
            english_info: LanguageInfo for English - needed because we need English WorksheetInfos
        Returns:
            string with mediawiki code for a whole paragraph with the complete table
        """
        content: str = "== Worksheets ==\n"
        content += '{| class="wikitable" style="width:100%"\n|-\n'
        content += f"! [[{language_info.english_name}#Available_training_resources_in_{language_info.english_name}|"
        content += "Listed?]]\n! Worksheet\n! Translation\n! Progress\n! colspan=\"2\" | PDF\n! ODT\n! Version\n"
        content += "! CorrectBot\n"
        for page, en_worksheet in english_info.worksheets.items():
            lang_worksheet = language_info.worksheets[page] if page in language_info.worksheets else None
            content += self.create_worksheet_line(language_info.language_code, en_worksheet, lang_worksheet)
        content += "|}\n"
        return content

    def _note(self, en_worksheet: WorksheetInfo) -> str:
        """Helper function to add a quick note for certain worksheets

        Currently we only use this for the Bible Reading Hints (by including a template)
        Returns:
            string with mediawiki code or an empty string (for all other worksheets)
        """
        if en_worksheet.title == "Bible Reading Hints":
            return " {{4training:ReportNote-BibleReadingHints}}"
        return ""

    def create_worksheet_line(self, language_code: str,
                              en_worksheet: WorksheetInfo, lang_worksheet: Optional[WorksheetInfo]) -> str:
        """Create mediawiki code with report for one worksheet (one line of the overview)

        Args:
            language_code: Which language we're writing this report line for
                           (we can't use worksheet_info.language_code because worksheet_info may be None)
            en_worksheet: WorksheetInfo for the English original
            lang_worksheet: WorksheetInfo for the translation if it exists, otherwise None
        Returns:
            string with mediawiki code for one line of our table
        """
        # column 1: Is this worksheet listed in the language overview page?
        if lang_worksheet is not None and lang_worksheet.show_in_list(en_worksheet):
            content = "| style=\"text-align:center\" | ✓\n"
        else:
            content = "| style=\"text-align:center\" | -\n"

        # column 2: Link to English worksheet
        content += f"| [[{en_worksheet.title}]]\n"

        # column 3: Link to translated worksheet (if existing)
        if lang_worksheet is not None:
            content += f"| [[{en_worksheet.title}/{language_code}|{lang_worksheet.title}]]{self._note(en_worksheet)}\n"
        else:
            content += "| -\n"

        # column 8: Version information (we need to process this here because version_color is needed for other columns)
        version_color = Color.RED
        if lang_worksheet is None:
            version_content = f'| style="background-color:{Color.RED}" | -\n'
        elif lang_worksheet.has_same_version(en_worksheet):
            version_color = Color.GREEN
            version_content = f'| style="background-color:{Color.GREEN}" | {en_worksheet.version}\n'
        else:
            version_content = f'| style="background-color:{Color.RED}" '
            version_content += f"| {lang_worksheet.version} (Original: {en_worksheet.version})\n"

        # column 4: Translation progress
        translated_unit_count: int = lang_worksheet.progress.translated if lang_worksheet is not None else 0
        progress: int = round(translated_unit_count / en_worksheet.progress.total * 100)
        if lang_worksheet is None:
            progress_color = Color.RED
        elif progress == 100 and version_color == Color.GREEN:
            progress_color = Color.GREEN
        elif lang_worksheet.show_in_list(en_worksheet) and progress < 100:
            # This produces a warning in the line for this language in WriteSummary, so make it red
            progress_color = Color.RED
        else:
            progress_color = Color.ORANGE

        # in case the worksheet doesn't exist, the whole line will be red
        color_css = f";background-color:{progress_color}" if lang_worksheet is not None else ""
        content += f'| style="text-align:right{color_css}" '
        # Add link to translation view, showing either untranslated units (progress < 100%) or translated units
        content += f"| [{self.fortraininglib.index_url}?title=Special:Translate&group=page-{en_worksheet.page}"
        content += f"&action=page&filter={'' if progress == 100 else '!'}translated"
        content += f"&language={language_code} {progress}%]\n"

        # column 5: Link to translated PDF file (if existing)
        if lang_worksheet is not None and (file_info := lang_worksheet.get_file_type_info("pdf")) is not None:
            pdf_color = Color.GREEN if version_color == Color.GREEN else Color.ORANGE
            if file_info.metadata is not None and not file_info.metadata.correct:
                pdf_color = Color.ORANGE
                if file_info.metadata.version != lang_worksheet.version:
                    # TODO: Is this the right place to log this warning?
                    self.logger.warning(f"{lang_worksheet.page}/{lang_worksheet.language_code} has version "
                                        f"{lang_worksheet.version} but PDF has version {file_info.metadata.version}!")
                    pdf_color = Color.RED
            content += f'| style="background-color:{pdf_color}" '
            content += f"| [[File:{lang_worksheet.get_file_type_name('pdf')}]]\n"

            # column 6: PDF metadata details
            if file_info.metadata is not None:
                content += f'| style="background-color:{pdf_color}" | {file_info.metadata.to_html()}\n'
            else:
                content += f'| style="background-color:{Color.GREY} | ?\n'
        else:
            pdf_color = Color.RED
            content += f'| colspan="2" style="background-color:{Color.RED}; text-align:center" | -\n'

        # column 7: Link to translated ODT/ODG file (if existing)
        if lang_worksheet is not None and (lang_worksheet.has_file_type("odt") or lang_worksheet.has_file_type("odg")):
            od_color = Color.GREEN if version_color == Color.GREEN else Color.ORANGE
            content += f'| style="background-color:{od_color}" '
            od_file = lang_worksheet.get_file_type_name('odt')
            if od_file == "":
                od_file = lang_worksheet.get_file_type_name('odg')
            content += f"| [[File:{od_file}]]\n"
        else:
            od_color = Color.RED
            content += f'| style="background-color:{Color.RED}; text-align:center" | -\n'

        # Now we append content for column 7: version information
        content += version_content

        # column 9: CorrectBot status (do we have an up-to-date report?)
        if lang_worksheet is not None:
            content += self.create_correctbot_mediawiki(lang_worksheet.page, lang_worksheet.language_code)
        else:
            content += "| -\n"

        # Determine the line color (for the first two cells)
        line_color = Color.RED
        if version_color == Color.GREEN or progress_color != Color.RED or \
           od_color != Color.RED or pdf_color != Color.RED:
            line_color = Color.ORANGE
        if version_color == Color.GREEN and progress_color == Color.GREEN and \
           od_color == Color.GREEN and pdf_color == Color.GREEN:
            line_color = Color.GREEN
        content = f'|- style="background-color:{line_color}"\n' + content
        return content
