import copy
import json
import logging
import os
from configparser import ConfigParser
from typing import Any, Dict, Final, Optional, Set

import pywikibot
import requests

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.htmltools.beautify_html import BeautifyHTML
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import (
    FileInfo,
    LanguageInfo,
    WorksheetInfo,
)
from pywikitools.resourcesbot.modules.post_processing import LanguagePostProcessor
from pywikitools.resourcesbot.reporting import LanguageReport


class CustomBeautifyHTML(BeautifyHTML):
    """
    Class to collect all images used in the generated HTML files
    TODO do something about links to worksheets that are not translated yet
    """

    def __init__(self, change_hrefs: Dict[str, str], file_collector: Set[str]):
        super().__init__(img_src_base="files/", change_hrefs=change_hrefs)
        self.file_collector = file_collector

    def img_rewrite_handler(self, element):
        super().img_rewrite_handler(element)
        self.file_collector.add(element["src"][6:])  # Remove leading "files/"


def make_html_name(title: str) -> str:
    return ForTrainingLib.convert_to_filename(title) + ".html"


class ExportHTML(LanguagePostProcessor):
    """
    Export all finished worksheets of this language as HTML into a folder
    This is a step towards having a git repo with this content always up-to-date
    """
    @classmethod
    def help_summary(cls) -> str:
        return "Exports finished worksheets of a language to HTML"

    @classmethod
    def abbreviation(cls) -> str:
        return "html"

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
        self._base_folder: str = self._config.get("Paths", "htmlexport", fallback="")
        self.logger: Final[logging.Logger] = logging.getLogger(
            "pywikitools.resourcesbot.modules.export_html"
        )
        if self._base_folder != "":
            try:
                os.makedirs(self._base_folder, exist_ok=True)
            except OSError as err:
                self.logger.warning(
                    f"Error creating directories for HTML export: {err}. "
                    f"Won't export HTML files."
                )
                self._base_folder = ""
        else:
            self.logger.warning(
                "Missing htmlexport path in config.ini. Won't export HTML files."
            )

    def has_relevant_change(self, worksheet: str, changes: ChangeLog) -> bool:
        """
        Is there a relevant change for worksheet?
        TODO: Define what exactly we consider relevant
            (for re-generating that worksheet's HTML)
        """
        for change_item in changes:
            if change_item.worksheet == worksheet:
                # TODO check change_item.change_type
                return True
        return False

    def download_file(self, files_folder: str, filename: str) -> bool:
        """Download a file from the mediawiki server

        If a file already exists locally, we don't download it again because
        usually those files (graphics) don't change.
        TODO: Implement a way to force re-downloading of files
            (in case a file was updated in the mediawiki system).
        Two possible ways:
        - an extra flag (e.g. --force-rewrite-files)
        - by getting the time stamp of the file in the mediawiki system,
            comparing it with the last
        modified timestamp of the local file and download again if the first is newer
        (would require adjustments of get_file_url() to also request timestamp)

        @return True if we actually downloaded the file, False if not
        """
        file_path = os.path.join(files_folder, filename)
        if os.path.isfile(file_path):
            self.logger.info(
                f"File {file_path} already exists locally, not downloading."
            )
            return False
        else:
            url = self.fortraininglib.get_file_url(filename)
            if url is None:
                self.logger.error(f"Could not get URL of file {filename}, skipping.")
                return False

            response = requests.get(url, allow_redirects=True)
            with open(file_path, "wb") as fh:
                fh.write(response.content)
            self.logger.info(f"Successfully downloaded and saved {file_path}")
            return True

    def run(
        self,
        language_info: LanguageInfo,
        english_info: LanguageInfo,
        changes: ChangeLog,
        _english_changes,
        *,
        force_rewrite: bool = False
    ):
        if self._base_folder == "":
            return
        # Remove worksheets that aren't finished - don't change the
        # language_info object we got
        lang_info: LanguageInfo = copy.deepcopy(language_info)
        del language_info  # prevent accidental usage of the wrong object
        for worksheet in list(lang_info.worksheets.keys()):
            if not lang_info.worksheets[worksheet].show_in_list(
                english_info.worksheets[worksheet]
            ):
                del lang_info.worksheets[worksheet]

        lang_code = lang_info.language_code
        folder: str = os.path.join(self._base_folder, lang_code)
        files_folder: str = os.path.join(folder, "files/")
        structure_folder: str = os.path.join(folder, "structure/")
        # Make sure all the folders exist and are ready to be used
        try:
            os.makedirs(folder, exist_ok=True)
            if not os.path.isdir(files_folder):
                os.makedirs(files_folder)
            if not os.path.isdir(structure_folder):
                os.makedirs(structure_folder)
        except OSError as err:
            self.logger.warning(
                f"Error creating directories for HTML export: {err}. "
                f"Won't export HTML files for language {lang_code}."
            )
            return

        change_hrefs: Dict[str, str] = (
            {}
        )  # Dictionary to set correct targets for links in the HTML files
        for worksheet, info in lang_info.worksheets.items():
            # Most links can stay the same, but we need to add them to change_hrefs;
            # otherwise links are removed
            change_hrefs[f"/{worksheet}/{lang_code}"] = f"/{worksheet}/{lang_code}"
            if lang_code == "en":  # English links normally don't have /en at the end
                change_hrefs[f"/{worksheet}"] = f"/{worksheet}/en"

        file_collector: Set[str] = set()
        beautifyhtml = CustomBeautifyHTML(
            change_hrefs=change_hrefs, file_collector=file_collector
        )

        html_counter: int = 0  # Counting exported HTML files
        file_counter: int = 0  # Counting downloaded files (images)

        # Download all worksheets and save the transformed HTML
        for worksheet, info in lang_info.worksheets.items():
            # As elsewhere, we ignore outdated / unfinished translations
            if force_rewrite or self.has_relevant_change(worksheet, changes):
                content = self.fortraininglib.get_page_html(f"{worksheet}/{lang_code}")
                if content is None:
                    self.logger.warning(
                        f"Couldn't get content of {worksheet}/{lang_code}. Skipping"
                    )
                    continue
                html_counter += 1
                filename = make_html_name(info.title)
                with open(os.path.join(folder, filename), "w") as f:
                    self.logger.info(f"Exporting HTML to {filename}")
                    content = f"<h1>{info.title}</h1>" + beautifyhtml.process_html(
                        content
                    )
                    f.write(content)

        # Download all images we came across in the previous step
        for file in file_collector:
            if self.download_file(files_folder, file):
                file_counter += 1

        # Write contents.json
        # TODO define specifications for contents.json
        #   (similar to language jsons?) - for now just a simple structure
        if force_rewrite or html_counter > 0:
            encoded_json = StructureEncoder().encode(lang_info)
            pretty_printed_json = json.dumps(json.loads(encoded_json), indent=4)
            with open(os.path.join(structure_folder, "contents.json"), "w") as f:
                self.logger.info("Exporting contents.json")
                f.write(pretty_printed_json)

        self.logger.info(
            f"ExportHTML {lang_code}: "
            f"Downloaded {html_counter} HTML files, {file_counter} images"
        )
        lang_report = HtmlLanguageReport(lang_code, html_counter, file_counter)
        return lang_report


