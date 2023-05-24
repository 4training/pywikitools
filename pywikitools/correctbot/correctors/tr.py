from typing import List

from .base import CorrectorBase
from .universal import NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector, UniversalCorrector


class TurkishCorrector(CorrectorBase, UniversalCorrector, NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector):
    """
    Correct Turkish typos:
    * Turkish quotations start with “ and end with ”
    * Common corrections from UniversalCorrector and NoSpaceBeforePunctuationCorrector
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct Turkish quotes (example: “alıntı”)"""
        return self._correct_quotes('“', '”', text)

    def _suffix_for_print_version(self) -> str:
        return "_yazdır"

    def _capitalization_exceptions(self) -> List[str]:
        return ["vs.", "vb."]

    def _missing_spaces_exceptions(self) -> List[str]:
        return ["1.Yuhanna", "2.Yuhanna", "3.Yuhanna", "1.Selanikliler", "2.Selanikliler", "1.Timoteos", "2.Timoteos",
                "1.Korintliler", "2.Korintliler", "1.Petrus", "2.Petrus", "1.Samuel", "2.Samuel",
                "1.Krallar", "2.Krallar", "1.Tarihler", "2.Tarihler"]
