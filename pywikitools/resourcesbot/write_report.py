from enum import Enum
import logging
from typing import Dict, Optional
import pywikibot
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import LanguageInfo, WorksheetInfo
from pywikitools.resourcesbot.post_processing import GlobalPostProcessor


class Color(Enum):
    GREEN = "green"
    ORANGE = "orange"
    RED = "red"
    GREY = "grey"

    def __str__(self) -> str:
        return self.value


class WriteReport(GlobalPostProcessor):
    """
    Write/update status reports for all languages (for translators and translation coordinators).

    Every language report has a table with the translation status of all worksheets:
    Which worksheet is translated? Is the translation 100% complete? Is it the same version as the English original?
    Do we have ODT and PDF files for download?
    To help interpreting the results, we use colors (green / orange / red) for each cell.

    We can't implement this as a LanguagePostProcessor because we need the English LanguageInfo object
    as well to write a report for one language.
    """
    def __init__(self, site: pywikibot.site.APISite, force_rewrite: bool = False):
        """
        @param site: our pywikibot object to be able to write to the mediawiki system
        @param force_rewrite: rewrite even if there were no (relevant) changes
        """
        self._site = site
        self._force_rewrite = force_rewrite
        self.logger = logging.getLogger('pywikitools.resourcesbot.write_report')

    def run(self, language_data: Dict[str, LanguageInfo], changes: Dict[str, ChangeLog]):
        """Entry function"""
        if "en" not in language_data:
            self.logger.warning("No English language info found. Don't writing any reports.")
            return
        english_info = language_data["en"]

        for lang_code, lang_info in language_data.items():
            if self._force_rewrite or (lang_code in changes and not changes[lang_code].is_empty()):
                if lang_code == "en":   # We don't need a report for English as it is the source language
                    continue
                if "-" in lang_code and lang_code != "pt-br":   # Don't write reports for language variants
                    continue                    # (except Brazilian Portuguese) TODO this should go somewhere else
                # Language report needs to be (re-)written.
                self.save_language_report(lang_info, english_info)

    def save_language_report(self, language_info: LanguageInfo, english_info: LanguageInfo):
        """
        Saving a language report (URL e.g.: https://www.4training.net/4training:German)
        @param language_info: The language we want to write the report for
        @param english_info: We need the details of the English original worksheets as well
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
            if page.text != report:
                page.text = report
                page.save("Updated language report")    # TODO write human-readable changes here in the save message
                self.logger.info(f"Updated language report for {language_info.english_name}")

    def create_mediawiki(self, language_info: LanguageInfo, english_info: LanguageInfo) -> str:
        """Build mediawiki code for the complete report page"""
        content: str = self.create_worksheet_overview(language_info, english_info)
        content += "Check also the mediawiki [https://www.4training.net/Special:LanguageStats"
        content += f"?language={language_info.language_code}&x=D Language Statistics for {language_info.english_name}]"
        return content

    def create_worksheet_overview(self, language_info: LanguageInfo, english_info: LanguageInfo) -> str:
        """Create mediawiki code to display the whole worksheet overview table"""
        content: str = "== Worksheets ==\n"
        content += '{| class="wikitable" style="width:100%"\n'
        content += "|-\n! Worksheet\n! Translation\n! Progress\n! PDF\n! ODT\n! Version\n"
        for page, english_worksheet_info in english_info.worksheets.items():
            language_worksheet_info = language_info.worksheets[page] if page in language_info.worksheets else None
            content += self.create_worksheet_line(english_worksheet_info, language_worksheet_info)
        content += "|}\n"
        return content

    def create_worksheet_line(self, english_info: WorksheetInfo, worksheet_info: Optional[WorksheetInfo]) -> str:
        """Create mediawiki code with report for one worksheet (one line of the overview)"""
        # column 1: Link to English worksheet
        content: str = f"| [[{english_info.title}]]\n"

        # column 2: Link to translated worksheet (if existing)
        if worksheet_info is not None:
            content += f"| [[{english_info.title}/{worksheet_info.language_code}|{worksheet_info.title}]]\n"
        else:
            content += "| -\n"

        # column 7: Version information (we need to process this here because version_color is needed for other columns)
        version_color = Color.RED
        if worksheet_info is None:
            version_content = f'| style="background-color:{Color.RED}" | -\n'
        elif worksheet_info.has_same_version(english_info):
            version_color = Color.GREEN
            version_content = f'| style="background-color:{Color.GREEN}" | {english_info.version}\n'
        else:
            version_content = f'| style="background-color:{Color.RED}" '
            version_content += f"| {worksheet_info.version} (Original: {english_info.version})\n"

        # column 3: Translation progress
        translated_unit_count: int = worksheet_info.progress.translated if worksheet_info is not None else 0
        progress: int = round(translated_unit_count / english_info.progress.total * 100)
        if worksheet_info is None:
            progress_color = Color.RED
        elif progress == 100 and version_color == Color.GREEN:
            progress_color = Color.GREEN
        else:
            progress_color = Color.ORANGE
        if progress_color != Color.RED:
            content += f'| style="background-color:{progress_color}"  '
        content += f"| {progress}%\n"

        # column 4: Link to translated PDF file (if existing)
        if worksheet_info is not None and (file_info := worksheet_info.get_file_type_info("pdf")) is not None:
            pdf_color = Color.GREEN if version_color == Color.GREEN else Color.ORANGE
            if file_info.metadata is not None and not file_info.metadata.correct:
                pdf_color = Color.ORANGE
            content += f'| style="background-color:{pdf_color}" '
            content += f"| [[File:{worksheet_info.get_file_type_name('pdf')}]]\n"

            # column 5: PDF metadata details
            if file_info.metadata is not None:
                content += f'| style="background-color:{pdf_color}" | {file_info.metadata.to_html()}\n'
            else:
                content += f'| style="background-color:{Color.GREY} | ?\n'
        else:
            pdf_color = Color.RED
            content += f'| colspan="2" style="background-color:{Color.RED}; text-align:center" | -\n'

        # column 6: Link to translated ODT file (if existing)
        if worksheet_info is not None and worksheet_info.has_file_type("odt"):
            odt_color = Color.GREEN if version_color == Color.GREEN else Color.ORANGE
            content += f'| style="background-color:{odt_color}" '
            content += f"| [[File:{worksheet_info.get_file_type_name('odt')}]]\n"
        else:
            odt_color = Color.RED
            content += f'| style="background-color:{Color.RED}; text-align:center" | -\n'

        # Now we append content for column 6: version information
        content += version_content

        # Determine the line color (for the first two cells)
        line_color = Color.RED
        if version_color == Color.GREEN or progress_color != Color.RED or \
           odt_color != Color.RED or pdf_color != Color.RED:
            line_color = Color.ORANGE
        if version_color == Color.GREEN and progress_color == Color.GREEN and \
           odt_color == Color.GREEN and pdf_color == Color.GREEN:
            line_color = Color.GREEN
        content = f'|- style="background-color:{line_color}"\n' + content
        return content
