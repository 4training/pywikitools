#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Bot that replaces common typos for different languages. It works directly in-place and writes the changes
to the system. Additionally it writes a report into the CorrectBot namespace, e.g.
https://www.4training.net/CorrectBot:My_Story_with_God/fr

All correction rules for different languages are in the correctbot/correctors/ folder in separate classes.

Example: Check and correct the French translation of "Forgiving Step by Step" (simulation: don't make changes)
    python3 correct_bot.py --simulate Forgiving_Step_by_Step fr

Example: Now write the corrections to the system + write report
    python3 correct_bot.py Forgiving_Step_by_Step fr

Configuration needs to be set in config.ini (see config.example.ini).

This is only the wrapper script, all main logic is in correctbot/bot.py
"""

import argparse
from configparser import ConfigParser
import logging
from os.path import abspath, dirname, join
import sys
from typing import List

from pywikitools.correctbot.bot import CorrectBot


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
    parser.add_argument("--only", help="Only apply the correction rule with the specified method name")
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
    config.read(join(dirname(abspath(__file__)), "config.ini"))

    correctbot = CorrectBot(config, args.simulate)
    apply_only_rule = None
    if args.only is not None:
        apply_only_rule = str(args.only)

    correctbot.run(args.page, args.language_code, apply_only_rule)
