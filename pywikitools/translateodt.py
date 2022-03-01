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
import shlex
import os.path
import re
from subprocess import Popen, TimeoutExpired
from time import sleep
from configparser import ConfigParser
from typing import Any, List, Optional
import requests
import uno          # type: ignore
from com.sun.star.connection import NoConnectException
from com.sun.star.beans import PropertyValue
from com.sun.star.lang import Locale
from pywikitools import fortraininglib
from pywikitools.lang.libreoffice_lang import LANG_LOCALE
from pywikitools.lang.translated_page import TranslationUnit

PORT = 2002             # port where libreoffice is running
CONNECT_TRIES = 10      # how often we re-try to connect to libreoffice
TIMEOUT = 200           # The script will be aborted if it's running longer than this amount of seconds
SNIPPET_WARN_LENGTH = 4 # give a warning when search or replace string is shorter than 4 characters
# The following templates don't contain any translation units and can be ignored
IGNORE_TEMPLATES = ['Template:DocDownload', 'Template:OdtDownload', 'Template:PdfDownload',
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

        self.desktop: Optional[Any] = None     # LibreOffice central desktop element (com.sun.star.frame.Desktop)
        self.model: Optional[Any] = None       # LibreOffice current component
        self.proc: Optional[Any] = None        # LibreOffice process handle

    def open_file(self, file_name: str):
        """Opens an existing LibreOffice document

        This starts LibreOffice and establishes a socket connection to it
        If something doesn't work the script will abort with sys.exit()
        """
        self.logger.info(f"Opening file {file_name}")

        args = 'soffice ' + shlex.quote(file_name)
        if self.config.getboolean('translateodt', 'headless'):
            args += " --headless"
        args += f' --accept="socket,host=localhost,port={PORT};urp;StarOffice.ServiceManager"'
        self.logger.debug(args)
        self.proc = Popen(args, shell=True)

        local_context = uno.getComponentContext()
        resolver = local_context.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local_context)

        # connect to the running LibreOffice
        retries = 0
        ctx = None
        search_ready = False
        while not search_ready and retries < CONNECT_TRIES:
            if ctx is None:
                try:
                    ctx = resolver.resolve(f"uno:socket,host=localhost,port={PORT};urp;StarOffice.ComponentContext")
                except NoConnectException as error:
                    self.logger.info(f"Failed to connect to LibreOffice: {error}. Retrying...")
            else:
                self.desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
                self.model = self.desktop.getCurrentComponent()
                if self.model:
                    try:
                        self.model.createSearchDescriptor()
                    except AttributeError as error:
                        self.logger.info(f"Error while preparing LibreOffice for searching: {error}. Retrying...")
                    else:
                        search_ready = True

            retries += 1
            # Sleep in any case as sometimes the loading of the document isn't complete yet
            sleep(2)

        if not search_ready:
            self.logger.warning("Error trying to access the LibreOffice document."
                               f"Tried {retries} times, giving up now.")
            sys.exit(2)

    def is_search_and_replace_necessary(self, orig: str, trans: str) -> bool:
        """
        Checks if we need to do a search and replace or if there are other exceptions
        Logs warnings for certain circumstances
        @return true if we need to do search and replace
        """
        # if string is empty there is nothing to do
        if orig == '':
            return False

        # if string is a file name, we ignore it
        if orig.endswith(('.pdf', '.odt', '.doc')):
            return False

        if orig == trans:
            self.logger.debug(f"Search and replace string are identical, ignoring: {orig}")
            return False

        if len(orig) < SNIPPET_WARN_LENGTH:
            if (orig in [' ', '.', ',', ':', ';']):
                self.logger.warning("Warning: Problematic search string detected! Please check and correct."
                                f" Replaced {orig} with {trans}")
            else:
                self.logger.warning("Potential problem: short search string. This can be totally normal but please check."
                                f" Replaced {orig} with {trans}")
        return True


    def process_snippet(self, orig: str, trans: str):
        """
        Looks at one snippet, does some preparations and tries to do search and replace
        @param orig the original string (what to search for)
        @param trans the translated string (what we're going to replace it with)
        """
        self.logger.debug(f"process_snippet, orig: {orig}, trans: {trans}")
        orig = orig.strip()
        trans = trans.strip()

        if not self.is_search_and_replace_necessary(orig, trans):
            return
        # if translation snippet can be found in document, replace
        try:
            replaced = self.search_and_replace(orig, trans)
            if replaced:
                self.logger.info(f"Replaced: {orig} with: {trans}")
            else:
                # Second try: split at newlines (or similar strange breaks) and try again
                self.logger.info(f"Couldn't find {orig}. Splitting at newlines and trying again.")

                orig_split = re.split("[\t\n\r\f\v]", orig)
                trans_split = re.split("[\t\n\r\f\v]", trans)
                if len(orig_split) != len(trans_split):
                    self.logger.warning("Couldn't process the following translation snippet. Please check.")
                    self.logger.warning(f"Original: \n{orig}")
                    self.logger.warning(f"Translation: \n{trans}")
                    return
                for search, replace in zip(orig_split, trans_split):
                    if not self.is_search_and_replace_necessary(search.strip(), replace.strip()):
                        continue
                    replaced = self.search_and_replace(search, replace)
                    if replaced:
                        self.logger.info(f"Replaced: {search} with: {replace}")
                    else:
                        self.logger.warning(f"Not found:\n{search}\nTranslation:\n{replace}")

        except AttributeError as error:
            self.logger.error(f"AttributeError: {error}")  # todo: wait some seconds and try again


    def search_and_replace(self, search: str, replace: str) -> bool:
        """
        Replaces first occurence of search with replace in a LibreOffice document
        @return True if successful
        """
        # source: https://wiki.openoffice.org/wiki/Documentation/BASIC_Guide/Editing_Text_Documents
        assert self.model is not None
        searcher = self.model.createSearchDescriptor()
        searcher.SearchCaseSensitive = True
        searcher.SearchString = search

        found = bool(self.model.findFirst(searcher))
        if found:
            found_x = self.model.findFirst(searcher)
            found_x.setString(replace)
        return found

    def close_and_save_file(self, file_name: str):
        """Saves file, exports it as PDF and closes LibreOffice
        @param filename where to save the odt file (full URL, e.g. /home/user/worksheets/de/Gebet.odt )
        """
        assert self.model is not None and self.desktop is not None and self.proc is not None
        uri = f"file://{file_name}"
        args = []   # arguments for saving

        # Overwrite file if it already exists
        arg0 = PropertyValue()
        arg0.Name = "Overwrite"
        arg0.Value = True
        args.append(arg0)

        self.model.storeAsURL(uri, args) # save as ODT
        self.logger.info(f"Saved translated document to {uri}")

        opts = []   # options for PDF export
        # Archive PDF/A
        opt1 = PropertyValue()
        opt1.Name = "SelectPdfVersion"
        opt1.Value = 1
        opts.append(opt1)
        # Reduce image resolution to 300dpi
        opt2 = PropertyValue()
        opt2.Name = "MaxImageResolution"
        opt2.Value = 300
        opts.append(opt2)
        # Export bookmarks
        opt3 = PropertyValue()
        opt3.Name = "ExportBookmarks"
        opt3.Value = True
        opts.append(opt3)
        # 90% JPEG image compression
        opt4 = PropertyValue()
        opt4.Name = "Quality"
        opt4.Value = 90
        opts.append(opt4)

        # Export to pdf property
        arg1 = PropertyValue()
        arg1.Name = "FilterName"
        arg1.Value = "writer_pdf_Export"
        args.append(arg1)
        # Collect options
        arg2 = PropertyValue()
        arg2.Name = "FilterData"
        arg2.Value = uno.Any("[]com.sun.star.beans.PropertyValue", tuple(opts))
        args.append(arg2)

        # export as pdf
        self.model.storeToURL(uri.replace(".odt", ".pdf"), tuple(args))
        self.logger.info(f"Exported translated document as PDF to {uri.replace('.odt', '.pdf')}")

        # close
        if self.config.getboolean('translateodt', 'closeoffice'):
            self.desktop.terminate()
        try:
            return self.proc.wait(timeout=TIMEOUT)
        except TimeoutExpired:
            self.logger.error(f"soffice process didn't terminate within {TIMEOUT}s. Killing it.")
            self.proc.kill()

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


    def translate_odt(self, worksheet: str, language_code: str) -> Optional[str]:
        """Central function to process the given worksheet
        @param worksheet name of the worksheet (e.g. "Forgiving_Step_by_Step")
        @param language_code what language we should translate to (e.g. "de")
        @return file name of the created ODT file (or None in case of error)
        """
        self.logger.debug(f"Worksheet: {worksheet}, language code: {language_code}")
        translations: List[TranslationUnit] = fortraininglib.get_translation_units(worksheet, language_code)
        if len(translations) == 0:
            self.logger.error(f"Couldn't get translation units of {worksheet}.")
            return None

        # Check for templates we need to read as well
        templates = set(fortraininglib.list_page_templates(worksheet)) - set(IGNORE_TEMPLATES)
        for template in templates:
            template_units = fortraininglib.get_translation_units(template, language_code)
            if len(template_units) == 0:
                self.logger.warning(f"Couldn't get translations of {template}, ignoring this template.")
            else:
                translations.extend(template_units)

        # find out version, name of original odt-file and name of translated odt-file
        version = None
        version_orig = None
        odt = None
        filename = None
        for t in translations:
            if re.search(r"\.odt$", t.get_definition()):
                odt = t.get_definition()
                filename = t.get_translation()
            # Searching for version number (valid examples: 1.0; 2.1; 0.7b; 1.5a)
            if re.search(r"^\d\.\d[a-zA-Z]?$", t.get_definition()):
                if t.get_definition() != t.get_translation():
                    self.logger.warning(f"English original has version {t.get_definition()}, "
                                f"translation has version {t.get_translation()}. "
                                "Please update translation. "
                                "Ask an administrator for a list of changes in the English original.")
                version = t.get_translation()
                version_orig = t.get_definition()

        if not odt:
            self.logger.error(f"Couldn't find name of odt file in page {worksheet}")
            return None
        if not version_orig:
            self.logger.error(f"Couldn't find version number in page {worksheet}")
            return None
        if not version:
            self.logger.warning("Translation of version is missing!")
            version = version_orig
        if not filename:
            self.logger.warning("Translation of file name is missing!")

        # Add footer (Template:CC0Notice) to translation list
        translations.extend([TranslationUnit("Template:CC0Notice", language_code,
            fortraininglib.get_cc0_notice(version_orig, 'en'), fortraininglib.get_cc0_notice(version, language_code))])

        odt_path = self._fetch_english_file(odt)
        if not odt_path:
            return None

        self.open_file(odt_path)

        # for each translation unit:
        for t in translations:
            if t.get_definition() == "":
                self.logger.warning(f"Empty unit in original detected: Ignoring {t.get_name()}")
                continue
            if t.get_translation() == "":
                self.logger.warning(f"Translation of {t.get_name()} missing. Please translate: {t.get_definition()}")
                continue
            if t.get_definition() == version_orig:
                # We don't try to do search and replace with the version string. We later process the whole CC0 notice
                continue

            self.logger.debug(f"Translation unit: {t.get_definition()}")
            t.remove_links()

            # Check if number of <br/> is equal, otherwise replace by newline
            br_in_orig = len(re.split("< *br */ *>", t.get_definition())) - 1
            br_in_trans = len(re.split("< *br */ *>", t.get_translation())) - 1
            if br_in_orig != br_in_trans:
                # TODO in the future remove this? At least find out how much this is necessary
                self.logger.info("Number of <br/> differs between original and translations. Replacing with newlines.")
                t.set_definition(re.sub("< *br */ *>", '\n', t.get_definition()))
                t.set_translation(re.sub("< *br */ *>", '\n', t.get_translation()))

            if not t.is_translation_well_structured():
                # We can't process this translation unit. Logging messages are already written
                continue
            if br_in_orig != br_in_trans:
                self.logger.warning(f"Issue with <br/> (line breaks). There are {br_in_orig} in the original "
                            f"but {br_in_trans} of them in the translation. "
                            f"We still can process {t.get_name()}. You may ignore this warning.")

            for (search, replace) in t:     # for each snippet of translation unit:
                self.process_snippet(search.content, replace.content)

        ############################################################################################
        # Set properties
        ############################################################################################
        assert self.model is not None
        docProps = self.model.getDocumentProperties()

        # check if there is a subtitle in docProps.Subject:
        subtitle_en = ""
        subtitle_lan = ""
        if docProps.Subject != "":
            if docProps.Subject != translations[1].get_definition():
                self.logger.info(f"Assuming we have no subtitle. Subject in properties is {docProps.Subject}"
                            f", but second translation unit is {translations[1].get_definition()}")
            else:
                subtitle_en = " - " + translations[1].get_definition()
                subtitle_lan = " - " + translations[1].get_translation()

        # Title: [translated Title]
        headline = translations[0].get_translation()
        if headline is None:
            self.logger.error("Headline doesn't seem to be translated. Exiting now.")
            return None
        docProps.Title = headline
        docProps.Title += subtitle_lan


        # Subject: [English title] [Languagename in English] [Languagename autonym]
        docProps.Subject = str(translations[0].get_definition())
        docProps.Subject += subtitle_en
        docProps.Subject += " " + str(fortraininglib.get_language_name(language_code, 'en'))
        docProps.Subject += " " + str(fortraininglib.get_language_name(language_code))

        # Keywords: [Translated copyright notice with replaced version number] - copyright-free, version [versionnumber]
        # ",version [versionnumber]" is omitted in languages where the translation of "version" is very similar
        cc0_notice = fortraininglib.get_cc0_notice(version, language_code) + " - copyright-free"
        if language_code not in NO_ADD_ENGLISH_VERSION:
            if re.search(r"^[0-9]\.[0-9][a-zA-Z]?$", version):
                cc0_notice += ", version " + version
            else:
                cc0_notice += ", version " + version_orig
                self.logger.warning("Version number seems not to use standard decimal numbers."
                            f"Assuming this is identical to {version_orig}. Please check File->Properties->Keywords")
        docProps.Keywords = [cc0_notice]

        # create filename from headline
        filename_check: str = re.sub(" ", '_', headline)
        filename_check = re.sub("[':]", "", filename_check)
        filename_check += ".odt"
        if filename != filename_check:
            self.logger.warning("Warning: Is the file name not correctly translated? Please correct. "
                        f"Translation: {filename}, according to the headline it should be: {filename_check}")
            filename = filename_check

        par_styles = self.model.getStyleFamilies().getByName("ParagraphStyles")
        default_style = None
        if par_styles.hasByName('Default Style'):       # until LibreOffice 6
            default_style = par_styles.getByName('Default Style')
        elif par_styles.hasByName('Default Paragraph Style'):
            # got renamed in LibreOffice 7, see https://bugs.documentfoundation.org/show_bug.cgi?id=129568
            default_style = par_styles.getByName('Default Paragraph Style')
        else:
            self.logger.warning("Couldn't find Default Style in paragraph styles."
                        "Can't set RTL and language locale, please do that manually.")

        if default_style is not None:
            if fortraininglib.get_language_direction(language_code) == "rtl":
                self.logger.debug("Setting language direction to RTL")
                default_style.ParaAdjust = 1 # alignment (0: left; 1: right; 2: justified; 3: center)
                default_style.WritingMode = 1 # writing direction (0: LTR; 1: RTL; 4: "use superordinate object settings")

            # default_style.CharLocale.Language and .Country seem to be read-only
            self.logger.debug("Setting language locale of Default Style")
            if language_code in LANG_LOCALE:
                lang = LANG_LOCALE[language_code]
                struct_locale = lang.to_locale()
                self.logger.info(f"Assigning Locale for language '{language_code}': {lang}")
                if lang.is_standard():
                    default_style.CharLocale = struct_locale
                if lang.is_asian():
                    default_style.CharLocaleAsian = struct_locale
                if lang.is_complex():
                    default_style.CharLocaleComplex = struct_locale
                if lang.has_custom_font():
                    self.logger.warning(f'Using font "{lang.get_custom_font()}". Please make sure you have it installed.')
                    default_style.CharFontName = lang.get_custom_font()
                    default_style.CharFontNameAsian = lang.get_custom_font()
                    default_style.CharFontNameComplex = lang.get_custom_font()
            else:
                self.logger.warning(f"Language '{language_code}' not in LANG_LOCALE. Please ask an administrator to fix this.")
                struct_locale = Locale(language_code, "", "")
                # We don't know which of the three this language belongs to... so we assign it to all Fontstyles
                # (unfortunately e.g. 'ar' can be assigned to "Western Font" so try-and-error-assigning doesn't work)
                default_style.CharLocale = struct_locale
                default_style.CharLocaleAsian = struct_locale
                default_style.CharLocaleComplex = struct_locale

        # Save in folder worksheets/[language_code]/ as odt and pdf, close LibreOffice
        save_path = self.config['Paths']['worksheets'] + language_code
        if not os.path.isdir(save_path):
            os.makedirs(save_path)
        file_path = save_path + '/' + filename
        self.close_and_save_file(file_path)

        if self.keep_english_file:
            self.logger.info(f"Keeping {odt_path}")
        else:
            self.logger.debug(f"Removing {odt_path}")
            os.remove(odt_path)
        return file_path

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
