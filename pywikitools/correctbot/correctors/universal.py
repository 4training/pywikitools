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
from typing import List

from pywikitools.correctbot.correctors.base import suggest_only, use_snippets


class UniversalCorrector():
    """Has language-independent correction functions"""
    # TODO: Instead of ellipsis (…), use "..." - write a function for it.
    # Should we have that in this class, e.g. do we want this for all languages?

#    def correct_replace_e_with_i(self, text: str) -> str:
#        """TODO for testing only: Replace e with i"""
#        return text.replace("e", "i")

    @suggest_only
    @use_snippets
    def correct_wrong_capitalization(self, text: str) -> str:
        """Fix wrong capitalization at the beginning of a sentence or after a colon.
        Only do that if our text ends with a dot to avoid correcting single words / short phrases
        """
        # Or to say it differently: the letter following a .!?;: will be capitalized

        # TODO maybe this needs to be cut out of UniversalCorrector into a separate class
        # because there may be languages where this doesn't work

        # TODO: Quotation marks are not yet covered - double check if necessary
        if len(text) <= 1:
            return text
        find_wrong_capitalization = re.compile(r'[.!?]\s*([a-z])')
        result: str = text
        for match in re.finditer(find_wrong_capitalization, text):
            result = result[:match.end() - 1] + match.group(1).upper() + result[match.end():]
        result = result[0].upper() + result[1:]
        return result

    @suggest_only
    def correct_multiple_spaces_also_in_title(self, text: str) -> str:
        """Reduce multiple spaces to one space"""
        check_multiple_spaces = re.compile(r'( ){2,}')
        return re.sub(check_multiple_spaces, ' ', text)

    @suggest_only
    def correct_missing_spaces(self, text: str) -> str:
        """Insert missing spaces between punctuation and characters"""
        # not including : and ; because that would give too many false positives from definition lists
        check_missing_spaces = re.compile(r'([.!?,؛،؟])([\w])')
        # As we need to check for exceptions (surrounded by digits), it's a bit complicated. Otherwise it'd be just
        # return re.sub(check_missing_spaces, r'\1 \2', text)
        last_start_pos = 0              # necessary to not run into endless loops
        while match := check_missing_spaces.search(text, last_start_pos):
            if match.start(1) == 0:     # it would be strange if our text directly started with a punctuation mark.
                last_start_pos += 1     # also the following if statement would raise an IndexError
                continue
            if match.string[match.start(1) - 1].isdigit() and match.group(2).isdigit():
                # Exception: Don't correct if punctuation mark is directly between characters
                # (this is most likely used in a Bible reference like John 3:16 and should not be corrected)
                last_start_pos = match.end(2)
                continue
            text = text[:match.end(1)] + " " + text[match.start(2):]    # match.expand(r"\1 \2")
            last_start_pos = match.end(2) + 1   # +1 because we inserted a space

        return text

    def correct_spaces_before_comma_and_dot(self, text: str) -> str:
        """Erase redundant spaces before commas and dots"""
        # basically we check for r' +([.,])'.
        # We want to allow "I forgive ___ ." so we add [^_] in the beginning
        # But we don't want to capture ... so we add [^.] in the end
        # Now we would miss "end ." so we add the alternative with |
        check_wrong_spaces = re.compile(r'([^_]) +([.,])$|([^_]) +([.,])([^.])')
        return re.sub(check_wrong_spaces, r'\1\2\3\4\5', text)

    def correct_wrong_dash_also_in_title(self, text: str) -> str:
        """When finding a normal dash ( - ) surrounded by spaces: Make long dash ( – ) out of it"""
        return re.sub(' - ', ' – ', text)

    @suggest_only
    @use_snippets
    def correct_missing_final_dot(self, text: str, original: str) -> str:
        """If the original has a trailing dot, the translation also needs one at the end."""
        if original.endswith("."):
            if len(text.strip()) > 1 and not text.strip().endswith("."):
                return text.strip() + "."
        return text

    def correct_mediawiki_bold_italic(self, text: str) -> str:
        """Replace mediawiki formatting '''bold''' with <b>bold</b> and ''italic'' with <i>italic</i>"""
        # Three times doing almost the same but order is important: We need to start with the longest search string
        # So first correcting ''''', then ''' and finally '' - is a shorter implementation possible?

        # Replacing ''''' (bold and italic)
        splitted_text: List[str] = re.split("'''''", text)
        if (len(splitted_text) % 2) != 1:   # Not an even amount of ''''': we don't do anything
            logger = logging.getLogger(__name__)
            logger.warning(f"Found uneven amount of bold italic formatting (''''') Please correct manually: {text}")
        else:
            # Put all parts together again, replacing ''''' with <b><i> and </i></b> (alternating)
            text = splitted_text[0]
            for counter in range(1, len(splitted_text)):
                text += '<b><i>' if counter % 2 == 1 else '</i></b>'
                text += splitted_text[counter]

        # Replacing ''' (bold)
        splitted_text = re.split("'''", text)
        if (len(splitted_text) % 2) != 1:   # Not an even amount of ''': we don't do anything
            logger = logging.getLogger(__name__)
            logger.warning(f"Found uneven amount of bold formatting (''') Please correct manually: {text}")
        else:
            # Put all parts together again, replacing ''' with <b> and </b> (alternating)
            text = splitted_text[0]
            for counter in range(1, len(splitted_text)):
                text += '<b>' if counter % 2 == 1 else '</b>'
                text += splitted_text[counter]

        # Replacing '' (italic)
        splitted_text = re.split("''", text)
        if (len(splitted_text) % 2) != 1:   # Not an even amount of '': we don't do anything
            logger = logging.getLogger(__name__)
            logger.warning(f"Found uneven amount of italic formatting ('') Please correct manually: {text}")
        else:
            # Put all parts together again, replacing '' with <i> and </i> (alternating)
            text = splitted_text[0]
            for counter in range(1, len(splitted_text)):
                text += '<i>' if counter % 2 == 1 else '</i>'
                text += splitted_text[counter]
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


class NoSpaceBeforePunctuationCorrector():
    """
    This is an extra class only for !?:; punctuation marks that must not be preceded by a space.
    Removing spaces before comma and dot is already covered by UniversalCorrector.correct_spaces_before_comma_and_dot()
    This class is extra as e.g. French requires non-breaking spaces before them
    (in contrast to most other languages which have no spaces before these punctuation marks as well)
    """
    def correct_no_spaces_before_punctuation(self, text: str) -> str:
        """Erase redundant spaces before punctuation marks."""
        # Having things like ... ? is okay so we add [^.…_] in the beginning
        check_wrong_spaces = re.compile(r'([^.…_]) +([!?;:])')
        return re.sub(check_wrong_spaces, r'\1\2', text)


class RTLCorrector():
    """Corrections for right-to-left languages"""

    def correct_wrong_spaces_in_rtl(self, text: str) -> str:
        """Erase redundant spaces before RTL punctuation marks"""
        check_wrong_spaces = re.compile(r'\s+([؛،؟])')
        return re.sub(check_wrong_spaces, r'\1', text)

    def fix_rtl_title(self, text: str) -> str:
        """When title ends with closing parenthesis, add a RTL mark at the end"""
        return re.sub(r'\)$', ')\u200f', text)

    def fix_rtl_filename(self, text: str) -> str:
        """When file name has a closing parenthesis before the file ending, make sure we have a RTL mark afterwards!"""
        return re.sub(r'\)\.([a-z]{3})$', ')\u200f.\\1', text)
