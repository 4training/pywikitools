"""
Provides a bridge from mediawiki to Drupal

Reads a page as HTML using the mediawiki API and imports it as a node to the Drupal system.
The parsed HTML gets processed with BeautifulSoup to remove some unwanted pieces
(like the "edit this section" links or the list of available translations of this page)

Afterwards it writes the page to Drupal by using the JSON:API
For this, the Web Services related modules which are part of Drupal core need to be enabled:
HAL, HTTP Basic Auth, JSON:API, RESTful Web Services, Serialization
Inspired by:
https://weimingchenzero.medium.com/use-python-to-call-drupal-9-core-restful-api-to-create-new-content-9f3fa8628ab4

This uses HTTP Basic Auth. Make sure the communication with the endpoint is encrypted via https!
TODO: improving security by supporting OAuth2

Configuration with credentials is in the [mediawiki2drupal] part of config.ini (see config.example.ini)
"""
import requests
import os
import logging
from typing import Final, Dict, Optional
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup, Comment
import configparser
import fortraininglib

class Mediawiki2Drupal():
    """The main class containing all major functionality to import pages from mediawiki into Drupal"""

    HEADERS: Final[Dict[str, str]] = {
        'Accept': 'application/vnd.api+json',
        'Content-Type': 'application/vnd.api+json'
    }

    def __init__(self, endpoint: str, username: str, password: str):
        self._endpoint = endpoint
        self._username = username
        self._password = password
        self.logger = logging.getLogger('pywikitools.mediawiki2drupal')

    def _process_html(self, input: str) -> str:
        """
        Take the original HTML coming from mediawiki and remove unnecessary tags or attributes.

        If we would request the English originals like fortraininglib.get_page_html("Prayer"),
        we would need to remove the [edit] sections. But as we request them with
        fortraininglib.get_page_html("Prayer/en"), we don't have to take care of that anymore
        """
        soup = BeautifulSoup(input, 'html.parser')
        soup.div.unwrap()   # Remove enclosing <div class="mw_parser_output">...</div>
        # Remove the language overview
        for element in soup.find_all(class_="noprint"):
            element.decompose()
        # Removing comments
        for child in soup.children:
            if isinstance(child, Comment):
                child.extract()
        # Changing <h2><span class="mw-headline" id="Headline">Headline</span></h2>
        # to <h2>Headline</h2>
        # TODO: do we need the id tag again to be able to set internal links?
        for element in soup.find_all("span", class_="mw-headline"):
            element.unwrap()
        # Remove empty <span> tags (not sure why they're even there)
        for element in soup.find_all("span"):
            if element.string is None:
                element.extract()
        return str(soup)

    def import_page(self, page: str, language_code: str) -> bool:
        """
        Request the translated page and import it to Drupal
        TODO: count number of languages the page is translated to and import that also into customized field
        @return False on error
        """
        title = fortraininglib.get_translated_title(page, language_code)
        if title is None:
            self.logger.warning(f"Importing page failed: Couldn't get translated title of page {page}.")
            return False
        content = fortraininglib.get_page_html(f"{page}/{language_code}")
        if content is None:
            self.logger.warning(f"Importing page failed: Couldn't get content of page {page}/{language_code}")
            return False

        payload = {
            "data": {
                "type": "node--article",    # TODO: make this configurable
                "attributes": {
                    "title": title,
                    "body": {
                        "value": self._process_html(content),
                        "format": "full_html"
                    }
                }
            }
        }

        r = requests.post(self._endpoint, headers=self.HEADERS, auth=(self._username, self._password), json=payload)
        return r.status_code == 201


if __name__ == "__main__":
    # Read the configuration from config.ini in the same directory
    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')
    if config.has_option("mediawiki2drupal", "endpoint") and \
    config.has_option("mediawiki2drupal", "username") and \
    config.has_option("mediawiki2drupal", "password"):
        mediawiki2drupal = Mediawiki2Drupal(config.get("mediawiki2drupal", "endpoint"),
            config.get("mediawiki2drupal", "username"), config.get("mediawiki2drupal", "password"))
        # TODO: Read parameters from command line
        mediawiki2drupal.import_page("Prayer", "de")
    else:
        print("Configuration in config.ini missing. Aborting now")
