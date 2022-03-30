"""
Test the function of native_numerals

Run tests:
    python3 -m unittest test_native_numerals.py
"""
import unittest

from pywikitools.lang.native_numerals import NativeNumerals


class TestNativeNumerals(unittest.TestCase):

    def test_native_to_standard_numeral(self):
        self.assertEqual(NativeNumerals.native_to_standard_numeral('xy', '0123456789'), '0123456789')
        self.assertEqual(NativeNumerals.native_to_standard_numeral('hi', 'no change'), 'no change')
        self.assertEqual(NativeNumerals.native_to_standard_numeral('hi', '०१२३४.५.६.७८९'), '01234.5.6.789')
        self.assertEqual(NativeNumerals.native_to_standard_numeral('ka', '೦೧.೨.೩.೪.೫೬೭.೮೯'), '01.2.3.4.567.89')
        self.assertEqual(NativeNumerals.native_to_standard_numeral('ta', '௦௧.௨.௩.௪.௫.௬௭௮௯'), '01.2.3.4.5.6789')


if __name__ == '__main__':
    unittest.main()
