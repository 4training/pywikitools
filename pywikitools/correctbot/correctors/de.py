from typing import List

from .base import CorrectorBase
from .universal import NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector, UniversalCorrector


class GermanCorrector(CorrectorBase, UniversalCorrector, NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector):
    """
    Correct German typos:
    * German quotations start with „ and end with “ („Beispiel“)
    * Common corrections from UniversalCorrector and NoSpaceBeforePunctuationCorrector
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct German quotes (example: „korrekt“)"""
        return self._correct_quotes('„', '“', text)

    def _suffix_for_print_version(self) -> str:
        return "_Druckversion"

    def _capitalization_exceptions(self) -> List[str]:
        return ["Z.B.", "z.B.", "ggf.", "Ggf.", "usw."]

    def _missing_spaces_exceptions(self) -> List[str]:
        return ["1.Mose", "2.Mose", "3.Mose", "4.Mose", "5.Mose", "1.Samuel", "2.Samuel", "1.Könige", "2.Könige",
                "1.Chronik", "2.Chronik", "1.Korinther", "2.Korinther", "1.Thessalonicher", "2.Thessalonicher",
                "1.Timotheus", "2.Timotheus", "1.Petrus", "2.Petrus", "3.Petrus", "1.Johannes", "2.Johannes",
                "z.B.", "Z.B."]
