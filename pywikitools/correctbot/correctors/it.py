from typing import List

from .base import CorrectorBase
from .universal import NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector, UniversalCorrector


class ItalianCorrector(CorrectorBase, UniversalCorrector, NoSpaceBeforePunctuationCorrector, QuotationMarkCorrector):
    """
    Correct Italian typos:
    * For Italian quotes we “ at the beginning and ” in the end
      (There is also «quotes» in use but we decided for them)
    * Common corrections from UniversalCorrector and NoSpaceBeforePunctuationCorrector
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct Italian quotes (example: “quote”)"""
        return self._correct_quotes('“', '”', text)

    def _suffix_for_print_version(self) -> str:
        return "_print"     # TODO

    def _capitalization_exceptions(self) -> List[str]:
        return []

    def _missing_spaces_exceptions(self) -> List[str]:
        return []
