:py:mod:`pywikitools.mediawiki2drupal`
======================================

.. py:module:: pywikitools.mediawiki2drupal

.. autoapi-nested-parse::

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



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.mediawiki2drupal.Mediawiki2Drupal




.. py:class:: Mediawiki2Drupal(fortraininglib: pywikitools.fortraininglib.ForTrainingLib, endpoint: str, username: str, password: str, content_type: str = 'page', change_hrefs: Dict[str, str] = None, img_src_rewrite: Dict[str, str] = None)

   The main class containing all major functionality to import pages from mediawiki into Drupal

   .. py:method:: get_page_id(self, search_criteria: Dict[str, str])

      Search for a page where the given field matches the given value
      If at least one page exists, return the ID of the first page
      This will issue a warning if more than one page was found
      @param search_criteria: at least one entry of field_name -> value
      Example: get_page_id({"title": "Gebet"}) will call /jsonapi/node/page?filter[title][value]=Gebet
      @return None in case no matching page was found


   .. py:method:: import_page(self, page: str, language_code: str, article_id: int = None, custom_fields: Dict[str, str] = None) -> bool

      Request the translated page and import it to Drupal
      @param article_id if given, try to patch this existing node. If None, create new node
      @param custom_fields allows to set more fields of the content type to custom values
      @return False on error



