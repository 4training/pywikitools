from typing import List

from .base import CorrectorBase
from .universal import NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector, UniversalCorrector


class KyrgyzCorrector(CorrectorBase, UniversalCorrector, NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector):
    """
    Correct Kyrgyz typos:
    * Kyrgyz quotations start with « and end with »
    * Common corrections from UniversalCorrector and NoSpaceBeforePunctuationCorrector
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct Kyrgyz quotes (example: «quote»)"""
        return self._correct_quotes('«', '»', text)

    def _suffix_for_print_version(self) -> str:
        return "_көчүрмөсүн_чыгаруу"

    def _capitalization_exceptions(self) -> List[str]:
        return []

    def _missing_spaces_exceptions(self) -> List[str]:
        return []
