from typing import List

from .base import CorrectorBase
from .universal import NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector, UniversalCorrector


class DutchCorrector(CorrectorBase, UniversalCorrector, NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector):
    """
    Correct Dutch typos:
    * Dutch quotations start with “ and end with ”
    * Common corrections from UniversalCorrector and NoSpaceBeforePunctuationCorrector
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct Dutch quotes (example: “quote”)"""
        return self._correct_quotes('“', '”', text)

    def _suffix_for_print_version(self) -> str:
        return "_print"     # TODO

    def _capitalization_exceptions(self) -> List[str]:
        return ["bijv.", "bv.", "Bv.", "Bijv."]

    def _missing_spaces_exceptions(self) -> List[str]:
        return []
