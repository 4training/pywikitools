import re
from typing import List
from .base import CorrectorBase
from .universal import UniversalCorrector, RTLCorrector


class ArabicCorrector(CorrectorBase, UniversalCorrector, RTLCorrector):

    def correct_punctuation(self, text: str) -> str:
        """Replace normal comma, semicolon, question mark with Arabic version of it"""
        text = text.replace(",", "،")
        text = text.replace("?", "؟")
        # Replace semicolon only if it's after a character or a space (not at the beginning of a line)
        return re.sub(r"([\w ])[;]", "\\1؛", text)

    def _capitalization_exceptions(self) -> List[str]:
        return []   # TODO

    def _missing_spaces_exceptions(self) -> List[str]:
        return []   # TODO
