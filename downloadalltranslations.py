#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to download all translated PDFs of a worksheet, e.g. downloadalltranslations.py Forgiving_Step_by_Step
The PDF files are named [languagename in English] - [language autonym].pdf
They're put into a (newly created) subdirectory named after the worksheet
"""
import sys
import os
import logging
import getopt
import requests
from pywikitools.fortraininglib import ForTrainingLib


def usage():
    print("Usage: python3 downloadalltranslations.py [-l {debug, info, warning, error, critical}] <worksheetname>")


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hl:", ["help", "loglevel"])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)
        usage()
        sys.exit(2)
    if len(args) != 1:
        usage()
        sys.exit(2)
    worksheetname = args[0]
    for o, a in opts:
        if o == "-l":
            numeric_level = getattr(logging, a.upper(), None)
            if not isinstance(numeric_level, int):
                raise ValueError(f"Invalid log level: {a}")
            logging.basicConfig(level=numeric_level)
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            logging.info("unhandled option")
    logging.debug(f"Worksheetname: {worksheetname}")
    try:
        os.mkdir(worksheetname)
    except FileExistsError:
        pass

    fortraininglib = ForTrainingLib("https://www.4training.net")
    translations = fortraininglib.list_page_translations(worksheetname)
    logging.info(f'Worksheet {worksheetname} is translated into {len(translations)} languages: {translations.keys()}')
    for language in translations.keys():
        pdf = fortraininglib.get_pdf_name(worksheetname, language)
        if pdf is None:
            logging.warning(f"Couldn't find PDF name in {worksheetname}/{language}")
            continue
        logging.debug(f"Language: {language}, filename: {pdf}")
        url = fortraininglib.get_file_url(pdf)
        if not url:
            logging.warning(f"Language: {language}, file: {pdf} doesn't seem to exist, ignoring")
            continue
        file_request = requests.get(url, allow_redirects=True)
        language_autonym = fortraininglib.get_language_name(language)
        language_english = fortraininglib.get_language_name(language, 'en')
        if language_autonym is None or language_english is None:
            logging.warning(f"Strang: couldn't get language name for language {language}, ignoring")
            continue
        file_name = f"{worksheetname}/{language_english} - {language_autonym}.pdf"
        try:
            open(file_name, 'wb').write(file_request.content)
        except FileNotFoundError:
            logging.warning(f"Language: {language}, error while trying to open file {file_name}, ignoring")
        logging.info(f"We saved {file_name}")
