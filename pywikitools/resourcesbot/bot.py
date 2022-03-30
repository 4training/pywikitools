import os
import re
import sys
import logging
import json
from configparser import ConfigParser
from typing import List, Optional, Dict, Tuple
import pywikibot

from pywikitools import fortraininglib
from pywikitools.fortraininglib import TranslationProgress
from pywikitools.resourcesbot.changes import ChangeLog
from pywikitools.resourcesbot.consistency_checks import ConsistencyCheck
from pywikitools.resourcesbot.export_html import ExportHTML
from pywikitools.resourcesbot.export_repository import ExportRepository
from pywikitools.resourcesbot.write_lists import WriteList
from pywikitools.resourcesbot.data_structures import WorksheetInfo, LanguageInfo, DataStructureEncoder, json_decode


class ResourcesBot:
    """Contains all the logic of our bot"""

    def __init__(self, config: ConfigParser, limit_to_lang: Optional[str] = None, rewrite_all: bool = False,
                 read_from_cache: bool = False, loglevel: Optional[str] = None):
        """
        @param limit_to_lang: limit processing to one language (string with a language code)
        @param rewrite_all: Rewrite all language information less, regardless if we find changes or not
        @param read_from_cache: Read from json cache from the mediawiki system (don't query individual worksheets)
        @param loglevel: define how much logging output should be written
        """
        # read-only list of download file types
        self._file_types = fortraininglib.get_file_types()
        # Read the configuration from config.ini in the same directory
        self._config = config
        self.logger = logging.getLogger('pywikitools.resourcesbot')
        self.set_loglevel(loglevel)
        self.site: pywikibot.site.APISite = pywikibot.Site()
        self._limit_to_lang: Optional[str] = limit_to_lang
        self._read_from_cache: bool = read_from_cache
        self._rewrite_all: bool = rewrite_all
        if self._limit_to_lang is not None:
            self.logger.info(f"Parameter lang is set, limiting processing to language {limit_to_lang}")
        if self._read_from_cache:
            self.logger.info("Parameter --read-from-cache is set, reading from JSON...")
        if self._rewrite_all:
            self.logger.info('Parameter --rewrite-all is set, rewriting all language information pages')

        # e.g. str(self._translation_progress["Prayer"]["de"]) == "59+0/59"
        # TODO get rid of this - it's already stored in class WorksheetInfo
        self._translation_progress: Dict[str, Dict[str, TranslationProgress]] = {}

        # Stores details on all languages: language code -> information about all worksheets in that language
        self._result: Dict[str, LanguageInfo] = {}

        # Changes since the last run (will be filled after gathering of all information is done)
        self._changelog: Dict[str, ChangeLog] = {}

    def run(self):
        if self._read_from_cache:
            try:
                language_list: List[str] = []   # List of languages to be read from cache
                if self._limit_to_lang is None:
                    page = pywikibot.Page(self.site, "4training:languages.json")
                    if not page.exists():
                        raise RuntimeError(f"Couldn't load list of languages from 4training:languages.json")
                    language_list = json.loads(page.text)
                    assert isinstance(language_list, list)
                else:
                    language_list.append(self._limit_to_lang)

                for lang in language_list:      # Now we read the details for each language
                    self.logger.info(f"Reading details for language {lang} from cache...")
                    page = pywikibot.Page(self.site, f"4training:{lang}.json")
                    if not page.exists():
                        raise RuntimeError(f"Couldn't load from cache for language {lang}")
                    language_info = json.loads(page.text, object_hook=json_decode)
                    assert isinstance(language_info, LanguageInfo)
                    assert language_info.language_code == lang
                    self._result[lang] = language_info
            except AssertionError:
                raise RuntimeError(f"Unexpected error while parsing JSON data from cache.")

        else:
            self._result["en"] = LanguageInfo("en")
            for worksheet in fortraininglib.get_worksheet_list():
                # Gather all data (this takes quite some time!)
                self._query_translations(worksheet)

        # That shouldn't be necessary but for some reasons the script sometimes failed with WARNING from pywikibot:
        # "No user is logged in on site 4training:en" -> better check and try to log in if necessary
        if not self.site.logged_in():
            self.logger.warning("We're not logged in. Trying to log in...")
            self.site.login()
            if not self.site.logged_in():
                self.logger.error("Login with pywikibot failed! Exiting now.")
                self.site.getuserinfo()
                self.logger.warning(f"userinfo: {self.site.userinfo}")
                sys.exit(2)

        if not self._read_from_cache:   # Find out what has been changed since our last run
            for lang, language_info in self._result.items():
                self._changelog[lang] = self._sync_and_compare(language_info)
            if self._limit_to_lang is None:
                self._save_languages_list()
                self._save_number_of_languages()        # TODO move this to a GlobalPostProcessor

        # Run all LanguagePostProcessors
        write_list = WriteList(self.site, self._config.get("resourcesbot", "username", fallback=""),
            self._config.get("resourcesbot", "password", fallback=""), self._rewrite_all)
        consistency_check = ConsistencyCheck()
        export_html = ExportHTML(self._config.get("Paths", "htmlexport", fallback=""), self._rewrite_all)
        export_repository = ExportRepository(self._config.get("Paths", "htmlexport", fallback=""))
        for lang in self._result:
            change_log = self._changelog[lang] if not self._read_from_cache else ChangeLog()
            consistency_check.run(self._result[lang], ChangeLog())
            export_html.run(self._result[lang], change_log)
            export_repository.run(self._result[lang], change_log)
            write_list.run(self._result[lang], change_log)

        # Now run all GlobalPostProcessors
        # TODO move the following into a GlobalPostProcessor
        if self._limit_to_lang is not None:
            self.create_summary(self._limit_to_lang)
        else:
            self.total_summary()

    def get_english_version(self, page_source: str) -> Tuple[str, int]:
        """
        Extract version of an English worksheet
        @return Tuple of version string and the number of the translation unit where it is stored
        """
        handler = re.search(r"\{\{Version\|<translate>*?<!--T:(\d+)-->\s*([^<]+)</translate>", page_source)
        if handler:
            return (handler.group(2), int(handler.group(1)))
        self.logger.warning("Couldn't retrieve version from English worksheet!")
        return ("", 0)

    def _add_file_type(self, worksheet: WorksheetInfo, file_type: str, file_name: str, unit: Optional[int] = None):
        try:
            file_page = pywikibot.FilePage(self.site, file_name)
            if file_page.exists():
                worksheet.add_file_info(file_type=file_type, from_pywikibot=file_page.latest_file_info,
                                        unit=unit)
            else:
                self.logger.warning(f"Page {worksheet.page}/{worksheet.language_code}: Couldn't find {file_name}.")
        except pywikibot.exceptions.Error as err:
            self.logger.warning(f"Exception thrown for {file_type} file: {err}")

    def _add_english_file_infos(self, page_source: str, worksheet: WorksheetInfo):
        """
        Finds out the names of the English downloadable files (originals)
        and adds them to worksheet
        """
        for file_type in self._file_types:
            handler = re.search(r"\{\{" + file_type.capitalize() +
                                r"Download\|<translate>*?<!--T:(\d+)-->\s*([^<]+)</translate>", page_source)
            if handler:
                self._add_file_type(worksheet, file_type, handler.group(2), int(handler.group(1)))


    def _query_translations(self, page: str):
        """
        Go through one worksheet, check all existing translations and gather information into self._result
        @param: page: Name of the worksheet
        """
        # This is querying more data than necessary when self._limit_to_lang is set. But to save time we'd need to find
        # a different API call that is only requesting progress for one particular language... for now it's okay
        available_translations = fortraininglib.list_page_translations(page, include_unfinished=True)
        english_title = fortraininglib.get_translated_title(page, "en")
        page_source = fortraininglib.get_page_source(page)
        if english_title is None or page_source is None:
            self.logger.error(f"Couldn't get English page {page}, skipping.")
            return
        version, version_unit = self.get_english_version(page_source)
        english_page_info: WorksheetInfo = WorksheetInfo(page, "en", english_title, available_translations["en"],
                                                         version, version_unit)
        self._add_english_file_infos(page_source, english_page_info)
        self._result["en"].add_worksheet_info(page, english_page_info)
        self._translation_progress[page] = available_translations   # TODO remove this

        finished_translations = []
        for language, progress in available_translations.items():
            if (self._limit_to_lang is not None) and (self._limit_to_lang != language):
                continue
            if language == "en":    # We only want translations in finished_translations
                continue
            if progress.is_unfinished():
                self.logger.info(f"Ignoring translation {page}/{language} - ({progress} translation units translated)")
            else:
                finished_translations.append(language)
                if progress.is_incomplete():
                    self.logger.warning(f"Incomplete translation {page}/{language} - {progress}")
        self.logger.info(f"This worksheet is translated into: {str(finished_translations)}")

        # now let's retrieve the translated file names
        for lang in finished_translations:
            translated_title = fortraininglib.get_translated_title(page, lang)
            if translated_title is None:  # apparently this translation doesn't exist
                self.logger.warning(f"Language {lang}: Title of {page} not translated, skipping.")
                continue
            translated_version = fortraininglib.get_translated_unit(page, lang, version_unit)
            if translated_version is None:
                self.logger.warning(f"Language {lang}: Version of {page} not translated, skipping.")
                translated_version = ""
            elif translated_version != version:
                self.logger.warning(f"Language {lang}: {translated_title} has version {translated_version}"
                                    f" - {english_title} has version {version}")

            page_info = WorksheetInfo(page, lang, translated_title, available_translations[lang], translated_version)
            for file_type, file_info in english_page_info.get_file_infos().items():
                assert file_info.translation_unit is not None   # TODO exception documentation
                translation = fortraininglib.get_translated_unit(page, lang, file_info.translation_unit)
