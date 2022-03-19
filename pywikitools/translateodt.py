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
from typing import List, Optional
import requests
from pywikitools import fortraininglib
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

class TranslateODT:
    def __init__(self, keep_english_file: bool = False, loglevel: Optional[str] = None):
        """Variable initializations (no connection to LibreOffice here)
        @param keep_english_file Don't delete English ODT file afterwards (command line option)
        """
        # Read configuration from config.ini in this folder; set default values in case it doesn't exist
        self.config: ConfigParser = ConfigParser()
        self.config.read_dict({'Paths' : {'worksheets' : os.path.abspath(os.getcwd()) + '/worksheets/'},
                               'translateodt' : {'closeoffice': True,
                                                 'headless': False}})
        self.config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')

        self.logger = logging.getLogger('pywikitools.translateodt')

        if loglevel is not None:
            numeric_level = getattr(logging, loglevel.upper(), None)
            if not isinstance(numeric_level, int):
                raise ValueError(f"Invalid log level: {loglevel}")
            logging.basicConfig(level=numeric_level)
            self.logger.setLevel(numeric_level)

        self.keep_english_file: bool = keep_english_file

        self._loffice = LibreOffice(self.config.getboolean('translateodt', 'headless'))

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
            replaced = self._loffice.search_and_replace(orig, trans)
            if replaced:
                self.logger.info(f"Replaced: {orig} with: {trans}")
            else:
                # Second try: split at newlines (or similar strange breaks) and try again
                self.logger.warning(f"Couldn't find {orig}. Splitting at newlines and trying again.")

                orig_split = re.split("[\t\n\r\f\v]", orig)
                trans_split = re.split("[\t\n\r\f\v]", trans)
                if len(orig_split) != len(trans_split):
                    self.logger.warning("Couldn't process the following translation snippet. Please check.")
                    self.logger.warning(f"Original: \n{orig}")
                    self.logger.warning(f"Translation: \n{trans}")
                    return
                for search, replace in zip(orig_split, trans_split):
                    if not self._is_search_and_replace_necessary(search.strip(), replace.strip()):
                        continue
                    replaced = self._loffice.search_and_replace(search, replace)
                    if replaced:
                        self.logger.info(f"Replaced: {search} with: {replace}")
                    else:
                        self.logger.warning(f"Not found:\n{search}\nTranslation:\n{replace}")

        except AttributeError as error:
            self.logger.error(f"AttributeError: {error}")  # todo: wait some seconds and try again

    def _search_and_replace(self, translated_page: TranslatedPage):
        """Go through the whole document, search for original text snippets and replace them
        with the translated text snippets"""
        for t in translated_page:           # for each translation unit:
            if t.get_definition() == "":
                self.logger.warning(f"Empty unit in original detected: Ignoring {t.get_name()}")
                continue
            if t.get_translation() == "":
                self.logger.warning(f"Translation of {t.get_name()} missing. Please translate: {t.get_definition()}")
                continue
            if t.get_definition() == translated_page.get_original_version():
                # We don't try to do search and replace with the version string. We later process the whole CC0 notice
                continue

            self.logger.debug(f"Translation unit: {t.get_definition()}")
            t.remove_links()

            # Check if number of <br/> is equal, otherwise replace by newline
            br_in_orig = len(re.split("< *br */ *>", t.get_definition())) - 1
            br_in_trans = len(re.split("< *br */ *>", t.get_translation())) - 1
            if br_in_orig != br_in_trans:
                # TODO in the future remove this? At least find out how much this is necessary
                self.logger.warning("Number of <br/> differs between original and translations. Replacing with newlines.")
                t.set_definition(re.sub("< *br */ *>", '\n', t.get_definition()))
                t.set_translation(re.sub("< *br */ *>", '\n', t.get_translation()))

            if not t.is_translation_well_structured(use_fallback=True):
                # We can't process this translation unit. Logging messages are already written
                continue
            if br_in_orig != br_in_trans:
                self.logger.warning(f"Issue with <br/> (line breaks). There are {br_in_orig} in the original "
                                    f"but {br_in_trans} of them in the translation. "
                                    f"We still can process {t.get_name()}. You may ignore this warning.")

            for (search, replace) in t:     # for each snippet of translation unit:
                self._process_snippet(search.content, replace.content)


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
            url = fortraininglib.get_file_url(odt_file)
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
        filename: str = re.sub(" ", '_', translated_page.get_translated_headline())
        filename = re.sub("[':]", "", filename)
        filename += ".odt"
        if translated_page.get_translated_odt() != filename:
            self.logger.warning("Warning: Is the file name not correctly translated? Please correct. "
                                f"Translation: {translated_page.get_translated_odt()}, "
                                f"according to the headline it should be: {filename}")
        return filename

    def translate_odt(self, worksheet: str, language_code: str) -> Optional[str]:
        """Central function to process the given worksheet
        @param worksheet name of the worksheet (e.g. "Forgiving_Step_by_Step")
        @param language_code what language we should translate to (e.g. "de")
        @return file name of the created ODT file (or None in case of error)
        """
        self.logger.debug(f"Worksheet: {worksheet}, language code: {language_code}")
        translated_page: Optional[TranslatedPage] = fortraininglib.get_translation_units(worksheet, language_code)
        if translated_page is None:
            self.logger.error(f"Couldn't get translation units of {worksheet}.")
            return None
        if translated_page.is_untranslated():
            self.logger.error(f"Worksheet {worksheet} is not translated into language {language_code}")
            return None

        # Check for templates we need to read as well
        templates = set(fortraininglib.list_page_templates(worksheet)) - set(IGNORE_TEMPLATES)
        for template in templates:
            template_page: Optional[TranslatedPage] = fortraininglib.get_translation_units(template, language_code)
            if template_page is None:
                self.logger.warning(f"Couldn't get translations of {template}, ignoring this template.")
            else:
                for translation_unit in template_page:
                    translated_page.add_translation_unit(translation_unit)

        translated_version: str = translated_page.get_translated_version()
        if translated_version == "":
            self.logger.warning("Translation of version is missing!")
            translated_version = translated_page.get_original_version()
        elif not translated_version.startswith(translated_page.get_original_version()):
            self.logger.warning(f"English original has version {translated_page.get_original_version()}, "
                                f"translation has version {translated_version}. "
                                "Please update translation. "
                                "Ask an administrator for a list of changes in the English original.")

        if translated_page.get_original_odt() == "":
            self.logger.error(f"Couldn't find name of odt file in page {worksheet}")
            return None
        if translated_page.get_original_version() == "":
            self.logger.error(f"Couldn't find version number in page {worksheet}")
            return None
        if translated_page.get_translated_odt() == "":
            self.logger.warning("Translation of file name is missing!")

        # Add footer (Template:CC0Notice) to translation list
        translated_page.add_translation_unit(TranslationUnit("Template:CC0Notice", language_code,
            fortraininglib.get_cc0_notice(translated_page.get_original_version(), 'en'),
            fortraininglib.get_cc0_notice(translated_version, language_code)))

        odt_path = self._fetch_english_file(translated_page.get_original_odt())
        if not odt_path:
            return None

        try:
            self._loffice.open_file(odt_path)
        except ConnectionError as err:
            self.logger.error(err)
            sys.exit(2)

        self._search_and_replace(translated_page)

        self._set_properties(translated_page)
        self._loffice.set_default_style(language_code, fortraininglib.get_language_direction(language_code) == "rtl")

        # Save in folder worksheets/[language_code]/ as odt and pdf, close LibreOffice
        save_path = self.config['Paths']['worksheets'] + translated_page.language_code
        if not os.path.isdir(save_path):
            os.makedirs(save_path)
        filename = self._get_odt_filename(translated_page)
        file_path = f"{save_path}/{filename}"

        self.logger.info(f"Saving translated document to {file_path}...")
        self._loffice.save_odt(file_path)
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
                self.logger.error(f"{page.page} only has {len(page.units)} translation units! Exiting now.")
                return None
            if subject != page.units[1].get_definition():
                self.logger.info(f"Assuming we have no subtitle. Subject in properties is {subject}"
                                 f", but second translation unit is {page.units[1].get_definition()}")
            else:
                subtitle_en = " - " + page.units[1].get_definition()
                subtitle_lan = " - " + page.units[1].get_translation()

        # Title: [translated Title]
        headline = page.get_translated_headline()
        if headline == "":
            self.logger.error("Headline doesn't seem to be translated. Exiting now.")
            return None
        headline += subtitle_lan

        # Subject: [English title] [Languagename in English] [Languagename autonym]
        subject  = page.get_original_headline()
        subject += subtitle_en
        subject += " " + str(fortraininglib.get_language_name(page.language_code, 'en'))
        subject += " " + str(fortraininglib.get_language_name(page.language_code))

        # Keywords: [Translated no-copyright notice + version] - copyright-free, version [original version]
        # ",version [original version]" is omitted in languages where the translation of "version" is very similar
        cc0_notice = fortraininglib.get_cc0_notice(page.get_translated_version(), page.language_code)
        cc0_notice += " - copyright-free"
        if page.language_code not in NO_ADD_ENGLISH_VERSION:
            if re.search(r"^[0-9]\.[0-9][a-zA-Z]?$", page.get_translated_version()):
                cc0_notice += f", version {page.get_translated_version()}"
            else:
                cc0_notice += f", version {page.get_original_version()}"
                self.logger.warning("Version number seems not to use standard decimal numbers."
                                    f"Assuming this is identical to {page.get_original_version()}."
                                    "Please check File->Properties->Keywords")

        self._loffice.set_properties(headline, subject, cc0_notice)

if __name__ == '__main__':
    log_levels: List[str] = ['debug', 'info', 'warning', 'error']

    msg = "Create translated ODT file of a worksheet"
    parser = argparse.ArgumentParser(prog="python3 translateodt.py", description=msg)
    parser.add_argument("worksheet", help="Name of the mediawiki page")
    parser.add_argument("language_code", help="Language code of the translation language")
    parser.add_argument("-l", "--loglevel", choices=log_levels, help="set loglevel for the script")
    parser.add_argument("--keep-english-file", dest="keep_english_file", action="store_true",
                        help="Don't delete the downloaded English ODT file after we're finished")

    args = parser.parse_args()
    translateodt = TranslateODT(args.keep_english_file, args.loglevel)
    translateodt.translate_odt(args.worksheet, args.language_code, )
