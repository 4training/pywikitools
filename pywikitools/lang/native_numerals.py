from typing import Dict


class NativeNumerals:
    # Constants
    hindi: Dict[str, str] = {
        '०': '0',
        '१': '1',
        '२': '2',
        '३': '3',
        '४': '4',
        '५': '5',
        '६': '6',
        '७': '7',
        '८': '8',
        '९': '9'
    }

    kannada: Dict[str, str] = {
        '೦': '0',
        '೧': '1',
        '೨': '2',
        '೩': '3',
        '೪': '4',
        '೫': '5',
        '೬': '6',
        '೭': '7',
        '೮': '8',
        '೯': '9'
    }

    tamil: Dict[str, str] = {
        '௦': '0',
        '௧': '1',
        '௨': '2',
        '௩': '3',
        '௪': '4',
        '௫': '5',
        '௬': '6',
        '௭': '7',
        '௮': '8',
        '௯': '9'
    }

    languages: Dict[str, Dict] = {
        'hi': hindi,
        'ka': kannada,
        'ta': tamil
    }

    @staticmethod
    def native_to_standard_numeral(language_code: str, native_text: str) -> str:
        """
        Replace native numerals in a str with standard numerals.

        @param language_code Selects which languages numerals are to be replaced
        @param native_text Text in which native numerals are to be replaced
        @return str with native numerals replaced by standard numerals
        """
        if language_code in NativeNumerals.languages.keys():
            for native_numeral, standard_numeral in NativeNumerals.languages[language_code].items():
                native_text = native_text.replace(native_numeral, standard_numeral)

        return native_text

