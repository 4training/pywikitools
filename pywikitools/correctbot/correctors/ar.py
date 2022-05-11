from .base import CorrectorBase
from .universal import UniversalCorrector, RTLCorrector


class ArabicCorrector(CorrectorBase, UniversalCorrector, RTLCorrector):

    def correct_punctuation(self, text: str) -> str:
        """Replace normal comma, semicolon, question mark with Arabic version of it"""
        result = text.replace(",", "،")
        result = result.replace("?", "؟")
        return result.replace(";", "؛")