class StructureEncoder(json.JSONEncoder):
    """
    Serializes all information needed for the app into a JSON string.
    This is similar to DataStructureEncoder but removes some stuff we don't need
    """

    def default(self, o):
        if isinstance(o, LanguageInfo):
            # Don't include unfinished / outdated worksheets
            return {
                "language_code": o.language_code,
                "english_name": o.english_name,
                "worksheets": list(o.worksheets.values()),
            }
        if isinstance(o, WorksheetInfo):
            worksheet_json: Dict[str, Any] = {
                "page": o.page,
                "title": o.title,
                "filename": make_html_name(o.title),
                "version": o.version,
            }
            pdf_info: Optional[FileInfo] = o.get_file_type_info("pdf")
            if pdf_info:
                pos: int = pdf_info.url.rfind("/")
                if pos > -1:
                    worksheet_json["pdf"] = pdf_info.url[pos + 1:]
            return worksheet_json
        return super().default(o)


class HtmlLanguageReport(LanguageReport):
    """
    A specialized report for export_html,
    containing information about saved htmls and images
    """

    def __init__(self, language_code: str, html_counter: int, image_counter: int):
        super().__init__(language_code)

        self.html_counter = html_counter
        self.image_counter = image_counter

    def get_html_number(self) -> int:
        """
        Returns the number of HTML elements processed.
        """
        return self.html_counter

    def get_image_number(self) -> int:
        """
        Returns the number of images downloaded.
        """
        return self.image_counter

    def get_summary(self) -> str:
        if self.html_counter + self.image_counter == 0:
            return ""
        return (f"Ran ExportHTML for {self.language}: "
                f"Processed {self.html_counter} htmls, downloaded {self.image_counter} images.")

    @classmethod
    def get_module_name(cls) -> str:
        return "export_html"

    @classmethod
    def get_module_summary(cls, lang_reports: list) -> str:
        if len(lang_reports) == 0:
            return ""

        total_htmls = sum(report.get_html_number() for report in lang_reports)
        total_images = sum(report.get_image_number() for report in lang_reports)
        if total_htmls + total_images == 0:
            return ""
        return (f"Ran export_html for {len(lang_reports)} languages, "
                f"processed {total_htmls} htmls, downloaded {total_images} images.")
