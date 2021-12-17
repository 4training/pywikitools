"""
Test the Lang class defined in lang/libreoffice_lang.py

Run tests:
    python3 test_lang.py
"""
import unittest
import uno
from com.sun.star.lang import Locale
from lang.libreoffice_lang import FontType, Lang


class TestLang(unittest.TestCase):
    def setUp(self):
        self.de = Lang('de', 'DE')
        self.zh = Lang('zh', 'CN', FontType.FONT_ASIAN)
        self.kn = Lang('kn', 'IN', FontType.FONT_CTL, 'Gentium')

    def test_is_standard(self):
        self.assertTrue(self.de.is_standard())
        self.assertFalse(self.zh.is_standard())
        self.assertFalse(self.kn.is_standard())

    def test_is_asian(self):
        self.assertFalse(self.de.is_asian())
        self.assertTrue(self.zh.is_asian())
        self.assertFalse(self.kn.is_asian())

    def test_is_complex(self):
        self.assertFalse(self.de.is_complex())
        self.assertFalse(self.zh.is_complex())
        self.assertTrue(self.kn.is_complex())

    def test_has_custom_font(self):
        self.assertFalse(self.de.has_custom_font())
        self.assertTrue(self.kn.has_custom_font())

    def test_get_custom_font(self):
        self.assertEqual(self.de.get_custom_font(), '')
        self.assertEqual(self.kn.get_custom_font(), 'Gentium')

    def test_to_str(self):
        self.assertEqual(str(self.de), '("de","DE","")')
        self.assertEqual(str(self.zh), '("zh","CN","")')
        self.assertEqual(str(self.kn), '("kn","IN","")')

    def test_to_locale(self):
        locale = Locale('de', 'DE', '')
        self.assertEqual(self.de.to_locale(), locale)

if __name__ == '__main__':
    unittest.main()
