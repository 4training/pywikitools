from typing import Dict, Final, Set

SNIPPET_WARN_LENGTH = 3     # give a warning when search or replace string is shorter than 3 characters
# The following templates don't contain any translation units and can be ignored
IGNORE_TEMPLATES = ['Template:DocDownload', 'Template:OdtDownload', 'Template:PdfDownload',
                    'Template:PrintPdfDownload',
                    'Template:Translatable template', 'Template:Version', 'Module:Template translation',
                    'Template:Italic']
# for the following languages we don't add ", version x.y" to the keywords in the document properties
# because the translation of "version" is very close to the English word "version"
# TODO should 'ko' be in this list?
NO_ADD_ENGLISH_VERSION = ['de', 'pt-br', 'cs', 'nl', 'fr', 'id', 'ro', 'es', 'sv', 'tr', 'tr-tanri']


class TranslateOdtConfig:
    """Contains configuration on how to process one worksheet:
    Which translation units should be ignored?
    Which translation units should be processed multiple times?

    It is read from a config file (see TranslateODT.read_worksheet_config()) of the following structure:
    [Ignore]
    # Don't process the following translation units
    Template:BibleReadingHints/18
    Template:BibleReadingHints/25

    [Multiple]
    # Process the following translation unit 5 times
    Template:BibleReadingHints/6 = 5
    """
    __slots__ = ["ignore", "multiple"]

    def __init__(self):
        # Set of translation unit identifiers that shouldn't be processed
        self.ignore: Final[Set[str]] = set()
        # Translation unit identifier -> number of times it should be processed
        self.multiple: Final[Dict[str, int]] = {}
