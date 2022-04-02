import logging
import shlex
from subprocess import Popen, TimeoutExpired
from time import sleep
from typing import Any, Optional
import uno                                              # type: ignore
from com.sun.star.connection import NoConnectException  # type: ignore
from com.sun.star.beans import PropertyValue            # type: ignore
from com.sun.star.lang import Locale                    # type: ignore
from com.sun.star.task import ErrorCodeIOException      # type: ignore
from com.sun.star.io import IOException                 # type: ignore

from pywikitools.lang.libreoffice_lang import LANG_LOCALE


class LibreOffice:
    """Connecting to LibreOffice via PyUNO:
    A class to open files, do some actions (search and replace; setting properties; setting locale of default style)
    and save the file as ODT or export it as PDF.

    You need to make sure that you first call open_file() before calling other functions,
    otherwise you get an AssertionError
    """
    PORT = 2002             # port where libreoffice is running
    CONNECT_TRIES = 10      # how often we re-try to connect to libreoffice
    TIMEOUT = 200           # The script will be aborted if it's running longer than this amount of seconds

    """Class to handle files with LibreOffice write"""
    def __init__(self, headless: bool = False):
        """Variable initializations (no connection to LibreOffice here)
        @param headless: Should we start LibreOffice with the --headless flag?
        """
        self.logger = logging.getLogger('pywikitools.libreoffice')
        self._headless: bool = headless

        self._desktop: Optional[Any] = None     # LibreOffice central desktop element (com.sun.star.frame.Desktop)
        self._model: Optional[Any] = None       # LibreOffice current component
        self._proc: Optional[Any] = None        # LibreOffice process handle

    def open_file(self, file_name: str):
        """Opens an existing LibreOffice document

        This starts LibreOffice and establishes a socket connection to it
        Raises ConnectionError if something doesn't work
        """
        self.logger.info(f"Opening file {file_name}")

        command = 'soffice ' + shlex.quote(file_name)
        if self._headless:
            command += " --headless"
        command += f' --accept="socket,host=localhost,port={self.PORT};urp;StarOffice.ServiceManager"'
        self.logger.debug(command)
        self._proc = Popen(command, shell=True)

        local_context = uno.getComponentContext()
        resolver = local_context.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local_context)

        # connect to the running LibreOffice
        retries = 0
        ctx = None
        search_ready = False
        while not search_ready and retries < self.CONNECT_TRIES:
            if ctx is None:
                try:
                    ctx = resolver.resolve(f"uno:socket,host=localhost,port={self.PORT};"
                                           "urp;StarOffice.ComponentContext")
                except NoConnectException as error:
                    self.logger.info(f"Failed to connect to LibreOffice: {error}. Retrying...")
            else:
                self._desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
                self._model = self._desktop.getCurrentComponent()
                if self._model:
                    try:
                        self._model.createSearchDescriptor()
                    except AttributeError as error:
                        self.logger.info(f"Error while preparing LibreOffice for searching: {error}. Retrying...")
                    else:
                        search_ready = True

            retries += 1
            # Sleep in any case as sometimes the loading of the document isn't complete yet
            sleep(2)

        if not search_ready:
            raise ConnectionError("Error trying to access the LibreOffice document."
                                  f"Tried {retries} times, giving up now.")

    def search_and_replace(self, search: str, replace: str) -> bool:
        """
        Replaces first occurence of search with replace in the currently opened LibreOffice document
        @return True if successful
        """
        # source: https://wiki.openoffice.org/wiki/Documentation/BASIC_Guide/Editing_Text_Documents
        assert self._model is not None
        searcher = self._model.createSearchDescriptor()
        searcher.SearchCaseSensitive = True
        searcher.SearchString = search

        found = bool(self._model.findFirst(searcher))
        if found:
            found_x = self._model.findFirst(searcher)
            found_x.setString(replace)
        return found

    def save_odt(self, file_name: str):
        """
        Save the currently opened document as ODT file.
        @param filename: where to save the odt file (full URL, e.g. "/path/to/file.odt" )
        @raises FileExistsError if file already exists and is currently opened; OSError
        """
        uri = f"file://{file_name}"
        args = []   # arguments for saving

        # Overwrite file if it already exists
        arg0 = PropertyValue()
        arg0.Name = "Overwrite"
        arg0.Value = True
        args.append(arg0)

        assert self._model is not None
        try:
            self._model.storeAsURL(uri, args) # save as ODT
        except ErrorCodeIOException as err:
            raise FileExistsError(err)
        except IOException as err:
            raise OSError(err)

    def export_pdf(self, file_name: str):
        """
        Export the currently opened document as PDF
        @param filename: where to save the PDF file (full URL, e.g. "/path/to/file.pdf" )
        """
        uri = f"file://{file_name}"
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

        args = []
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
        assert self._model is not None
        self._model.storeToURL(uri, tuple(args))

    def close(self):
        """Closes LibreOffice"""
        assert self._desktop is not None and self._proc is not None
        self._desktop.terminate()
        try:
            return self._proc.wait(timeout=self.TIMEOUT)
        except TimeoutExpired:
            self.logger.error(f"soffice process didn't terminate within {self.TIMEOUT}s. Killing it.")
            self._proc.kill()

    def get_properties_subject(self) -> str:
        """Return the subject property of the currently open document"""
        assert self._model is not None
        properties = self._model.getDocumentProperties()
        return properties.Subject

    def set_properties(self, title: str, subject: str, keywords: str):
        """Set the properties (subject, title and keywords) of the ODT file"""
        assert self._model is not None
        properties = self._model.getDocumentProperties()
        properties.Title = title
        properties.Subject = subject
        properties.Keywords = [keywords]

    def set_default_style(self, language_code: str, rtl: bool = False):
        """Setting properties of the ODT document's default style:
        Locale (with language code) and writing mode (LTR/RTL)
        Does some logging on errors (not optimal from software design perspective)
        """
        assert self._model is not None
        par_styles = self._model.getStyleFamilies().getByName("ParagraphStyles")
        default_style = None
        if par_styles.hasByName("Default Style"):       # until LibreOffice 6
            default_style = par_styles.getByName("Default Style")
        elif par_styles.hasByName("Default Paragraph Style"):
            # got renamed in LibreOffice 7, see https://bugs.documentfoundation.org/show_bug.cgi?id=129568
            default_style = par_styles.getByName("Default Paragraph Style")
        else:
            self.logger.warning("Couldn't find Default Style in paragraph styles."
                                "Can't set RTL and language locale, please do that manually.")
            return

        if rtl:
            self.logger.debug("Setting language direction to RTL")
            default_style.ParaAdjust = 1 # alignment (0: left; 1: right; 2: justified; 3: center)
            default_style.WritingMode = 1 # writing direction (0: LTR; 1: RTL; 4: use superordinate object settings)

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
            self.logger.warning(f'Language "{language_code}" not in LANG_LOCALE. '
                                "Please ask an administrator to fix this.")
            struct_locale = Locale(language_code, "", "")
            # We don't know which of the three this language belongs to... so we assign it to all Fontstyles
            # (unfortunately e.g. "ar" can be assigned to "Western Font" so try-and-error-assigning doesn't work)
            default_style.CharLocale = struct_locale
            default_style.CharLocaleAsian = struct_locale
            default_style.CharLocaleComplex = struct_locale
