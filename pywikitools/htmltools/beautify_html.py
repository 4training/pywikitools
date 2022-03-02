import logging
from typing import Dict
from bs4 import BeautifulSoup, Comment

class BeautifyHTML:
    """
    Take the original HTML coming from mediawiki and remove unnecessary tags or attributes.

    This involves removing of comments, removing some CSS classes and
    rewriting <img src="" so that the resulting HTML can be used elsewhere
    """
    def __init__(self, img_src_base: str = '/files/', change_hrefs: Dict[str, str] = None,
                 img_src_rewrite: Dict[str, str] = None):
        """
        @param img_src_base: Change all <img src=""> tags to src="[img_src_base][image name]"
        @param change_hrefs: Rewriting <a href=""> destinations (old destination -> new destination)
        @param img_src_rewrite: Rewriting <img src=""> (old file name -> new file name; without any folders)
        """
        self._img_src_base = img_src_base
        self._change_hrefs = change_hrefs
        self._img_src_rewrite = img_src_rewrite
        self.logger = logging.getLogger('pywikitools.lib.htmltools.BeautifyHTML')

    def process_html(self, text: str) -> str:
        """
        Entry function: Expects input from fortraininglib.get_page_html() and returns improved html

        TODO For English pages you need to take fortraininglib.get_page_html("Prayer/en").
        Don't use fortraininglib.get_page_html("Prayer") as we would need to remove the [edit] sections
        TODO think of a better architecture?
        """
        soup = BeautifulSoup(text, 'html.parser')
        soup.div.unwrap()   # Remove enclosing <div class="mw-parser-output">...</div>
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
            self.img_rewrite_handler(element)

        for element in soup.find_all("a", href=True):
            if element['href'].startswith("/File:"):
                # Remove <a> links around <img> tags
                element.unwrap()
                continue
            # Rewrite hrefs
            if self._change_hrefs is not None:
                if element['href'] in self._change_hrefs:
                    new_href = self._change_hrefs[element['href']]
                    self.logger.info(f"Rewriting a href source {element['href']} with {new_href}")
                    element['href'] = new_href
                else:
                    self.logger.warning(f"Couldn't find href rewrite for destination {element['href']}")
            del element['title']

        return str(soup)

    def _extract_image_name(self, path: str) -> str:
        """
        Extract the "real" name of the image in the mediawiki system out of a given path

        We receive <img> tags with src tags following one of two possible structures:
          src="/mediawiki/images/thumb/5/51/Hand_5.png/30px-Hand_5.png" -> extract "Hand_5.png"
          src="/mediawiki/images/a/ab/Family.png" -> extract "Family.png"
        """
        parts = path.split('/')
        if (len(parts) < 4) or (parts[0] != '') or (parts[1] != 'mediawiki') or (parts[2] != 'images'):
            self.logger.warning(f'Unexpected source attribute in <img>: src="{path}"')
            return parts.pop()  # return the last part

        if parts[3] == 'thumb':
            if len(parts) != 8:
                self.logger.warning(f'Unexpected source attribute in <img>: src="{path}"')
                return parts.pop()
            return parts[6]
        return parts.pop()

    def img_rewrite_handler(self, element):
        """
        Do some rewriting of <img> elements

        In our default implementation we remove the srcset attribute (as we don't need it)
        and apply replacements for the src attribute.

        You can customize the behaviour by sub-classing BeautifyHTML and overwriting this method
        @param element: Part of the BeautifulSoup data structure, will be modified directly
        """
        del element['srcset']
        img_src = self._extract_image_name(str(element['src']))
        element['src'] = self._img_src_base + img_src
        if self._img_src_rewrite is not None:
            if img_src in self._img_src_rewrite:
                new_src = self._img_src_base + self._img_src_rewrite[img_src]
                self.logger.info(f"Replacing img src {element['src']} with {new_src}")
                element['src'] = new_src
            else:
                self.logger.info(f"No img src replacement for {img_src}")
