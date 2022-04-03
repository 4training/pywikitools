"""
This module contains correction rules that are used in more than one language:
- UniversalCorrector containing rules that can be applied in all languages
- Corrector classes for groups of languages

Caution: functions in a language-specific corrector must never have the same names as
one of the functions here (otherwise only one of it gets called in the case of multiple inheritance)

Each function should have a documentation string which will be used for print_stats()
"""
import logging
import re

class UniversalCorrector():
    """Has language-independent correction functions"""
    # TODO: Instead of ellipsis (…), use "..." - write a function for it.
    # Should we have that in this class, e.g. do we want this for all languages?

#    def correct_replace_e_with_i(self, text: str) -> str:
#        """TODO for testing only: Replace e with i"""
#        return text.replace("e", "i")

    def correct_wrong_capitalization(self, text: str) -> str:
        """
        Fix wrong capitalization at the beginning of a sentence or after a colon.
        Only do that if our text ends with a dot to avoid correcting single words / short phrases
        """
        # Or to say it differently: the letter following a .!?;: will be capitalized

        # TODO maybe this needs to be cut out of UniversalCorrector into a separate class
        # because there may be languages where this doesn't work

        # TODO: Quotation marks are not yet covered - double check if necessary
        if len(text) > 1:
            find_wrong_capitalization = re.compile(r'[.!?]\s*([a-z])')
            result: str = text
            for match in re.finditer(find_wrong_capitalization, text):
                result = result[:match.end() - 1] + match.group(1).upper() + result[match.end():]
            result = result[0].upper() + result[1:]
            if text.endswith("."):
                return result
            elif result != text:
                logging.getLogger('pywikitools.correctbot.universal').warning(f"Please check capitalization in {text}")
        return text

    def correct_multiple_spaces_also_in_title(self, text: str) -> str:
        """Reduce multiple spaces to one space"""
        check_multiple_spaces = re.compile(r'( ){2,}')
        return re.sub(check_multiple_spaces, ' ', text)

    def correct_missing_spaces(self, text: str) -> str:
        """Insert missing spaces between punctuation and characters"""
        check_missing_spaces = re.compile(r'([.!?;,؛،؟])(\w)')
        return re.sub(check_missing_spaces, r'\1 \2', text)

    def correct_wrong_spaces(self, text: str) -> str:
        """Erase redundant spaces before punctuation"""
        check_wrong_spaces = re.compile(r'\s+([.!?;,؛،؟])')
        return re.sub(check_wrong_spaces, r'\1', text)

    def correct_wrong_dash_also_in_title(self, text: str) -> str:
        """When finding a normal dash ( - ) surrounded by spaces: Make long dash ( – ) out of it"""
        return re.sub(' - ', ' – ', text)

    def correct_missing_final_dot(self, text: str, original: str) -> str:
        """If the original has a trailing dot, the translation also needs one at the end."""
        if original.endswith("."):
            if len(text.strip()) > 1 and not text.strip().endswith("."):
                return text.strip() + "."
        return text

    def make_lowercase_extension_in_filename(self, text: str) -> str:
        """Have file ending in lower case"""
        if len(text) <= 4:
            logging.warning(f"File name too short: {text}")
            return text
        return text[:-4] + text[-4:].lower()

    def remove_spaces_in_filename(self, text: str) -> str:
        """Replace spaces in file name with single underscore"""
        return re.sub(r"( )+", '_', text)

    def remove_multiple_underscores_in_filename(self, text: str) -> str:
        """Replace multiple consecutive underscores with single underscore in file name"""
        return re.sub(r"_+", '_', text)


class RTLCorrector():
    """Corrections for right-to-left languages"""

    def fix_rtl_title(self, text: str) -> str:
        """When title ends with closing parenthesis, add a RTL mark at the end"""
        return re.sub(r'\)$', ')\u200f', text)

    def fix_rtl_filename(self, text: str) -> str:
        """When file name has a closing parenthesis before the file ending, make sure we have a RTL mark afterwards!"""
        return re.sub(r'\)\.([a-z]{3})$', ')\u200f.\\1', text)
