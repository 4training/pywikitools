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
import importlib
import sys
from typing import Callable, List

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

def load_corrector(language_code: str) -> Callable:
    """Load the corrector class and return it (None in case of an error)"""
    try:
        # Dynamically load e.g. correctors/de.py
        module = importlib.import_module(f"correctors.{language_code}", ".")
        # There should be exactly one class named "XYCorrector" in there - let's get the name of it
        class_name = next(s for s in dir(module) if "Corrector" in s)
        # Now let's load it
        corrector_class = getattr(module, class_name)

    except ModuleNotFoundError as err:
        logging.fatal(f"Couldn't load corrector for language {language_code}: {err}")
        sys.exit(1)

    return corrector_class

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

    corrector_class = load_corrector(page_wrapper.language)
    corrector_class_instance = corrector_class()

    corrected_translations: List[str] = []
    for counter in range(len(page_wrapper.original_translations)):
        # TODO simplify this a bit
        text = page_wrapper.original_translations[counter]
        corrected_translations.append(corrector_class_instance.correct(text))

    print(corrector_class_instance.print_stats())

    page_wrapper.set_corrected_translations(corrected_translations)

    page_wrapper.print_diff()
    # if not simulation_mode:
    #     communicator.save_content(page_wrapper)


if __name__ == "__main__":
    main()
