import os
import configparser
import logging
from ast import Str
from typing import Dict

from pywikitools.pywikitools.resourcesbot.data_structures import LanguageInfo
from pywikitools.resourcesbot.post_processing import LanguagePostProcessor, GlobalPostProcessor

class LanguageReport(LanguagePostProcessor):
    """
    Creates Report for each Language
    """

    def __init__(self) -> None:
        super().__init__()
        self._config = configparser.ConfigParser()
        self._config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')
        self.logger = logging.getLogger('pywikitools.resourcesbot.reports')
    
    def create_summary(self, language_info: LanguageInfo):
        """
        @param: language_info: LanguageInfo: Language code for the language we want to get a summary
        @return tuple with 2 values: number of translated worksheets, number of incomplete worksheets
        """
        number_of_translated_sheets = LanguageInfo.count_finished_translations
        number_of_incomplete_sheets = len(LanguageInfo.list_incomplete_translations)
        return number_of_translated_sheets, number_of_incomplete_sheets

    def log_languagereport(self, filename: str, text: str):
        """
        @param: filename (str): Name of the log file
        @param: text (str): Text to write into the log file
        @return: -
        """
        if self._config.has_option("Paths", "languagereports"):
            dirname = os.path.join(self._config['Paths']['languagereports'])
            os.makedirs(dirname, exist_ok=True)
            with open(os.path.join(dirname, filename), "w") as f:
                f.write(text)
        else:
            self.logger.warning(f"Option languagereports not found in section [Paths] in config.ini. Not writing {filename}.")


class GlobalReport(GlobalPostProcessor):
    """
    Creates full report for all languages
    """
    def __init__(self) -> None:
        super().__init__()

    def total_summary(language_data: Dict[str, LanguageInfo]):
        total_number_of_translated_sheets = 0
        total_number_of_incomplete_sheets = 0
        for lang in language_data:
            report = LanguageReport.create_summary(lang)
            total_number_of_translated_sheets += report[0]
            total_number_of_incomplete_sheets += report[1]

        summary = f"""Total Summary:
        - Finished worksheet translation with with PDF: {total_number_of_translated_sheets}
        - Incomplete translations: {total_number_of_incomplete_sheets}
        """
        LanguageReport.log_languagereport("summary.txt", summary)
