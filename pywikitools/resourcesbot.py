"""
Script to fill the "Available Resources in ..." sections of all languages

This scripts scans through the worksheets and all their translations, saving also the links for PDF and ODT files.
It checks if new translations were added and changes the language overview pages where necessary.
It is supposed to run daily as a cronjob,

Main steps:
    1. fill general_result
       This will take some time as it is many API calls (needs to go through every single translated worksheet we have)
    2. Update language overview pages where necessary
       For example: https://www.4training.net/German#Available_training_resources_in_German
       The script will read the current list, and if changes happened, it will write the new list and update the page
    3. Post-processing
       With information like "we now have a Hindi translation of the Prayer worksheet" we can do helpful things, e.g.
       - update a zip file with all Hindi worksheets
       - send an email notification to all interested in the Hindi resources

Command line options:
    --lang LANGUAGECODE: only look at this one language (significantly faster)
    -l, --loglevel: change logging level (standard: warning; other options: debug, info)
    --rewrite-all: Rewrite all language information pages

Examples:

Have lots of debugging output
    python3 pwb.py resourcesbot.py -l debug

Only update German language information page
    python3 pwb.py resourcesbot.py --lang de
"""

import os
import re
import sys
from pprint import pprint
import logging
import json
import urllib
import argparse # For CLI arguments
import configparser
from typing import Optional
import pywikibot
from pywikibot.data.api import Request
import pathlib

from pywikibot.tools import empty_iterator
import fortraininglib

#absolute path of directory
REPOSITORY_LOC = pathlib.Path(__file__).parent.parent.absolute()
#absolute path of log directory
LOG_FOLDER_LOC = os.path.join(REPOSITORY_LOC, "logs")

# Set variables that are globally needed
global_site = pywikibot.Site()
# Result dictionary: contains information about existing translations and the downloadable file names if existing
"""
dictionary with language codes
    of a dictionary with worksheet names
        of a dictionary with properties
Example for German with two worksheets:
global_result['de'] = {
    'Church': {
        'title' : 'Gemeinde',
        'pdf-timestamp' : '2019-01-28T16:00:11Z'
        'pdf' : 'https://www.4training.net/mediawiki/images/5/51/Gemeinde.pdf',
        'odt-timestamp' : '2019-01-28T16:00:40Z'
        'odt' : 'https://www.4training.net/mediawiki/images/9/97/Gemeinde.odt'
    },
    'Baptism': {
        'title' : 'Taufe',
        'pdf-timestamp' : "2020-07-10T09:46:24Z"
        'pdf' : 'https://www.4training.net/mediawiki/images/f/f3/Taufe.pdf',
        'odt-timestamp' : "2020-07-10T09:46:04Z"
        'odt' : 'https://www.4training.net/mediawiki/images/9/9f/Taufe.odt'
    }
}
Warning: the structure of global_result['en'] is a bit different (TODO change that a bit?):
global_result['en'] = {
    'Baptism': {
        'pdf': {
            'number': '11', # TODO change name? this is the number of the translation unit containing the PDF file name
            'name': 'Baptism.pdf'
        },
        'odt': {
            'number': '12', # TODO change name? this is the number of the translation unit containing the ODT file name
            'name': 'Baptism.odt'
        },
        'odg': {
            'number': 0,
            'name': ''
        }
    }
"""
global_result = {}
global_result['en'] = {}

# read-only list of download file types
global_file_types = fortraininglib.get_file_types()

# optional argument: limit processing to one language (then this variable holds a string with a language code)
global_only_lang = None
# optional argument: rewrite all lists, regardless if we find changes or not
rewrite_all = False

logger = logging.getLogger('4training.resourcesbot')


def change_message_translation(msg_title: str, content: str) -> list:
    """
    @param: msgTitle (str): Title of the message we want to change
    @param: content (str): New text of the translation unit
    TODO should we do it this way or probably we could just use the pywikibot.Page class and set the text?!
    """

    global global_site
    logger.info(F"Change_message_translation: {msg_title}: {content}")
    requeste_for_token: list = Request(site=global_site, action="query", meta="tokens").submit()
    my_token: str = requeste_for_token['query']['tokens']['csrftoken']
    result: list = Request(site=global_site, action="edit",
                                       title=msg_title, token=my_token, text=content).submit()
    return result


