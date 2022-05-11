"""
Script to fill the "Available Resources in ..." sections of all languages

This scripts scans through the worksheets and all their translations, saving also the links for PDF and ODT files.
It checks if new translations were added and changes the language overview pages where necessary.
It is supposed to run daily as a cronjob.

Main steps:
    1. gather data: go through all worksheets and all their translations
       This will take quite some time as it is many API calls
    2. Update language overview pages where necessary
       For example: https://www.4training.net/German#Available_training_resources_in_German
       To make that easier, a JSON representation is saved for every language, e.g.
       https://www.4training.net/4training:de.json
       The script will compare its results to the JSON and update the JSON and the language overview page when necessary
    3. Post-processing (TODO: not yet implemented)
       With information like "we now have a Hindi translation of the Prayer worksheet" we can do helpful things, e.g.
       - update a zip file with all Hindi worksheets
       - send an email notification to all interested in the Hindi resources

Command line options:
    --lang LANGUAGECODE: only look at this one language (significantly faster)
    -l, --loglevel: change logging level (standard: warning; other options: debug, info)
    --rewrite-all: Rewrite all language information pages
    --read-from-cache: Read from the JSON structure instead of querying the current status of all worksheets

Logging:
    If configured in config.ini (see config.example.ini), output will be logged to three different files
    in three different verbosity levels (WARNING, INFO, DEBUG)

Reports:
    We write language reports into the folder specified in config.ini
    (section Paths, variable languagereports)

Examples:

Only update German language information page with more logging
    python3 resourcesbot.py --lang de -l info

Normal run (updating language information pages where necessary)
    python3 resourcesbot.py

Run script completely without making any changes on the server:
Best for understanding what the script does, but requires running via pywikibot pwb.py
    python3 pwb.py -simulate resourcesbot.py -l info

This is only the wrapper script, all main logic is in resourcesbot/bot.py
"""
import argparse
from configparser import ConfigParser
import logging
import os
import sys
import traceback
from typing import List

from pywikitools.resourcesbot.bot import ResourcesBot


def parse_arguments() -> ResourcesBot:
    """
    Parses command-line arguments.
    @return: ResourcesBot instance
    """
    msg: str = 'Update list of available training resources in the language information pages'
    epi_msg: str = 'Refer to https://datahub.io/core/language-codes/r/0.html for language codes.'
    log_levels: List[str] = ['debug', 'info', 'warning', 'error']

    parser = argparse.ArgumentParser(prog='python3 resourcesbot.py', description=msg, epilog=epi_msg)
    parser.add_argument('--lang', help='run script for only one language')
    parser.add_argument('-l', '--loglevel', choices=log_levels, default="warning", help='set loglevel for the script')
    parser.add_argument('--read-from-cache', action='store_true', help='Read results from json cache from the server')
    parser.add_argument('--rewrite-all', action='store_true', help='rewrites all overview lists')

    args = parser.parse_args()
    limit_to_lang = None
    if args.lang is not None:
        limit_to_lang = str(args.lang)
    config = ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    assert isinstance(numeric_level, int)
    set_loglevel(config, numeric_level)
    return ResourcesBot(config, limit_to_lang=limit_to_lang, rewrite_all=args.rewrite_all,
                        read_from_cache=args.read_from_cache)


def set_loglevel(config: ConfigParser, loglevel: int):
    """
    Setting up logging to three log files and to stdout.

    The file paths for the three log files (for each log level WARNING, INFO and DEBUG) are
    configured in the config.ini
    @param loglevel: logging.WARNING is standard, logging.INFO for more details, logging.DEBUG for a lot of output
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    # The following is necessary so that debug messages go to debuglogfile
    logging.getLogger('pywikitools.resourcesbot').setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(loglevel)
    fformatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    sh.setFormatter(fformatter)
    root.addHandler(sh)

    log_path = config.get('Paths', 'logs', fallback='')
    if log_path == '':
        root.warning('No log directory specified in configuration. Using current working directory')
    # Logging output to files with different verbosity
    if config.has_option("resourcesbot", "logfile"):
        fh = logging.FileHandler(f"{log_path}{config['resourcesbot']['logfile']}")
        fh.setLevel(logging.WARNING)
        fh.setFormatter(fformatter)
        root.addHandler(fh)
    if config.has_option("resourcesbot", "infologfile"):
        fh_info = logging.FileHandler(f"{log_path}{config['resourcesbot']['infologfile']}")
        fh_info.setLevel(logging.INFO)
        fh_info.setFormatter(fformatter)
        root.addHandler(fh_info)
    if config.has_option("resourcesbot", "debuglogfile"):
        fh_debug = logging.FileHandler(f"{log_path}{config['resourcesbot']['debuglogfile']}")
        fh_debug.setLevel(logging.DEBUG)
        fh_debug.setFormatter(fformatter)
        root.addHandler(fh_debug)


if __name__ == "__main__":
    try:
        resourcesbot = parse_arguments()
        resourcesbot.run()
    except Exception as e:
        logging.error(f"Exiting because of uncaught exception: {e}")
        logging.error(traceback.format_exc())
