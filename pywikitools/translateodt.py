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
import os.path
import re
from configparser import ConfigParser
from typing import Dict, Final, List, Optional, Set
import requests
from pywikitools.fortraininglib import ForTrainingLib
from pywikitools.correctbot.correctors.universal import UniversalCorrector
from pywikitools.lang.native_numerals import native_to_standard_numeral
from pywikitools.lang.translated_page import TranslatedPage, TranslationUnit
from pywikitools.libreoffice import LibreOffice

SNIPPET_WARN_LENGTH = 3 # give a warning when search or replace string is shorter than 3 characters
# The following templates don't contain any translation units and can be ignored
IGNORE_TEMPLATES = ['Template:DocDownload', 'Template:OdtDownload', 'Template:PdfDownload',
                    'Template:PrintPdfDownload',
                    'Template:Translatable template', 'Template:Version', 'Module:Template translation',
                    'Template:Italic']
# for the following languages we don't add ", version x.y" to the keywords in the document properties
# because the translation of "version" is very close to the English word "version"
# TODO should 'ko' be in this list?
NO_ADD_ENGLISH_VERSION = ['de', 'pt-br', 'cs', 'nl', 'fr', 'id', 'ro', 'es', 'sv', 'tr', 'tr-tanri']

class TranslateOdtConfig:
    """Contains configuration on how to process one worksheet:
    Which translation units should be ignored?
    Which translation units should be processed multiple times?

    It is read from a config file (see TranslateODT.read_worksheet_config()) of the following structure:
    [Ignore]
    # Don't process the following translation units
    Template:BibleReadingHints/18
    Template:BibleReadingHints/25

    [Multiple]
    # Process the following translation unit 5 times
    Template:BibleReadingHints/6 = 5
    """
    __slots__ = ["ignore", "multiple"]
    def __init__(self):
        # Set of translation unit identifiers that shouldn't be processed
        self.ignore: Final[Set[str]] = set()
        # Translation unit identifier -> number of times it should be processed
        self.multiple: Final[Dict[str, int]] = {}

