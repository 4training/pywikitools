from typing import Final, Dict, Optional
from enum import Enum
import uno                              # type: ignore
from com.sun.star.lang import Locale    # type: ignore

class FontType(Enum):
    """LibreOffice has three different font categories"""
    FONT_STANDARD = 1   # Western Text Font
    FONT_ASIAN = 2      # Asian Text Font
    FONT_CTL = 3        # Complex Text Layout (CTL) Font

class Lang:
    """ Defining the parameters of a language for LibreOffice
    When editing styles we need to know which of the three FontTypes a language belongs to.
    The Locale struct has the following parameters: "ISO language code","ISO country code", "variant (browser specific)"
    See also https://www.openoffice.org/api/docs/common/ref/com/sun/star/lang/Locale.html
    Currently there is no need for the variant and we always set it as an empty string
    """
    __slots__ = ["language_code", "country_code", "font_type", "_custom_font"]

    def __init__(self, language_code: str, country_code: str,
                 font_type: FontType = FontType.FONT_STANDARD, custom_font: Optional[str] = None):
        """
        @param language_code: ISO language code
        @param country_code: ISO country code
        @custom_font can be defined to use a different font than Arial (used for some complex layout languages)
        """
        self.language_code: Final[str] = language_code
        self.country_code: Final[str] = country_code
        self.font_type: Final[FontType] = font_type
        self._custom_font: Optional[str] = custom_font

    def __str__(self):
        return f'("{self.language_code}","{self.country_code}","")'

    def is_standard(self) -> bool:
        return self.font_type == FontType.FONT_STANDARD

    def is_asian(self) -> bool:
        return self.font_type == FontType.FONT_ASIAN

    def is_complex(self) -> bool:
        return self.font_type == FontType.FONT_CTL

    def has_custom_font(self) -> bool:
        return self._custom_font is not None

    def get_custom_font(self) -> str:
        """Returns empty string if there was no custom font defined"""
        return str(self._custom_font or '')

    def to_locale(self) -> Locale:
        """ Return a LibreOffice Locale object """
        return Locale(self.language_code, self.country_code, '')

# Configuration for each language:
# - the LibreOffice language configuration counterpart (languagecode, countrycode, category)
# - potentially a font name that renders this language well
#
# TODO add missing languages -> unfortunately it seems like we always need a country code as well
# See https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes column alpha-2
LANG_LOCALE: Final[Dict[str, Lang]] = {
        'de': Lang('de', 'DE'),
        'az': Lang('az', 'AZ'),
        'bg': Lang('bg', 'BG'),
        'cs': Lang('cs', 'CZ'),
        'en': Lang('en', 'US'),
        'fr': Lang('fr', 'FR'),
        'pt-br': Lang('pt', 'BR'),
        'nl': Lang('nl', 'NL'),
        'id': Lang('id', 'ID'),
        'ro': Lang('ro', 'RO'),
        'es': Lang('es', 'ES'),
        'it': Lang('it', 'IT'),
        'ka': Lang('ka', 'GE'),
        'ku': Lang('ku', 'TR'),
        'sv': Lang('sv', 'SE'),
        'sq': Lang('sq', 'AL'),
        'pl': Lang('pl', 'PL'),
        'ru': Lang('ru', 'RU'),
        'sk': Lang('sk', 'SK'),
        'tr': Lang('tr', 'TR'),
        'tr-tanri': Lang('tr', 'TR'),
        'vi': Lang('vi', 'VN'),
        'ky': Lang('ky', 'KG'),
        'sw': Lang('sw', 'KE'),
        'sr': Lang('sh', 'RS'),
        'nb': Lang('nb', 'NO'),
        'zh': Lang('zh', 'CN', FontType.FONT_ASIAN),
        'ko': Lang('ko', 'KR', FontType.FONT_ASIAN),
        'ar': Lang('ar', 'EG', FontType.FONT_CTL),
        'ar-urdun': Lang('ar', 'JO', FontType.FONT_CTL),
        'hi': Lang('hi', 'IN', FontType.FONT_CTL, 'Lohit Devanagari'),  # sudo apt-get install fonts-lohit-deva
        'kn': Lang('kn', 'IN', FontType.FONT_CTL, 'Gentium'),           # sudo apt-get install fonts-sil-gentiumplus
        'ml': Lang('ml', 'IN', FontType.FONT_CTL, 'Gentium'),
        'ckb': Lang('ckb', 'IQ', FontType.FONT_CTL),
        'fa': Lang('fa', 'IR', FontType.FONT_CTL),
        'ta': Lang('ta', 'IN', FontType.FONT_CTL, 'TAMu_Kalyani'),      # sudo apt-get install fonts-taml-tamu
        'te': Lang('te', 'IN', FontType.FONT_CTL),
        'th': Lang('th', 'TH', FontType.FONT_CTL),
        'ti': Lang('ti', 'ER', FontType.FONT_CTL, 'Abyssinica SIL')}    # sudo apt-get install fonts-sil-abyssinica
