"""
Run translateodt on all worksheets from one language (but without invoking LibreOffice)
python3 check_translateodt.py language_code
"""

import argparse
import logging
import sys
from typing import List
from unittest.mock import Mock

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.libreoffice import LibreOffice
from pywikitools.translateodt import TranslateODT


class DummyLibreOffice(LibreOffice):
    """Inherited class to produce a dummy LibreOffice that doesn't do anything
    TODO: Currently unused. Is their any benefit in this approach over just using a Mock()?
    """
    def __init__(self, headless: bool = False):
        super().__init__(headless)

    def open_file(self, file_name: str):
        self.logger.debug(f"DummyLibreOffice.open_file({file_name})")

    def search_and_replace(self, search: str, replace: str,
                           warn_if_pages_change: bool = False, parse_formatting: bool = False) -> bool:
        self.logger.debug("DummyLibreOffice.search_and_replace()")
        return True

    def save_odt(self, file_name: str):
        self.logger.debug("DummyLibreOffice.save_odt()")

    def export_pdf(self, file_name: str):
        self.logger.debug(f"DummyLibreOffice.export_pdf({file_name})")

    def close(self):
        self.logger.debug("DummyLibreOffice.close()")

    def get_properties_subject(self) -> str:
        self.logger.debug("DummyLibreOffice.get_properties_subject()")
        return ""

    def set_properties(self, title: str, subject: str, keywords: str):
        self.logger.debug("DummyLibreOffice.set_properties()")

    def set_default_styles(self, language_code: str, rtl: bool = False):
        self.logger.debug("DummyLibreOffice.set_default_style()")


class DummyTranslateODT(TranslateODT):
    def __init__(self):
        super().__init__(keep_english_file=True)
        # self._loffice = DummyLibreOffice(headless=False)
        self._loffice = Mock()
        self._loffice.search_and_replace.return_value = True

    def _fetch_english_file(self, odt_file: str) -> str:
        self.logger.debug(f"DummyTranslateODT._fetch_english_file({odt_file})")
        return odt_file


def parse_arguments() -> argparse.Namespace:
    """
    Parses the arguments given from outside

    Returns:
        argparse.Namespace: parsed arguments
    """
    log_levels: List[str] = ['debug', 'info', 'warning', 'error']

    parser = argparse.ArgumentParser()
    parser.add_argument("language_code", help="Language code")
    parser.add_argument("-l", "--loglevel", choices=log_levels, default="warning", help="set loglevel for the script")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    fformatter = logging.Formatter('%(levelname)s: %(message)s')
    sh.setFormatter(fformatter)
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    assert isinstance(numeric_level, int)
    sh.setLevel(numeric_level)
    root.addHandler(sh)

    fortraininglib = ForTrainingLib("https://www.4training.net")
    translate_odt = DummyTranslateODT()
#    translate_odt = TranslateODT(keep_english_file=False)    # uncomment this to invoke LibreOffice for each worksheet
    for worksheet in fortraininglib.get_worksheet_list():
        translate_odt.translate_worksheet(worksheet, args.language_code)