def get_translated_unit(page: str, lang: str, translation_unit_identifier: int) -> Optional[str]:
    """
    Returns the translation of one translation unit of a page into a give language
    @param page (str): name of the page
    @param lang (str): language code
    @param translation_unit_identifier (int): number of the translation unit
    TODO this can also be a string with "Page display title"!
    TODO move this function to fortraininglib, make an extra function get_translated_page_title(page, lang)
    @return the translated string or None if translation doesn't exist
    """
    wiki_page = pywikibot.Page(global_site, F"Translations:{page}/{str(translation_unit_identifier)}/{lang}")
    if wiki_page.pageid == 0:
        return None
    return wiki_page.text


def process_page(page: str):
    """
    Go through one worksheet, check all existing translations and gather information into global_result
    @param: page (str): Name of the page
    """
    global global_site, global_result
    p = pywikibot.Page(global_site, page)
    if not p.exists():
        logger.warning(F'Warning: page {page} does not exist!')
        return
    # finding out the name of the English downloadable files (originals)
    file_details = {}
    for file_type in global_file_types:
        re_identifier: str = r"\d+"
        re_name: str = r"[^<]+"
        handler = re.search(r"\{\{" + file_type.capitalize() + r"Download\|<translate>*?<!--T:(" +
                            re_identifier + r")-->\s*(" + re_name + ")</translate>", p.text)
        # identifier of the translation section containing the name of that file
        translation_section_identifier: int = 0
        # name of the translation section containing the name of that file
        translation_section_name: str = ""
        if handler:
            translation_section_identifier = handler.group(1)
            translation_section_name = handler.group(2)
        file_details[file_type] = {}
        file_details[file_type]['number'] = translation_section_identifier
        file_details[file_type]['name'] = translation_section_name
    logger.info(F"Processing page {page}. PDF name: {file_details['pdf']['name']} "
                F"is in translation unit {str(file_details['pdf']['number'])}")

    global_result['en'][page] = file_details

    if global_only_lang is None:
        # Standard: look up all existing translations of this worksheet
        available_translations = fortraininglib.list_page_translations(page)
        logger.info(F"This worksheet is translated into: {str(available_translations)}")
        if 'en' in available_translations:
            available_translations.remove('en')
    else:
        # We only look at this one language
        available_translations = [global_only_lang]
    # now let's retrieve the translated file names
    for lang in available_translations:
        page_info: dict = {}
        page_info['title'] = get_translated_unit(page, lang, "Page display title")
        if page_info['title'] is None:  # apparently this translation doesn't exist
            logger.warning(F"Language {lang}: Title of {page} not translated, skipping.")
            continue
        for file_type in file_details:
            if file_details[file_type]['number'] == 0:    # in English original this is not existing, skip it
                continue
            translation = get_translated_unit(page, lang, file_details[file_type]['number'])
            logger.debug(F"{page}/{file_details[file_type]['number']}/{lang} is {translation}")
            if translation is None:
                logger.warning(F"Warning: translation {page}/{file_details[file_type]['number']}/{lang} "
                               F"(for file {file_type}) does not exist!")
                # TODO fill it with "-"
            elif (translation == '-') or (translation == '.'):
                logger.warning(F"Warning: translation {page}/{file_details[file_type]['number']}/{lang} "
                               F"(for file {file_type}) is placeholder: {translation}")
                # TODO fill it with "-"
            elif translation == file_details[file_type]['name']:
                logger.warning(F"Warning: translation {page}/{file_details[file_type]['number']}/{lang} "
                               F"(for file {file_type}) is identical with English original")
                # TODO fill it with "-"
            else:
                # We have the name of the translated file, check if it actually exists
                try:
                    file_page = pywikibot.FilePage(global_site, translation)
                    if file_page.exists():
                        dirty_timestamp: str = str(file_page.latest_file_info["timestamp"])
                        timestamp: str = dirty_timestamp.replace("Timestamp(", "").replace(")", "").split(",")[0]
                        page_info[file_type+"-timestamp"] = timestamp
                        page_info[file_type] = urllib.parse.unquote(file_page.get_file_url())
                        logger.debug(F"{file_type} timestamp: {timestamp}, url: {page_info[file_type]}")
                    else:
                        logger.info(F"Language {lang}, page {page}: File {translation} does not seem to exist")
                except:
                    logger.warning(F"Language {lang}, page {page}: File {translation} not existing, exception thrown.")

        if lang not in global_result:
            global_result[lang] = {}
        global_result[lang][page] = page_info
        logger.debug(global_result)


