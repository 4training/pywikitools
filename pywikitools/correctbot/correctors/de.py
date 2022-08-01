import logging
import re
from typing import List

from .base import CorrectorBase
from .universal import NoSpaceBeforePunctuationCorrector, UniversalCorrector


class GermanCorrector(CorrectorBase, UniversalCorrector, NoSpaceBeforePunctuationCorrector):
    """
    Correct typical German typos. Currently one rule is implemented
    * German quotations start with „ and end with “ („Beispiel“)
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct German quotes (example: „korrekt“)"""
        splitted_text: List[str] = re.split('[„“”"]', text)
        if (len(splitted_text) % 2) != 1:   # Not an even amount of quotes: we don't do anything
            logger = logging.getLogger(__name__)
            logger.warning(f'Found uneven amount of quotation marks (")! Please correct manually: {text}')
        else:
            # Put all parts together again, replacing all simple quotation marks with „ and “ (alternating)
            text = splitted_text[0]
            for counter in range(1, len(splitted_text)):
                text += '„' if counter % 2 == 1 else '“'
                text += splitted_text[counter]
        return text

    def _capitalization_exceptions(self) -> List[str]:
        return ["Z.B.", "z.B.", "ggf.", "Ggf."]

    def _missing_spaces_exceptions(self) -> List[str]:
        return ["1.Mose", "2.Mose", "3.Mose", "4.Mose", "5.Mose", "1.Samuel", "2.Samuel", "1.Könige", "2.Könige",
                "1.Chronik", "2.Chronik", "1.Korinther", "2.Korinther", "1.Thessalonicher", "2.Thessalonicher",
                "1.Timotheus", "2.Timotheus", "1.Petrus", "2.Petrus", "3.Petrus", "1.Johannes", "2.Johannes",
                "z.B.", "Z.B."]
