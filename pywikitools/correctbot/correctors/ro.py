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

    def correct_s_and_t_comma_also_in_title(self, text: str) -> str:
        """Replace Ş/ş/Ţ/ţ with the correct Ș/ș/Ț/ț in Romanian"""
        # See https://en.wikipedia.org/wiki/S-comma and https://en.wikipedia.org/wiki/T-comma
        text = text.replace("Ţ", "Ț")
        text = text.replace("ţ", "ț")
        text = text.replace("Ş", "Ș")
        return text.replace("ş", "ș")

    def _suffix_for_print_version(self) -> str:
        return "_print"     # TODO

    def _capitalization_exceptions(self) -> List[str]:
        return ["ex.", "Ex.", "ș.a.m.d.", "ș.a.m.", "ș.a.", "Ș.a.m.d.", "Ș.a.m.", "Ș.a."]
        # TODO only adding "ș.a.m.d." is not enough, that's currently a workaround, find a better solution

    def _missing_spaces_exceptions(self) -> List[str]:
        return ["ș.a.m.d.", "Ș.a.m.d."]
