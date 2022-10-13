from typing import List

from .base import CorrectorBase
from .universal import NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector, UniversalCorrector


class AlbanianCorrector(CorrectorBase, UniversalCorrector, NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector):
    """
    Correct Albanian typos:
    * Albanian quotations start with « and end with »
    * Common corrections from UniversalCorrector and NoSpaceBeforePunctuationCorrector
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct Albanian quotes (example: «quote»)"""
        return self._correct_quotes('«', '»', text)

    def _capitalization_exceptions(self) -> List[str]:
        return ["p.sh.", "P.sh.", "p. sh.", "P. sh."]

    def _missing_spaces_exceptions(self) -> List[str]:
        return ["p.sh.", "P.sh."]
