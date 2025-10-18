import logging
from os.path import abspath, dirname, join
from typing import Optional
import pywikibot
import argparse
from pywikitools.family import Family
from pywikitools.fortraininglib import ForTrainingLib
from configparser import ConfigParser
from pywikitools.lang.translated_page import TranslatedPage

TIMEOUT: int = 30           # Timeout after 30s (prevent indefinite hanging when there is network issues)


class TransferTool:
    def __init__(self, config: ConfigParser):
        if not config.has_option('transfer', 'source_site') or \
           not config.has_option('transfer', 'destination_site') or \
           not config.has_option('transfer', 'destination_username'):
            raise RuntimeError("Missing settings for transfer in config.ini")

        self.logger: logging.Logger = logging.getLogger('pywikitools.transfer')

        self.unchanged: int = 0
        self.modified: int = 0
        self.created: int = 0

        self.source_site = config.get('transfer', 'source_site')
        self.destination_site = config.get('transfer', 'destination_site')

        family = Family()

        self.destination_wiki_site = pywikibot.Site(code=self.destination_site, fam=family,
                                                    user=config.get('transfer', 'destination_username'))
        if not self.destination_wiki_site.logged_in():
            self.destination_wiki_site.login()
            if not self.destination_wiki_site.logged_in():
                raise RuntimeError("Login with pywikibot failed to destination site failed.")
        # Set throttle to 0 to speed up write operations (otherwise pywikibot would wait up to 10s after each write)
        self.destination_wiki_site.throttle.set_delays(delay=0, writedelay=0, absolute=True)

        self.source_fortraininglib: ForTrainingLib = ForTrainingLib(family.base_url(self.source_site, ''),
                                                                    family.scriptpath(self.source_site))
        self.destination_fortraininglib: ForTrainingLib = ForTrainingLib(family.base_url(self.destination_site, ''),
                                                                         family.scriptpath(self.destination_site))

    def transfer(self, page_name, language_code, message=None):
        source_translation_page: Optional[TranslatedPage] = self.source_fortraininglib.get_translation_units(
            page_name, language_code)

        if source_translation_page is None:
            raise RuntimeError("Could not get translation units from source site")

        self.unchanged: int = 0
        self.modified: int = 0
        self.created: int = 0

        for source_translation_unit in source_translation_page:
            source_translation = source_translation_unit.get_translation()
            self.upload(f"{source_translation_unit.identifier}/{language_code}",
                        source_translation, message)

        numTotal = self.unchanged + self.modified + self.created
        print(f"Transfer of {numTotal} elements for '{page_name}/{language_code}' " +
              f"from '{self.source_site}' to '{self.destination_site}' completed.")
        print(f"unchanged: {self.unchanged} | modified: {self.modified} | created: {self.created}")

    def upload(self, identifier: str, translated_text: str, message=None):
        """Transfer a worksheet from one mediawiki system to another one"""
        destination_mediawiki_page = pywikibot.Page(self.destination_wiki_site, f"Translations:{identifier}")

        if not destination_mediawiki_page.exists():
            self.created += 1
        elif destination_mediawiki_page.text == translated_text:
            self.unchanged += 1
        else:
            self.modified += 1

        destination_mediawiki_page.text = translated_text

        if message is None:
            destination_mediawiki_page.save()
        else:
            destination_mediawiki_page.save(summary=message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Transfer a worksheet for a certain language from one site to another site.")
    parser.add_argument("worksheet_name", help="Name of the worksheet to transfer.")
    parser.add_argument("language_code", help="Target language code for transfer.")
    parser.add_argument("--message", nargs=1, help="This is a test")
    args = parser.parse_args()

    config = ConfigParser()
    config.read(join(dirname(abspath(__file__)), "config.ini"))

    transfer_tool = TransferTool(config)
    transfer_tool.transfer(args.worksheet_name, args.language_code, args.message)
