import re
import logging
from typing import Optional

import pywikibot
from pywikitools.resourcesbot.changes import ChangeLog, ChangeType
from pywikitools.resourcesbot.post_processing import LanguagePostProcessor
from pywikitools.resourcesbot.data_structures import FileInfo, LanguageInfo
from pywikitools import fortraininglib


class WriteList(LanguagePostProcessor):
    """
    Write/update the list of available training resources for languages.

    We only show worksheets that have a PDF file (to ensure good quality)

    This class can be re-used to call run() several times
    """
    def __init__(self, site: pywikibot.site.APISite, user_name: str, password: str, force_rewrite: bool=False):
        """
        @param user_name and password necessary to mark page for translation in case of changes
               In case they're empty we won't try to mark pages for translation
        @param force_rewrite rewrite even if there were no (relevant) changes
        """
        self._site = site
        self._user_name = user_name
        self._password = password
        self._force_rewrite = force_rewrite
        self.logger = logging.getLogger('pywikitools.resourcesbot.write_lists')
        if user_name == "" or password == "":
            self.logger.warning("Missing user name and/or password in config. Won't mark pages for translation.")

    def needs_rewrite(self, language_info: LanguageInfo, change_log: ChangeLog) -> bool:
        """Determine whether the list of available training resources needs to be rewritten."""
        lang = language_info.language_code
        needs_rewrite = self._force_rewrite
        for change_item in change_log:
            if change_item.change_type in [ChangeType.UPDATED_PDF, ChangeType.NEW_PDF, ChangeType.DELETED_PDF,
                                           ChangeType.NEW_WORKSHEET, ChangeType.DELETED_WORKSHEET]:
                needs_rewrite = True
            if (change_item.change_type in [ChangeType.NEW_ODT, ChangeType.DELETED_ODT]) \
                and language_info.worksheet_has_type(change_item.worksheet, "pdf"):
                needs_rewrite = True

        if needs_rewrite:
            self.logger.info(f"List of available training resources in language {lang} needs to be re-written.")
        else:
            self.logger.info(f"List of available training resources in language {lang} doesn't need to be re-written.")

        return needs_rewrite

    def _create_file_mediawiki(self, file_info: Optional[FileInfo]) -> str:
        """
        Return string with mediawiki code to display a downloadable file

        Example: [[File:pdficon_small.png|link={{filepath:Gebet.pdf}}]]
        @return empty string if file_info is None
        """
        if file_info is None:
            return ""
        file_name: str = file_info.url
        pos: int = file_name.rfind('/')
        if pos > -1:
            file_name = file_name[pos+1:]
        else:
            self.logger.warning(f"Couldn't find / in {file_name}")
        return f" [[File:{file_info.file_type}icon_small.png|" + r"link={{filepath:" + file_name + r"}}]]"

    def create_mediawiki(self, language_info: LanguageInfo) -> str:
        """
        Create the mediawiki string for the list of available training resources

        Output should look like the following line:
        * [[God's_Story_(five_fingers)/de|{{int:sidebar-godsstory-fivefingers}}]] \
          [[File:pdficon_small.png|link={{filepath:Gottes_Geschichte_(fünf_Finger).pdf}}]] \
          [[File:odticon_small.png|link={{filepath:Gottes_Geschichte_(fünf_Finger).odt}}]]
        """
        content: str = ''
        for worksheet, worksheet_info in language_info.worksheets.items():
            if worksheet_info.progress.is_unfinished():
                continue
            if not worksheet_info.has_file_type('pdf'):
                # Only show worksheets where we have a PDF file in the list
                self.logger.warning(f"Language {language_info.language_code}: worksheet {worksheet} has no PDF,"
                                    " not including in list.")
                continue

            content += f"* [[{worksheet}/{language_info.language_code}|"
            content += "{{int:" + fortraininglib.title_to_message(worksheet) + "}}]]"
            content += self._create_file_mediawiki(worksheet_info.get_file_type_info("pdf"))
            content += self._create_file_mediawiki(worksheet_info.get_file_type_info("odt"))
            content += "\n"

        self.logger.debug(content)
        return content

    def run(self, language_info: LanguageInfo, change_log: ChangeLog) -> None:
        if not self.needs_rewrite(language_info, change_log):
            return

        # Saving this to the language information page, e.g. https://www.4training.net/German
        language = fortraininglib.get_language_name(language_info.language_code, 'en')
        if language is None:
            self.logger.warning(f"Error while trying to get language name of {language_info.language_code}! Skipping")
            return
        self.logger.debug(f"Writing list of available resources in {language}...")
        page = pywikibot.Page(self._site, language)
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
            self.logger.info(page.text)
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
        new_page_content = page.text[0:list_start] + self.create_mediawiki(language_info) + page.text[list_end+1:]
        self.logger.debug(new_page_content)
        page.text = new_page_content
        page.save("Updated list of available training resources") # TODO write human-readable changes here in the save message
        if self._user_name != '' and self._password != '':
            fortraininglib.mark_for_translation(page.title(), self._user_name, self._password)
            self.logger.info(f"Updated language information page {language} and marked it for translation.")
        else:
            self.logger.info(f"Updated language information page {language}. Couldn't mark it for translation.")
