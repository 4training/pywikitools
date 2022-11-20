from typing import List
from .base import CorrectorBase
from .universal import QuotationMarkCorrector, UniversalCorrector, RTLCorrector


class PersianCorrector(CorrectorBase, UniversalCorrector, RTLCorrector, QuotationMarkCorrector):
    """
    Correct Persian typos:
    * Persian quotations start with start with « and end with »
    * Common corrections from UniversalCorrector and RTLCorrector
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct Persian quotes (example: «نقل قول»)"""
        return self._correct_quotes('«', '»', text)

    def _suffix_for_print_version(self) -> str:
        return "_برای_چاپ"

    def _capitalization_exceptions(self) -> List[str]:
        return []

    def _missing_spaces_exceptions(self) -> List[str]:
        return []
