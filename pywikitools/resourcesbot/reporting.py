"""
Contains the data-structures and main methods for the reporting.
Through reporting, the ressources-bot keeps track of what it did.
This information can then be made available to people who need to know what is going on.
"""

from abc import ABC, abstractmethod
from typing import Dict, List


class LanguageReport(ABC):
    """
    Basic data structure for the report of one module running once for one language.
    """

    def __init__(self, language_code: str):
        self.language = language_code
        self.summary_text = ""

    def was_anything_to_report(self) -> bool:
        return self.summary_text != ""

    @abstractmethod
    def get_summary(self) -> str:
        return self.summary_text

    @classmethod
    @abstractmethod
    def get_module_name(cls) -> str:
        return ""

    @classmethod
    @abstractmethod
    def get_module_summary(cls, lang_reports: list) -> str:
        if len(lang_reports) == 0:
            return ""
        else:
            return f"Ran module {cls.get_module_name()} for {len(lang_reports)} languages"


def print_summaries(module_reports: Dict[str, List[LanguageReport]]):
    for key, value in module_reports.items():
        if len(value) == 0:
            print(f"Module {key}: Empty Report")
        else:
            print(f"Module {key}'s report: {type(value[0]).get_module_summary(value)}")
