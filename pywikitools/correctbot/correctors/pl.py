import logging
import re
from typing import List

from .base import CorrectorBase
from .universal import NoSpaceBeforePunctuationCorrector, UniversalCorrector


class PolishCorrector(CorrectorBase, UniversalCorrector, NoSpaceBeforePunctuationCorrector):
    """
    Correct typical Polish typos. Currently one rule is implemented
    * Polish quotations start with „ and end with ”
    """
    def correct_quotes(self, text: str) -> str:
        """Ensure correct Polish quotes (example: „poprawny”)"""
        # This code is taken from the GermanCorrector (just that the ending quote is different)
        # TODO: create some way to reduce code redundancy
        splitted_text: List[str] = re.split('[„“”"]', text)
        if (len(splitted_text) % 2) != 1:   # Not an even amount of quotes: we don't do anything
            logger = logging.getLogger(__name__)
            logger.warning(f'Found uneven amount of quotation marks (")! Please correct manually: {text}')
        else:
            # Put all parts together again, replacing all simple quotation marks with „ and ” (alternating)
            text = splitted_text[0]
            for counter in range(1, len(splitted_text)):
                text += '„' if counter % 2 == 1 else '”'
                text += splitted_text[counter]
        return text

    def _capitalization_exceptions(self) -> List[str]:
        return []

    def _missing_spaces_exceptions(self) -> List[str]:
        return []
