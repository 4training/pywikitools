import os
import requests
import pywikibot
import argparse
from pywikitools.fortraininglib import ForTrainingLib
from googletrans import Translator
from configparser import ConfigParser

TIMEOUT: int = 30           # Timeout after 30s (prevent indefinite hanging when there is network issues)


class TranslationTool:
    def __init__(self):
        config = ConfigParser()
        config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')
        if not config.has_option('mediawiki', 'baseurl') or \
           not config.has_option('mediawiki', 'scriptpath'):
            raise RuntimeError("Missing settings for mediawiki connection in config.ini")

        if not config.has_option('autotranslate', 'deeplendpoint') or \
           not config.has_option('autotranslate', 'deeplapikey'):
            raise RuntimeError("Missing settings for DeepL connection in config.ini")

        self.deepl_endpoint = config.get('autotranslate', 'deeplendpoint')
        self.deepl_api_key = config.get('autotranslate', 'deeplapikey')
        self.fortraininglib = ForTrainingLib(config.get('mediawiki', 'baseurl'),
                                             config.get('mediawiki', 'scriptpath'))
        self.google_translator = Translator()
        self.language_supported_by_deepl = True

    def fetch_and_translate(self, page_name, language_code, force=False):
        translated_page = self.fortraininglib.get_translation_units(page_name, "en")

        if not force and self.fortraininglib.get_translated_title(page_name, language_code) is not None:
            print("Translation already exists. If you want to force overwrite, use the -f flag.")
            return

        # Split the translation units into snippets to avoid mark-up symbols
        for translation_unit in translated_page:
            translation_unit.split_all_tags = True  # We want that to get rid of all markup
            translation_unit.remove_links()

            for orig_snippet, trans_snippet in translation_unit:
                trans_snippet.content = self.translate_with_deepl_or_google(orig_snippet.content, language_code)
            translation_unit.sync_from_snippets()
            self.upload_translation(f"{translation_unit.identifier}/{language_code}",
                                    translation_unit.get_translation())

    def translate_with_deepl_or_google(self, text, language_code) -> str:
        """Do the translation: First try deepl, if that doesn't work (deepl supports less languages), use google"""
        if self.language_supported_by_deepl:
            data = {
                "auth_key": self.deepl_api_key,
                "text": text,
                "target_lang": language_code
            }
            response = requests.post(self.deepl_endpoint, data=data, timeout=TIMEOUT)
            if response.status_code == 200:
                return response.json()['translations'][0]['text']
            else:
                print(f"DeepL cannot translate to {language_code}. Using Google Translate instead.")
                self.language_supported_by_deepl = False

        # If DeepL fails, use Google Translate
        return self.google_translator.translate(text, dest=language_code).text

    def upload_translation(self, identifier: str, translated_text: str):
        """Upload the automatic translation of one translation unit back into the mediawiki system"""
        site = pywikibot.Site()
        if not site.logged_in():
            site.login()
            if not site.logged_in():
                raise RuntimeError("Login with pywikibot failed.")

        mediawiki_page = pywikibot.Page(site, f"Translations:{identifier}")
        mediawiki_page.text = translated_text
        mediawiki_page.save(summary="Automated translation upload")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Machine-translate a worksheet.")
    parser.add_argument("worksheet_name", help="Name of the worksheet to translate.")
    parser.add_argument("language_code", help="Target language code for translation.")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite if translation exists.")
    args = parser.parse_args()

    translator_tool = TranslationTool()
    translator_tool.fetch_and_translate(args.worksheet_name, args.language_code, args.force)
