#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 19 18:33:53 2021

@author: franz
"""
from .page_wrapper_packer import PageContentWrapper
from .page_wrapper import PageWrapper


class Communicator:
    """Encapsulation for PageContentWrapper class
    """
    __slots__ = ['__webpage_name', '__page_content_wrapper']

    def __init__(self, page_name):
        self.__webpage_name: str = page_name
        self.__page_content_wrapper: PageContentWrapper = PageContentWrapper(page_name)

    def fetch_content(self, language: str) -> PageWrapper:
        """Requests 4training.net-server for content text in given language and wraps the result in a PageContent

        Args:
            language (str): Language of text content to fetch

        Returns:
            PageWrapper: Contains the requested text content and meta data
        """
        return self.__page_content_wrapper.fetch_page_content_from_wiki(language)

    def save_content(self, page_content: PageWrapper) -> None:
        """Saves the content text to 4training.net-server

        Args:
            page_content (PageWrapper): Contains text content to be saved incl. meta data
        """
        self.__page_content_wrapper.save_page_content_to_wiki(page_content)
