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
from typing import Final, Dict
from bs4 import BeautifulSoup, Comment
import configparser
from pywikitools.fortraininglib import ForTrainingLib


class Mediawiki2Drupal():
    """The main class containing all major functionality to import pages from mediawiki into Drupal"""

    HEADERS: Final[Dict[str, str]] = {
        'Accept': 'application/vnd.api+json',
        'Content-Type': 'application/vnd.api+json'
    }

    def __init__(self, fortraininglib: ForTrainingLib, endpoint: str, username: str, password: str,
                 content_type: str = "page", change_hrefs: Dict[str, str] = None,
                 img_src_rewrite: Dict[str, str] = None):
        """
        @param content_type refers to the Drupal content type that we should create articles with.
        This needs to be the system name of a content type
        ("page" is the system name of the "basic page" content type, one of the defaults in Drupal)
        @param change_hrefs: rewrite <a href=""> properties
        @param img_src_rewrite: dictionary with new href sources
        """
        self._endpoint = endpoint
        self._username = username
        self._password = password
        self._content_type = content_type
        self._change_hrefs = change_hrefs
        self._img_src_rewrite = img_src_rewrite
        self.fortraininglib: Final[ForTrainingLib] = fortraininglib
        self.logger: logging.Logger = logging.getLogger('pywikitools.mediawiki2drupal')

    def _process_html(self, input: str, custom_fields: Dict[str, str] = None) -> str:
        """
        TODO Start using pywikitools.lib.html.BeautifyHTML
        TODO Subclass BeautifyHTML and overwrite image_rewrite_handler to add customizations for "hands" images
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

        # Correct image hrefs
        for element in soup.find_all("img"):
            del element['srcset']
            img_src = str(element['src'])
            last_slash = img_src.rfind('/')
            if last_slash >= 0:
                img_src = img_src[last_slash+1:]
            if (self._img_src_rewrite is not None) and (img_src in self._img_src_rewrite):
                self.logger.info(f"Replacing img src {element['src']} with {self._img_src_rewrite[img_src]}")
                element['src'] = self._img_src_rewrite[img_src]
                if img_src.startswith('30px-Hand'):  # some customizations for the five "hands" images in God's Story
                    del element['height']
                    del element['width']
                    element['style'] = 'height:80px; margin-right:20px'
                    element['align'] = 'left'
            else:
                self.logger.warning(f"Missing img src replacement for {img_src}")

        for element in soup.find_all("a", href=True):
            if element['href'].startswith("/File:"):
                # Remove <a> links around <img> tags
                element.unwrap()
                continue
            # Rewrite hrefs
            if self._change_hrefs is not None:
                if element['href'] in self._change_hrefs:
                    self.logger.info(f"Rewriting a href source {element['href']} "
                                     f"with {self._change_hrefs[element['href']]}")
                    element['href'] = self._change_hrefs[element['href']]
                else:
                    self.logger.warning(f"Couldn't find href rewrite for destination {element['href']}")
            del element['title']

        return str(soup)

    def get_page_id(self, search_criteria: Dict[str, str]):
        """
        Search for a page where the given field matches the given value
        If at least one page exists, return the ID of the first page
        This will issue a warning if more than one page was found
        @param search_criteria: at least one entry of field_name -> value
        Example: get_page_id({"title": "Gebet"}) will call /jsonapi/node/page?filter[title][value]=Gebet
        @return None in case no matching page was found
        """
        payload = {}
        for field_name, value in search_criteria.items():
            payload[f"filter[{field_name}][value]"] = value
        r = requests.get(f"{self._endpoint}/node/{self._content_type}",
                         auth=(self._username, self._password), params=payload)
        if "data" not in r.json():
            return None
        if not isinstance(r.json()["data"], list):
            return None
        if len(r.json()["data"]) == 0:
            return None
        if len(r.json()["data"]) > 1:
            self.logger.warning(f"Found more than one page with search criteria {field_name}={value}.")
        return r.json()["data"][0]["id"]

    def import_page(self, page: str, language_code: str, article_id: int = None,
                    custom_fields: Dict[str, str] = None) -> bool:
        """
        Request the translated page and import it to Drupal
        @param article_id if given, try to patch this existing node. If None, create new node
        @param custom_fields allows to set more fields of the content type to custom values
        @return False on error
        """
        title = self.fortraininglib.get_translated_title(page, language_code)
        if title is None:
            self.logger.warning(f"Importing page failed: Couldn't get translated title of page {page}.")
            return False
        content = self.fortraininglib.get_page_html(f"{page}/{language_code}")
        if content is None:
            self.logger.warning(f"Importing page failed: Couldn't get content of page {page}/{language_code}")
            return False

        payload = {
            "data": {
                "type": f"node--{self._content_type}",
                "attributes": {
                    "title": title,
                    "body": {
                        "value": self._process_html(content, custom_fields),
                        "format": "full_html"
                    }
                }
            }
        }
        payload["data"]["attributes"].update(custom_fields)
        self.logger.debug(payload)

        if article_id is None:
            # Create new article
            r = requests.post(f"{self._endpoint}/node/{self._content_type}",
                              headers=self.HEADERS, auth=(self._username, self._password), json=payload)
            self.logger.debug(r.status_code)
            self.logger.debug(r.json())
        else:
            # Update existing article
            payload["data"]["id"] = article_id
            r = requests.patch(f"{self._endpoint}/node/{self._content_type}/{article_id}",
                               headers=self.HEADERS, auth=(self._username, self._password), json=payload)
            self.logger.debug(r.status_code)
            self.logger.debug(r.json())

        if r.status_code not in [200, 201]:
            error = 'No error details given.'
            if "errors" in r.json() and isinstance(r.json()["errors"], list):
                if "title" in r.json()["errors"][0]:
                    error = r.json()["errors"][0]["title"]
                    if "detail" in r.json()["errors"][0]:
                        error += f". Details: {r.json()['errors'][0]['detail']}"
            self.logger.warning(f"Failed to import page {page}/{language_code}. {error}")
        return r.status_code in [200, 201]


if __name__ == "__main__":
    # Read the configuration from config.ini in the same directory
    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__)) + '/config.ini')
    if config.has_option("mediawiki", "baseurl") and config.has_option("mediawiki", "scriptpath") and \
       config.has_option("mediawiki2drupal", "endpoint") and \
       config.has_option("mediawiki2drupal", "username") and config.has_option("mediawiki2drupal", "password"):
        fortraininglib = ForTrainingLib(config.get("mediawiki", "baseurl"), config.get("mediawiki", "scriptpath"))
        mediawiki2drupal = Mediawiki2Drupal(fortraininglib, config.get("mediawiki2drupal", "endpoint"),
                                            config.get("mediawiki2drupal", "username"),
                                            config.get("mediawiki2drupal", "password"))
        # TODO: Read parameters from command line
        mediawiki2drupal.import_page("Prayer", "de")
    else:
        print("Configuration in config.ini missing. Aborting now")
