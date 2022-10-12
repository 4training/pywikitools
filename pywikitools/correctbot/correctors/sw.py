from typing import List

from .base import CorrectorBase
from .universal import NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector, UniversalCorrector


class SwahiliCorrector(CorrectorBase, UniversalCorrector, NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector):
    """
    Correct Swahili typos:
    * Swahili quotations start with “ and end with ”
    * Common corrections from UniversalCorrector and NoSpaceBeforePunctuationCorrector
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct Swahili quotes (example: “quote”)"""
        return self._correct_quotes('“', '”', text)

    def _capitalization_exceptions(self) -> List[str]:
        return []

    def _missing_spaces_exceptions(self) -> List[str]:
        return []
