#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 17:59:58 2021

@author: franz
"""
from typing import List, Final
import difflib


class PageWrapper:
    """Struct containing 4training.net page content: full original text, its language and its amount of paragraphs
    """
    __slots__ = ['__original_translations', '__language', '__size', '__corrected_translations']

    # Font color for terminal output
    RED: Final[str] = "\033[0;31m"
    GREEN: Final[str] = "\033[0;32m"
    NO_COLOR: Final[str] = "\033[0m"

    def __init__(self, page: List[str], language: str, size: int) -> None:
        self.__original_translations: List[str] = page
        self.__language: str = language
        self.__size: int = size
        self.__corrected_translations: List[str] = page

    @property
    def original_translations(self) -> List[str]:
        """
        Returns list of unchanged paragraphs
        """
        return self.__original_translations

    @property
    def language(self) -> str:
        """
        Returns language of the paragraphs
        """
        return self.__language

    @property
    def size(self) -> int:
        """
        Returns amount of contained paragraphs
        """
        return self.__size

    @property
    def corrected_translations(self) -> List[str]:
        """
        Returns list of changed paragraphs
        """
        return self.__corrected_translations

    def set_corrected_translations(self, trans: List[str]):
        """
        TODO is there a better way to do this?
        """
        self.__corrected_translations = trans

    @property
    def is_modified(self) -> bool:
        """
        Returns true if pageWrapper is modified, otherwise returns false
        """
        return self.__original_translations != self.__corrected_translations

    def print_diff(self) -> None:
        """
        If pageWrapper got modified, prints differences: deletions in red, insertions in green
        """
        diffs: str = ""
        for counter in range(self.__size):
            original_paragraph = self.__original_translations[counter]
            corrected_paragraph = self.__corrected_translations[counter]

            if self.is_modified:
                seq_mat = difflib.SequenceMatcher(a=original_paragraph, b=corrected_paragraph, autojunk=True)
                diff_list: List[str] = [""]
                for operation, orig_start, orig_end, fixed_start, fixed_end in seq_mat.get_opcodes():
                    if operation == "delete":
                        deleted_text: str = original_paragraph[orig_start:orig_end]
                        diff_list.append(self.RED + "{" + deleted_text + ",}" + self.NO_COLOR)
                    elif operation == "replace":
                        deleted_text: str = original_paragraph[orig_start:orig_end]
                        inserted_text: str = corrected_paragraph[fixed_start:fixed_end]
                        diff_list.append(self.RED + "{" + deleted_text + ",")
                        diff_list.append(self.GREEN + inserted_text + "}" + self.NO_COLOR)
                    elif operation == "insert":
                        inserted_text: str = corrected_paragraph[fixed_start:fixed_end]
                        diff_list.append(self.GREEN + "{" + inserted_text + "}" + self.NO_COLOR)
                    elif operation == "equal":
                        diff_list.append(corrected_paragraph[fixed_start:fixed_end])

                diffs += "".join(diff_list) + "\n\n"
        if not diffs:
            print(F"No difference found. Nothing to save.")
        else:
            print(diffs)
