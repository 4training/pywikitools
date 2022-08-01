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
        if not self._config.has_option('mediawiki', 'baseurl') or \
           not self._config.has_option('mediawiki', 'scriptpath'):
            raise RuntimeError("Missing settings for mediawiki connection in config.ini")
        self.fortraininglib: ForTrainingLib = ForTrainingLib(self._config.get('mediawiki', 'baseurl'),
                                                             self._config.get('mediawiki', 'scriptpath'))
        self.logger: logging.Logger = logging.getLogger("pywikitools.correctbot")
        self.site: pywikibot.site.APISite = pywikibot.Site()
        self._simulate: bool = simulate
        self._correction_diff: str = ""
        self._suggestion_diff: str = ""
        self._warnings: str = ""
        self._correction_stats: Optional[str] = None
        self._suggestion_stats: Optional[str] = None
        self._correction_counter: int = 0
        self._suggestion_counter: int = 0
        self._warning_counter: int = 0

    def _load_corrector(self, language_code: str) -> Callable:
        """Load the corrector class for the specified language and return it.

        Raises ImportError if corrector class can't be found"""
        # Dynamically load e.g. correctors/de.py
        module_name = f"pywikitools.correctbot.correctors.{language_code}"
        module = importlib.import_module(module_name)

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
        if unit.get_translation() == unit.get_definition():
            if len(unit.get_definition()) < 15:
                # Sometimes a translation for a single word maybe exactly the same as the English original
                return None
            else:
                # But for any longer content there's most likely something wrong
                return CorrectionResult(unit, unit, {}, {}, "Translation is the same as English original.")
        return corrector.correct(unit)

    def check_page(self, page: str, language_code: str) -> Optional[List[CorrectionResult]]:
        """
        Check one specific page and store the results in this class

        This does not write anything back to the server. Changes can be read with
        get_correction_counter(), get_suggestion_counter() and get_warning_counter();
        get_correction_stats(), get_suggestion_stats() and get_warnings();
        get_correction_diff() and get_suggestion_diff()

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
        self._warnings = ""
        self._warning_counter = 0
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
                self._warning_counter += result.warnings.count("\n") + 1
                self._warnings += f"{translation_unit.get_name()}: {result.warnings}\n"

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

    def get_warnings(self) -> str:
        warnings: str = f"{self._warning_counter} warnings"
        if self._warning_counter > 0:
            warnings += ":\n" + self._warnings
        return warnings

    def get_correction_counter(self) -> int:
        """How many corrections did we do (in the last run)?"""
        return self._correction_counter

    def get_suggestion_counter(self) -> int:
        """How many suggestions did we receive (in the last run)?"""
        return self._suggestion_counter

    def get_warning_counter(self) -> int:
        """How many warnings did we get (in the last run)?"""
        return self._warning_counter

    def get_correction_diff(self) -> str:
        """Print a diff of the corrections (made in the last run)"""
        return self._correction_diff

    def get_suggestion_diff(self) -> str:
        """Print a diff of the suggestions (made in the last run)"""
        return self._suggestion_diff

    def save_to_mediawiki(self, results: List[CorrectionResult]) -> bool:
        """
        Write corrections back to mediawiki

        You should disable pywikibot throttling to avoid CorrectBot runs to take quite long:
        `put_throttle = 0` in user-config.py

        Returns:
            bool: Did we save any corrections to the mediawiki system?
        """
        saved_corrections = False
        for result in results:
            if result.corrections.has_translation_changes():
                mediawiki_page = pywikibot.Page(self.site, result.corrections.get_name())
                mediawiki_page.text = result.corrections.get_translation()
                mediawiki_page.save(minor=True)
                saved_corrections = True
        return saved_corrections

    def save_report(self, page: str, language_code: str, results: List[CorrectionResult]) -> bool:
        """Save report with the correction results to the mediawiki system

        We save the report in our custom CorrectBot namespace, for example to CorrectBot:Prayer/de

        Returns:
            Did we save a report? False means there is already exactly the same report in the system,
            so there is nothing new to report.

        """
        page_name: str = f"CorrectBot:{page}/{language_code}"
        summary: str = f"{self.get_correction_counter()} corrections, {self.get_suggestion_counter()} suggestions, "
        summary += f"{self.get_warning_counter()} warnings"

        report: str = f"__NOTOC____NOEDITSECTION__\nResults for this CorrectBot run of [[{page}/{language_code}]]: "
        report += f"<b>{summary}</b> (for older reports see [[Special:PageHistory/{page_name}|report history]])\n"
        if self.fortraininglib.count_jobs() > 0:
            self.logger.warning("MediaWiki job queue is not empty!")
            report += "  <i>Warning: MediaWiki job queue is not empty, some corrections may not be visible yet.</i>\n"
        if self.get_correction_counter() > 0:
            report += f"\n== Corrections ==\n{self.get_correction_stats()}\n<i>You can also look at the "
            report += f"[[Special:PageHistory/{page}/{language_code}|version history of {page}/{language_code}]]"
            report += " and compare revisions.</i>\n"
            for result in results:
                if result.corrections.has_translation_changes():
                    report += f"=== [{self.fortraininglib.index_url}?title={result.corrections.get_name()}&action=edit"
                    report += f" {result.corrections.get_name()}] ===\n"
                    report += "{{StringDiff|" + result.corrections.get_original_translation()
                    report += "|" + result.corrections.get_translation() + "}}\n"
        if self.get_suggestion_counter() > 0:
            report += f"\n== Suggestions ==\n{self.get_suggestion_stats()}\n<i>Look at the following suggestions. "
            report += f"If you find good ones, please correct them manually in [{self.fortraininglib.index_url}"
            report += f"?title=Special:Translate&group=page-{page}&action=page&filter=&language={language_code}"
            report += " the translation view]</i>\n"
            for result in results:
                if result.suggestions.has_translation_changes():
                    report += f"=== [{self.fortraininglib.index_url}?title={result.suggestions.get_name()}&action=edit"
                    report += f" {result.suggestions.get_name()}] ===\n"
                    report += "{{StringDiff|" + result.suggestions.get_original_translation()
                    report += "|" + result.suggestions.get_translation() + "}}\n"

        if self.get_warning_counter() > 0:
            report += "\n== Warnings ==\n"
            for result in results:
                if result.warnings != "":
                    report += f"=== [{self.fortraininglib.index_url}?title={result.corrections.get_name()}&action=edit"
                    report += f" {result.corrections.get_name()}] ===\n"
                    report += f"<b><pre><nowiki>{result.warnings}</nowiki></pre></b>\n"
                    report += "{| class=\"wikitable\"\n|-\n! Original\n! Translation\n|- style=\"vertical-align:top\"\n"
                    report += f"|\n{result.corrections.get_definition()}\n|\n{result.corrections.get_translation()}\n"
                    report += "|}\n"

        report_page = pywikibot.Page(self.site, page_name)
        if report_page.text.strip() != report.strip():
            report_page.text = report
            report_page.save(summary)
            return True
        return False

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
                script = subprocess.Popen(args, stdout=subprocess.DEVNULL)
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
        page = page.replace(' ', '_')   # spaces may lead to problems in some places: "Time with God" -> "Time_with_God"
        results = self.check_page(page, language_code)
        if results is None:
            print(f"Error while trying to correct {page}")
            return
        saved_corrections = False
        saved_report = False
        if not self._simulate:
            # That shouldn't be necessary but for some reasons the script sometimes failed with WARNING from pywikibot:
            # "No user is logged in on site 4training:en" -> better check and try to log in if necessary
            if not self.site.logged_in():
                self.logger.info("We're not logged in. Trying to log in...")
                self.site.login()
                if not self.site.logged_in():
                    self.site.getuserinfo()
                    self.logger.warning(f"userinfo: {self.site.userinfo}")
                    raise RuntimeError("Login with pywikibot failed.")

            saved_corrections = self.save_to_mediawiki(results)
            self.empty_job_queue()
            saved_report = self.save_report(page, language_code, results)

        # Print summary of what we did
        if not saved_report:
            print("NOTHING SAVED.")
            if self._simulate:
                print("We're running with --simulate. No corrections are written back to the mediawiki system.")
            elif not saved_corrections:
                print("Nothing new. The existing CorrectBot report in the mediawiki system is still correct.")
            else:
                print("WARNING: Inconsistency! Please inform an administrator. Saved corrections but not report.")

        print(self.get_correction_stats())
        if self._correction_counter > 0:
            print(self.get_correction_diff())
        print(self.get_suggestion_stats())
        if self._suggestion_counter > 0:
            print(self.get_suggestion_diff())
        print(self.get_warnings())


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
