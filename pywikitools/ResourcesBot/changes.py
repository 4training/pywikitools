"""
Contains the classes ChangeType, ChangeItem and ChangeLog that describe the list of changes on the 4training.net website
since the last run of the resourcesbot.
"""
from enum import Enum
from typing import List, Set

class ChangeType(Enum):
    """
    The different types of changes that can happen.
    Normally there wouldn't be any deletions
    """
    NEW_WORKSHEET = 'new worksheet'
    NEW_PDF = 'new PDF'
    NEW_ODT = 'new ODT'
    UPDATED_WORKSHEET = 'updated worksheet'
    UPDATED_PDF = 'updated PDF'
    UPDATED_ODT = 'updated ODT'
    DELETED_WORKSHEET = 'deleted worksheet'
    DELETED_PDF = 'deleted PDF'
    DELETED_ODT = 'deleted ODT'

class ChangeItem:
    """
    Holds the details of one change
    This shouldn't be modified after creation (is there a way to enforce that?)
    """
    __slots__ = ['lang', 'worksheet', 'change_type']
    def __init__(self, lang: str, worksheet: str, change_type: ChangeType):
        self.lang = lang
        self.worksheet = worksheet
        self.change_type = change_type

    def __str__(self):
        return f"{self.change_type}: {self.worksheet}/{self.lang}"

class ChangeLog:
    """
    Holds all changes that happened since the last resourcesbot run
    """
    def __init__(self):
        self._changes: List[ChangeItem] = []
        self._affected_langs: Set[str] = set()

    def add_change(self, lang:str, worksheet: str, change_type: ChangeType):
        change_item = ChangeItem(lang, worksheet, change_type)
        self._changes.append(change_item)
        self._affected_langs.add(lang)

    def is_empty(self):
        return len(self._changes) == 0

    def is_language_affected(self, lang: str):
        """ Are there any changes in this language? """
        return lang in self._affected_langs

    def get_affected_languages(self) -> Set[str]:
        return self._affected_langs

    def get_all_changes(self) -> List[ChangeItem]:
        return self._changes
