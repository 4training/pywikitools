import re
import logging
from typing import Dict

import pywikibot
from pywikitools.ResourcesBot.changes import ChangeLog, ChangeType
from pywikitools.ResourcesBot.post_processing import LanguagePostProcessor
from pywikitools.ResourcesBot import LanguageInfo
from pywikitools import fortraininglib


class WriteList(LanguagePostProcessor):
    """
    Write/update the list of available training resources for languages.

    We only show worksheets that have a PDF file (to ensure good quality)

    This class can be re-used to call run() several times
    """
    __slots__ = ['_site', '_force_rewrite', 'logger']

    def __init__(self, site: pywikibot.site.APISite, user_name: str, password: str, force_rewrite: bool=False):
        """
        @param user_name and password necessary to mark page for translation in case of changes
        @param force_rewrite rewrite even if there were no (relevant) changes
        """
        self._site = site
        self._user_name = user_name
        self._password = password
        self._force_rewrite = force_rewrite
        self.logger = logging.getLogger('4training.resourcesbot.write_lists')

    def needs_rewrite(self, language_info: LanguageInfo, change_log: ChangeLog):
        """Determine whether the list of available training resources needs to be rewritten."""
        lang = language_info.get_language_code()
        needs_rewrite = False
        for change_item in change_log.get_all_changes():
            if change_item.change_type in [ChangeType.UPDATED_PDF, ChangeType.NEW_PDF, ChangeType.DELETED_PDF]:
                needs_rewrite = True
            if (change_item.change_type in [ChangeType.NEW_ODT, ChangeType.DELETED_ODT]) \
                and language_info.worksheet_has_type(change_item.worksheet, "pdf"):
                needs_rewrite = True

        if needs_rewrite:
            self.logger.info(f"List of available training resources in language {lang} needs to be re-written.")
        else:
            self.logger.info(f"List of available training resources in language {lang} doesn't need to be re-written.")

        return needs_rewrite

    def create_mediawiki(self, language_info: LanguageInfo):
        """
        Create the mediawiki string for the list of available training resources

        Output should look like the following line:
        * [[God's_Story_(five_fingers)/de|{{int:sidebar-godsstory-fivefingers}}]] [[File:pdficon_small.png|link={{filepath:Gottes_Geschichte_(fünf_Finger).pdf}}]] [[File:odticon_small.png|link={{filepath:Gottes_Geschichte_(fünf_Finger).odt}}]]
        """
        content = ''
        for worksheet, worksheet_info in language_info.worksheets.items():
            if not worksheet_info.has_file_type('pdf'):
                # Only show worksheets where we have a PDF file in the list
                self.logger.warning(f"Language {language_info.get_language_code()}: worksheet {worksheet} has no PDF, "
                                     "not including in list.")
                continue

            content += f"* [[{worksheet}/{language_info.get_language_code()}|"
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
        return content

    def run(self, language_info: LanguageInfo, change_log: ChangeLog):
        """
        """
        lang = language_info.get_language_code()
        self.logger.debug(f"Writing list of available resources in {lang}...")

        # Saving this to the language information page, e.g. https://www.4training.net/German
        language = fortraininglib.get_language_name(lang, 'en')
        if language is None:
            self.logger.warning(f"Error while trying to get language name of {lang}! Skipping")
            return
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



