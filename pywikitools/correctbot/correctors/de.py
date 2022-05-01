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
            logger = logging.getLogger('pywikitools.correctbot.de')
            logger.warning(f'Found uneven amount of quotation marks (")! Please correct manually: {text}')
        else:
            # Put all parts together again, replacing all simple quotation marks with „ and “ (alternating)
            text = splitted_text[0]
            for counter in range(1, len(splitted_text)):
                text += '„' if counter % 2 == 1 else '“'
                text += splitted_text[counter]
        return text
