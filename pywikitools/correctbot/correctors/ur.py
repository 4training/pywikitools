import re
from typing import List

from .base import CorrectorBase, use_snippets
from .universal import QuotationMarkCorrector, RTLCorrector, UniversalCorrector

# Characters that aren't part of the Urdu alphabet but are easily typed by mistake
# (they look similar and are on Arabic / Persian keyboard layouts) -> their Urdu counterparts
_URDU_CHARACTERS = str.maketrans(
    {
        "ك": "ک",  # ARABIC LETTER KAF (ك) -> ARABIC LETTER KEHEH (ک)
        "ي": "ی",  # ARABIC LETTER YEH (ي) -> ARABIC LETTER FARSI YEH (ی)
        "ى": "ی",  # ARABIC LETTER ALEF MAKSURA (ى) -> ARABIC LETTER FARSI YEH (ی)
        "ه": "ہ",  # ARABIC LETTER HEH (ه) -> ARABIC LETTER HEH GOAL (ہ)
    }
)

# Letters and diacritics of the Urdu alphabet (excluding digits, punctuation and the full stop ۔)
_URDU_LETTERS: str = "ؠ-ٟٮ-ۓەۺ-ۿ"

# What can stand directly before the full stop at the end of an Urdu sentence:
# an Urdu letter or a closing quotation mark / bracket
_URDU_SENTENCE_END: str = f"[{_URDU_LETTERS}“”»)\\]]"


class UrduCorrector(
    CorrectorBase, UniversalCorrector, RTLCorrector, QuotationMarkCorrector
):
    """
    Correct Urdu typos:
    * Urdu quotations start with ” and end with “
    * Urdu sentences end with the Urdu full stop (۔) and not with a dot
    * Characters not existing in Urdu (ك ي ى ه) get replaced by their Urdu counterpart (ک ی ی ہ)
    * Common corrections from UniversalCorrector and RTLCorrector
    """

    def correct_quotes(self, text: str) -> str:
        """Ensure correct Urdu quotes (example: ”اردو“)

        Like in Arabic it must be this way round because ” and “ are not mirrored characters
        in unicode, so in RTL ” comes first and “ at the end (see TestUrduCorrector)
        """
        return self._correct_quotes("”", "“", text)

    def correct_urdu_characters_also_in_title(self, text: str) -> str:
        """Replace characters not existing in Urdu (ك ي ى ه) with their Urdu counterpart (ک ی ی ہ)

        These Arabic characters look very similar to the Urdu ones but are different code points,
        so they break searching and spell checking. They're not part of the Urdu alphabet,
        so any occurrence of them is a typing mistake (except in Arabic quotations).
        """
        return text.translate(_URDU_CHARACTERS)

    def correct_missing_space_after_urdu_full_stop(self, text: str) -> str:
        """Insert missing space after an Urdu full stop (۔)

        correct_missing_spaces() of UniversalCorrector doesn't cover the Urdu full stop
        """
        return re.sub(r"۔(?=\w)", "۔ ", text)

    @use_snippets
    def correct_urdu_full_stop(self, text: str) -> str:
        """Use the Urdu full stop (۔) at the end of a sentence instead of a dot (.)

        Only dots directly following an Urdu letter (or a closing quotation mark / bracket)
        and ending a sentence are affected, so dots in numbers, file names, links,
        numbered lists or Latin text are left alone.
        This runs before correct_missing_final_dot() of UniversalCorrector (which only makes
        suggestions), so that one sees the Urdu full stop and doesn't add another one.
        """
        return re.sub(rf"(?<={_URDU_SENTENCE_END})\.(?=\s|$)", "۔", text)

    def remove_trailing_urdu_full_stop_in_title(self, text: str) -> str:
        """Remove trailing Urdu full stop (۔) in a worksheet title"""
        if text.endswith("۔"):
            return text[:-1]
        return text

    def _final_punctuation(self) -> str:
        return "۔"

    def _suffix_for_print_version(self) -> str:
        return "_print"  # TODO

    def _capitalization_exceptions(self) -> List[str]:
        return []

    def _missing_spaces_exceptions(self) -> List[str]:
        return []
