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
       To make that easier, a JSON representation is saved for every language, e.g. https://www.4training.net/4training:de.json
       The script will compare its results to the JSON and update the JSON and the language overview page when necessary
    3. Post-processing (TODO: not yet implemented)
       With information like "we now have a Hindi translation of the Prayer worksheet" we can do helpful things, e.g.
       - update a zip file with all Hindi worksheets
       - send an email notification to all interested in the Hindi resources

Command line options:
    --lang LANGUAGECODE: only look at this one language (significantly faster)
    -l, --loglevel: change logging level (standard: warning; other options: debug, info)
    --rewrite-all: Rewrite all language information pages

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

"""

import os
import re
import sys
import logging
import json
import urllib
import datetime
import argparse # For CLI arguments
import configparser
from typing import Optional, Dict, List, Any
import pywikibot
from pywikibot.exceptions import InconsistentTitleError
from uno import Bool

import fortraininglib
from fortraininglib import TranslationProgress

# Result dictionary: contains information about existing translations and the downloadable file names if existing
""" TODO delete this
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
"""

class FileInfo:
    """
    Holds information on one file that is available on the website
    This shouldn't be modified after creation (is there a way to enforce that?)
    """
    __slots__ = ['file_type', 'url', 'timestamp']
    def __init__(self, file_type: str, url: str, timestamp: datetime.datetime):
        self.file_type = file_type
        self.url: str = url
        self.timestamp: datetime.datetime = timestamp

    def __str__(self):
        return f"{self.file_type} {self.url} {self.timestamp.isoformat()}"

class WorksheetInfo:
    """Holds information on one worksheet in one specific language
    Only for worksheets that are at least partially translated
    """
    __slots__ = ['_name', '_language', '_files', 'title', 'progress']

    def __init__(self, en_name: str, language: str, title: str, progress: TranslationProgress):
        """
        @param en_name: English name of the worksheet
        @param language: language code
        @param title: translated worksheet title
        @param progress: how much is already translated"""
#        self._en_name: str = en_name
#        self._language: str = language
        self._files: Dict[str, FileInfo] = {}
        self.title: str = title
        self.progress: TranslationProgress = progress

    def add_file_info(self, file_type: str, url: str = None, timestamp: str = None,
                      file_info: pywikibot.page.FileInfo = None) -> Optional[FileInfo]:
        """Add information about another file associated with this worksheet
        Either give url and timestamp or file_info
        This will log on errors but shouldn't raise exceptions
        @return FileInfo or None if it wasn't successful
        """
        new_file_info = None
        logger = logging.getLogger('4training.resourcesbot.worksheetinfo')
        if url is not None and timestamp is not None:
            if isinstance(timestamp, str):
                try:
                    timestamp = timestamp.replace('Z', '+00:00')    # we want to support this format as well
                    new_file_info = FileInfo(file_type, url, datetime.datetime.fromisoformat(timestamp))
                except (ValueError, TypeError):
                    logger.warning("Couldn't parse timestamp {timestamp}. add_file_info() failed.")
            else:
                logger.warning("add_file_info() failed: timestamp is not of type str.")
        elif file_info is not None:
            new_file_info = FileInfo(file_type, urllib.parse.unquote(file_info.url), file_info.timestamp)
        if new_file_info is not None:
            self._files[file_type] = new_file_info
        return new_file_info

    def get_file_infos(self) -> Dict[str, FileInfo]:
        """Returns all available files associated with this worksheet"""
        return self._files

    def has_file_type(self, file_type: str) -> Bool:
        """Does the worksheet have a file for download (e.g. "pdf")?"""
        return file_type in self._files

    def get_file_type_info(self, file_type: str) -> Optional[FileInfo]:
        """Returns FileInfo of specified type (e.g. "pdf"), None if not existing"""
        if file_type in self._files:
            return self._files[file_type]
        return None


class LanguageInfo:
    """Holds information on all available worksheets in one specific language"""
    __slots__ = '_language_code', 'worksheets'

    def __init__(self, language_code: str):
        self._language_code: str = language_code
        self.worksheets: Dict[str, WorksheetInfo] = {}

    def deserialize(self, obj):
        """Reads a JSON object of a data structure into this LanguageInfo object
        This is a top-down approach

        TODO: The JSON data structure isn't very good - improve it to make bottom-up approach possible
        Then we could use json.JSONDecoder() which would be a bit more elegant
        For that WorksheetInfo and FileInfo should also be well serializable / deserializable
        """
        logger = logging.getLogger('4training.resourcesbot.languageinfo')
        if isinstance(obj, Dict):
            for worksheet, details in obj.items():
                if isinstance(worksheet, str) and isinstance(details, Dict):
                    if "title" in details:
                        worksheet_info = WorksheetInfo(worksheet, self._language_code, details['title'], None)
                        for file_type in fortraininglib.get_file_types():
                            if file_type in details:
                                worksheet_info.add_file_info(file_type, url=details[file_type],
                                    timestamp=(details[file_type + '-timestamp']))

                        self.add_worksheet_info(worksheet, worksheet_info)
                    else:
                         logger.warning(f"No title attribute in {worksheet} object, skipping.")
                else:
                    logger.warning("Unexpected data structure while trying to deserialize LanguageInfo object.")
        else:
            logger.warning("Unexpected data structure. Couldn't deserialize LanguageInfo object.")

    def add_worksheet_info(self, name: str, worksheet_info: WorksheetInfo):
        self.worksheets[name] = worksheet_info

    def has_worksheet(self, name: str) -> Bool:
        return name in self.worksheets

    def get_worksheet(self, name: str) -> Optional[WorksheetInfo]:
        if name in self.worksheets:
            return self.worksheets[name]
        return None

    def compare(self, other) -> bool:
        """
        Compares to another LanguageInfo object: have there been relevant changes / updates?
        In other words: Does the list of available training resources for this language need to be re-written?

        Only worksheets with PDF are shown in the lists of available training resources,
        that's why not all changes are considered relevant
        @return true if list with available training resources needs to be re-written
        """
        needs_rewrite = False
        logger = logging.getLogger('4training.resourcesbot.languageinfo')
        if not isinstance(other, LanguageInfo):
            logger.warning("Comparison failed: expected LanguageInfo object.")
            return False
        for new_worksheet, new_worksheet_info in other.worksheets.items():
            if new_worksheet in self.worksheets:
                if (new_worksheet_info.has_file_type('pdf') and not self.worksheets[new_worksheet].has_file_type('pdf')):
                    logger.info(f"Comparison result: Added PDF for {new_worksheet}")
                    needs_rewrite = True
                if (new_worksheet_info.has_file_type('odt') and not self.worksheets[new_worksheet].has_file_type('odt')):
                    logger.info(f"Comparison result: Added ODT for {new_worksheet}")
                    # This is relevant if we have a PDF, otherwise it's anyway not listed in the available training resources
                    if not needs_rewrite:
                        needs_rewrite = self.worksheets[new_worksheet].has_file_type('pdf')
                if (not new_worksheet_info.has_file_type('pdf') and self.worksheets[new_worksheet].has_file_type('pdf')):
                    logger.warning(f"Comparison inconsistency for worksheet {new_worksheet}: PDF vanished.")
                    needs_rewrite = True
                if (not new_worksheet_info.has_file_type('odt') and self.worksheets[new_worksheet].has_file_type('odt')):
                    logger.warning(f"Comparison inconsistency for worksheet {new_worksheet}: ODT vanished.")
                    needs_rewrite = True
            else:
                logger.info(f"Comparison result: Added worksheet {new_worksheet}")
                if new_worksheet_info.has_file_type('pdf'):
                    needs_rewrite = True
        for worksheet in self.worksheets:
            if worksheet not in other.worksheets.keys():
                logger.warning(f"Comparison inconsistency: Worksheet {worksheet} vanished.")
                needs_rewrite = True

        return needs_rewrite

    def list_worksheets_with_missing_pdf(self) -> List[str]:
        """ Returns a list of worksheets which are translated but are missing the PDF
        """
        return [worksheet for worksheet in self.worksheets if not self.worksheets[worksheet].has_file_type('pdf')]

class LanguageInfoEncoder(json.JSONEncoder):
    """serialize the data structure stored in ResourcesBot._result
    TODO: This currently uses the legacy dictionary data structure that was stored in global_result before,
    think about it and define a better structure?
    """
    def default(self, obj):
        if isinstance(obj, LanguageInfo):
            return obj.worksheets
        if isinstance(obj, WorksheetInfo):
            worksheet_map = {}
            worksheet_map['title'] = obj.title
            for file_type, file_info in obj.get_file_infos().items():
                worksheet_map[f"{file_type}-timestamp"] = file_info.timestamp.isoformat()
                worksheet_map[file_type] = file_info.url
            return worksheet_map
        if isinstance(obj, pywikibot.Timestamp):
            return obj.isoformat()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

class ResourcesBot():
    """Contains all the logic of our bot"""
    # TODO subclass pywikibot.SingleSiteBot

    def __init__(self, limit_to_lang:Optional[str]=None, rewrite_all:Bool=False, loglevel:Optional[str]=None):
        """
        @param limit_to_lang: limit processing to one language (string with a language code)
        @param rewrite_all: Rewrite all language information less, regardless if we find changes or not
        @param loglevel: define how much logging output should be written
        """
        # read-only list of download file types
        self._file_types = fortraininglib.get_file_types()
        # Read the configuration from config.ini in the same directory
        self._config = configparser.ConfigParser()
        self._config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')
        self.logger = logging.getLogger('4training.resourcesbot')
        self.set_loglevel(loglevel)
        if not self._config.has_option("resourcesbot", "username") or \
            not self._config.has_option("resourcesbot", "password"):
            self.logger.warning("Missing user name and/or password in configuration. Won't mark pages for translation.")

        self.site: pywikibot.site.APISite = pywikibot.Site()
        # That shouldn't be necessary but for some reasons the script sometimes failed with WARNING from pywikibot:
        # "No user is logged in on site 4training:en" -> use this as a workaround and test with global_site.logged_in()
        self.site.login()
        self._limit_to_lang = limit_to_lang
        self._rewrite_all = rewrite_all
        if self._limit_to_lang is not None:
            self.logger.info(f"Parameter lang is set, limiting processing to language {limit_to_lang}")
        if self._rewrite_all:
            self.logger.info('Parameter --rewrite-all is set, rewriting all language information pages')

        # e.g. str(self._translation_progress["Prayer"]["de"]) == "59+0/59"
        # TODO get rid of this - it's already stored in class WorksheetInfo
        self._translation_progress: Dict[str, Dict[str, TranslationProgress]] = {}

        # Stores details on all other languages in a dictionary language code -> information about all worksheets in that language
        self._result: Dict[str, LanguageInfo] = {}

    def run(self):
        """
        Start the bot
        """
        for page in fortraininglib.get_worksheet_list():
            self.process_page(page)

        if not self.site.logged_in():
            self.logger.error("We're not logged in! Won't be able to write updated language information pages. Exiting now.")
            self.site.getuserinfo()
            self.logger.warning(f"userinfo: {self.site.userinfo}")
            sys.exit(2)

        for lang in self._result:
            if lang != 'en':
                self.process_language(lang)

        if self._limit_to_lang is not None:
            self.create_summary(self._limit_to_lang)
        else:
            self.total_summary()

    def process_page(self, page: str):
        """
        Go through one worksheet, check all existing translations and gather information into self._result
        @param: page (str): Name of the page
        """
        p = pywikibot.Page(self.site, page)
        if not p.exists():
            self.logger.warning(f'Warning: page {page} does not exist!')
            return
        # finding out the name of the English downloadable files (originals)
        en_file_details: Dict[str, Dict[str, Any]] = {}
        for file_type in self._file_types:
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
            en_file_details[file_type] = {}
            en_file_details[file_type]['number'] = translation_section_identifier
            en_file_details[file_type]['name'] = translation_section_name
        self.logger.info(f"Processing page {page}. PDF name: {en_file_details['pdf']['name']} "
                         f"is in translation unit {str(en_file_details['pdf']['number'])}")

        # Look up all existing translations of this worksheet
        available_translations = fortraininglib.list_page_translations(page, include_unfinished=True)
        self._translation_progress[page] = available_translations
        finished_translations = []
        for language, progress in available_translations.items():
            if progress.is_unfinished():
                self.logger.info(f"Ignoring translation {page}/{language} - ({progress} translation units translated)")
            else:
                finished_translations.append(language)
                if progress.is_incomplete():
                    self.logger.warning(f"Incomplete translation {page}/{language} - {progress}")

        if self._limit_to_lang is not None:
            # We could speed this up a bit by finding a different API call that isn't checking all translations
            # but only looks at the translation progress for this language. For now it's okay
            if self._limit_to_lang in finished_translations:
                finished_translations = [self._limit_to_lang]
            else:
                finished_translations = []
        if 'en' in finished_translations:
            finished_translations.remove('en')
        self.logger.info(f"This worksheet is translated into: {str(finished_translations)}")

        # now let's retrieve the translated file names
        for lang in finished_translations:
            translated_title = fortraininglib.get_translated_title(page, lang)
            if translated_title is None:  # apparently this translation doesn't exist
                self.logger.warning(f"Language {lang}: Title of {page} not translated, skipping.")
                continue
            page_info: WorksheetInfo = WorksheetInfo(page, lang, translated_title, available_translations[lang])
            for file_type in en_file_details:
                if en_file_details[file_type]['number'] == 0:    # in English original this is not existing, skip it
                    continue
                translation = fortraininglib.get_translated_unit(page, lang, en_file_details[file_type]['number'])
                self.logger.debug(f"{page}/{en_file_details[file_type]['number']}/{lang} is {translation}")
                if translation is None:
                    self.logger.warning(f"Warning: translation {page}/{en_file_details[file_type]['number']}/{lang} "
                                f"(for file {file_type}) does not exist!")
                    # TODO fill it with "-"
                elif (translation == '-') or (translation == '.'):
                    self.logger.warning(f"Warning: translation {page}/{en_file_details[file_type]['number']}/{lang} "
                                f"(for file {file_type}) is placeholder: {translation}")
                    # TODO fill it with "-"
                elif translation == en_file_details[file_type]['name']:
                    self.logger.warning(f"Warning: translation {page}/{en_file_details[file_type]['number']}/{lang} "
                                f"(for file {file_type}) is identical with English original")
                    # TODO fill it with "-"
                else:
                    # We have the name of the translated file, check if it actually exists
                    try:
                        file_page = pywikibot.FilePage(self.site, translation)
                        if file_page.exists():
                            new_file_info = page_info.add_file_info(file_type, file_info=file_page.latest_file_info)
                            self.logger.debug(new_file_info)
                            if new_file_info is None:
                                self.logger.warning(f"Language {lang}, page {page}: Couldn't add file of type {file_type}")
                        else:
                            self.logger.info(f"Language {lang}, page {page}: File {translation} does not seem to exist")
                    except pywikibot.exceptions.Error as err:
                        self.logger.warning(f"Exception thrown for {file_type} file: {err}")

            if lang not in self._result:
                self._result[lang] = LanguageInfo(lang)
            self._result[lang].add_worksheet_info(page, page_info)
            self.logger.debug(self._result)


    def write_available_resources(self, lang: str):
        """
        TODO Some refactoring: Create a method LanguageInfo.create_mediawiki() that takes the code for putting the list together
        Writes the list of available training resources for this language
        Reads from self._result
        Output should look like the following line:
        * [[God's_Story_(five_fingers)/de|{{int:sidebar-godsstory-fivefingers}}]] [[File:pdficon_small.png|link={{filepath:Gottes_Geschichte_(fünf_Finger).pdf}}]] [[File:odticon_small.png|link={{filepath:Gottes_Geschichte_(fünf_Finger).odt}}]]
        """
        self.logger.debug(f"Writing list of available resources in {lang}...")
        if lang not in self._result:
            self.logger.warning(f"Internal error: {lang} not in _result. Not doing anything for this language.")
            return

        # Creating the mediawiki string for the list of available training resources
        content = ''
        for worksheet, worksheet_info in self._result[lang].worksheets.items():
            if not worksheet_info.has_file_type('pdf'):
                # Only show worksheets where we have a PDF file in the list
                self.logger.warning(f"Language {lang}: worksheet {worksheet} doesn't have PDF, not including in list.")
                continue

            content += f"* [[{worksheet}/{lang}|"
            content += "{{int:" + fortraininglib.title_to_message(worksheet) + "}}]]"
            if worksheet_info.has_file_type('pdf'):
                pdfname = worksheet_info.get_file_type_info('pdf').url
                pos = pdfname.rfind('/')
                if pos > -1:
                    pdfname = pdfname[pos+1:]
                else:
                    self.logger.warning(f"Couldn't find / in {pdfname}")
                content += " [[File:pdficon_small.png|link={{filepath:"
                content += pdfname
                content += "}}]]"

            if worksheet_info.has_file_type('odt'):
                odtname = worksheet_info.get_file_type_info('odt').url
                pos = odtname.rfind('/')
                if pos > -1:
                    odtname = odtname[pos+1:]
                else:
                    self.logger.warning(f"Couldn't find / in {odtname}")
                content += " [[File:odticon_small.png|link={{filepath:"
                content += odtname
                content += "}}]]"
            content += "\n"
        self.logger.debug(content)

        # Saving this to the language information page, e.g. https://www.4training.net/German
        language = fortraininglib.get_language_name(lang, 'en')
        if language is None:
            self.logger.warning(f"Error while trying to get language name of {lang}! Skipping")
            return
        page = pywikibot.Page(self.site, language)
        if not page.exists():
            self.logger.warning(f"Language information page {language} doesn't exist!")
            return
        if page.isRedirectPage():
            self.logger.info(f"Language information page {language} is a redirect. Following the redirect...")
            page = page.getRedirectTarget()
            if not page.exists():
                self.logger.warning(f"Redirect target for language {language} doesn't exist!")
                return

        # Finding the exact positions of the existing list so that we know what to replace
        language_re = language.replace('(', r'\(')    # in case language name contains brackets, we need to escape them
        language_re = language_re.replace(')', r'\)') # Example would be language Turkish (secular)
        match = re.search(f"Available training resources in {language_re}\\s*?</translate>\\s*?==", page.text)
        if not match:
            self.logger.warning(f"Didn't find available training resources list in page {language}! Doing nothing.")
            self.logger.warning(f"Available training resources in {language_re}\\s*?</translate>\\s*?==")
            self.logger.warning(page.text)
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
                    self.logger.info(f"Looks like there is another list later in page {language}. Ignoring it.")
                    break
            list_end = m.end()
            self.logger.debug(f"Matching line: start={m.start()}, end={m.end()}, {m.group(0)}")
        if (list_start == 0) or (list_end == 0):
            self.logger.warning(f"Couldn't find list entries of available training resources in {language}! Doing nothing.")
            return
        self.logger.debug(f"Found existing list of available training resources @{list_start}-{list_end}. Replacing...")
        new_page_content = page.text[0:list_start] + content + page.text[list_end+1:]
        self.logger.debug(new_page_content)
        page.text = new_page_content
        page.save("Updated list of available training resources") # TODO write human-readable changes here in the save message
        user_name = self._config.get("resourcesbot", "username")
        password = self._config.get("resourcesbot", "password")
        if user_name != '' and password != '':
            fortraininglib.mark_for_translation(page.title(), user_name, password)
            self.logger.info(f"Updated language information page {language} and marked it for translation.")
        else:
            self.logger.info(f"Updated language information page {language}. Couldn't mark it for translation.")

    def process_language(self, lang: str):
        """
        Process the specified language, re-writing the list of available training resources if necessary
            - Reads and compares with the last list of available training resources
        @param lang language code
        """
        self.logger.debug(f"Processing language {lang}...")
        if lang not in self._result:
            self.logger.warning(f"Internal error: {lang} not in _result. Not doing anything for this language.")
            return

        rewrite_language: Bool = self._rewrite_all
        rewrite_json: Bool = self._rewrite_all
        # Reading data structure from our mediawiki, stored in e.g. https://www.4training.net/4training:de.json
        page = pywikibot.Page(self.site, f"4training:{lang}.json")
        if not page.exists():
            # There doesn't seem to be any information on this language stored yet!
            self.logger.warning(f"{page.full_url()} doesn't seem to exist yet. Creating...")
            page.text = LanguageInfoEncoder().encode(self._result[lang])
            page.save("Created JSON data structure")
            rewrite_json = False
            rewrite_language = True
        else:
            # compare and find out if new worksheets have been added
            language_info: LanguageInfo = LanguageInfo(lang)
            language_info.deserialize(json.loads(page.text))
            self.logger.debug(language_info)
            if LanguageInfoEncoder().encode(self._result[lang]) != page.text:
                rewrite_json = True
                rewrite_language = self._result[lang].compare(language_info)
        if rewrite_json:
            # Write the updated JSON structure
            page.text = LanguageInfoEncoder().encode(self._result[lang])
            page.save("Updated JSON data structure")
            self.logger.info(f"Updated {lang}.json")
        if rewrite_language:
            self.logger.info(f"List of available training resources in language {lang} needs to be re-written.")
            self.write_available_resources(lang)
        else:
            self.logger.info(f"List of available training resources in language {lang} doesn't need to be re-written.")


    def set_loglevel(self, loglevel=None):
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
        self.logger.setLevel(logging.DEBUG)  # This is necessary so that debug messages go to debuglogfile
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.WARNING)
        if loglevel is not None:
            numeric_level = getattr(logging, loglevel.upper(), None)
            if not isinstance(numeric_level, int):
                raise ValueError(f'Invalid log level: {loglevel}')
            sh.setLevel(numeric_level)
        fformatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
        sh.setFormatter(fformatter)
        root.addHandler(sh)

        log_path = self._config.get('Paths', 'logs', fallback='')
        if log_path == '':
            self.logger.warning('No log directory specified in configuration. Using current working directory')
        # Logging output to files with different verbosity
        if self._config.has_option("resourcesbot", "logfile"):
            fh = logging.FileHandler(f"{log_path}{self._config['resourcesbot']['logfile']}")
            fh.setLevel(logging.WARNING)
            fh.setFormatter(fformatter)
            root.addHandler(fh)
        if self._config.has_option("resourcesbot", "infologfile"):
            fh_info = logging.FileHandler(f"{log_path}{self._config['resourcesbot']['infologfile']}")
            fh_info.setLevel(logging.INFO)
            fh_info.setFormatter(fformatter)
            root.addHandler(fh_info)
        if self._config.has_option("resourcesbot", "debuglogfile"):
            fh_debug = logging.FileHandler(f"{log_path}{self._config['resourcesbot']['debuglogfile']}")
            fh_debug.setLevel(logging.DEBUG)
            fh_debug.setFormatter(fformatter)
            root.addHandler(fh_debug)


    def create_summary(self, lang: str):
        """
        @param: lang (str): Language code for the language we want to get a summary
        @return tuple with 2 values: number of translated worksheets, number of incomplete worksheets
        """
        incomplete_translations = []
        pdfcounter = 0
        if lang not in self._result:
            return 0, 0
        translated_worksheets = []
        incomplete_translations_reports = []
        #iterate through all worksheets to retrieve information about the translation status
        for worksheet in self._translation_progress:
            if lang in self._translation_progress[worksheet]:
                progress = self._translation_progress[worksheet][lang]
                if progress.translated < progress.total:
                    incomplete_translations.append(worksheet)
                    incomplete_translations_reports.append(f"{worksheet}: {progress}")
                if self._result[lang].has_worksheet(worksheet):
                    if self._result[lang].get_worksheet(worksheet).has_file_type("pdf"):
                        #check if there exists a pdf
                        pdfcounter += 1
                        translated_worksheets.append(worksheet)
        #create the summary string
        missing_pdf_report = ""
        total_worksheets = fortraininglib.get_worksheet_list()
        if len(translated_worksheets) < len(total_worksheets):
            missing_pdf_report = "PDF missing:"
            for worksheet in self._result[lang].list_worksheets_with_missing_pdf():
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
        report = f"""Report for: {language} ({lang})
--------------------------------
{len(translated_worksheets)} worksheets translated and with worksheets. See https://www.4training.net/{language}\n
""" +  incomplete_translations_report +  "\n" + missing_pdf_report
        self.log_languagereport(f"{lang}.txt", report)
        return translated_worksheets, incomplete_translations


    def log_languagereport(self, filename: str, text: str):
        """
        @param: filename (str): Name of the log file
        @param: text (str): Text to write into the log file
        @return: -
        """
        if self._config.has_option("Paths", "languagereports"):
            dirname = os.path.join(self._config['Paths']['languagereports'])
            os.makedirs(dirname, exist_ok=True)
            with open(os.path.join(dirname, filename), "w") as f:
                f.write(text)
        else:
            self.logger.warning(f"Option languagereports not found in section [Paths] in config.ini. Not writing {filename}.")


    def total_summary(self):
        """
        Creates and writes the reports for individual languages
        and afterwards writes a total summary, something like
        Total report:
        - Finished worksheet translations with PDF: 485
        - Translation finished, PDF missing: 134
        - Unfinished translations (ignored): 89
        """
        everything_top_counter = 0
        translated_without_pdf_counter = 0
        incomplete_translation_counter = 0

        for lang in self._result:
            # translated worksheets: with pdf, but no completeness required
            translated_worksheets, incomplete_translations = self.create_summary(lang)
            # incomplete_translations: some translation units are fuzzy or not translated
            everything_top = [worksheet for worksheet in translated_worksheets if worksheet not in incomplete_translations]
            # completely translated, but no pdf
            translated_without_pdf = [worksheet for worksheet in self._result[lang].worksheets if worksheet not in incomplete_translations and worksheet not in translated_worksheets]
            everything_top_counter += len(everything_top)
            translated_without_pdf_counter += len(translated_without_pdf)
            incomplete_translation_counter += len(incomplete_translations)

        report = f"""Total report:
    - Finished worksheet translations with PDF: {everything_top_counter}
    - Translation finished, PDF missing: {translated_without_pdf_counter}
    - Unfinished translations (ignored): {incomplete_translation_counter}"""

        self.log_languagereport("summary.txt", report)


def parse_arguments() -> ResourcesBot:
    """
    Parses command-line arguments.
    @return: ResourcesBot instance
    """
    msg: str = 'Update list of available training resources in the language information pages'
    epi_msg: str = 'Refer https://datahub.io/core/language-codes/r/0.html for language codes.'
    log_levels: list = ['debug', 'info', 'warning', 'error', 'critical']

    parser = argparse.ArgumentParser(prog='python3 pwb.py resourcesbot', description=msg, epilog=epi_msg)
    parser.add_argument('--lang', help='run script for only one language')
    parser.add_argument('-l', '--loglevel', choices=log_levels, help='set loglevel for the script')
    parser.add_argument('--rewrite-all', action='store_true', help='rewrites all overview lists, also if there have been no changes')

    args = parser.parse_args()
    limit_to_lang = None
    if args.lang is not None:
        limit_to_lang = str(args.lang)
    return ResourcesBot(limit_to_lang=limit_to_lang, rewrite_all=args.rewrite_all, loglevel=args.loglevel)

if __name__ == "__main__":
    resourcesbot = parse_arguments()
    resourcesbot.run()
