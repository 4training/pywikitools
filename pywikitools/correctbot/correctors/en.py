import re
from .base import CorrectorBase
from .universal import UniversalCorrector


class EnglishCorrector(CorrectorBase, UniversalCorrector):
    """
    Corrects typical English typos to follow the following rules:
    * TODO: No plain quotation marks: instead of "Foo" use “Foo”
    * TODO: No German quotation marks
      * “ must be at the beginning of a word, not at the end as in German (check for trailing whitespace?)
    * Substitute wrong apostrophe
    """

    def correct_single_apostrophe(self, text: str) -> str:
        """Correct single apostrophe ' with ’"""
        # TODO what if we have ''/''' as markup for italics/bold in text?
        return re.sub("'", '’', text)

    # TODO: Count appearances of german, english quotation marks
    # TODO: parse text from left to right and replace odd appearences with “ and even ones with ”
