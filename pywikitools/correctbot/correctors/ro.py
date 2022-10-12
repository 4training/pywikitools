from typing import List

from .base import CorrectorBase
from .universal import NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector, UniversalCorrector


class RomanianCorrector(CorrectorBase, UniversalCorrector, NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector):
    """
    Correct Romanian typos:
    * Romanian quotations start with „ and end with ”
    * Common corrections from UniversalCorrector and NoSpaceBeforePunctuationCorrector
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct Romanian quotes (example: „quote”)"""
        return self._correct_quotes('„', '”', text)

    def _capitalization_exceptions(self) -> List[str]:
        return ["ex.", "Ex."]

    def _missing_spaces_exceptions(self) -> List[str]:
        return []
