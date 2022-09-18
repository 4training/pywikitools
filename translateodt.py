"""
This script produces a translated ODT file for a given worksheet and a given language.
It does so by:
1. accessing the worksheet in the mediawiki system together with its translation
2. downloading the English ODT file (the URL is found in the result of the first step)
3. doing search and replace: For each translation unit
   - do some cleansing (removing links, unnecessary spaces)
   - split it up even further into small snippets (when the translation unit contains lists etc.)
   - search for each snippet and replace it by its translation
4. saving the created ODT file

It does quite some logging:
    - error level: serious issues where the script had to be aborted
    - warning level: these should be checked afterwards
    - info level: going along what the script does
    - debug level: extensive details for debugging

Command line options:
    -h, --help: help message
    -l [debug, info, warning, error]: set loglevel
    --keep-english-file: don't delete the downloaded English ODT file after we're finished
"""
import argparse
import sys
import logging
from typing import List

from pywikitools.translateodt import TranslateODT


if __name__ == '__main__':
    log_levels: List[str] = ['debug', 'info', 'warning', 'error']

    msg = "Create translated ODT file of a worksheet"
    parser = argparse.ArgumentParser(prog="python3 translateodt.py", description=msg)
    parser.add_argument("worksheet", help="Name of the mediawiki page")
    parser.add_argument("language_code", help="Language code of the translation language")
    parser.add_argument("-l", "--loglevel", choices=log_levels, default="warning", help="set loglevel for the script")
    parser.add_argument("--keep-english-file", dest="keep_english_file", action="store_true",
                        help="Don't delete the downloaded English ODT file after we're finished")

    args = parser.parse_args()
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    fformatter = logging.Formatter('%(levelname)s: %(message)s')
    sh.setFormatter(fformatter)
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    assert isinstance(numeric_level, int)
    sh.setLevel(numeric_level)
    root.addHandler(sh)

    translateodt = TranslateODT(keep_english_file=args.keep_english_file)
    translateodt.translate_worksheet(args.worksheet, args.language_code)