#                self.logger.debug(f"{page}/{en_file_details[file_type]['number']}/{lang} is {translation}")
                if translation is None:
                    self.logger.warning(f"Warning: translation {page}/{file_info.translation_unit}/{lang} "
                                        f"(for file {file_type}) does not exist!")
                    # TODO fill it with "-"
                elif (translation == '-') or (translation == '.'):
                    self.logger.warning(f"Warning: translation {page}/{file_info.translation_unit}/{lang} "
                                f"(for file {file_type}) is placeholder: {translation}")
                    # TODO fill it with "-"
                elif translation == file_info.get_file_name():
                    self.logger.warning(f"Warning: translation {page}/{file_info.translation_unit}/{lang} "
                                        f"(for file {file_type}) is identical with English original")
                    # TODO fill it with "-"
                else:
                    self._add_file_type(page_info, file_type, translation)

            if lang not in self._result:
                self._result[lang] = LanguageInfo(lang)
            self._result[lang].add_worksheet_info(page, page_info)

    def _sync_and_compare(self, language_info: LanguageInfo) -> ChangeLog:
        """
        Synchronize our generated data on this language with our "database" and return the changes.

        The "database" is the JSON representation of LanguageInfo and is stored in a mediawiki page.

        @param lang language code
        @return comparison to what was previously stored in our database
        """
        lang = language_info.language_code
        encoded_json = DataStructureEncoder().encode(language_info)
        old_language_info: LanguageInfo = LanguageInfo(lang)
        rewrite_json: bool = self._rewrite_all

        # Reading data structure from our mediawiki, stored in e.g. https://www.4training.net/4training:de.json
        page = pywikibot.Page(self.site, f"4training:{lang}.json")
        if not page.exists():
            # There doesn't seem to be any information on this language stored yet!
            self.logger.warning(f"{page.full_url()} doesn't seem to exist yet. Creating...")
            page.text = encoded_json
            page.save("Created JSON data structure")
            rewrite_json = False
        else:
            # Load "old" data structure of this language (from previous resourcesbot run)
            try:
                old_language_info = json.loads(page.text, object_hook=json_decode)
                assert isinstance(old_language_info, LanguageInfo)
                assert old_language_info.language_code == lang
            except AssertionError:
                self.logger.warning(f"Error while trying to load {lang}.json")

            if encoded_json != page.text:
                rewrite_json = True

        # compare and find out if new worksheets have been added
        changes: ChangeLog = language_info.compare(old_language_info)
        if changes.is_empty():
            self.logger.info(f"No changes in language {lang} since last run.")
        else:
            self.logger.info(f"Changes in language {lang} since last run:\n{changes}")

        if rewrite_json:
            # Write the updated JSON structure
            page.text = encoded_json
            page.save("Updated JSON data structure")
            self.logger.info(f"Updated 4training:{lang}.json")

        return changes

    def _save_languages_list(self):
        """
        Save a list of language codes of all our languages to the mediawiki server
        We want this list so that the bot can be run with --read-from-cache for all languages

        The list is stored to https://www.4training.net/4training:languages.json in alphabetical order
        """
        language_list = list(self._result)
        language_list.sort()
        encoded_json: str = json.dumps(language_list)
        previous_json: str = ""

        page = pywikibot.Page(self.site, f"4training:languages.json")
        if not page.exists():
            self.logger.warning("languages.json doesn't seem to exist yet. Creating...")
        else:
            previous_json = page.text

        # TODO compare language_list and json.loads(previous_json) to find out if a new language was added
        if previous_json != encoded_json:
            page.text = encoded_json
            page.save("Updated list of languages")
            self.logger.info(f"Updated 4training:languages.json")

    def _save_number_of_languages(self):
        """
        Count number of languages we have and save them to https://www.4training.net/MediaWiki:Numberoflanguages
        Language variants (any language code containing a "-") are not counted extra.
        TODO: Discuss how we want to count in some edge cases, e.g. count pt-br always extra as we have a
        separate page for Brazilian Portuguese?
        @param language_list: List of language codes
        """
        language_list: List[str] = list(self._result)
        number_of_languages = 0
        for lang in language_list:
            if "-" not in lang:
                number_of_languages += 1
            else:
                self.logger.debug(f"Not counting {lang} into the number of languages we have")
        self.logger.info(f"Number of languages: {number_of_languages}")

        previous_number_of_languages: int = 0
        page = pywikibot.Page(self.site, f"MediaWiki:Numberoflanguages")
        if page.exists():
            previous_number_of_languages = int(page.text)
        else:
            self.logger.warning("MediaWiki:Numberoflanguages doesn't seem to exist yet. Creating...")

        if previous_number_of_languages != number_of_languages:
            try:
                page.text = number_of_languages
                page.save("Updated number of languages")
                self.logger.info(f"Updated MediaWiki:Numberoflanguages to {number_of_languages}")
            except pywikibot.exceptions.PageSaveRelatedError as err:
                self.logger.warning(f"Error while trying to update MediaWiki:Numberoflanguages: {err}")

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
                    if self._result[lang].worksheet_has_type(worksheet, "pdf"):
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