def write_available_resources(lang: str):
    """
    Writes the list of available training resources for this language
    Reads from global_result
    Output should look like the following line:
    * [[God's_Story_(five_fingers)/de|{{int:sidebar-godsstory-fivefingers}}]] [[File:pdficon_small.png|link={{filepath:Gottes_Geschichte_(fünf_Finger).pdf}}]] [[File:odticon_small.png|link={{filepath:Gottes_Geschichte_(fünf_Finger).odt}}]]
    """
    logger.debug(F"Writing list of available resources in {lang}...")
    if lang not in global_result:
        logger.warning(F"Internal error: {lang} not in global_result. Not doing anything for this language.")
        return

    # Creating the mediawiki string for the list of available training resources
    content = ''
    for worksheet in global_result[lang]:
        if not 'pdf' in global_result[lang][worksheet]:
            # Only show worksheets where we have a PDF file in the list
            logger.warning(F"Language {lang}: worksheet {worksheet} doesn't have PDF, not including in list.")
            continue

        content += F"* [[{worksheet}/{lang}|"
        content += "{{int:" + fortraininglib.title_to_message(worksheet) + "}}]]"
        if 'pdf' in global_result[lang][worksheet]:
            pdfname = global_result[lang][worksheet]['pdf']
            pos = pdfname.rfind('/')
            if pos > -1:
                pdfname = pdfname[pos+1:]
            else:
                logger.warning(F"Couldn't find / in {pdfname}")
            content += " [[File:pdficon_small.png|link={{filepath:"
            content += pdfname
            content += "}}]]"

        if 'odt' in global_result[lang][worksheet]:
            odtname = global_result[lang][worksheet]['odt']
            pos = odtname.rfind('/')
            if pos > -1:
                odtname = odtname[pos+1:]
            else:
                logger.warning(F"Couldn't find / in {odtname}")
            content += " [[File:odticon_small.png|link={{filepath:"
            content += odtname
            content += "}}]]"
        content += "\n"
    logger.debug(content)

    # Saving this to the language information page, e.g. https://www.4training.net/German
    language = fortraininglib.get_language_name(lang, 'en')
    if language is None:
        logger.warning(F"Error while trying to get language name of {lang}! Skipping")
        return
    page = pywikibot.Page(global_site, language)
    if not page.exists():
        logger.warning(F"Language information page {language} doesn't exist!")
        return
    if page.isRedirectPage():
        logger.info(F"Language information page {language} is a redirect. Following the redirect...")
        page = page.getRedirectTarget()
        if not page.exists():
            logger.warning(F"Redirect target for language {language} doesn't exist!")
            return

    # Finding the exact positions of the existing list so that we know what to replace
    language_re = language.replace('(', r'\(')    # in case language name contains brackets, we need to escape them
    language_re = language_re.replace(')', r'\)') # Example would be language Turkish (secular)
    match = re.search(F"Available training resources in {language_re}\\s*?</translate>\\s*?==", page.text)
    if not match:
        logger.warning(F"Didn't find available training resources list in page {language}! Doing nothing.")
        logger.warning(F"Available training resources in {language_re}\\s*?</translate>\\s*?==")
        logger.warning(page.text)
        return
    list_start = 0
    list_end = 0
    # Find all following list entries
    pattern = re.compile(r'^\*.*$', re.MULTILINE)
    for m in pattern.finditer(page.text, match.end()):
        if list_start == 0:
            list_start = m.start()
        else:
            # Make sure there is no other line in between: We only want to find lines directly following each other
            if m.start() > (list_end + 1):
                logger.info(F"Looks like there is another list later in page {language}. Ignoring it.")
                break
        list_end = m.end()
        logger.debug(f"Matching line: start={m.start()}, end={m.end()}, {m.group(0)}")
    if (list_start == 0) or (list_end == 0):
        logger.warning(F"Couldn't find list entries of available training resources in {language}! Doing nothing.")
        return
    logger.debug(F"Found existing list of available training resources @{list_start}-{list_end}. Replacing...")
    new_page_content = page.text[0:list_start] + content + page.text[list_end+1:]
    logger.debug(new_page_content)
    page.text = new_page_content
    page.save("Updated list of available training resources")
    logger.info(F"Updated language information page {language}.")


