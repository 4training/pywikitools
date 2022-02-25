import logging
import re

from .base import CorrectorBase
from .universal import UniversalCorrector

class GermanCorrector(CorrectorBase, UniversalCorrector):
    """
    Correct typical German typos. Currently one rule is implemented
    * German quotations start with „ and end with “ („Beispiel“)
    """

    def correct_quotes(self, text: str) -> str:
        """Ensure correct German quotes (example: „korrekt“)"""
        logger = logging.getLogger('pywikitools.correctbot.de')
        pattern = re.compile('[„“”"]')  # Search for all kinds of quotation marks
        quote_counter = 0
        text_as_list = list(text)
        for quote in pattern.finditer(text):
            quote_counter += 1
            pos = quote.start()
            if (pos == 0) or text[pos - 1].isspace():
                # Looks like we found a starting quotation mark
                if (pos + 1 >= len(text)) or text[pos + 1].isspace():
                    # Now we're confused, this seems to be an isolated quotation mark: warn and don't correct
                    logger.warning(f"Found an isolated quotation mark in {text}: Ignoring.")
                    continue
                text_as_list[pos] = '„'
            elif (pos + 1 == len(text)) or text[pos + 1].isspace():
                # Looks like we found an ending quotation mark
                text_as_list[pos] = '“'
            else:
                # Now we're confused, this quotation mark seems to be directly surrounded by chars like th"is
                logger.warning(f"Found a quotation mark surrounded by characters in {text}: Ignoring.")

        if quote_counter % 2 != 0:
            logger.warning(f"Found an uneven amount of quotation marks in {text}. Please check.")
        return "".join(text_as_list)    # convert it back to a string

