#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Bot that replaces common typos for different languages.
This requires the pywikibot framework.

Documentation should also go to https://www.4training.net/User:TheCorrectBot

Run with dummy page with available translation units
www.4training.net/mediawiki/api.php?action=query&list=messagecollection&mcgroup=page-CorrectTestpage&mclanguage=fr
"""

import argparse
import logging

from corrector import Corrector
from communicator import PageWrapper
from communicator import Communicator

Logger = logging.getLogger("CorrectBot")


def parse_arguments() -> argparse.Namespace:
    """
    Parses the arguments given from outside

    Returns:
        argparse.Namespace: parsed arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("webpage", help="Name of the webpage")
    parser.add_argument("language_code", help="Language code")
    parser.add_argument("-s", "--simulate", type=bool, default=False, required=False,
                        help="Simulates the corrections but does not apply them to the webpage.")
    parser.add_argument("-l", "--log_level", type=str, default="debug", required=False,
                        help="Debug, Info, Warning, Error, Critical")
    return parser.parse_args()


def main():
    """
    Parse arguments, initialize logging, request data from webpage, run corrector and write it back if not in
    simulation mode
    """
    args = parse_arguments()

    name_of_webpage: str = args.webpage
    language: str = args.language_code
    simulation_mode: bool = args.simulate

    communicator: Communicator = Communicator(name_of_webpage)
    page_wrapper: PageWrapper = communicator.fetch_content(language)

    # corrector: Corrector = Corrector(page_wrapper.corrected_translations, page_wrapper.language)
    # corrector.fix_general_typos()
    # corrector.fix_language_specific_typos()

    # page_wrapper.corrected_translations = corrector.get_corrected_paragraphs

    page_wrapper.print_diff()
    # if not simulation_mode:
    #     communicator.save_content(page_wrapper)


if __name__ == "__main__":
    main()
