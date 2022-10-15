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

    def correct_s_comma(self, text: str) -> str:
        """Replace Ş/ş with the correct Ș/ș in Romanian"""
        # See https://en.wikipedia.org/wiki/S-comma
        text = text.replace("Ş", "Ș")
        return text.replace("ş", "ș")

    def _capitalization_exceptions(self) -> List[str]:
        return ["ex.", "Ex.", "ș.a.m.d.", "ș.a.m.", "ș.a.", "Ș.a.m.d.", "Ș.a.m.", "Ș.a."]
        # TODO only adding "ș.a.m.d." is not enough, that's currently a workaround, find a better solution

    def _missing_spaces_exceptions(self) -> List[str]:
        return ["ș.a.m.d.", "Ș.a.m.d."]
