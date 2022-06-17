import json
import logging
import os
import re
import requests
from typing import Dict, Set

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.htmltools.beautify_html import BeautifyHTML
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import LanguageInfo
from pywikitools.resourcesbot.post_processing import LanguagePostProcessor


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
        self.file_collector.add(element['src'][6:])     # Remove leading "files/"


class ExportHTML(LanguagePostProcessor):
    """
    Export all finished worksheets of this language as HTML into a folder
    This is a step towards having a git repo with this content always up-to-date
    """
    def __init__(self, fortraininglib: ForTrainingLib, folder: str, force_rewrite: bool = False):
        """
        @param folder: base directory for export; subdirectories will be created for each language
        @param force_rewrite: rewrite even if there were no (relevant) changes
        """
        self._base_folder: str = folder
        self._force_rewrite: bool = force_rewrite
        self.fortraininglib = fortraininglib
        self.logger = logging.getLogger('pywikitools.resourcesbot.export_html')
        if self._base_folder != "":
            try:
                os.makedirs(folder, exist_ok=True)
            except OSError as err:
                self.logger.warning(f"Error creating directories for HTML export: {err}. Won't export HTML files.")
                self._base_folder = ""
        else:
            self.logger.warning("Missing htmlexport path in config.ini. Won't export HTML files.")

    def has_relevant_change(self, worksheet: str, change_log: ChangeLog):
        """
        Is there a relevant change for worksheet?
        TODO: Define what exactly we consider relevant (for re-generating that worksheet's HTML)
        """
        for change_item in change_log:
            if change_item.worksheet == worksheet:
                # TODO check change_item.change_type
                return True
        return False

    def make_html_name(self, title: str) -> str:
        # TODO copied from TranslateODT._get_odt_filename() - move this to a central place to use it in both places?
        filename: str = re.sub(" ", '_', title)
        filename = re.sub("[':]", "", filename)
        filename += ".html"
        return filename

    def download_file(self, files_folder: str, filename: str) -> bool:
        """Download a file from the mediawiki server

        If a file already exists locally, we don't download it again because usually those
        files (graphics) don't change.
        TODO: Implement a way to force re-downloading of files (in case a file was updated in the mediawiki system).
        Two possible ways:
        - an extra flag (e.g. --force-rewrite-files)
        - by getting the time stamp of the file in the mediawiki system, comparing it with the last
        modified timestamp of the local file and download again if the first is newer
        (would require adjustments of get_file_url() to also request timestamp)

        @return True if we actually downloaded the file, False if not
        """
        file_path = os.path.join(files_folder, filename)
        if os.path.isfile(file_path):
            self.logger.info(f"File {file_path} already exists locally, not downloading.")
        else:
            url = self.fortraininglib.get_file_url(filename)
            if url is None:
                self.logger.error(f"Could not get URL of file {filename}, skipping.")
                return False

            response = requests.get(url, allow_redirects=True)
            with open(file_path, 'wb') as fh:
                fh.write(response.content)
            self.logger.info(f"Successfully downloaded and saved {file_path}")
            return True

    def run(self, language_info: LanguageInfo, english_info: LanguageInfo, change_log: ChangeLog):
        if self._base_folder == "":
            return
        folder: str = os.path.join(self._base_folder, language_info.language_code)
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
            self.logger.warning(f"Error creating directories for HTML export: {err}. "
                                f"Won't export HTML files for language {language_info.language_code}.")
            return

        change_hrefs: Dict[str, str] = {}   # Dictionary to set correct targets for links in the HTML files
        for worksheet, info in language_info.worksheets.items():
            change_hrefs[f"/{worksheet}/{language_info.language_code}"] = self.make_html_name(info.title)
        file_collector: Set[str] = set()
        beautifyhtml = CustomBeautifyHTML(change_hrefs=change_hrefs, file_collector=file_collector)

        html_counter: int = 0   # Counting exported HTML files
        file_counter: int = 0   # Counting downloaded files (images)

        # Download all worksheets and save the transformed HTML
        for worksheet, info in language_info.worksheets.items():
            # As elsewhere, we ignore unfinished worksheets and worksheets without PDF
            if info.progress.is_unfinished() or not info.has_file_type("pdf"):
                continue
            if self._force_rewrite or self.has_relevant_change(worksheet, change_log):
                content = self.fortraininglib.get_page_html(f"{worksheet}/{language_info.language_code}")
                if content is None:
                    self.logger.warning(f"Couldn't get content of {worksheet}/{language_info.language_code}. Skipping")
                    continue
                html_counter += 1
                filename = self.make_html_name(info.title)
                with open(os.path.join(folder, filename), "w") as f:
                    self.logger.info(f"Exporting HTML to {filename}")
                    content = f"<h1>{info.title}</h1>" + beautifyhtml.process_html(content)
                    f.write(content)

        # Download all images we came across in the previous step
        for file in file_collector:
            if self.download_file(files_folder, file):
                file_counter += 1

        # Write contents.json
        # TODO define specifications for contents.json (similar to language jsons?) - for now just a simple structure
        if self._force_rewrite or html_counter > 0:
            structure = []
            for worksheet, info in language_info.worksheets.items():
                structure.append({worksheet: self.make_html_name(info.title)})
            with open(os.path.join(structure_folder, "contents.json"), "w") as f:
                self.logger.info("Exporting contents.json")
                f.write(json.dumps(structure))

        self.logger.info(f"ExportHTML {language_info.language_code}: "
                         f"Downloaded {html_counter} HTML files, {file_counter} images")
