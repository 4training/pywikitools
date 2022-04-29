#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Bot that replaces common typos for different languages.

All correction rules for different languages are in the correctors/ folder in separate classes.

Run with dummy page:
    python3 correct_bot.py Test de
    python3 correct_bot.py CorrectTestpage fr

TODO: Not yet operational
"""

import argparse
from collections import Counter, defaultdict
import logging
import importlib
import re
import sys
from typing import Callable, DefaultDict, List, Optional

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.correctbot.correctors.base import CorrectionResult, CorrectorBase
from pywikitools.lang.translated_page import TranslatedPage, TranslationUnit

class CorrectBot:
    """Main class for doing corrections"""
    def __init__(self, fortraininglib: ForTrainingLib, simulate: bool = False):
        self.fortraininglib: ForTrainingLib = fortraininglib
        self.logger: logging.Logger = logging.getLogger("pywikitools.correctbot")
        self._simulate: bool = simulate
        self._diff: str = ""
        self._stats: Optional[str] = None
        self._correction_counter: int = 0

    def _load_corrector(self, language_code: str) -> Callable:
        """Load the corrector class for the specified language and return it.

        Raises ImportError if corrector class can't be found"""
        # Dynamically load e.g. correctors/de.py
        module_name = f"correctors.{language_code}"
        module = importlib.import_module(module_name, ".")
        # There should be exactly one class named "XYCorrector" in there - let's get it
        for class_name in dir(module):
            if "Corrector" in class_name:
                corrector_class = getattr(module, class_name)
                # Filter out CorrectorBase (in module correctors.base) and classes from correctors.universal
                if corrector_class.__module__ == module_name:
                    return corrector_class

        raise ImportError(f"Couldn't load corrector for language {language_code}. Giving up")

    def check_unit(self, corrector: CorrectorBase, unit: TranslationUnit) -> Optional[CorrectionResult]:
        """
        Check one specific translation unit: Run the right correction rules on it.
        For this we analyze: Is it a title, a file name or a "normal" translation unit?
        """
        if unit.get_translation() == "":
            return None
        if unit.is_title():
            # translation unit holds the title
            return corrector.title_correct(unit)
        if re.search(r"\.(odt|pdf|odg)$", unit.get_definition()):
            # translation unit holds a filename
            return corrector.filename_correct(unit)
        if re.search(r"^\d\.\d[a-zA-Z]?$", unit.get_definition()):
            # translation unit holds the version number -> ignore it
            return None

        return corrector.correct(unit)

    def check_page(self, page: str, language_code: str) -> bool:
        """
        Check one specific page and store the results in this class

        This does not write anything back to the server. Changes can be read with
        get_stats(), get_correction_counter() and get_diff()
        @returns True on success, False if an error occurred
        """
        self._diff = ""
        self._stats = None
        self._correction_counter = 0
        correction_stats: Counter = Counter()
        translated_page: Optional[TranslatedPage] = self.fortraininglib.get_translation_units(page, language_code)
        if translated_page is None:
            return False
        corrector = self._load_corrector(language_code)()
        for translation_unit in translated_page:
            result = self.check_unit(corrector, translation_unit)
            if result is None:
                continue
            if result.warnings != "":
                self.logger.warning(result.warnings)
            if (diff := result.corrections.get_translation_diff()) != "":
                self._diff += f"{translation_unit.get_name()}: {diff}\n"
            correction_stats += Counter(result.correction_stats)
            # TODO Handle suggestions as well
        self._stats = corrector.print_stats(correction_stats)
        self._correction_counter = sum(correction_stats.values())
        return True

    def get_stats(self) -> str:
        """Return a summary: which correction rules could be applied (in the last run)?"""
        if self._stats is None:
            self.logger.warning("No statistics available. You need to run check_page() first.")
            return ""
        return self._stats

    def get_correction_counter(self) -> int:
        """How many corrections did we do (in the last run)?"""
        return self._correction_counter

    def get_diff(self) -> str:
        """Print a diff of the corrections (made in the last run)"""
        return self._diff

    def run(self, page: str, language_code: str):
        """
        Correct the translation of a page.
        TODO write it back to the system if we're not in simulation mode
        """
        self.check_page(page, language_code)
        print(self.get_diff())
        print(self.get_stats())

        # TODO save changes back to mediawiki system


def parse_arguments() -> argparse.Namespace:
    """Parses the arguments given from outside"""
    log_levels: List[str] = ['debug', 'info', 'warning', 'error']

    parser = argparse.ArgumentParser()
    parser.add_argument("page", help="Name of the mediawiki page")
    parser.add_argument("language_code", help="Language code")
    parser.add_argument("-s", "--simulate", type=bool, default=False, required=False,
                        help="Simulates the corrections but does not apply them to the webpage.")
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

    # TODO read mediawiki baseurl from config.ini
    correctbot = CorrectBot(ForTrainingLib("https://www.4training.net"), args.simulate)
    correctbot.run(args.page, args.language_code)
