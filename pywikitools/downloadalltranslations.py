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
import requests
import getopt
import fortraininglib

def usage():
    print("Usage: python3 downloadalltranslations.py [-l {debug, info, warning, error, critical}] <worksheetname>")

try:
    opts, args = getopt.getopt(sys.argv[1:], "hl:", ["help", "loglevel"])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err)
    usage()
    sys.exit(2)
if (len(args) != 1):
    usage()
    sys.exit(2)
worksheetname = args[0]
for o, a in opts:
    if o == "-l":
        numeric_level = getattr(logging, a.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % loglevel)
        logging.basicConfig(level=numeric_level)
    elif o in ("-h", "--help"):
        usage()
        sys.exit()
    else:
        logging.info("unhandled option")
logging.debug("Worksheetname: " + worksheetname)
try:
    os.mkdir(worksheetname)
except FileExistsError:
    pass

translations = fortraininglib.list_page_translations(worksheetname)
logging.info('Worksheet ' + worksheetname + ' is translated into ' + str(len(translations)) + ' languages: ' + str(translations))
for language in translations:
    pdf = fortraininglib.get_pdf_name(worksheetname, language)
    logging.debug("Language: " + language + ", filename: " + pdf)
    url = fortraininglib.get_file_url(pdf)
    if not url:
        logging.warning('Language: ' + language + ', file: ' + pdf + " doesn't seem to exist, ignoring")
        continue
    file_request = requests.get(url, allow_redirects = True)
    file_name = worksheetname + '/' + fortraininglib.get_language_name(language, 'en') + ' - ' + fortraininglib.get_language_name(language) + '.pdf'
    try:
        open(file_name, 'wb').write(file_request.content)
    except FileNotFoundError:
        logging.warning('Language: ' + language + ', error while trying to open file ' + file_name + ', ignoring')
        pass
    logging.info('We saved ' + file_name)

