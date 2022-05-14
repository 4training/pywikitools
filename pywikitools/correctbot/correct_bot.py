#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Bot that replaces common typos for different languages.

All correction rules for different languages are in the correctors/ folder in separate classes.

Run with dummy page:
    python3 correct_bot.py Test de
    python3 correct_bot.py CorrectTestpage fr

"""

import argparse
from collections import Counter
from configparser import ConfigParser
import logging
import importlib
from os.path import abspath, dirname, join
import subprocess
import pywikibot
import re
import sys
from typing import Callable, List, Optional

from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.correctbot.correctors.base import CorrectionResult, CorrectorBase
from pywikitools.lang.translated_page import TranslatedPage, TranslationUnit


class CorrectBot:
    """Main class for doing corrections"""
    def __init__(self, config: ConfigParser, simulate: bool = False):
        self._config = config
        if not self._config.has_option('mediawiki', 'baseurl'):
            raise RuntimeError("Missing settings for mediawiki connection in config.ini")
        self.fortraininglib: ForTrainingLib = ForTrainingLib(self._config.get('mediawiki', 'baseurl'))
        self.logger: logging.Logger = logging.getLogger("pywikitools.correctbot")
        self.site: pywikibot.site.APISite = pywikibot.Site()
        self._simulate: bool = simulate
        self._correction_diff: str = ""
        self._suggestion_diff: str = ""
        self._correction_stats: Optional[str] = None
        self._suggestion_stats: Optional[str] = None
        self._correction_counter: int = 0
        self._suggestion_counter: int = 0

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

        Returns:
            Result of running all correction functions on the translation unit
            None if we didn't run correctors (because the unit is not translated e.g.)
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

    def check_page(self, page: str, language_code: str) -> Optional[List[CorrectionResult]]:
        """
        Check one specific page and store the results in this class

        This does not write anything back to the server. Changes can be read with
        get_stats(), get_correction_counter() and get_diff()

        Returns:
            CorrectionResult for each processed translation unit
            None if an error occurred
        """
        self._correction_diff = ""
        self._suggestion_diff = ""
        self._correction_stats = None
        self._suggestion_stats = None
        self._correction_counter = 0
        self._suggestion_counter = 0
        correction_stats: Counter = Counter()
        suggestion_stats: Counter = Counter()

        translated_page: Optional[TranslatedPage] = self.fortraininglib.get_translation_units(page, language_code)
        if translated_page is None:
            return None
        corrector = self._load_corrector(language_code)()
        results: List[CorrectionResult] = []
        for translation_unit in translated_page:
            result = self.check_unit(corrector, translation_unit)
            if result is None:
                continue
            results.append(result)
            if result.warnings != "":
                self.logger.warning(result.warnings)

            if (correction_diff := result.corrections.get_translation_diff()) != "":
                self._correction_diff += f"{translation_unit.get_name()}: {correction_diff}\n"
            if (suggestion_diff := result.suggestions.get_translation_diff()) != "":
                self._suggestion_diff += f"{translation_unit.get_name()}: {suggestion_diff}\n"
            correction_stats += Counter(result.correction_stats)
            suggestion_stats += Counter(result.suggestion_stats)

        self._correction_stats = corrector.print_stats(correction_stats)
        self._suggestion_stats = corrector.print_stats(suggestion_stats)
        self._correction_counter = sum(correction_stats.values())
        self._suggestion_counter = sum(suggestion_stats.values())
        return results

    def get_correction_stats(self) -> str:
        """Return a summary: which correction rules could be applied (in the last run)?"""
        if self._correction_stats is None:
            self.logger.warning("No statistics available. You need to run check_page() first.")
            return ""
        stats: str = f"{self._correction_counter} corrections"
        if self._correction_counter > 0:
            stats += ":\n" + self._correction_stats
        return stats

    def get_suggestion_stats(self) -> str:
        """Return a summary: which corrections are suggested (in the last run)?"""
        if self._suggestion_stats is None:
            self.logger.warning("No statistics available. You need to run check_page() first.")
            return ""
        stats: str = f"{self._suggestion_counter} suggestions"
        if self._suggestion_counter > 0:
            stats += ":\n" + self._suggestion_stats
        return stats

    def get_correction_counter(self) -> int:
        """How many corrections did we do (in the last run)?"""
        return self._correction_counter

    def get_suggestion_counter(self) -> int:
        """How many suggestions did we receive (in the last run)?"""
        return self._suggestion_counter

    def get_correction_diff(self) -> str:
        """Print a diff of the corrections (made in the last run)"""
        return self._correction_diff

    def get_suggestion_diff(self) -> str:
        """Print a diff of the suggestions (made in the last run)"""
        return self._suggestion_diff

    def save_to_mediawiki(self, results: List[CorrectionResult]):
        """
        Write changes back to mediawiki

        You should disable pywikibot throttling to avoid CorrectBot runs to take quite long:
        `put_throttle = 0` in user-config.py
        """
        for result in results:
            if result.corrections.has_translation_changes():
                mediawiki_page = pywikibot.Page(self.site, result.corrections.get_name())
                mediawiki_page.text = result.corrections.get_translation()
                mediawiki_page.save(minor=True)

    def save_report(self, page: str, results: List[CorrectionResult]):
        # TODO: save report
        # report_page = pywikibot.Page(self.site, f"CorrectBot:{page}")
        pass

    def empty_job_queue(self) -> bool:
        """
        Empty the mediawiki job queue by running the runJobs.php maintenance script

        See https://www.mediawiki.org/wiki/Manual:RunJobs.php

        Returns:
            True if we could successfully run this script
            False if paths were not configured or there was an error while executing
        """
        if self._config.has_option('Paths', 'php') and self._config.has_option('correctbot', 'runjobs'):
            args = [self._config['Paths']['php'], self._config['correctbot']['runjobs']]
            try:
                script = subprocess.Popen(args)
                exit_code = script.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.logger.warning("Invoking runJobs.php didn't finished - job queue is maybe still not empty")
                return False
            if exit_code != 0:
                self.logger.warning(f"runJobs.php did not finish successfully. Exit code: {exit_code}")
                return False
            return True
        else:
            self.logger.warning("Settings for invoking runJobs.php missing in config.ini. Can't empty job queue.")
            return False

    def run(self, page: str, language_code: str):
        """
        Correct the translation of a page.
        """
        results = self.check_page(page, language_code)
        if results is None:
            print(f"Error while trying to correct {page}")
            return
        if self._simulate:
            print("We're running with --simulate. No changes are written back to the mediawiki system")
        else:
            self.save_to_mediawiki(results)
            self.empty_job_queue()

        print(self.get_correction_stats())
        if self._correction_counter > 0:
            print(self.get_correction_diff())
        print(self.get_suggestion_stats())
        if self._suggestion_counter > 0:
            print(self.get_suggestion_diff())


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments

    Returns:
        CorrectBot instance
    """
    log_levels: List[str] = ['debug', 'info', 'warning', 'error']

    parser = argparse.ArgumentParser()
    parser.add_argument("page", help="Name of the mediawiki page")
    parser.add_argument("language_code", help="Language code")
    parser.add_argument("-s", "--simulate", action="store_true",
                        help="Simulates the corrections but does not apply them to the webpage.")
    parser.add_argument("-l", "--loglevel", choices=log_levels, default="warning", help="set loglevel for the script")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    # Set up logging
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    fformatter = logging.Formatter('%(levelname)s: %(message)s')
    sh.setFormatter(fformatter)
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    assert isinstance(numeric_level, int)
    sh.setLevel(numeric_level)
    root.addHandler(sh)

    config = ConfigParser()
    config.read(join(dirname(abspath(__file__)), "..", "config.ini"))

    correctbot = CorrectBot(config, args.simulate)
    correctbot.run(args.page, args.language_code)