def compare(old: dict, new: dict) -> bool:
    """
    Compares data structures for a language: has there been changes / updates?
    @param old,new: dictionary of worksheets, each of them holds a dictionary with more parameters
        (see explanation of global_result)
    @return true if list with available training resources needs to be re-written
    """
    needs_rewrite = False
    for worksheet in new:
        if worksheet in old:
            if ('pdf' in new[worksheet]) and ('pdf' not in old[worksheet]):
                logger.info(F"Comparison result: Added PDF for {worksheet}")
                needs_rewrite = True
            if ('odt' in new[worksheet]) and ('odt' not in old[worksheet]):
                logger.info(F"Comparison result: Added ODT for {worksheet}")
                needs_rewrite = True
            if ('pdf' not in new[worksheet]) and ('pdf' in old[worksheet]):
                logger.warning(F"Comparison inconsistency for worksheet {worksheet}: PDF vanished.")
                needs_rewrite = True
            if ('odt' not in new[worksheet]) and ('odt' in old[worksheet]):
                logger.warning(F"Comparison inconsistency for worksheet {worksheet}: ODT vanished.")
                needs_rewrite = True
        else:
            logger.info(F"Comparison result: Added worksheet {worksheet}")
            needs_rewrite = True
    for worksheet in old:
        if worksheet not in new:
            logger.warning(F"Comparison inconsistency: Worksheet {worksheet} vanished.")
            needs_rewrite = True

    return needs_rewrite


def process_language(lang: str):
    """
    Process the specified language, re-writing the list of available training resources if necessary
        - Reads and compares with the last list of available training resources
    @param lang language code
    """
    logger.debug(F"Processing language {lang}...")
    if lang not in global_result:
        logger.warning(F"Internal error: {lang} not in global_result. Not doing anything for this language.")
        return

    rewrite_language = rewrite_all
    # Reading data structure from our mediawiki, stored in e.g. https://www.4training.net/4training:de.json
    page = pywikibot.Page(global_site, F"4training:{lang}.json")
    if not page.exists():
        # There doesn't seem to be any information on this language stored yet!
        logger.warning(f"{page.full_url()} doesn't seem to exist yet. Creating...")
        page.text = json.JSONEncoder().encode(global_result[lang])
        page.save("Created JSON data structure")
        rewrite_language = True
    else:
        try:
            # compare and find out if new worksheets have been added
            saved_structure = json.JSONDecoder().decode(page.text)
            logger.debug(saved_structure)
            if compare(saved_structure, global_result[lang]):
                rewrite_language = True
        except json.JSONDecodeError as err:
            logger.warning(F"Error while trying to read JSON data structure: {err}")
            rewrite_language = True
    if rewrite_language:
        # Write the updated JSON structure
        page.text = json.JSONEncoder().encode(global_result[lang])
        page.save("Updated JSON data structure") # TODO write human-readable changes here in the save message
        logger.info(F"List of available training resources in language {lang} needs to be re-written.")
        write_available_resources(lang)
    else:
        logger.debug(F"List of available training resources in language {lang} doesn't need to be re-written.")

