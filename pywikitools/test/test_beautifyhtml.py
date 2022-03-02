from typing import Dict
import unittest

from bs4 import BeautifulSoup, Comment
from bs4.element import NavigableString
from pywikitools import fortraininglib
from pywikitools.htmltools.beautify_html import BeautifyHTML

class TestBeautifyHTML(unittest.TestCase):
    def test_get_image_basename(self):
        beautify = BeautifyHTML()
        self.assertEqual(beautify._extract_image_name(
            "/mediawiki/images/thumb/5/51/Hand_5.png/30px-Hand_5.png"), "Hand_5.png")
        self.assertEqual(beautify._extract_image_name(
            "/mediawiki/images/a/ab/Family.png"), "Family.png")
        with self.assertLogs('pywikitools.lib.htmltools.BeautifyHTML', level='WARNING'):
            self.assertEqual(beautify._extract_image_name(
                "/path/Test.png"), "Test.png")
        with self.assertLogs('pywikitools.lib.htmltools.BeautifyHTML', level='WARNING'):
            self.assertEqual(beautify._extract_image_name(
                "/mediawiki/images/thumb/wrong_structure.png"), "wrong_structure.png")
        with self.assertLogs('pywikitools.lib.htmltools.BeautifyHTML', level='WARNING'):
            self.assertEqual(beautify._extract_image_name("Test.png"), "Test.png")

    def test_img_rewrite_handler(self):
        img_rewrite: Dict[str, str] = {
            "Family.png": "Rename_family.png",
            "Body.png": "Rename_body.png"
        }
        test_dict: Dict[str, str] = {   # Dictionary of input -> expected result
            "/mediawiki/images/thumb/5/51/Family.png/120px-Family.png": "/files/Rename_family.png",
            "/mediawiki/images/a/ab/Family.png": "/files/Rename_family.png",
            "/mediawiki/images/thumb/5/51/Hand_5.png/30px-Hand_5.png": "/files/Hand_5.png"
        }
        beautify = BeautifyHTML(img_src_rewrite=img_rewrite)
        for src_in, src_out in test_dict.items():
            element: Dict[str, str] = {'srcset': 'something', 'src': src_in}
            beautify.img_rewrite_handler(element)
            self.assertNotIn('srcset', element)
            self.assertEqual(element['src'], src_out)

    def test_with_real_example(self):
        """Request HTML via fortraininglib, process it and check the result with BeautifulSoup"""
        # We're not going through all of fortraininglib.get_worksheet_list() because that takes some extra time

        # There should be no empty <span> sections anymore
        soup = BeautifulSoup(BeautifyHTML().process_html(fortraininglib.get_page_html("Church/en")), 'html.parser')
        self.assertEqual(len(soup.find_all("div", class_="mw-parser-output")), 0)
        for element in soup.find_all("span"):
            self.assertIsNotNone(element.string)

        # Make sure there are only <h2>Title</h2> with no other tags inside
        for element in soup.find_all("h2"):
            self.assertEqual(len(element.contents), 1)
            self.assertIsInstance(element.contents[0], NavigableString)

        # Make sure we stripped out all comments
        for element in soup.descendants:
            self.assertNotIsInstance(element, Comment)

        # There shouldn't be any <a><img ... /></a> left
        self.assertEqual(len(soup.select("a img")), 0)

        # Now check the change_hrefs functionality
        change_hrefs: Dict[str, str] = {
            "/Prayer": "/Prayer_redirected",
            "/Church": "/redirected/Church"
        }
        beautify = BeautifyHTML(change_hrefs=change_hrefs)
        self.assertEqual(beautify.process_html('<div><a href="/Prayer"><span>test</span></a></div>'),
                                               '<a href="/Prayer_redirected"><span>test</span></a>')
        self.assertEqual(beautify.process_html('<div><p><b><a href="/Church">Test<br/></a></b></p></div>'),
                                               '<p><b><a href="/redirected/Church">Test<br/></a></b></p>')
        with self.assertLogs('pywikitools.lib.htmltools.BeautifyHTML', level='WARNING'):
            self.assertEqual(beautify.process_html('<div><a href="/other">not in change_hrefs</a></div>'),
                                                   '<a href="/other">not in change_hrefs</a>')


if __name__ == '__main__':
    unittest.main()

