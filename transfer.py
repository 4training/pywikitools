import logging
from os.path import abspath, dirname, join
import pywikibot
import argparse
from pywikitools.family import Family
from pywikitools.fortraininglib import ForTrainingLib
from configparser import ConfigParser

TIMEOUT: int = 30           # Timeout after 30s (prevent indefinite hanging when there is network issues)


class TransferTool:
    def __init__(self, config: ConfigParser):
        if not config.has_option('transfer', 'source_site') or \
           not config.has_option('transfer', 'source_username') or \
           not config.has_option('transfer', 'destination_site') or \
           not config.has_option('transfer', 'destination_username'):
            raise RuntimeError("Missing settings for transfer in config.ini")

        self.logger: logging.Logger = logging.getLogger('pywikitools.transfer')

        self.source_site = config.get('transfer', 'source_site')
        self.destination_site = config.get('transfer', 'destination_site')

        family = Family()

        self.source_wiki_site = pywikibot.Site(code=self.source_site, fam=family,
                                               user=config.get('transfer', 'source_username'))
        if not self.source_wiki_site.logged_in():
            self.source_wiki_site.login()
            if not self.source_wiki_site.logged_in():
                raise RuntimeError("Login with pywikibot failed to source site failed.")
        # Set throttle to 0 to speed up write operations (otherwise pywikibot would wait up to 10s after each write)
        self.source_wiki_site.throttle.set_delays(delay=0, writedelay=0, absolute=True)

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

    def transfer(self, page_name, language_code):
        source_translation_page = self.source_fortraininglib.get_translation_units(page_name, language_code)

        for translation_unit in source_translation_page:
            self.upload(f"{translation_unit.identifier}/{language_code}", translation_unit.get_translation())

    def upload(self, identifier: str, translated_text: str):
        """Transfer a workshoot from one mediawiki system to another one"""
        destination_mediawiki_page = pywikibot.Page(self.destination_wiki_site, f"Translations:{identifier}")
        destination_mediawiki_page.text = translated_text
        destination_mediawiki_page.save(
            summary=f"Transfer of '{identifier}' from '{self.source_site}' to '{self.destination_site}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Transfer a worksheet for a certain language from one site to another site.")
    parser.add_argument("worksheet_name", help="Name of the worksheet to transfer.")
    parser.add_argument("language_code", help="Target language code for transfer.")
    args = parser.parse_args()

    config = ConfigParser()
    config.read(join(dirname(abspath(__file__)), "config.ini"))

    transfer_tool = TransferTool(config)
    transfer_tool.transfer(args.worksheet_name, args.language_code)