def parse_arguments() -> dict:
    """
    Parses command-line arguments.
    @return: (dict): parsed arguments
    """
    MSG: str = 'Verify all worksheet translations'
    EPI_MSG: str = 'Refer https://datahub.io/core/language-codes/r/0.html for language codes.'
    LOG_LEVELS: list = ['debug', 'info', 'warning', 'error', 'critical']

    parser = argparse.ArgumentParser(prog='python3 pwb.py resourcesbot', description=MSG, epilog=EPI_MSG)
    parser.add_argument('--lang', help='run script for only one language')
    parser.add_argument('-l', '--loglevel', choices=LOG_LEVELS, help='set loglevel for the script')
    parser.add_argument('--rewrite-all', action='store_true', help='rewrites all overview lists, also if there have been no changes')

    return vars(parser.parse_args())


def set_loglevel(loglevel_arg):
    """
    Setting loglevel
        logging.WARNING is standard,
        logging.INFO for more details,
        logging.DEBUG for a lot of output
    @param: loglevel_arg (str): loglevel argument
    @return: -
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)  # This is necessary so that debug messages go to debuglogfile
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.WARNING)
    if loglevel_arg is not None:
        numeric_level = getattr(logging, loglevel_arg.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(F'Invalid log level: {loglevel_arg}')
        sh.setLevel(numeric_level)
    fformatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    sh.setFormatter(fformatter)
    root.addHandler(sh)

    # Read the configuration from config.ini in the same directory
    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')
    log_path = config.get('Paths', 'logs', fallback='')
    if log_path == '':
        logger.warning('No log directory specified in configuration. Using current working directory')
    if config.has_option("resourcesbot", "logfile"):
        fh = logging.FileHandler(log_path + config['resourcesbot']['logfile'])
        fh.setLevel(logging.WARNING)
        fh.setFormatter(fformatter)
        root.addHandler(fh)
    if config.has_option("resourcesbot", "debuglogfile"):
        fh_debug = logging.FileHandler(log_path + config['resourcesbot']['debuglogfile'])
        fh_debug.setLevel(logging.DEBUG)
        fh_debug.setFormatter(fformatter)
        root.addHandler(fh_debug)

msggroupstats = {}

def get_all_msggroupstats():
    """
    example: msggroupstats["Church"] = [{
                "total": 44,
                "translated": 0,
                "fuzzy": 0,
                "proofread": 0,
                "code": "af",
                "language": "af"
            }, ..., {
                "total": 44,
                "translated": 44,
                "fuzzy": 0,
                "proofread": 0,
                "code": "en",
                "language": "en"
            }, ...]
    """
    global msggroupstats
    for worksheet in fortraininglib.get_worksheet_list():
        temp = fortraininglib.get_msggroupstats(worksheet)
        if temp != "":
            msggroupstats[worksheet] = temp["query"]["messagegroupstats"]

def create_summary(lang: str):
    """
    @param: lang (str): Language code for the language we want to get a summary
    """
    incomplete_translations = []
    if not msggroupstats:
        get_all_msggroupstats()
    pdfcounter = 0
    lang_result = global_result[lang]
    translated_worksheets = []
    incomplete_translations_reports = []
    #iterate through all worksheets to retrieve information about the translation status
    for worksheet in lang_result:
        allstats = msggroupstats[worksheet]
        for language_info in allstats:
            if language_info["code"] == lang:
                if language_info["translated"] < language_info["total"]:
                    incomplete_translations.append(worksheet)
                    n_trans = language_info["translated"]
                    n_fuzzy = language_info["fuzzy"]
                    n_total = language_info["total"]
                    #report translation status, 
                    # e.g. The_Three-Thirds_Process: 13+1/14 
                    # is short for 13 translated units and one fuzzy translation unit out of 14 total translation units
                    incomplete_translations_reports.append(f"{worksheet}: {n_trans}+{n_fuzzy}/{n_total}")
        worksheet_dict = lang_result[worksheet]
        #check if there exists a pdf
        try:
            temp = worksheet_dict["pdf"]
            pdfcounter += 1
            translated_worksheets.append(worksheet)
        except: 
            pass
    #create the summary string
    missing_pdf_report = ""
    total_worksheets = fortraininglib.get_worksheet_list()
    if len(translated_worksheets) < len(total_worksheets):
        missing_pdf_report = "PDF missing:"
        missing_pdfs = [worksheet for worksheet in total_worksheets if worksheet not in translated_worksheets]
        for worksheet in missing_pdfs:
            missing_pdf_report += "\n " + worksheet
    else:
        missing_pdf_report = "No missing PDFs"
    incomplete_translations_report = ""
    if len(incomplete_translations) > 0:
        incomplete_translations_report = "Incomplete translations:"
        for line in incomplete_translations_reports:
            incomplete_translations_report += "\n " + line
    else:
        incomplete_translations_report = "All translations are complete"
    language = fortraininglib.get_language_name(lang, "en")
    retstring = F"""Report for: {language} ({lang})
