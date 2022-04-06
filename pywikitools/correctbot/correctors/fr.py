import logging
import re
from typing import List
from .base import CorrectorBase
from .universal import UniversalCorrector

class FrenchCorrector(CorrectorBase, UniversalCorrector):
    """
    Corrects typical French typos to follow the following rules:
    * False friends (example / exemple)
    * TODO Instead of ellipsis, use "..."
    * Ensure correct French quotation marks: « Foo » (with non-breaking whitespaces \u00a0 before/after the guillemets!)
    """
    def correct_false_friends(self, text: str) -> str:
        """
        Correct typical mistakes
        Currently only one rule:
        "example" is English -> "exemple" is correct French
        """
        return text.replace("example", "exemple").replace("Example", "Exemple")

    def correct_spaces_before_punctuation(self, text: str) -> str:
        """
        Ensure we have non-breaking spaces before : ; ! ? (a specialty of French grammar, different to most languages)
        """
        # Insert missing space if there is none before punctuation
        text = re.sub(r"(\w)([:;!?])", "\\1\u00A0\\2", text)
        # Replace normal space with non-breaking space before punctuation
        text = re.sub(r" ([:;!?])", "\u00A0\\1", text)
        return text

    def correct_quotation_marks(self, text: str) -> str:
        """
        Ensure correct French quotation marks: « Foo »
        (with non-breaking whitespaces \u00a0 before/after the guillemets!)
        """
        logger = logging.getLogger('pywikitools.correctbot.fr')
        if re.match('[„“”]', text):
            logger.warning("Found at least one special quotation mark (one of „“”). Please correct manually.")

        splitted_text: List[str] = re.split('"', text)
        if (len(splitted_text) % 2) != 1:
            logger.warning('Found uneven amount of quotation marks (")! Please correct manually.')
        else:
            # Put all parts together again, replacing all simple quotation marks with « and » (alternating)
            text = splitted_text[0]
            for counter in range(1, len(splitted_text)):
                text += '«' if counter % 2 == 1 else '»'
                text += splitted_text[counter]

        # Now we insert non-breaking spaces if necessary
        text = re.sub('« ', '«\u00A0', text)
        text = re.sub('«([^\s])', '«\u00A0\\1', text)
        text = re.sub(' »', '\u00A0»', text)
        text = re.sub('([^\s])»', '\\1\u00A0»', text)
        return text
