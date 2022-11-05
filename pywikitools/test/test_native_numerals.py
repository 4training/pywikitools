"""
Test the function of native_numerals

Run tests:
    python3 -m unittest test_native_numerals.py
"""
import unittest

from pywikitools.lang.native_numerals import native_to_standard_numeral


class TestNativeNumerals(unittest.TestCase):

    def test_native_to_standard_numeral(self):
        self.assertEqual(native_to_standard_numeral('xy', '0123456789'), '0123456789')
        self.assertEqual(native_to_standard_numeral('hi', 'no change'), 'no change')
        self.assertEqual(native_to_standard_numeral('fa', '۰۱.۲۳.۴۵.۶۷.۸۹'), '01.23.45.67.89')
        self.assertEqual(native_to_standard_numeral('hi', '०१२३४.५.६.७८९'), '01234.5.6.789')
        self.assertEqual(native_to_standard_numeral('kn', '೦೧.೨.೩.೪.೫೬೭.೮೯'), '01.2.3.4.567.89')
        self.assertEqual(native_to_standard_numeral('ta', '௦௧.௨.௩.௪.௫.௬௭௮௯'), '01.2.3.4.5.6789')


if __name__ == '__main__':
    unittest.main()
