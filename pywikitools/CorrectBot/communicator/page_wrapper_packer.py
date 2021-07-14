#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 18:49:47 2021

@author: franz
"""
from .page_wrapper import PageWrapper
from .server_communicator import ServerCommunicator
import logging
from typing import Final, List
import re
import sys

Logger = logging.getLogger("PageContentWrapper")


class PageContentWrapper:
    """Wraps requested page content from server language independently and unwraps it for saving to server
    """
    __slots__ = ['__server_communicator', '__page_name']

    PATTERN_CONTENT_UNIT: Final[str] = r'<translate>.*?<!--T:(\d\d?)-->\s([\s\S])+?(?=</translate>)'

    def __init__(self, page_name):
        self.__server_communicator: ServerCommunicator = ServerCommunicator()
        self.__page_name: str = page_name

    def __request_text_from_server(self, address: str) -> str:
        return self.__server_communicator.request_text_from_server(address)

    def __send_text_to_server(self, address: str, paragraph: str) -> None:
        return self.__server_communicator.send_text_to_server(address, paragraph)

    @staticmethod
    def __get_number_of_paragraphs(page: str) -> int:
        """Get number of paragraphs found in full text content

        Args:
            page (str): Full text to be examined

        Returns:
            int: Number of paragraphs
        """
        return int(list(re.finditer(PageContentWrapper.PATTERN_CONTENT_UNIT, page))[-1].group(1))

    @staticmethod
    def __sanity_check(expected_amount_of_paragraphs, real_amount_of_paragraphs) -> None:
        """Sanity check of expected amount of paragraphs matches to real amount of paragraphs

        Args:
            expected_amount_of_paragraphs ([type]): expected amount of fetched paragraphs
            real_amount_of_paragraphs ([type]): real amount of fetched paragraphs
        """
        if expected_amount_of_paragraphs != real_amount_of_paragraphs:
            logging.fatal(
                F"Problem while parsing the content. Some text got lost.\n"
                F"Expected {expected_amount_of_paragraphs} paragraphs, but only found {real_amount_of_paragraphs}.")
            sys.exit(1)

    def __get_extracted_paragraphs_from_wiki_text(self, language: str, number_of_paragraphs: int) -> List[str]:
        """Extracts language independently paragraphs from requested wiki page

        Args:
            language (str): language of page text
            number_of_paragraphs (int): amount of paragraphs to be expected

        Returns:
            List[str]: Listed paragraphs
        """
        if len(language) != 2:
            Logger.fatal("Unknown language code")
            sys.exit(1)

        page_of_units: List[str] = []
        if language != "en":
            for counter in range(number_of_paragraphs):
                address: str = F"Translations:{self.__page_name}/{counter + 1}/{language}"
                page_unit: str = self.__request_text_from_server(address)
                page_of_units.append(page_unit)
        else:
            full_content: str = self.__request_text_from_server(self.__page_name)
            pattern = re.finditer(PageContentWrapper.PATTERN_CONTENT_UNIT, full_content, re.MULTILINE | re.ASCII)
            for matched_paragraph in list(pattern):
                page_of_units.append(matched_paragraph.group(2))
            self.__sanity_check(len(page_of_units), number_of_paragraphs)
        return page_of_units

    def fetch_page_content_from_wiki(self, language: str) -> PageWrapper:
        """Fetches content from 4training.net-wiki and wraps its content to a PageContent. 
        Distinguishes between translations and original version (english)

        Args:
            language (str): language of text content

        Returns:
            PageWrapper: Wrapper with text content and meta info
        """
        page_content: str = self.__request_text_from_server(self.__page_name)
        number_of_paragraphs: int = self.__get_number_of_paragraphs(page_content)
        paragraphs: List[str] = self.__get_extracted_paragraphs_from_wiki_text(language, number_of_paragraphs)

        return PageWrapper(paragraphs, language, number_of_paragraphs)

    def save_page_content_to_wiki(self, page_content: PageWrapper) -> None:
        """Saves content to 4training.net-wiki. Distinguishes between translations and original version (english)

        Args:
            page_content (PageWrapper): Wrapper containing text content and meta info
        """
        if page_content.language != "en":
            for counter in range(page_content.size):
                original_paragraph = page_content.original_translations[counter]
                fixed_content: str = page_content.corrected_translations[counter]
                if fixed_content != original_paragraph:
                    address: str = F"Translations:{self.__page_name}/{counter + 1}/{page_content.language}"
                    self.__send_text_to_server(address, fixed_content)
        else:
            address: str = self.__page_name
            full_content: str = self.__request_text_from_server(address)
            for counter in range(page_content.size):
                original_paragraph: str = page_content.original_translations[counter]
                fixed_content: str = page_content.corrected_translations[counter]
                if fixed_content != original_paragraph:
                    full_content = full_content.replace(original_paragraph, fixed_content)
            self.__send_text_to_server(address, full_content)
