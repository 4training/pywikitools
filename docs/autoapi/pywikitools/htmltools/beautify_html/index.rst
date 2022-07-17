:orphan:

:py:mod:`pywikitools.htmltools.beautify_html`
=============================================

.. py:module:: pywikitools.htmltools.beautify_html


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   pywikitools.htmltools.beautify_html.BeautifyHTML




.. py:class:: BeautifyHTML(img_src_base: str = '/files/', change_hrefs: Dict[str, str] = None, img_src_rewrite: Dict[str, str] = None)

   Take the original HTML coming from mediawiki and remove unnecessary tags or attributes.

   This involves removing of comments, removing some CSS classes and
   rewriting <img src="" so that the resulting HTML can be used elsewhere

   .. py:method:: process_html(self, text: str) -> str

      Entry function: Expects input from fortraininglib.get_page_html() and returns improved html

      TODO For English pages you need to take fortraininglib.get_page_html("Prayer/en").
      Don't use fortraininglib.get_page_html("Prayer") as we would need to remove the [edit] sections
      TODO think of a better architecture?


   .. py:method:: img_rewrite_handler(self, element)

      Do some rewriting of <img> elements

      In our default implementation we remove the srcset attribute (as we don't need it)
      and apply replacements for the src attribute.

      You can customize the behaviour by sub-classing BeautifyHTML and overwriting this method
      @param element: Part of the BeautifulSoup data structure, will be modified directly



