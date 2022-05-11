"""
Contains the classes ChangeType, ChangeItem and ChangeLog that describe the list of changes on the 4training.net website
since the last run of the resourcesbot.
"""
from enum import Enum
from typing import List


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
    __slots__ = ['worksheet', 'change_type']

    def __init__(self, worksheet: str, change_type: ChangeType):
        self.worksheet = worksheet
        self.change_type = change_type

    def __str__(self) -> str:
        return f"{self.change_type}: {self.worksheet}"

    def __eq__(self, other) -> bool:
        return self.worksheet == other.worksheet and self.change_type == other.change_type

    def __hash__(self) -> int:
        return hash((self.worksheet, self.change_type))


class ChangeLog:
    """
    Holds all changes that happened in one language since the last resourcesbot run
    """
    __slots__ = ['_changes', '_iterate_pos']

    def __init__(self):
        self._changes: List[ChangeItem] = []
        self._iterate_pos: int = 0

    def add_change(self, worksheet: str, change_type: ChangeType):
        change_item = ChangeItem(worksheet, change_type)
        self._changes.append(change_item)

    def is_empty(self):
        return len(self._changes) == 0

    def count_changes(self) -> int:
        return len(self._changes)

    def __str__(self) -> str:
        output = ""
        for change_item in self._changes:
            output += f"{change_item}\n"
        return output

    def __iter__(self):
        """Make this class iterable in a simple way (not suitable for concurrency!)"""
        self._iterate_pos = 0
        return self

    def __next__(self) -> ChangeItem:
        """Return a next ChangeItem"""
        while self._iterate_pos < len(self._changes):
            self._iterate_pos += 1
            return self._changes[self._iterate_pos - 1]
        raise StopIteration