class TranslateODT:
    def __init__(self, *, keep_english_file: bool = False, config: Dict[str, Dict[str, str]] = {}):
        """Variable initializations (no connection to LibreOffice here)
        @param keep_english_file: Don't delete English ODT file afterwards (command line option)
        @param config: can be used to overwrite config settings
        """
        # Read configuration from config.ini in this folder; set default values in case it doesn't exist
        self.config: ConfigParser = ConfigParser()
        self.config.read_dict({'Paths' : {'worksheets' : os.path.abspath(os.getcwd()) + '/worksheets/'},
                               'translateodt' : {'closeoffice': True,
                                                 'headless': False}})
        self.config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')
        self.config.read_dict(config)

        self.logger = logging.getLogger('pywikitools.translateodt')
        self.keep_english_file: bool = keep_english_file
        if not self.config.has_option('mediawiki', 'baseurl'):
            raise RuntimeError("Missing settings for mediawiki connection in config.ini")
        # TODO also use config.get('mediawiki', 'apipath')
        self.fortraininglib: ForTrainingLib = ForTrainingLib(self.config.get('mediawiki', 'baseurl'))

        self._loffice = LibreOffice(self.config.getboolean('translateodt', 'headless'))
        self._original_page_count: int = 0          # How many pages did the currently opened file have originally?
        self._did_page_count_change: bool = False   # Did the page count of the currently opened file change?

    def _is_search_and_replace_necessary(self, orig: str, trans: str) -> bool:
        """
        Checks if we need to do a search and replace or if there are other exceptions
        Logs warnings for certain circumstances
        @return true if we need to do search and replace
        """
        if orig.endswith((".pdf", ".odt", ".odg")): # if string is a file name, we ignore it
            return False

        if orig == trans:
            self.logger.debug(f"Search and replace string are identical, ignoring: {orig}")
            return False

        if len(orig) < SNIPPET_WARN_LENGTH:
            if orig in ["", " ", ".", ",", ":", ";"]:
                self.logger.warning("Warning: Problematic search string detected! Please check and correct."
                                    f" Replaced {orig} with {trans}")
            else:
                self.logger.warning("Potential problem: short search string. "
                                    f"This can be totally normal but please check. Replaced {orig} with {trans}")
        return True


    def _process_snippet(self, orig: str, trans: str):
        """
        Looks at one snippet, does some preparations and tries to do search and replace
        @param orig the original string (what to search for)
        @param trans the translated string (what we're going to replace it with)
        """
        self.logger.debug(f"process_snippet, orig: {orig}, trans: {trans}")

        orig = orig.strip()
        trans = trans.strip()
        if not self._is_search_and_replace_necessary(orig, trans):
            return

        # if translation snippet can be found in document, replace
        try:
            replaced = self._loffice.search_and_replace(orig, trans, not self._did_page_count_change, True)
            if replaced:
                self.logger.debug(f"Replaced: {orig} with: {trans}")
            else:
                self.logger.warning("Couldn't replace the following translation snippet. Please check.")
                self.logger.warning(f"Original: \n{orig}")
                self.logger.warning(f"Translation: \n{trans}")

        except AttributeError as error:
            self.logger.error(f"AttributeError: {error}")  # todo: wait some seconds and try again

        if self._loffice.get_page_count() != self._original_page_count:
            self._did_page_count_change = True

    def _search_and_replace(self, translated_page: TranslatedPage):
        """Go through the whole document, search for original text snippets and replace them
        with the translated text snippets"""
        for t in translated_page:           # for each translation unit:
            self.logger.debug(f"Translation unit: {t.get_definition()}")

            is_well_structured, warning = t.is_translation_well_structured()
            if not is_well_structured:  # We can't process this translation unit
                self.logger.warning(warning)
                continue

            for (search, replace) in t:   # for each snippet of translation unit
                self._process_snippet(search.content, replace.content)

        if self._did_page_count_change:
            if self._loffice.get_page_count() > self._original_page_count:
                self.logger.warning(f"Page count of translation is {self._loffice.get_page_count()}. "
                                    f"Please edit and fit it to {self._original_page_count} pages like the original.")
            else:
                # in the (rare) case that first translations were longer so that page count increased
                # but later translations were shorter so that page count decreased again.
                self.logger.warning("Page structure change detected. Did the position of the page break change? "
                                    "Please check and correct if necessary.")

    def _fetch_english_file(self, odt_file: str) -> str:
        """Download the specified file from the mediawiki server
        @return full path of the downloaded file (empty string on error)
        """
        en_path = self.config['Paths']['worksheets'] + 'en'
        if not os.path.isdir(en_path):
            os.makedirs(en_path)
        odt_path = f"{en_path}/{odt_file}"
        if os.path.isfile(odt_path):
            self.logger.warning(f"File {odt_path} already exists locally, not downloading.")
        else:
            url = self.fortraininglib.get_file_url(odt_file)
            if url is None:
                self.logger.error(f"Could not get URL of file {odt_file}")
                return ""

            odt_doc = requests.get(url, allow_redirects=True)
            with open(odt_path, 'wb') as fh:
                fh.write(odt_doc.content)
            self.logger.info(f"Successfully downloaded and saved {odt_path}")
        return odt_path

    def _get_odt_filename(self, translated_page: TranslatedPage) -> str:
        """Create filename from headline of translated page

        E.g. page "Hearing from God" -> "Hearing_from_God.odt"
        Compares it to the translated file name and gives a warning if it doesn't match"""
        # TODO correct wrong filename translations automatically in the system?
        filename: str = re.sub(" ", '_', translated_page.get_worksheet_info().title)
        filename = re.sub("[':]", "", filename)
        filename += ".odt"
        if translated_page.get_worksheet_info().get_file_type_name("odt") != filename:
            self.logger.warning("Warning: Is the file name not correctly translated? Please correct. "
                                f"Translation: {translated_page.get_worksheet_info().get_file_type_name('odt')}, "
                                f"according to the headline it should be: {filename}")
        return filename

    def _cleanup_units(self, translated_page: TranslatedPage, config: TranslateOdtConfig) -> TranslatedPage:
        """
        Clean up translation units before we do search and replace:
        - filter out empty/irrelevant units
        - remove [[links]]
        - remove bold/italic/underline formatting from definition
        - replace '' / ''' with <i> / <b> in translation
        - check order of translation units and rearrange if necessary
        - process config: remove ignored units, replicate units that should be processed multiple times

        We can run into troubles if a we have a short translation snippet that is contained in another snippet
        -> search and replace will likely happen at the wrong place
        Let's loop through all units and in the case a snippet is contained in anoher one, we'll move the short
        translation unit to the end: We always try to match long search strings first

        @param config: Instructions on which units should be ignored and which should be processed multiple times
        @return a cleaned up copy TranslatedPage (as in-place manipulation isn't easily possible)
        """
        result: List[TranslationUnit] = []
        for t in translated_page:
            if t.get_definition() == "":
                self.logger.warning(f"Empty unit in original detected: Ignoring {t.get_name()}")
                continue
            if t.get_translation() == "":
                self.logger.warning(f"Translation of {t.get_name()} missing. Please translate: {t.get_definition()}")
                continue
            if t.get_definition() == translated_page.get_english_info().version:
                # We don't try to do search and replace with the version string. We later process the whole CC0 notice
                continue
            if t.identifier in config.ignore:
                self.logger.info(f"Ignoring translation unit {t.identifier}")
                continue

            # Do some normalization on the translation unit now: first remove [[Links]]
            t.remove_links()
            # remove bold/italic/underline formatting from definition
            t.set_definition(re.sub("\'\'+|</?[biu]>", '', t.get_definition()))
            # replace '' / ''' with <i> / <b> in translation (necessary for LibreOffice.search_and_replace())
            corrector = UniversalCorrector()
            t.set_translation(corrector.correct_mediawiki_bold_italic(t.get_translation()))

            if t.identifier in config.multiple:
                self.logger.info(f"{t.identifier} will be processed {config.multiple[t.identifier]} times")
                for i in range(1, config.multiple[t.identifier]):
                    result.append(t)
            result.append(t)

        self.special_sort_units(result)
        return TranslatedPage(translated_page.page, translated_page.language_code, result)

    def special_sort_units(self, units: List[TranslationUnit]) -> None:
        """
        Order the TranslationUnits in such a way that units with a short snippet
        (that is part of another one) are moved to the end of the list
        ["long", "A long sentence", "long sentence"] -> ["A long sentence", "long sentence", "long"]

        Then we first search and replace the long strings, avoiding replacing at the wrong places.
        This is not a "typical" ordering like ordering alphabetically. That's why we can't use Python's sort()
        method but really must compare each element with all other elements. This has O(n^2) complexity
        but for normal use-cases (less than 1000 translation units) that shouldn't be an issue

        If no snippet contains another one, nothing will be re-ordered
        @param units: The list of translation units will be re-ordered in-place
        """
        for i in range(len(units)):
            if not units[i].is_translation_well_structured()[0]:
                continue
            for j in range(len(units)):
                if i == j:
                    continue
                # Do the actual sorting
                if (units[i] < units[j]) and (i < j):
                    self.logger.info(f"{units[i].get_definition()} is part of {units[j].get_definition()}. "
                                     f"Reordering. ({i} / {j})")
                    temp_unit = units[i]
                    units[i] = units[j]
                    units[j] = temp_unit

                # More consistency checks
                if not units[j].is_translation_well_structured()[0]:
                    self.logger.warning(f"{units[j].get_name()} is not well structured.")
                    continue
                for i_snippet_orig, i_snippet_trans in units[i]:
                    if i_snippet_orig.content == i_snippet_trans.content:
                        # translation == original: will be ignored anyway
                        continue
                    for _, j_snippet_trans in units[j]:
                        # warn in case a search string can be found in a translation (unlikely but better check)
                        if i_snippet_orig.content in j_snippet_trans.content:
                            self.logger.warning(f'Search string "{i_snippet_orig.content}" ({units[i].get_name()}) '
                                            f'is in translation "{j_snippet_trans.content}" ({units[j].get_name()})!')


    def read_worksheet_config(self, worksheet: str) -> TranslateOdtConfig:
        """
        Read processing configuration for a specific worksheet from the MediaWiki system.
        The config is read from page [worksheet-name].config in the Project namespace
        (example: https://www.4training.net/4training:Bible_Reading_Hints.config ).
        If there is no such config, the two members of the data structure returned will both be empty
        """
        result = TranslateOdtConfig()
        config = ConfigParser(delimiters=('='), allow_no_value=True)
        config.optionxform = str    # We want to have the options case-sensitive
        config_string = self.fortraininglib.get_page_source(f"Project:{worksheet}.config")
        if config_string is None:
            self.logger.info(f"No config found for worksheet {worksheet}")
            return result
        config.read_string(config_string)
        if config.has_section("Ignore"):
            for option in config["Ignore"]:
                result.ignore.add(option)
        if config.has_section("Multiple"):
            for option, value in config.items("Multiple"):
                result.multiple[option] = int(value)
        self.logger.info(f"Read config: Ignoring {len(result.ignore)} translation units, "
                         f"{len(result.multiple)} translation units will be processed multiple times")
        return result

    def translate_odt(self, odt_path: str, translated_page: TranslatedPage, config: TranslateOdtConfig) -> None:
        """Open the specified ODT file and replace contents with translation
        @param odt_path: Path of the ODT file
        @param translated_page: Contains all translation units we'll do search&replace with
        Raises ConnectionError (coming from LibreOffice.open_file) if LibreOffice connection didn't work
        """
        self._loffice.open_file(odt_path)
        self._did_page_count_change = False
        self._original_page_count = self._loffice.get_page_count()
        self._search_and_replace(self._cleanup_units(translated_page, config))

    def translate_worksheet(self, worksheet: str, language_code: str) -> Optional[str]:
        """Create translated worksheet: Fetch information, download original ODT, process it, save translated ODT
        @param worksheet name of the worksheet (e.g. "Forgiving_Step_by_Step")
        @param language_code what language we should translate to (e.g. "de")
        @return file name of the created ODT file (or None in case of error)
        """
        self.logger.debug(f"Worksheet: {worksheet}, language code: {language_code}")
        translated_page: Optional[TranslatedPage] = self.fortraininglib.get_translation_units(worksheet, language_code)
        if translated_page is None:
            self.logger.error(f"Couldn't get translation units of {worksheet}.")
            return None
        if translated_page.is_untranslated():
            self.logger.error(f"Worksheet {worksheet} is not translated into language {language_code}")
            return None

        # Check for templates we need to read as well
        templates = set(self.fortraininglib.list_page_templates(worksheet)) - set(IGNORE_TEMPLATES)
        for template in templates:
            template_page: Optional[TranslatedPage] = self.fortraininglib.get_translation_units(template, language_code)
            if template_page is None:
                self.logger.warning(f"Couldn't get translations of {template}, ignoring this template.")
            else:
                for translation_unit in template_page:
                    translated_page.add_translation_unit(translation_unit)

        translated_version: str = translated_page.get_worksheet_info().version
        if translated_version == "":
            self.logger.warning("Translation of version is missing!")
            translated_version = translated_page.get_english_info().version
        elif not translated_page.get_worksheet_info().has_same_version(translated_page.get_english_info()):
            self.logger.warning(f"English original has version {translated_page.get_english_info().version}, "
                                f"translation has version {translated_version}. "
                                "Please update translation. "
                                "Ask an administrator for a list of changes in the English original.")

        if translated_page.get_english_info().get_file_type_name("odt") == "":
            self.logger.error(f"Couldn't find name of odt file in page {worksheet}")
            return None
        if translated_page.get_english_info().version == "":
            self.logger.error(f"Couldn't find version number in page {worksheet}")
            return None
        if translated_page.get_worksheet_info().get_file_type_name("odt") == "":
            self.logger.warning("Translation of file name is missing!")

        # Add footer (Template:CC0Notice) to translation list
        translated_page.add_translation_unit(TranslationUnit("Template:CC0Notice", language_code,
            self.fortraininglib.get_cc0_notice(translated_page.get_english_info().version, 'en'),
            self.fortraininglib.get_cc0_notice(translated_version, language_code)))

        odt_path = self._fetch_english_file(translated_page.get_english_info().get_file_type_name("odt"))
        if not odt_path:
            return None

        config = self.read_worksheet_config(worksheet)
        self.translate_odt(odt_path, translated_page, config)
        self._set_properties(translated_page)
        self._loffice.set_default_style(translated_page.language_code,
            self.fortraininglib.get_language_direction(translated_page.language_code) == "rtl")

        # Save in folder worksheets/[language_code]/ as odt and pdf, close LibreOffice
        save_path = self.config['Paths']['worksheets'] + translated_page.language_code
        if not os.path.isdir(save_path):
            os.makedirs(save_path)
        filename = self._get_odt_filename(translated_page)
        file_path = f"{save_path}/{filename}"

        self.logger.info(f"Saving translated document to {file_path}...")
        try:
            self._loffice.save_odt(file_path)
        except FileExistsError:
            self.logger.error(f"Couldn't save {file_path}: File exists and is currently opened.")
        pdf_path = file_path.replace(".odt", ".pdf")
        self.logger.info(f"Exporting translated document as PDF to {pdf_path}...")
        self._loffice.export_pdf(pdf_path)

        if self.config.getboolean('translateodt', 'closeoffice'):
            self._loffice.close()

        if self.keep_english_file:
            self.logger.info(f"Keeping {odt_path}")
        else:
            self.logger.debug(f"Removing {odt_path}")
            os.remove(odt_path)
        return file_path

    def _set_properties(self, page: TranslatedPage):
        """Set the properties of the ODT file"""
        # Read the existing subject to check if there is a subtitle in our document
        subject: str = self._loffice.get_properties_subject()
        subtitle_en = ""
        subtitle_lan = ""
        if subject != "":
            if len(page.units) < 2:
                # TODO: Check this already in the beginning
                self.logger.error(f"{page.page} only has {len(page.units)} translation units! Exiting now.")
                return None
            if subject != page.units[1].get_definition():
                self.logger.info(f"Assuming we have no subtitle. Subject in properties is {subject}"
                                 f", but second translation unit is {page.units[1].get_definition()}")
            else:
                subtitle_en = " - " + page.units[1].get_definition()
                subtitle_lan = " - " + page.units[1].get_translation()

        # Title: [translated Title]
        headline = page.get_worksheet_info().title
        if headline == "":
            # TODO: Check that already in the beginning
            self.logger.error("Headline doesn't seem to be translated. Exiting now.")
            return None
        headline += subtitle_lan

        # Subject: [English title] [Languagename in English] [Languagename autonym]
        subject  = page.get_english_info().title
        subject += subtitle_en
        subject += " " + str(self.fortraininglib.get_language_name(page.language_code, 'en'))
        subject += " " + str(self.fortraininglib.get_language_name(page.language_code))

        # Keywords: [Translated no-copyright notice + version] - copyright-free, version [original version]
        # ",version [original version]" is omitted in languages where the translation of "version" is very similar
        cc0_notice = self.fortraininglib.get_cc0_notice(page.get_worksheet_info().version, page.language_code)
        cc0_notice += " - copyright-free"
        if page.language_code not in NO_ADD_ENGLISH_VERSION:
            cc0_notice += ", version "
            cc0_notice += native_to_standard_numeral(page.language_code, page.get_worksheet_info().version)

        self._loffice.set_properties(headline, subject, cc0_notice)

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
