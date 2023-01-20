from typing import List
from .base import CorrectorBase
from .universal import QuotationMarkCorrector, UniversalCorrector, RTLCorrector


class ArabicCorrector(CorrectorBase, UniversalCorrector, RTLCorrector, QuotationMarkCorrector):
    """
    Correct Arabic typos:
    * Arabic quotations start with start with “ and end with ”
      (at least that's what we're doing for now, in some contexts also «quote» is used)
    * Common corrections from UniversalCorrector and RTLCorrector
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct Arabic quotes (example: “Arabic”)

        It must be this way round because ” and “ are not mirrored characters in unicode,
        so in RTL ” comes first and “ at the end (see TestArabicCorrector)
        """
        return self._correct_quotes('”', '“', text)

    def _suffix_for_print_version(self) -> str:
        return "_print"

    def _capitalization_exceptions(self) -> List[str]:
        return []

    def _missing_spaces_exceptions(self) -> List[str]:
        return []
