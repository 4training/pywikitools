import requests
import pywikibot
import argparse
from pywikitools.fortraininglib import ForTrainingLib
from googletrans import Translator
from configparser import ConfigParser

# Constants
BASE_URL = "https://test.4training.net"
TEXT_ENDPOINT = f"{BASE_URL}/mediawiki/api.php?action=query&format=json&list=messagecollection&mcgroup=page-"
DEEPL_ENDPOINT = "https://api-free.deepl.com/v2/translate"

# Configuration
config = ConfigParser()
config.read('deepl_config.ini')
DEEPL_API_KEY = config.get('DEEPL', 'API_KEY')

class TranslationTool:
    def __init__(self, base_url, text_endpoint, deepl_endpoint):
        self.base_url = base_url
        self.text_endpoint = text_endpoint
        self.deepl_endpoint = deepl_endpoint
        self.fortraininglib = ForTrainingLib(self.base_url)
        self.translator = Translator()
        self.language_supported_by_deepl = True

    def fetch_and_translate(self, page_name, language_code, force):
        response = requests.get(f"{self.text_endpoint}{page_name}&mclanguage=en")
        data = response.json()

        if force or self.fortraininglib.get_translated_title(page_name, language_code) is None:
            print("No translation found!")
        else:
            print("Translation existed already. If you want to force overwrite, use the -f flag.")
            return

        for item in data["query"]["messagecollection"]:
            translated_text = self.translate_with_deepl_or_google(item["definition"], language_code)
            self.upload_translation(item["key"], translated_text, page_name, language_code)

    def translate_with_deepl_or_google(self, text, language_code):
        if self.language_supported_by_deepl:
            data = {
                "auth_key": DEEPL_API_KEY,
                "text": text,
                "target_lang": language_code
            }
            response = requests.post(self.deepl_endpoint, data=data)
            if response.status_code == 200:
                return response.json()['translations'][0]['text']
            else:
                print(f"DeepL cannot translate to {language_code}. Using Google Translate instead.")
                self.language_supported_by_deepl = False

        # If DeepL fails, use Google Translate
        return self.translator.translate(text, dest=language_code).text

    def upload_translation(self, key, translated_text, page_name, language_code):
        page_number = key.split("/")[-1]
        page_title = f'Translations:{page_name}/{page_number}/{language_code}'
        
        site = pywikibot.Site()
        if not site.logged_in():
            site.login()
            if not site.logged_in():
                raise RuntimeError("Login with pywikibot failed.")
            
        mediawiki_page = pywikibot.Page(site, page_title)
        mediawiki_page.text = translated_text
        mediawiki_page.save(summary="Automated translation upload")


def main():
    parser = argparse.ArgumentParser(description="Auto-translate a worksheet.")
    parser.add_argument("worksheet_name", help="Name of the worksheet to translate.")
    parser.add_argument("language_code", help="Target language code for translation.")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite if translation exists.")
    args = parser.parse_args()

    translator_tool = TranslationTool(BASE_URL, TEXT_ENDPOINT, DEEPL_ENDPOINT)
    translator_tool.fetch_and_translate(args.worksheet_name, args.language_code, args.force)

if __name__ == "__main__":
    main()
