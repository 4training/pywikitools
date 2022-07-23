from collections import Counter
import logging
from typing import Dict, Final
import pywikibot
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import LanguageInfo
from pywikitools.resourcesbot.post_processing import GlobalPostProcessor


class WriteSummary(GlobalPostProcessor):
    """
    Write/update global status report with an overview over the translation progress in all languages:

    How many worksheets are finished and how many of them are outdated?
    How many translations are finished but PDFs are missing?
    How many unfinished / very outdated translations do we have?

    This is a summary of all the language reports written by WriteReport.
    It will be written to https://www.4training.net/4training:Summary - see also there for more explanations
    """
    def __init__(self, site: pywikibot.site.APISite, *, force_rewrite: bool = False):
        """
        Args:
            site: our pywikibot object to be able to write to the mediawiki system
            force_rewrite: rewrite report even if there were no (relevant) changes
        """
        self._site: Final[pywikibot.site.APISite] = site
        self._force_rewrite: Final[bool] = force_rewrite
        self.logger: Final[logging.Logger] = logging.getLogger('pywikitools.resourcesbot.write_summary')
        self.total_stats: Counter = Counter()   # Summing up statistics for all languages

    def run(self, language_data: Dict[str, LanguageInfo], changes: Dict[str, ChangeLog]):
        """Entry function"""
        has_changes = False
        for change_log in changes.values():
            if not change_log.is_empty():
                has_changes = True
        if self._force_rewrite or has_changes:
            self.save_summary(language_data)

    def save_summary(self, language_data: Dict[str, LanguageInfo]):
        """
        Saving the summary report (URL: https://www.4training.net/4training:Summary)

        Args:
            language_data: All the details for all languages
        """
        if "en" not in language_data:
            self.logger.warning("No English language info found. Can't write summary report.")
            return

        page_url = "4training:Summary"
        page = pywikibot.Page(self._site, page_url)
        report = self.create_mediawiki(language_data)
        if not page.exists():
            self.logger.warning(f"Summary report page {page_url} doesn't exist, creating...")
            page.text = report
            page.save("Created summary report")
        else:
            if page.text != report:
                page.text = report
                page.save("Updated summary report")    # TODO write human-readable changes here in the save message
                self.logger.info("Updated summary report")

    def create_mediawiki(self, language_data: Dict[str, LanguageInfo]) -> str:
        """Build mediawiki code for the complete summary page

        Additional explanations are transcluded from https://www.4training.net/Template:SummaryExplanations
        """
        content = self.create_language_overview(language_data)
        content += r"{{SummaryExplanations}}"
        return content

    def create_language_overview(self, language_data: Dict[str, LanguageInfo]) -> str:
        """Create mediawiki code to display the whole language overview table"""
        content = """__NOTOC__== Languages ==
{| class="wikitable sortable" style="width:100%; text-align:right"
|-
! colspan="2" | &nbsp;
! colspan="2" | Listed (= with PDF)
! colspan="2" | Unlisted
|-
! Language !! Code !! Up-to-date !! Outdated !! Up-to-date (= PDF missing) !! Unfinished / very outdated
"""
        content += self.create_language_line(language_data["en"], language_data["en"], "sorttop")
        self.total_stats = Counter()        # Reset our total statistics (don't count English in)

        # Sort alphabetically by language name to ensure a stable ordering in the table
        for language_info in sorted(language_data.values(), key=lambda language_info: language_info.english_name):
            if language_info.language_code == "en":   # We already had details for English in the first line
                continue
            content += self.create_language_line(language_info, language_data["en"])

        content += f"|-\n! Translations total !! {self.total_stats['languages']}"
        content += f"!! {self.total_stats['listed_uptodate']}"
        if self.total_stats['listed_uptodate_warning'] > 0:
            content += f" ({self.total_stats['listed_uptodate_warning']} ⚠)"
        content += f"!! {self.total_stats['listed_outdated']} !! {self.total_stats['unlisted_uptodate']} "
        content += f"!! {self.total_stats['unlisted_outdated']} (with PDF: {self.total_stats['unlisted_outdated_pdf']})"
        content += "\n|}\n"
        return content

    def create_language_line(self, language_info: LanguageInfo, english_info: LanguageInfo,
                             row_class: str = "") -> str:
        """Create mediawiki code with report for one language (one line of the overview)

        Args:
            row_class: CSS class to apply for the whole row (used to exclude English row from sorting)
                       See https://meta.wikimedia.org/wiki/Help:Sorting#Excluding_the_first_row_from_sorting
        """
        # Go through all worksheets to gather statistics for this language
        language_stats: Counter = Counter()
        for page, worksheet in language_info.worksheets.items():
            if worksheet.show_in_list(english_info.worksheets[page]):
                if worksheet.has_same_version(english_info.worksheets[page]):
                    language_stats["listed_uptodate"] += 1
                    pdf_info = worksheet.get_file_type_info("pdf")
                    assert pdf_info is not None     # PDF must exist because worksheet.show_in_list() was True
                    # We warn if either translation progress is < 100% or
                    # if worksheet version is different from PDF version
                    if worksheet.progress.translated < worksheet.progress.total or \
                       (pdf_info.metadata is None) or (pdf_info.metadata.version != worksheet.version):
                        language_stats["listed_uptodate_warning"] += 1
                else:
                    language_stats["listed_outdated"] += 1
            else:
                if worksheet.has_same_version(english_info.worksheets[page]):
                    language_stats["unlisted_uptodate"] += 1
                elif worksheet.has_file_type("pdf"):
                    language_stats["unlisted_outdated_pdf"] += 1
                else:
                    language_stats["unlisted_outdated"] += 1

        self.total_stats += language_stats
        self.total_stats["languages"] += 1

        # column 1: Language name
        content: str = "|-"
        if row_class != "":
            content += f' class="{row_class}"'
        content += f"\n| [[4training:{language_info.english_name}|{language_info.english_name}]] "

        # column 2: Language code
        content += f"|| {language_info.language_code} "

        # column 3: Listed, up-to-date (= with PDF)
        content += f"|| {language_stats['listed_uptodate']} "
        if language_stats['listed_uptodate_warning'] > 0:
            content += f"({language_stats['listed_uptodate_warning']} ⚠) "

        # column 4: Listed, outdated (= with PDF)
        content += f"|| {language_stats['listed_outdated']} "

        # column 5: Unlisted, up-to-date (= just PDF missing)
        content += f"|| {language_stats['unlisted_uptodate']} "

        # column 6: Unlisted, unfinished / very outdated
        content += f"|| {language_stats['unlisted_outdated']} (with PDF: {language_stats['unlisted_outdated_pdf']})\n"
        return content
