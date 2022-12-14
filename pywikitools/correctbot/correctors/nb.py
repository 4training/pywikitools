from typing import List

from .base import CorrectorBase
from .universal import NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector, UniversalCorrector


class NorwegianCorrector(CorrectorBase, UniversalCorrector, NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector):
    """
    Correct Norwegian typos:
    * Norwegian quotations start with « and end with »
    * Common corrections from UniversalCorrector and NoSpaceBeforePunctuationCorrector
    This is Norwegian Bokmål
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct Norwegian quotes (example: «quote»)"""
        return self._correct_quotes('«', '»', text)

    def _suffix_for_print_version(self) -> str:
        return "_print"     # TODO

    def _capitalization_exceptions(self) -> List[str]:
        return []

    def _missing_spaces_exceptions(self) -> List[str]:
        return []