--------------------------------
{len(translated_worksheets)} worksheets translated and with worksheets. See https://www.4training.net/{language}\n
""" +  incomplete_translations_report +  "\n" + missing_pdf_report
    #write summary into log file in the directory logs/languagereports
    log_languagereport(lang + ".txt", retstring)
    return retstring, translated_worksheets, incomplete_translations

def log_languagereport(filename: str, text: str):
    """
    @param: filename (str): Name of the log file
    @param: text (str): Text to write into the log file
    @return: -
    """
    dirname = os.path.join(LOG_FOLDER_LOC, "languagereports")
    os.makedirs(dirname, exist_ok=True)
    with open(os.path.join(dirname, filename), "w") as f:
        f.write(text)

def total_summary():
    """
    @param: -
    @return: restring (str): summary, e.g.
    Total report:
    - Finished worksheet translations with PDF: 485
    - Translation finished, PDF missing: 134
    - Unfinished translations (ignored): 89
    """
    #create list with all language codes
    langlist = global_result.keys()

    everything_top_counter = 0
    translated_without_pdf_counter = 0
    incomplete_translation_counter = 0

    for lang in langlist:
        #translated worksheets: with pdf, but no completeness required
        _, translated_worksheets, incomplete_translations = create_summary(lang) 
        #incomplete_translations: some translation units are fuzzy or not translated
        everything_top = [worksheet for worksheet in translated_worksheets if worksheet not in incomplete_translations]
        #completely translated, but no pdf
        translated_without_pdf = [worksheet for worksheet in global_result[lang] if worksheet not in incomplete_translations and worksheet not in translated_worksheets]
        everything_top_counter += len(everything_top)
        translated_without_pdf_counter += len(translated_without_pdf)
        incomplete_translation_counter += len(incomplete_translations)
    
    retstring = f"""Total report:
- Finished worksheet translations with PDF: {everything_top_counter}
- Translation finished, PDF missing: {translated_without_pdf_counter}
- Unfinished translations (ignored): {incomplete_translation_counter}"""

    log_languagereport("summary.txt", retstring)

    return retstring

if __name__ == "__main__":
    args = parse_arguments()
    set_loglevel(args['loglevel'])
    if args['rewrite_all']:
        logger.info('Parameter --rewrite-all is set, rewriting all language information pages')
        rewrite_all = True
    if args['lang']:
        logger.info(F"Parameter lang is set, limiting processing to language {args['lang']}")
        global_only_lang = args['lang']

    for page in fortraininglib.get_worksheet_list():
        process_page(page)

    for lang in global_result:
        if lang != 'en':
            process_language(lang)
    #with open("global_result.json", "w") as f:
    #    f.write(json.dumps((global_result)))
    #with open("global_result.json", "r") as f:
    #    global_result = dict(json.load(f))
    
    total_summary()