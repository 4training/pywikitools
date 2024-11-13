import copy
import logging
import os
import requests
from typing import Final, Optional

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.data_structures import FileInfo, LanguageInfo
from pywikitools.resourcesbot.modules.post_processing import LanguagePostProcessor


class ExportPDF(LanguagePostProcessor):
    """
    Export all PDF files of this language into a folder
    This is a step towards having a git repo with this content always up-to-date
    """
    def __init__(self, fortraininglib: ForTrainingLib, folder: str, *, force_rewrite: bool = False):
        """
        Args:
            folder: base directory for export; subdirectories will be created for each language
            force_rewrite: rewrite even if there were no (relevant) changes
        """
        self._base_folder: str = folder
        self._force_rewrite: Final[bool] = force_rewrite
        self.fortraininglib: Final[ForTrainingLib] = fortraininglib
        self.logger: Final[logging.Logger] = logging.getLogger(
            'pywikitools.resourcesbot.modules.export_pdf'
        )
        if self._base_folder != "":
            try:
                os.makedirs(folder, exist_ok=True)
            except OSError as err:
                self.logger.warning(f"Error creating directories for PDF export: {err}. Won't export PDF files.")
                self._base_folder = ""
        else:
            self.logger.warning("Missing pdfexport path in config.ini. Won't export PDF files.")

    def has_relevant_change(self, worksheet: str, changes: ChangeLog) -> bool:
        """
        Is there a relevant change for the given worksheet?
        TODO: Define what exactly we consider relevant: UPDATED_PDF, NEW_PDF
        TODO: How do we handle DELETED_PDF?
        """
        for change_item in changes:
            if change_item.worksheet == worksheet:
                # TODO check change_item.change_type
                return True
        return False

    def run(self, language_info: LanguageInfo, english_info: LanguageInfo, changes: ChangeLog, _english_changes):
        if self._base_folder == "":
            return
        # Remove worksheets that aren't finished - don't change the language_info object we got
        lang_info: LanguageInfo = copy.deepcopy(language_info)
        del language_info   # prevent accidental usage of the wrong object
        for worksheet in list(lang_info.worksheets.keys()):
            if not lang_info.worksheets[worksheet].show_in_list(english_info.worksheets[worksheet]):
                del lang_info.worksheets[worksheet]

        lang_code = lang_info.language_code
        folder: str = os.path.join(self._base_folder, lang_code)
        # Make sure all the folders exist and are ready to be used
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError as err:
            self.logger.warning(f"Error creating directories for PDF export: {err}. "
                                f"Won't export PDF files for language {lang_code}.")
            return

        file_counter: int = 0   # Counting downloaded PDF files

        # Download and save all PDF files
        for worksheet, info in lang_info.worksheets.items():
            pdf_info: Optional[FileInfo] = info.get_file_type_info('pdf')
            if pdf_info is None:
                continue
            # As elsewhere, we ignore outdated / unfinished translations
            if self._force_rewrite or self.has_relevant_change(worksheet, changes):
                response = requests.get(pdf_info.url, allow_redirects=True)
                file_path = os.path.join(folder, pdf_info.get_file_name())
                with open(file_path, 'wb') as fh:
                    fh.write(response.content)
                file_counter += 1
                self.logger.info(f"Successfully downloaded and saved {file_path}")

        self.logger.info(f"ExportPDF {lang_code}: Downloaded {file_counter} PDF files")
