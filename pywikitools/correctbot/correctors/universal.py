"""
This module contains correction rules that are used in more than one language:
- UniversalCorrector containing rules that can be applied in all languages
- Corrector classes for groups of languages

Caution: functions in a language-specific corrector must never have the same names as
one of the functions here (otherwise only one of it gets called in the case of multiple inheritance)

Each function should have a documentation string which will be used for print_stats()
"""
from abc import ABC, abstractmethod
import logging
import re
from typing import List, Match

from pywikitools.correctbot.correctors.base import suggest_only, use_snippets


class UniversalCorrector(ABC):
    """Has language-independent correction functions"""
    # TODO: Instead of ellipsis (…), use "..." - write a function for it.
    # Should we have that in this class, e.g. do we want this for all languages?

#    def correct_replace_e_with_i(self, text: str) -> str:
#        """TODO for testing only: Replace e with i"""
#        return text.replace("e", "i")

    @abstractmethod
    def _capitalization_exceptions(self) -> List[str]:
        """Define exceptions to the following function correct_wrong_capitalization()

        You need to implement this for every language-specific class (that wants to use UniversalCorrector)
        Returns:
            A list of short strings where directly afterwards capitalization shouldn't get corrected
        """
        return []

    @suggest_only
    @use_snippets
    def correct_wrong_capitalization(self, text: str) -> str:
        """Fix wrong capitalization at the beginning of a sentence or after a colon.

        Only do that if our text ends with a dot to avoid correcting single words / short phrases
        Don't correct if it's after a string defined in _capitalization_exceptions().
        """
        # Or to say it differently: the letter following a .!?;: will be capitalized

        # TODO maybe this needs to be cut out of UniversalCorrector into a separate class
        # because there may be languages where this doesn't work

        # TODO: Quotation marks are not yet covered - double check if necessary
        def is_exception(punctuation_pos: int):
            """Is the punctuation found in text at position punctuation_pos part of an exception?"""
            nonlocal text
            for exception in self._capitalization_exceptions():
                # Example: text = "Use e.g. tests" and exception = "e.g."
                # Then is_exception(5) and is_exception(7) both return True as both dots are part of an exception
                for punctuation_match in re.finditer(re.compile(r'[.!?]'), exception):
                    start_pos = punctuation_pos - punctuation_match.start(0)
                    end_pos = start_pos + len(exception)
                    if start_pos >= 0 and len(text) > end_pos and text[start_pos:end_pos] == exception:
                        return True
            return False

        if len(text) <= 1:
            return text
        find_wrong_capitalization = re.compile(r'[.!?]\s*([a-z])')
        result: str = text
        for match in re.finditer(find_wrong_capitalization, text):
            if is_exception(match.start(0)):
                continue
            result = result[:match.end() - 1] + match.group(1).upper() + result[match.end():]
        result = result[0].upper() + result[1:]
        return result

    @suggest_only
    def correct_multiple_spaces_also_in_title(self, text: str) -> str:
        """Reduce multiple spaces to one space"""
        check_multiple_spaces = re.compile(r'( ){2,}')
        return re.sub(check_multiple_spaces, ' ', text)

    @abstractmethod
    def _missing_spaces_exceptions(self) -> List[str]:
        """Define exceptions to the following function correct_missing_spaces()

        You need to implement this for every language-specific class (that wants to use UniversalCorrector)
        Returns:
            A list of strings that correct_missing_spaces() won't correct
        """
        return []

    def correct_missing_spaces(self, text: str) -> str:
        """Insert missing spaces between punctuation and characters

        Exceptions are punctuation marks between digits (as in John 3:16) and those
        defined by a language in _missing_spaces_exceptions()"""
        # not including : and ; because that would give too many false positives from definition lists
        check_missing_spaces = re.compile(r'([.!?,؛،؟])([\w])')
        # As we need to check for exceptions (surrounded by digits and custom list), it's a bit complicated.
        # Otherwise it'd be just
        # return re.sub(check_missing_spaces, r'\1 \2', text)
        last_start_pos = 0              # necessary to not run into endless loops

        def does_match_exception(match: Match) -> bool:
            nonlocal check_missing_spaces, text, last_start_pos
            for exception in self._missing_spaces_exceptions():
                exception_match = check_missing_spaces.search(exception)
                if not exception_match:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Ignoring wrong exception '{exception}' for correct_missing_spaces()")
                    return False
                start_pos = match.start(1) - exception_match.start(1)
                end_pos = start_pos + len(exception)
                if (start_pos >= 0) and (end_pos <= len(text)) and (text[start_pos:end_pos] == exception):
                    last_start_pos = end_pos
                    return True
            return False

        while match := check_missing_spaces.search(text, last_start_pos):
            if match.start(1) == 0:     # it would be strange if our text directly started with a punctuation mark.
                last_start_pos += 1     # also the following if statement would raise an IndexError
                continue
            if match.string[match.start(1) - 1].isdigit() and match.group(2).isdigit():
                # Exception: Don't correct if punctuation mark is directly between characters
                # (this is most likely used in a Bible reference like John 3:16 and should not be corrected)
                last_start_pos = match.end(2)
                continue
            if does_match_exception(match):
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
            logging.getLogger(__name__).warning(f"File name too short: {text}")
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


class QuotationMarkCorrector(ABC):
    """Ensure correct starting and ending quotation marks

    This can be used for any language where we just need to define which characters are used
    for the start and the end of a quotation.
    (For more complex rules like in French involving non-breaking spaces you can't use this class)

    To use it, implement a function that calls _correct_quotes() with the right quotation mark for start and end.
    Example for Spanish:
    def correct_quotes(self, text: str) -> str:
        return self._correct_quotes('“', '”', text)
    """

    def _correct_quotes(self, start_quotation_mark: str, end_quotation_mark: str, text: str) -> str:
        """Correct quotation marks: Ensure correct starting and ending quotation mark

        We do this by replacing all of „“”" with start and end quotation mark (alternating).
        This only works if we have an even amount of quotation marks. If not, we issue a warning
        and don't change anything.

        Args:
            start_quotation_mark: The character used at the start of a quotation
            end_quotation_mark: The character used at the end of a quotation
        """
        splitted_text: List[str] = re.split('[„“”"]', text)
        if (len(splitted_text) % 2) != 1:   # Not an even amount of quotes: we don't do anything
            logger = logging.getLogger(__name__)
            logger.warning(f'Found uneven amount of quotation marks (")! Please correct manually: {text}')
        else:
            # Put all parts together again, replacing all simple quotation marks
            text = splitted_text[0]
            for counter in range(1, len(splitted_text)):
                text += start_quotation_mark if counter % 2 == 1 else end_quotation_mark
                text += splitted_text[counter]
        return text


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

    def correct_punctuation(self, text: str) -> str:
        """Replace normal comma, semicolon, question mark with RTL version of it"""
        text = text.replace(",", "،")
        text = text.replace("?", "؟")
        # Replace semicolon only if it's after a character or a space (not at the beginning of a line)
        return re.sub(r"([\w ])[;]", "\\1؛", text)
