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
import logging
import importlib
import sys
from typing import Callable, List, Optional

from pywikitools import fortraininglib
from pywikitools.lang.translated_page import TranslatedPage

class CorrectBot:
    """Main class for doing corrections"""
    def __init__(self, simulate: bool = False):
        self.logger = logging.getLogger("pywikitools.correctbot")
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
        translated_page: Optional[TranslatedPage] = fortraininglib.get_translation_units(page, language_code)
        if translated_page is None:
            return False
        corrector = self._load_corrector(language_code)()
        for translation_unit in translated_page:
            if translation_unit.is_translation_well_structured():
                for orig_snippet, trans_snippet in translation_unit:
                    trans_snippet.content = corrector.correct(trans_snippet.content, orig_snippet.content)
                translation_unit.sync_from_snippets()
            else:
                self.logger.warning(f"{translation_unit.get_name()} is not well structured.")
                translation_unit.set_translation(corrector.correct(translation_unit.get_translation(),
                                                                   translation_unit.get_definition()))

            diff = translation_unit.get_translation_diff()
            if diff != "":
                self._diff += f"{translation_unit.get_name()}: {diff}\n"
        self._stats = corrector.print_stats()
        self._correction_counter = corrector.count_corrections()
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

    correctbot = CorrectBot(args.simulate)
    correctbot.run(args.page, args.language_code)
