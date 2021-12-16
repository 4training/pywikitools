from com.sun.star.lang import Locale

class Lang:
    """ Defining the parameters of a language for LibreOffice
    When editing styles there are three different font categories:
        - Western Text Font
        - Asian Text Font
        - Complex Text Layout (CTL) Font
        -> we need to know which of the three a language belongs to
    the Locale struct has the following parameters: "ISO language code","ISO country code", "variant (browser specific)"
    See also https://www.openoffice.org/api/docs/common/ref/com/sun/star/lang/Locale.html
    """
    FONT_STANDARD = 1
    FONT_ASIAN = 2
    FONT_CTL = 3
    def __init__(self, language_code, country_code=None, font_type=None, custom_font=None):
        """
        @param languagecode: ISO language code
        @param countrycode: ISO country code
        @font_type either Lang.FONT_STANDARD or Lang.FONT_ASIAN or Lang.FONT_CTL
        @custom_font can be defined to use a different font than Arial (used for some complex layout languages)
        """
        self._language_code = language_code
        if country_code is None:
            self._country_code = ''
        else:
            self._country_code = country_code
        self._variant = ''   # Currently it looks like we never need to set it
        if font_type is None:
            self._font_type = Lang.FONT_STANDARD
        else:
            self._font_type = font_type
        self._custom_font = custom_font

    def __str__(self):
        return f'("{self._language_code}","{self._country_code}","{self._variant}")'

    def is_standard(self):
        return self._font_type == Lang.FONT_STANDARD

    def is_asian(self):
        return self._font_type == Lang.FONT_ASIAN

    def is_complex(self):
        return self._font_type == Lang.FONT_CTL

    def has_custom_font(self):
        return self._custom_font is not None

    def get_custom_font(self) -> str:
        return str(self._custom_font)

    def to_locale(self) -> Locale:
        """ Return a LibreOffice Locale object """
        return Locale(self._language_code, self._country_code, '')

# Configuration for each language:
# - the LibreOffice language configuration counterpart (languagecode, countrycode, category)
# - potentially a font name that renders this language well
#
# TODO add missing languages -> unfortunately it seems like we always need a country code as well
# See https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes column alpha-2
LANG_LOCALE = {
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
        'zh': Lang('zh', 'CN', Lang.FONT_ASIAN),
        'ko': Lang('ko', 'KR', Lang.FONT_ASIAN),
        'ar': Lang('ar', 'EG', Lang.FONT_CTL),
        'ar-urdun': Lang('ar', 'JO', Lang.FONT_CTL),
        'hi': Lang('hi', 'IN', Lang.FONT_CTL, 'Lohit Devanagari'),
        'kn': Lang('kn', 'IN', Lang.FONT_CTL, 'Gentium'),
        'ml': Lang('ml', 'IN', Lang.FONT_CTL, 'Gentium'),
        'ckb': Lang('ckb', 'IQ', Lang.FONT_CTL),
        'fa': Lang('fa', 'IR', Lang.FONT_CTL),
        'ta': Lang('ta', 'IN', Lang.FONT_CTL, 'TAMu_Kalyani'),
        'te': Lang('te', 'IN', Lang.FONT_CTL),
        'th': Lang('th', 'TH', Lang.FONT_CTL),
        'ti': Lang('ti', 'ER', Lang.FONT_CTL, 'Abyssinica SIL')}
