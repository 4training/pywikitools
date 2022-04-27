"""
Checks all translations of one language for typos.
Runs the corrector on it and prints out the result but doesn't write any changes to the mediawiki system.

Usage:
python3 check_for_typos.py language_code
"""

import argparse
import logging
import sys
from typing import List
from pywikitools.fortraininglib import ForTrainingLib

from pywikitools.correctbot.correct_bot import CorrectBot

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

    # TODO read mediawiki baseurl from config.ini
    fortraininglib = ForTrainingLib("https://www.4training.net")

    correctbot = CorrectBot(fortraininglib, simulate=True)
    for worksheet in fortraininglib.get_worksheet_list():
        correctbot.check_page(worksheet, args.language_code)
        print(f"{worksheet}: {correctbot.get_correction_counter()} corrections")
        if correctbot.get_correction_counter() > 0:
            print(correctbot.get_diff())
            print(correctbot.get_stats())
